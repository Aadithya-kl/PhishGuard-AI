from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import Any
import uuid

from app.database import get_db
from app.schemas.investigation import (
    InvestigationCreate, InvestigationResponse, InvestigationDetailResponse,
    ArtifactCreate, NoteCreate
)
from app.models.investigation import (
    Investigation, InvestigationStatus, InvestigationPriority, InvestigationSeverity,
    InvestigationArtifact, ArtifactType, InvestigationNote,
    InvestigationTimelineEvent, TimelineEventType
)
from app.models.user import User
from app.core.tenant_context import TenantContext, requires_permission, Permission

router = APIRouter()

# --- Helper to append timeline events ---
def add_timeline_event(db: AsyncSession, inv_id: uuid.UUID, event_type: TimelineEventType, description: str, user_id: uuid.UUID):
    evt = InvestigationTimelineEvent(
        investigation_id=inv_id,
        event_type=event_type,
        description=description,
        triggered_by=user_id
    )
    db.add(evt)


@router.post("", response_model=dict)
async def create_investigation(
    data: InvestigationCreate, 
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_INVESTIGATIONS))
):
    inv = Investigation(
        organization_id=tenant.organization.id,
        title=data.title,
        description=data.description,
        priority=data.priority,
        severity=data.severity,
        created_by=tenant.user.id
    )
    db.add(inv)
    await db.flush()  # To get inv.id
    
    add_timeline_event(db, inv.id, TimelineEventType.created, "Investigation opened", tenant.user.id)
    await db.commit()
    
    return {"id": str(inv.id), "message": "Investigation created successfully"}


@router.get("", response_model=list[InvestigationResponse])
async def list_investigations(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_INVESTIGATIONS))
):
    res = await db.execute(
        select(Investigation)
        .where(Investigation.organization_id == tenant.organization.id)
        .order_by(desc(Investigation.created_at))
    )
    return [InvestigationResponse.model_validate(inv) for inv in res.scalars()]


@router.get("/{id}", response_model=InvestigationDetailResponse)
async def get_investigation(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_INVESTIGATIONS))
):
    query = (
        select(Investigation)
        .where(Investigation.id == id, Investigation.organization_id == tenant.organization.id)
        .options(
            selectinload(Investigation.artifacts),
            selectinload(Investigation.notes),
            selectinload(Investigation.timeline)
        )
    )
    res = await db.execute(query)
    inv = res.scalar_one_or_none()
    
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found or access denied")
        
    return InvestigationDetailResponse.model_validate(inv)


@router.post("/{id}/artifacts", response_model=dict)
async def add_artifact(
    id: uuid.UUID, 
    data: ArtifactCreate, 
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_INVESTIGATIONS))
):
    res = await db.execute(select(Investigation).where(Investigation.id == id, Investigation.organization_id == tenant.organization.id))
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found or access denied")
        
    art = InvestigationArtifact(
        investigation_id=id,
        artifact_type=data.artifact_type,
        artifact_value=data.artifact_value,
        added_by=tenant.user.id
    )
    db.add(art)
    
    # Event mapping
    evt_type = TimelineEventType.ioc_added
    if data.artifact_type == ArtifactType.campaign:
        evt_type = TimelineEventType.campaign_added
    elif data.artifact_type == ArtifactType.scan:
        evt_type = TimelineEventType.scan_added
        
    add_timeline_event(db, id, evt_type, f"Added {data.artifact_type.value}: {data.artifact_value}", tenant.user.id)
    await db.commit()
    return {"id": str(art.id), "message": "Artifact added successfully"}


@router.post("/{id}/notes", response_model=dict)
async def add_note(
    id: uuid.UUID, 
    data: NoteCreate, 
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_INVESTIGATIONS))
):
    res = await db.execute(select(Investigation).where(Investigation.id == id, Investigation.organization_id == tenant.organization.id))
    inv = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found or access denied")
        
    note = InvestigationNote(
        investigation_id=id,
        author_id=tenant.user.id,
        content=data.content
    )
    db.add(note)
    add_timeline_event(db, id, TimelineEventType.note_added, f"Note added: '{data.content[:30]}...'", tenant.user.id)
    
    # Update properties if provided
    if data.priority and data.priority != inv.priority:
        old = inv.priority.value
        inv.priority = data.priority
        add_timeline_event(db, id, TimelineEventType.priority_changed, f"Priority changed from {old} to {inv.priority.value}", tenant.user.id)
        
    if data.severity and data.severity != inv.severity:
        old = inv.severity.value
        inv.severity = data.severity
        add_timeline_event(db, id, TimelineEventType.severity_changed, f"Severity changed from {old} to {inv.severity.value}", tenant.user.id)
        
    if data.status and data.status != inv.status:
        old = inv.status.value
        inv.status = data.status
        add_timeline_event(db, id, TimelineEventType.status_changed, f"Status changed from {old} to {inv.status.value}", tenant.user.id)
        
    await db.commit()
    return {"id": str(note.id), "message": "Note added and timeline updated"}
