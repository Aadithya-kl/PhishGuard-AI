import uuid
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.models.user import User
from app.models.report import Report, ReportType, ReportFormat, ReportStatus
from app.workers.report_tasks import generate_report_task

router = APIRouter()

class ReportGenerateRequest(BaseModel):
    target_id: uuid.UUID
    report_type: ReportType
    format: ReportFormat = ReportFormat.pdf
    graph_snapshot: str | None = Field(default=None, description="Base64 encoded PNG of the knowledge graph")

class ReportResponse(BaseModel):
    id: uuid.UUID
    report_type: ReportType
    status: ReportStatus
    generated_at: str | None = None
    
    class Config:
        from_attributes = True

@router.post("/generate", response_model=ReportResponse)
def generate_report(req: ReportGenerateRequest, db: Session = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.GENERATE_REPORTS))):
    report = Report(
        organization_id=tenant.organization.id,
        user_id=tenant.user.id,
        report_type=req.report_type,
        format=req.format,
        status=ReportStatus.pending
    )
    
    if req.report_type == ReportType.scan:
        report.scan_id = req.target_id
    elif req.report_type == ReportType.investigation:
        report.investigation_id = req.target_id
    elif req.report_type == ReportType.campaign:
        report.campaign_id = req.target_id
    elif req.report_type == ReportType.threat_actor:
        report.actor_id = req.target_id
        
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Queue Celery Task
    generate_report_task.delay(str(report.id), req.graph_snapshot)
    
    return report

@router.get("", response_model=List[ReportResponse])
def list_reports(db: Session = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    reports = db.execute(select(Report).where(Report.organization_id == tenant.organization.id).order_by(Report.created_at.desc())).scalars().all()
    # Format generated_at for pydantic
    for r in reports:
        if r.generated_at:
            setattr(r, "generated_at", r.generated_at.isoformat())
    return reports

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    report = db.execute(select(Report).where(Report.id == report_id, Report.organization_id == tenant.organization.id)).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.generated_at:
        setattr(report, "generated_at", report.generated_at.isoformat())
    return report

@router.get("/{report_id}/download")
def download_report(report_id: uuid.UUID, db: Session = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    report = db.execute(select(Report).where(Report.id == report_id, Report.organization_id == tenant.organization.id)).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if report.status != ReportStatus.completed or not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=400, detail="Report file is not available")
        
    return FileResponse(
        path=report.file_path,
        media_type="application/pdf",
        filename=f"PhishGuard_Report_{report.report_type.value}_{report.id}.pdf"
    )
