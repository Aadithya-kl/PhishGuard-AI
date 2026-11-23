"""Celery task that renders PDF reports."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session_factory
from app.models.investigation import Investigation
from app.models.report import Report, ReportStatus, ReportType
from app.models.scan import EmailScan
from app.services.report_generator import ReportGeneratorService
from app.workers.celery_app import celery_app


async def _scan_data(db, report: Report) -> dict:
    scan = (
        await db.execute(
            select(EmailScan)
            .where(EmailScan.id == report.scan_id, EmailScan.organization_id == report.organization_id)
            .options(selectinload(EmailScan.ai_analysis), selectinload(EmailScan.iocs))
        )
    ).scalar_one_or_none()
    if not scan:
        raise ValueError("Scan not found")
    ai = scan.ai_analysis
    tactics = [
        f"{t.get('tactic', 'Tactic')}: {t.get('description', '')}" for t in (ai.tactics_detected or []) if isinstance(t, dict)
    ] if ai else []
    return {
        "title": f"Scan Report: {scan.subject}",
        "summary": "Security findings for the analysed email.",
        "metadata": {
            "Subject": scan.subject,
            "Sender": f"{scan.sender_display_name} <{scan.sender_address}>",
            "Recipient": scan.recipient,
            "Risk Level": scan.risk_level.value.upper(),
            "Overall Score": scan.overall_risk_score,
            "Attack Type": scan.attack_type or "None",
        },
        "findings": (ai.reasoning if ai else "") or "No AI analysis available.",
        "recommendations": "\n".join(ai.recommended_actions or []) if ai and isinstance(ai.recommended_actions, list) else
        "Quarantine the message, block listed indicators and notify affected recipients if the verdict is malicious.",
        "mitre": tactics,
        "iocs": [f"{i.ioc_type.value}: {i.value}" for i in scan.iocs[:200]],
    }


async def _investigation_data(db, report: Report) -> dict:
    inv = (
        await db.execute(
            select(Investigation).where(
                Investigation.id == report.investigation_id, Investigation.organization_id == report.organization_id
            )
        )
    ).scalar_one_or_none()
    if not inv:
        raise ValueError("Investigation not found")
    return {
        "title": f"Investigation Report: {inv.title}",
        "summary": getattr(inv, "summary", None) or inv.description or "Investigation report.",
        "metadata": {
            "Priority": inv.priority.value.upper(),
            "Severity": inv.severity.value.upper(),
            "Status": inv.status.value.upper(),
            "Created": inv.created_at.strftime("%Y-%m-%d %H:%M UTC"),
        },
        "findings": "See investigation timeline and artifacts in PhishGuard.",
        "recommendations": "Contain affected accounts, block indicators, and close out with lessons learned.",
        "mitre": getattr(inv, "mitre_tactics", None) or [],
        "iocs": [],
    }


async def _generate_report(report_id: str, graph_b64: Optional[str] = None) -> dict:
    async with async_session_factory() as db:
        report = await db.get(Report, uuid.UUID(report_id))
        if not report:
            return {"status": "error", "message": "Report not found"}
        try:
            report.status = ReportStatus.processing
            await db.commit()

            if report.report_type == ReportType.scan:
                data = await _scan_data(db, report)
            elif report.report_type == ReportType.investigation:
                data = await _investigation_data(db, report)
            else:
                raise ValueError(f"Unsupported report type {report.report_type.value}")

            pdf_path = await asyncio.to_thread(ReportGeneratorService().generate_pdf, data, graph_b64)
            report.file_path = pdf_path
            report.status = ReportStatus.completed
            report.generated_at = datetime.now(timezone.utc)
            await db.commit()
            return {"status": "success", "report_id": report_id}
        except Exception as exc:
            logger.exception(f"Report {report_id} failed")
            await db.rollback()
            report = await db.get(Report, uuid.UUID(report_id))
            if report:
                report.status = ReportStatus.failed
                await db.commit()
            return {"status": "error", "message": type(exc).__name__}


@celery_app.task(name="app.workers.report_tasks.generate_report_task", soft_time_limit=240, time_limit=300)
def generate_report_task(report_id: str, graph_b64: Optional[str] = None):
    return asyncio.run(_generate_report(report_id, graph_b64))
