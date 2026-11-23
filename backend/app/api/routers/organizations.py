"""Organization membership and invitations.

Invitation tokens are stored hashed (SHA-256); the raw token is shown to the
inviting admin exactly once so they can share the invite link.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_user, hash_password, password_policy_errors
from app.core.rate_limit import limiter
from app.core.tenant_context import ROLE_RANK, Permission, TenantContext, requires_permission
from app.database import get_db
from app.models.organization import (
    InvitationStatus,
    OrganizationInvitation,
    OrganizationMember,
    OrganizationRole,
)
from app.models.user import User
from app.schemas.organization import (
    AcceptInviteRequest,
    InviteCreatedResponse,
    InviteRegisterRequest,
    InviteRequest,
    InviteResponse,
    MemberUpdateRequest,
    OrganizationMemberResponse,
)

router = APIRouter()
_manage = requires_permission(Permission.MANAGE_ORGANIZATION)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _parse_role(value: str) -> OrganizationRole:
    for role in OrganizationRole:
        if value in (role.value, role.name):
            return role
    raise HTTPException(status_code=400, detail="Invalid role")


def _assert_can_grant(tenant: TenantContext, role: OrganizationRole) -> None:
    # Nobody can hand out platform_admin via the API, and admins cannot grant above their own rank.
    if role == OrganizationRole.platform_admin or ROLE_RANK[role] > ROLE_RANK[tenant.role]:
        raise HTTPException(status_code=403, detail="You cannot grant a role higher than your own")


def _member_out(m: OrganizationMember) -> OrganizationMemberResponse:
    out = OrganizationMemberResponse.model_validate(m)
    if m.user:
        out.email, out.full_name = m.user.email, m.user.full_name
    return out


@router.get("/members", response_model=List[OrganizationMemberResponse])
async def list_members(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_manage)):
    res = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.organization_id == tenant.organization.id)
        .options(selectinload(OrganizationMember.user))
    )
    return [_member_out(m) for m in res.scalars().all()]


@router.patch("/members/{member_id}", response_model=OrganizationMemberResponse)
async def update_member(
    member_id: uuid.UUID,
    body: MemberUpdateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(_manage),
):
    res = await db.execute(
        select(OrganizationMember)
        .where(OrganizationMember.id == member_id, OrganizationMember.organization_id == tenant.organization.id)
        .options(selectinload(OrganizationMember.user))
    )
    member = res.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.user_id == tenant.user.id:
        raise HTTPException(status_code=400, detail="You cannot change your own membership")
    if ROLE_RANK[member.role] > ROLE_RANK[tenant.role]:
        raise HTTPException(status_code=403, detail="You cannot modify a member with a higher role")
    if body.role is not None:
        role = _parse_role(body.role)
        _assert_can_grant(tenant, role)
        member.role = role
    if body.is_active is not None:
        member.is_active = body.is_active
    await db.commit()
    return _member_out(member)


@router.get("/invites", response_model=List[InviteResponse])
async def list_invites(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_manage)):
    res = await db.execute(
        select(OrganizationInvitation)
        .where(
            OrganizationInvitation.organization_id == tenant.organization.id,
            OrganizationInvitation.status == InvitationStatus.pending,
        )
        .order_by(OrganizationInvitation.created_at.desc())
    )
    return res.scalars().all()


@router.post("/invites", response_model=InviteCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(data: InviteRequest, db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_manage)):
    role = _parse_role(data.role)
    _assert_can_grant(tenant, role)
    email = data.email.lower()

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user:
        existing = await db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user.id, OrganizationMember.organization_id == tenant.organization.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="User is already a member")

    token = secrets.token_urlsafe(32)
    invite = OrganizationInvitation(
        organization_id=tenant.organization.id,
        email=email,
        role=role,
        invitation_token=_hash_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    out = InviteCreatedResponse.model_validate({**InviteResponse.model_validate(invite).model_dump(), "invitation_token": token})
    return out


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(invite_id: uuid.UUID, db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_manage)):
    invite = (
        await db.execute(
            select(OrganizationInvitation).where(
                OrganizationInvitation.id == invite_id, OrganizationInvitation.organization_id == tenant.organization.id
            )
        )
    ).scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    invite.status = InvitationStatus.revoked
    await db.commit()


async def _load_valid_invite(db: AsyncSession, raw_token: str) -> OrganizationInvitation:
    invite = (
        await db.execute(
            select(OrganizationInvitation).where(
                OrganizationInvitation.invitation_token == _hash_token(raw_token),
                OrganizationInvitation.status == InvitationStatus.pending,
            )
        )
    ).scalar_one_or_none()
    if not invite or invite.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    return invite


@router.post("/invites/accept")
@limiter.limit("10/minute")
async def accept_invite(
    request: Request,
    data: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Existing, signed-in user accepts an invitation addressed to their e-mail."""
    invite = await _load_valid_invite(db, data.invitation_token)
    if invite.email.lower() != current_user.email.lower():
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    existing = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == current_user.id, OrganizationMember.organization_id == invite.organization_id
        )
    )
    if not existing.scalar_one_or_none():
        db.add(OrganizationMember(organization_id=invite.organization_id, user_id=current_user.id, role=invite.role, is_active=True))
    invite.status = InvitationStatus.accepted
    await db.commit()
    return {"message": "Invitation accepted. Sign in again to switch to the new organization."}


@router.post("/invites/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register_with_invite(request: Request, data: InviteRegisterRequest, db: AsyncSession = Depends(get_db)):
    """New user creates their account from an invitation link (works when public sign-up is disabled)."""
    invite = await _load_valid_invite(db, data.invitation_token)
    if (await db.execute(select(User).where(User.email == invite.email))).scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An account already exists for this e-mail; sign in and accept the invite")
    errors = password_policy_errors(data.password, invite.email)
    if errors:
        raise HTTPException(status_code=422, detail=f"Password {', '.join(errors)}")
    user = User(email=invite.email, full_name=data.full_name.strip(), hashed_password=hash_password(data.password), is_active=True)
    db.add(user)
    await db.flush()
    db.add(OrganizationMember(organization_id=invite.organization_id, user_id=user.id, role=invite.role, is_active=True))
    invite.status = InvitationStatus.accepted
    await db.commit()
    return {"message": "Account created. You can now sign in.", "email": invite.email}
