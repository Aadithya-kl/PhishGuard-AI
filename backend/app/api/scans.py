"""Email scan endpoints: submit, list, inspect, preview and delete."""

from __future__ import annotations

import base64
import hashlib
import math
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.rate_limit import user_limiter
from app.core.security import safe_filename, sanitize_html
from app.core.tenant_context import Permission, TenantContext, requires_permission
from app.database import get_db
from app.models.scan import EmailScan, RiskLevel, ScanStatus
from app.schemas.scan import SandboxResponse, ScanDetailResponse, ScanListResponse, ScanSummaryResponse
from app.services.billing import billing_service
from app.services.email_parser import EmailParser, ParsedEmail
from app.workers.scan_tasks import process_scan_task

router = APIRouter()
parser = EmailParser()

_ALLOWED_EXTENSIONS = (".eml", ".msg", ".txt")
_MAX_ATTACHMENTS = 50
_SCAN_RATE = f"{settings.RATE_LIMIT_SCAN_PER_MINUTE}/minute"


def _attachment_metadata(parsed: ParsedEmail) -> list[dict[str, Any]]:
    """Hash attachments at ingest; persist only metadata + a small header sample."""
    out: list[dict[str, Any]] = []
    for att in (parsed.attachments or [])[:_MAX_ATTACHMENTS]:
        content = att.content or b""
        out.append({
            "filename": safe_filename(att.filename),
            "content_type": (att.content_type or "application/octet-stream")[:100],
            "size": att.size or len(content),
            "md5": hashlib.md5(content).hexdigest() if content else "",
            "sha1": hashlib.sha1(content).hexdigest() if content else "",
            "sha256": hashlib.sha256(content).hexdigest() if content else "",
            "head_b64": base64.b64encode(content[:2048]).decode() if content else "",
        })
    return out


async def _create_scan(db: AsyncSession, tenant: TenantContext, parsed: ParsedEmail) -> dict:
    if not await billing_service.check_scan_limit(db, tenant.organization.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Scan limit reached for this billing period. Please upgrade your plan.",
        )
    mime = dict(parsed.mime_structure or {})
    mime["attachments"] = _attachment_metadata(parsed)
    scan = EmailScan(
        organization_id=tenant.organization.id,
        user_id=tenant.user.id,
        subject=str(parsed.subject or "(no subject)")[:1000],
        sender_address=(parsed.sender_address or "unknown")[:320],
        sender_display_name=(parsed.sender_display_name or "")[:255],
        recipient=(parsed.recipient or "unknown")[:320],
        reply_to=parsed.reply_to[:320] if parsed.reply_to else None,
        return_path=parsed.return_path[:320] if parsed.return_path else None,
        raw_headers=parsed.raw_headers or "",
        body_text=parsed.body_text or "",
        body_html=parsed.body_html or "",
        parsed_headers=parsed.parsed_headers,
        mime_structure=mime,
        status=ScanStatus.pending,
    )
    db.add(scan)
    await billing_service.increment_scan_usage(db, tenant.organization.id)
    await db.commit()
    await db.refresh(scan)

    try:
        process_scan_task.delay(str(scan.id))
    except Exception as exc:
        logger.error(f"Could not enqueue scan {scan.id}: {exc}")
        scan.status = ScanStatus.failed
        await db.commit()
        raise HTTPException(status_code=503, detail="Analysis queue unavailable; please retry shortly")

    return {"id": str(scan.id), "status": scan.status.value, "message": "Scan queued"}


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
@user_limiter.limit(_SCAN_RATE)
async def upload_scan(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.UPLOAD_SCANS)),
) -> Any:
    filename = safe_filename(file.filename or "")
    if not filename.lower().endswith(_ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=415, detail="Only .eml, .msg or .txt files are accepted")

    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
            )
    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    raw = bytes(content)
    if filename.lower().endswith(".msg"):
        parsed = parser.parse_msg(raw)
    elif filename.lower().endswith(".txt"):
        parsed = parser.parse_raw(raw.decode("utf-8", errors="replace"))
    else:
        parsed = parser.parse_eml(raw)
    return await _create_scan(db, tenant, parsed)


