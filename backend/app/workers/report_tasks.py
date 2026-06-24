import uuid
import asyncio
from datetime import datetime, timezone
from celery import shared_task
from app.database import async_session_factory
from app.models.report import Report, ReportStatus, ReportType
from app.services.report_generator import ReportGeneratorService
from sqlalchemy import select

async def _generate_report(report_id: str, graph_b64: str = None):
    async with async_session_factory() as db:
        try:
            res = await db.execute(select(Report).where(Report.id == uuid.UUID(report_id)))
            report = res.scalar_one_or_none()
            if not report:
                return {"status": "error", "message": "Report not found"}

            report.status = ReportStatus.processing
            await db.commit()

            generator = ReportGeneratorService(db)
            
            if report.report_type == ReportType.scan:
                data = await generator.fetch_scan_data(report.scan_id)
            elif report.report_type == ReportType.investigation:
                data = await generator.fetch_investigation_data(report.investigation_id)
            else:
                data = {"title": f"{report.report_type.value.capitalize()} Report", "summary": "Not implemented yet"}

            pdf_path = await generator.generate_pdf(data, graph_b64)
            
            report.file_path = pdf_path
            report.status = ReportStatus.completed
            report.generated_at = datetime.now(timezone.utc)
            await db.commit()
            
            return {"status": "success", "report_id": report_id, "pdf_path": pdf_path}
        except Exception as e:
            res = await db.execute(select(Report).where(Report.id == uuid.UUID(report_id)))
            report = res.scalar_one_or_none()
            if report:
                report.status = ReportStatus.failed
                await db.commit()
            return {"status": "error", "message": str(e)}

@shared_task(name="app.workers.report_tasks.generate_report_task")
def generate_report_task(report_id: str, graph_b64: str = None):
    return asyncio.run(_generate_report(report_id, graph_b64))
