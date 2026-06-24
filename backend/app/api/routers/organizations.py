from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import secrets
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.models.organization import OrganizationMember, OrganizationInvitation, OrganizationRole
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas.organization import (
    OrganizationMemberResponse, InviteRequest, InviteResponse, AcceptInviteRequest
)

router = APIRouter()

@router.get("/members", response_model=List[OrganizationMemberResponse])
async def list_members(
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_ORGANIZATION))
):
    result = await db.execute(
        select(OrganizationMember).where(OrganizationMember.organization_id == tenant.organization.id)
    )
    return result.scalars().all()

@router.post("/invites", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    data: InviteRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(requires_permission(Permission.MANAGE_ORGANIZATION))
):
    # Check if user is already a member
    user_res = await db.execute(select(User).where(User.email == data.email))
    user = user_res.scalar_one_or_none()
    if user:
        mem_res = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == tenant.organization.id
            )
        )
        if mem_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User is already a member")

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    
    try:
        role_enum = OrganizationRole(data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    invite = OrganizationInvitation(
        organization_id=tenant.organization.id,
        email=data.email,
        role=role_enum,
        invitation_token=token,
        invited_by=tenant.user.id,
        expires_at=expires
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite

@router.post("/invites/accept", status_code=status.HTTP_200_OK)
async def accept_invite(
    data: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify token
    res = await db.execute(
        select(OrganizationInvitation).where(
            OrganizationInvitation.invitation_token == data.invitation_token,
            OrganizationInvitation.email == current_user.email
        )
    )
    invite = res.scalar_one_or_none()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found or email mismatch")
        
    if invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invitation expired")
        
    # Check if already a member
    mem_res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.organization_id == invite.organization_id
        )
    )
    if mem_res.scalar_one_or_none():
        # Clean up invite
        await db.delete(invite)
        await db.commit()
        return {"message": "Already a member"}

    # Create membership
    member = OrganizationMember(
        organization_id=invite.organization_id,
        user_id=current_user.id,
        role=invite.role,
        is_active=True
    )
    db.add(member)
    await db.delete(invite)
    await db.commit()
    
    return {"message": "Invitation accepted"}