@router.post("/paste", status_code=status.HTTP_202_ACCEPTED)
@user_limiter.limit(_SCAN_RATE)
async def paste_scan(
    request: Request,
    raw_content: str = Form(..., min_length=10),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.UPLOAD_SCANS)),
) -> Any:
    if len(raw_content.encode("utf-8")) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Pasted content is too large")
    return await _create_scan(db, tenant, parser.parse_raw(raw_content))


@router.get("", response_model=ScanListResponse)
async def list_scans(
    page: int = Query(1, ge=1, le=10_000),
    page_size: int = Query(20, ge=1, le=100),
    risk_level: Optional[RiskLevel] = None,
    scan_status: Optional[ScanStatus] = Query(None, alias="status"),
    q: Optional[str] = Query(None, max_length=200),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS)),
):
    filters = [EmailScan.organization_id == tenant.organization.id]
    if risk_level:
        filters.append(EmailScan.risk_level == risk_level)
    if scan_status:
        filters.append(EmailScan.status == scan_status)
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        filters.append(or_(EmailScan.subject.ilike(like, escape="\\"), EmailScan.sender_address.ilike(like, escape="\\")))

    total = (await db.execute(select(func.count(EmailScan.id)).where(*filters))).scalar() or 0
    rows = (
        await db.execute(
            select(EmailScan)
            .where(*filters)
            .order_by(EmailScan.scanned_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return ScanListResponse(
        items=[ScanSummaryResponse.model_validate(s) for s in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


async def _get_scan(db: AsyncSession, tenant: TenantContext, scan_id: uuid.UUID, full: bool = False) -> EmailScan:
    query = select(EmailScan).where(EmailScan.id == scan_id, EmailScan.organization_id == tenant.organization.id)
    if full:
        query = query.options(
            selectinload(EmailScan.header_analysis),
            selectinload(EmailScan.url_analyses),
            selectinload(EmailScan.attachment_analyses),
            selectinload(EmailScan.ai_analysis),
            selectinload(EmailScan.iocs),
        )
    scan = (await db.execute(query)).scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.get("/{scan_id}")
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS)),
) -> Any:
    scan = await _get_scan(db, tenant, scan_id, full=True)
    return ScanDetailResponse.model_validate(scan).model_dump(mode="json")


@router.get("/{scan_id}/preview", response_model=SandboxResponse)
async def preview_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS)),
):
    """Sanitised HTML rendition of the email body for the sandboxed viewer."""
    scan = await _get_scan(db, tenant, scan_id)
    if scan.body_html:
        html_out, warnings = sanitize_html(scan.body_html)
    else:
        import html as _html

        html_out, warnings = f"<pre>{_html.escape(scan.body_text or '')}</pre>", []
    return SandboxResponse(sanitized_html=html_out, warnings=warnings)


@router.get("/{scan_id}/raw-headers")
async def raw_headers(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS)),
):
    scan = await _get_scan(db, tenant, scan_id)
    return {"raw_headers": scan.raw_headers or ""}


@router.post("/{scan_id}/rescan", status_code=status.HTTP_202_ACCEPTED)
@user_limiter.limit(_SCAN_RATE)
async def rescan(
    request: Request,
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.UPLOAD_SCANS)),
):
    scan = await _get_scan(db, tenant, scan_id)
    if scan.status in (ScanStatus.pending, ScanStatus.analyzing):
        raise HTTPException(status_code=409, detail="Scan is already being analysed")
    scan.status = ScanStatus.pending
    await db.commit()
    process_scan_task.delay(str(scan.id))
    return {"id": str(scan.id), "status": scan.status.value}


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.DELETE_SCANS)),
):
    scan = await _get_scan(db, tenant, scan_id)
    await db.delete(scan)
    await db.commit()
