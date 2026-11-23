"""Celery task that runs the full analysis pipeline for one email scan."""

from __future__ import annotations

import asyncio
import base64
import uuid

from loguru import logger
from sqlalchemy import delete, select

from app.database import async_session_factory
from app.models.ioc import EmailIoc
from app.models.scan import (
    AiAnalysis,
    AttachmentAnalysis,
    EmailScan,
    HeaderAnalysis,
    RiskLevel,
    ScanStatus,
    SeverityLevel,
    UrlAnalysis,
)
from app.services.ai_engine import AIEngine
from app.services.ioc_extractor import IocExtractor
from app.services.threat_intel.manager import ThreatIntelManager
from app.workers.celery_app import celery_app

ai_engine = AIEngine()
ioc_extractor = IocExtractor()
threat_intel_manager = ThreatIntelManager()


def _risk_level(score: float) -> RiskLevel:
    if score > 75:
        return RiskLevel.high
    if score > 40:
        return RiskLevel.suspicious
    if score > 15:
        return RiskLevel.low
    return RiskLevel.safe


def _attachments_from_scan(scan: EmailScan) -> list[dict]:
    out = []
    for meta in (scan.mime_structure or {}).get("attachments", []) or []:
        item = dict(meta)
        head = item.pop("head_b64", "")
        try:
            item["head"] = base64.b64decode(head) if head else b""
        except Exception:
            item["head"] = b""
        out.append(item)
    return out


async def _clear_previous_results(session, scan_id: uuid.UUID) -> None:
    """Make re-scans idempotent (several tables have unique scan_id constraints)."""
    for model in (HeaderAnalysis, UrlAnalysis, AttachmentAnalysis, AiAnalysis, EmailIoc):
        await session.execute(delete(model).where(model.scan_id == scan_id))


