import asyncio
import uuid
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.database import async_session_factory
from app.models.scan import (
    EmailScan, ScanStatus, HeaderAnalysis, UrlAnalysis, 
    AttachmentAnalysis, AiAnalysis, RiskLevel, SeverityLevel
)
from app.services.ai_engine import AIEngine
from app.services.ioc_extractor import IocExtractor
from app.services.threat_intel.manager import ThreatIntelManager

ai_engine = AIEngine()
ioc_extractor = IocExtractor()
threat_intel_manager = ThreatIntelManager()

async def async_process_scan(scan_id: str):
    async with async_session_factory() as session:
        # Load scan
        result = await session.execute(select(EmailScan).where(EmailScan.id == uuid.UUID(scan_id)))
        scan = result.scalar_one_or_none()
        if not scan:
            logger.error(f"Scan {scan_id} not found")
            return

        try:
            scan.status = ScanStatus.analyzing
            await session.commit()

            from app.services.email_parser import _extract_urls
            extracted_urls = _extract_urls(scan.body_text or "") + _extract_urls(scan.body_html or "")
            extracted_urls = list(set(extracted_urls))

            parsed_email = {
                "subject": scan.subject,
                "sender_address": scan.sender_address,
                "recipient": scan.recipient,
                "body_text": scan.body_text,
                "body_html": scan.body_html,
                "urls": extracted_urls,
                "attachments": [],
                "raw_headers": scan.raw_headers,
                "parsed_headers": scan.parsed_headers or {}
            }
            
            # Extract IOCs
            iocs = ioc_extractor.extract(scan_id=scan_id, parsed_email=parsed_email)
            for ioc in iocs:
                session.add(ioc)
                
            # Run Threat Intel Manager on extracted IOCs
            threat_intel_results = await threat_intel_manager.analyze_iocs(iocs)
            
            # Save IOC threat info to database explicitly
            await session.commit()
            
            # Run Detections
            from app.detections.engine import DetectionEngine
            det_engine = DetectionEngine()
            detections = det_engine.run_detections(scan)
            scan.detections = [d.model_dump() for d in detections]
            
            # Run AI Engine passing the threat intel and detections
            results = await ai_engine.analyze(parsed_email, threat_intel=threat_intel_results, detections=scan.detections)

            # Map Header Analysis
            h_res = results.get("header_analysis", {})
            header_analysis = HeaderAnalysis(
                scan_id=scan.id,
                spf_pass=h_res.get("spf_pass", True),
                spf_result=h_res.get("spf_result", "pass"),
                dkim_pass=h_res.get("dkim_pass", True),
                dkim_result=h_res.get("dkim_result", "pass"),
                dmarc_pass=h_res.get("dmarc_pass", True),
                dmarc_result=h_res.get("dmarc_result", "pass"),
                sender_spoofed=h_res.get("sender_spoofed", False),
                display_name_impersonation=h_res.get("display_name_impersonation", False),
                domain_mismatch=h_res.get("domain_mismatch", False),
                trust_score=h_res.get("trust_score", 100.0)
            )
            session.add(header_analysis)
            
            # Extract URLs from Threat Intel Results for UrlAnalysis records
            phishing_matches = threat_intel_results.get("phishing_matches", {})
            for url, data in phishing_matches.items():
                if url == "status": continue
                session.add(UrlAnalysis(
                    scan_id=scan.id,
                    original_url=url,
                    domain=url.split("/")[2] if "//" in url else url.split("/")[0],
                    risk_score=data.get("threat_score", 0.0),
                    threat_intel_results=data
                ))

            # Map AI Analysis
            ai_res = results.get("ai_analysis", {})
            sev_str = ai_res.get("severity_level", "low").lower()
            if sev_str not in ["low", "medium", "high", "critical"]: sev_str = "low"
            
            ai_analysis = AiAnalysis(
                scan_id=scan.id,
                model_used=ai_res.get("model_used", "unknown"),
                attack_classification=ai_res.get("attack_classification", "benign"),
                confidence_score=ai_res.get("confidence_score", 0.0),
                severity_level=SeverityLevel(sev_str),
                reasoning=ai_res.get("reasoning", "No threats detected."),
                tactics_detected=ai_res.get("tactics_detected", []),
                structured_output=ai_res.get("structured_output", {})
            )
            session.add(ai_analysis)

            # Map Risk Assessment
            risk = results.get("risk_assessment", {})
            scan.risk_breakdown = risk.get("breakdown", {})
            
            overall_score = risk.get("overall_score", 0.0)
            scan.overall_risk_score = overall_score
            
            risk_str = risk.get("risk_level", "safe").lower()
            if overall_score > 75: risk_str = "high"
            elif overall_score > 40: risk_str = "suspicious"
            elif overall_score > 0: risk_str = "low"
            else: risk_str = "safe"
                
            if risk_str not in ["safe", "low", "suspicious", "high"]: risk_str = "safe"
            scan.risk_level = RiskLevel(risk_str)
            
            scan.status = ScanStatus.completed
            await session.commit()
            
            logger.info(f"Scan {scan_id} completed. Risk: {scan.overall_risk_score}, Level: {scan.risk_level.value}")
            
            # Execute relationship engine automatically at the end of every completed scan.
            from app.services.relationship_engine import RelationshipEngine
            rel_engine = RelationshipEngine()
            await rel_engine.process_scan(session, scan.id)
            
        except Exception as e:
            logger.exception(f"Error processing scan {scan_id}")
            scan.status = ScanStatus.failed
            await session.commit()

@celery_app.task
def process_scan_task(scan_id: str):
    logger.info(f"Starting analysis for scan {scan_id}")
    asyncio.run(async_process_scan(scan_id))
    return {"status": "completed", "scan_id": scan_id}
