"""PDF report generation and download (tenant-scoped)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.rate_limit import user_limiter
from app.core.tenant_context import Permission, TenantContext, requires_permission
from app.database import get_db
from app.models.investigation import Investigation
from app.models.report import Report, ReportFormat, ReportStatus, ReportType
from app.models.scan import EmailScan
from app.workers.report_tasks import generate_report_task

router = APIRouter()

_SUPPORTED = {ReportType.scan, ReportType.investigation}


class ReportGenerateRequest(BaseModel):
    target_id: uuid.UUID
    report_type: ReportType
    format: ReportFormat = ReportFormat.pdf
    graph_snapshot: Optional[str] = Field(default=None, max_length=8 * 1024 * 1024, description="Base64 PNG")


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    report_type: ReportType
    status: ReportStatus
    scan_id: Optional[uuid.UUID] = None
    investigation_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
@user_limiter.limit("10/minute")
async def generate_report(
    request: Request,
    req: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.GENERATE_REPORTS)),
):
    if req.report_type not in _SUPPORTED:
        raise HTTPException(status_code=400, detail="Only scan and investigation reports are supported")
    if req.format != ReportFormat.pdf:
        raise HTTPException(status_code=400, detail="Only PDF output is supported")

    # The target must belong to the caller's organization (prevents IDOR).
    model = EmailScan if req.report_type == ReportType.scan else Investigation
    owned = await db.execute(select(model.id).where(model.id == req.target_id, model.organization_id == tenant.organization.id))
    if owned.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Target not found")

    report = Report(
        organization_id=tenant.organization.id,
        user_id=tenant.user.id,
        report_type=req.report_type,
        format=req.format,
        status=ReportStatus.pending,
        scan_id=req.target_id if req.report_type == ReportType.scan else None,
        investigation_id=req.target_id if req.report_type == ReportType.investigation else None,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    generate_report_task.delay(str(report.id), req.graph_snapshot)
    return report


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS)),
):
    res = await db.execute(
        select(Report).where(Report.organization_id == tenant.organization.id).order_by(Report.created_at.desc()).limit(200)
    )
    return res.scalars().all()


async def _owned_report(db: AsyncSession, tenant: TenantContext, report_id: uuid.UUID) -> Report:
    report = (
        await db.execute(select(Report).where(Report.id == report_id, Report.organization_id == tenant.organization.id))
    ).scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS)),
):
    return await _owned_report(db, tenant, report_id)


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS)),
):
    report = await _owned_report(db, tenant, report_id)
    if report.status != ReportStatus.completed or not report.file_path:
        raise HTTPException(status_code=409, detail="Report is not ready")

    # Never serve a path outside the report directory, even if the DB row was tampered with.
    base = os.path.realpath(settings.REPORT_DIR)
    path = os.path.realpath(report.file_path)
    if os.path.commonpath([base, path]) != base or not os.path.isfile(path):
        raise HTTPException(status_code=410, detail="Report file is no longer available")

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=f"PhishGuard_{report.report_type.value}_report_{report.id}.pdf",
    )