async def async_process_scan(scan_id: str) -> None:
    async with async_session_factory() as session:
        scan = (await session.execute(select(EmailScan).where(EmailScan.id == uuid.UUID(scan_id)))).scalar_one_or_none()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return

        try:
            scan.status = ScanStatus.analyzing
            await _clear_previous_results(session, scan.id)
            await session.commit()

            from app.services.email_parser import _extract_urls

            extracted_urls = list(dict.fromkeys(_extract_urls(scan.body_text or "") + _extract_urls(scan.body_html or "")))
            attachments = _attachments_from_scan(scan)

            parsed_email = {
                "subject": scan.subject,
                "sender_address": scan.sender_address,
                "sender_display_name": scan.sender_display_name,
                "reply_to": scan.reply_to,
                "return_path": scan.return_path,
                "recipient": scan.recipient,
                "body_text": scan.body_text,
                "body_html": scan.body_html,
                "urls": extracted_urls[:200],
                "attachments": attachments,
                "raw_headers": scan.raw_headers,
                "parsed_headers": scan.parsed_headers or {},
            }

            # IOCs + threat intel
            iocs = ioc_extractor.extract(scan_id=scan_id, parsed_email=parsed_email)
            session.add_all(iocs)
            threat_intel_results = await threat_intel_manager.analyze_iocs(iocs)
            await session.commit()

            # Rule-based detections
            from app.detections.engine import DetectionEngine

            detections = DetectionEngine().run_detections(scan)
            scan.detections = [d.model_dump() for d in detections]

            # Multi-signal analysis
            results = await ai_engine.analyze(parsed_email, threat_intel=threat_intel_results, detections=scan.detections)

            h_res = results.get("header_analysis", {}) or {}
            session.add(HeaderAnalysis(
                scan_id=scan.id,
                spf_pass=h_res.get("spf_pass"),
                spf_result=str(h_res.get("spf_result", "none"))[:50],
                dkim_pass=h_res.get("dkim_pass"),
                dkim_result=str(h_res.get("dkim_result", "none"))[:50],
                dmarc_pass=h_res.get("dmarc_pass"),
                dmarc_result=str(h_res.get("dmarc_result", "none"))[:50],
                sender_spoofed=bool(h_res.get("sender_spoofed", False)),
                display_name_impersonation=bool(h_res.get("display_name_impersonation", False)),
                domain_mismatch=bool(h_res.get("domain_mismatch", False)),
                trust_score=float(h_res.get("trust_score", 100.0)),
                evidence=h_res.get("evidence"),
            ))

            # URL analyses — every extracted URL, enriched with intel where available
            phishing_matches = threat_intel_results.get("phishing_matches", {}) or {}
            url_details = {u.get("original_url"): u for u in (results.get("url_analysis", {}) or {}).get("analyses", []) if isinstance(u, dict)}
            for url in extracted_urls[:200]:
                intel = phishing_matches.get(url) if isinstance(phishing_matches.get(url), dict) else {}
                detail = url_details.get(url, {})
                domain = url.split("/")[2] if "//" in url else url.split("/")[0]
                session.add(UrlAnalysis(
                    scan_id=scan.id,
                    original_url=url[:2048],
                    domain=domain[:255],
                    tld=(domain.rsplit(".", 1)[-1] if "." in domain else "")[:20],
                    is_shortened=bool(detail.get("is_shortened", False)),
                    is_homoglyph=bool(detail.get("is_homoglyph", False)),
                    is_typosquatting=bool(detail.get("is_typosquatting", False)),
                    is_ip_based=bool(detail.get("is_ip_based", False)),
                    risk_score=float(max(intel.get("threat_score", 0.0) or 0.0, detail.get("risk_score", 0.0) or 0.0)),
                    threat_intel_results=intel or None,
                    evidence=detail.get("evidence"),
                ))

            # Attachment analyses
            for att in (results.get("attachment_analysis", {}) or {}).get("analyses", []):
                session.add(AttachmentAnalysis(
                    scan_id=scan.id,
                    filename=str(att.get("filename", "unnamed"))[:500],
                    content_type=str(att.get("content_type", ""))[:100],
                    file_size=int(att.get("file_size", 0) or 0),
                    md5_hash=att.get("md5_hash", "") or "",
                    sha256_hash=att.get("sha256_hash", "") or "",
                    is_executable=bool(att.get("is_executable")),
                    has_macros=bool(att.get("has_macros")),
                    is_double_extension=bool(att.get("is_double_extension")),
                    file_metadata=att.get("file_metadata"),
                    threat_score=float(att.get("threat_score", 0.0)),
                    evidence=att.get("evidence"),
                ))

            ai_res = results.get("ai_analysis", {}) or {}
            sev = str(ai_res.get("severity_level", "low")).lower()
            session.add(AiAnalysis(
                scan_id=scan.id,
                model_used=str(ai_res.get("model_used", "unknown"))[:100],
                attack_classification=str(ai_res.get("attack_classification", "benign"))[:100],
                confidence_score=float(ai_res.get("confidence_score", 0.0) or 0.0),
                severity_level=SeverityLevel(sev if sev in SeverityLevel._value2member_map_ else "low"),
                reasoning=str(ai_res.get("reasoning", "No threats detected.")),
                tactics_detected=[t for t in (ai_res.get("tactics_detected") or []) if isinstance(t, dict)],
                structured_output=ai_res.get("structured_output", {}),
                recommended_actions=[a for a in (ai_res.get("recommended_actions") or []) if isinstance(a, str)] or None,
                executive_summary=str(ai_res.get("executive_summary", "") or ""),
            ))

            risk = results.get("risk_assessment", {}) or {}
            score = float(risk.get("overall_score", 0.0) or 0.0)
            scan.risk_breakdown = risk.get("breakdown", {})
            scan.overall_risk_score = round(score, 1)
            scan.risk_level = _risk_level(score)
            classification = ai_res.get("attack_classification")
            if classification:
                scan.attack_type = "Benign" if scan.risk_level == RiskLevel.safe else str(classification)[:100]
            scan.status = ScanStatus.completed
            await session.commit()
            logger.info(f"Scan {scan_id} completed: score={scan.overall_risk_score} level={scan.risk_level.value}")

            from app.services.relationship_engine import RelationshipEngine

            await RelationshipEngine().process_scan(session, scan.id)

        except Exception:
            logger.exception(f"Error processing scan {scan_id}")
            await session.rollback()
            scan = await session.get(EmailScan, uuid.UUID(scan_id))
            if scan:
                scan.status = ScanStatus.failed
                await session.commit()
            raise


@celery_app.task(
    name="app.workers.scan_tasks.process_scan_task",
    bind=True,
    acks_late=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=600,
    time_limit=660,
)
def process_scan_task(self, scan_id: str):
    logger.info(f"Starting analysis for scan {scan_id}")
    try:
        asyncio.run(async_process_scan(scan_id))
    except Exception as exc:
        raise self.retry(exc=exc)
    return {"status": "completed", "scan_id": scan_id}
