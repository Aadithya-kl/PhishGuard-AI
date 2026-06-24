from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from typing import Any
import uuid
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.models.scan import EmailScan, ScanStatus
from app.services.email_parser import EmailParser
from app.services.billing import billing_service
from app.workers.scan_tasks import process_scan_task
from app.schemas.scan import ScanDetailResponse
from app.core.rate_limit import user_limiter
from fastapi import Request

router = APIRouter()
parser = EmailParser()

MAX_EMAIL_SIZE = 10 * 1024 * 1024  # 10MB

@router.post("/upload")
# @user_limiter.limit("10/minute")
async def upload_scan(
    request: Request,
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.UPLOAD_SCANS))
) -> Any:
    # 10MB chunked reading to prevent memory exhaustion
    content = bytearray()
    chunk_size = 1024 * 1024  # 1MB chunks
    
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        content.extend(chunk)
        if len(content) > MAX_EMAIL_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {MAX_EMAIL_SIZE / 1024 / 1024}MB"
            )
            
    if not await billing_service.check_scan_limit(db, tenant.organization.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Scan limit reached for this billing period. Please upgrade your plan."
        )

    content_bytes = bytes(content)
    
    if file.filename and file.filename.endswith(".msg"):
        parsed = parser.parse_msg(content_bytes)
    else:
        parsed = parser.parse_eml(content_bytes)
        
    scan = EmailScan(
        organization_id=tenant.organization.id,
        user_id=tenant.user.id,
        subject=parsed.subject[:1000],
        sender_address=parsed.sender_address[:320] if parsed.sender_address else "unknown",
        sender_display_name=parsed.sender_display_name[:255] if parsed.sender_display_name else "",
        recipient=parsed.recipient[:320] if parsed.recipient else "unknown",
        reply_to=parsed.reply_to[:320] if parsed.reply_to else None,
        return_path=parsed.return_path[:320] if parsed.return_path else None,
        raw_headers=parsed.raw_headers,
        body_text=parsed.body_text,
        body_html=parsed.body_html,
        parsed_headers=parsed.parsed_headers,
        mime_structure=parsed.mime_structure,
        status=ScanStatus.pending
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # Trigger celery task
    process_scan_task.delay(str(scan.id))
    
    # Increment usage
    await billing_service.increment_scan_usage(db, tenant.organization.id)
    
    return {"id": str(scan.id), "status": scan.status.value, "message": "Scan uploaded"}

@router.post("/paste")
@user_limiter.limit("10/minute")
async def paste_scan(
    request: Request,
    raw_content: str = Form(...), 
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.UPLOAD_SCANS))
) -> Any:
    
    # Simple length check for pasted text to prevent oversized payloads
    if len(raw_content.encode("utf-8")) > MAX_EMAIL_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Pasted content exceeds maximum allowed size"
        )
        
    if not await billing_service.check_scan_limit(db, tenant.organization.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Scan limit reached for this billing period. Please upgrade your plan."
        )

    parsed = parser.parse_raw(raw_content)
    
    scan = EmailScan(
        organization_id=tenant.organization.id,
        user_id=tenant.user.id,
        subject=parsed.subject[:1000],
        sender_address=parsed.sender_address[:320] if parsed.sender_address else "unknown",
        sender_display_name=parsed.sender_display_name[:255] if parsed.sender_display_name else "",
        recipient=parsed.recipient[:320] if parsed.recipient else "unknown",
        reply_to=parsed.reply_to[:320] if parsed.reply_to else None,
        return_path=parsed.return_path[:320] if parsed.return_path else None,
        raw_headers=parsed.raw_headers,
        body_text=parsed.body_text,
        body_html=parsed.body_html,
        parsed_headers=parsed.parsed_headers,
        mime_structure=parsed.mime_structure,
        status=ScanStatus.pending
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)
    
    # Trigger celery task
    process_scan_task.delay(str(scan.id))
    
    # Increment usage
    await billing_service.increment_scan_usage(db, tenant.organization.id)
    
    return {"id": str(scan.id), "status": scan.status.value, "message": "Scan submitted"}

@router.get("/{scan_id}")
async def get_scan(
    scan_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))
) -> Any:
    query = (
        select(EmailScan)
        .where(EmailScan.id == scan_id)
        .where(EmailScan.organization_id == tenant.organization.id)  # ENFORCE TENANT ISOLATION
        .options(
            selectinload(EmailScan.header_analysis),
            selectinload(EmailScan.url_analyses),
            selectinload(EmailScan.attachment_analyses),
            selectinload(EmailScan.ai_analysis),
            selectinload(EmailScan.iocs)
        )
    )
    result = await db.execute(query)
    scan = result.scalar_one_or_none()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found or access denied")
        
    return ScanDetailResponse.model_validate(scan).model_dump(mode='json')
