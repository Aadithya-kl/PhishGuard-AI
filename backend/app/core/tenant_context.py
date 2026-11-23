"""Tenant context and multi-tenancy dependency injection.

Every tenant-scoped endpoint depends on :func:`requires_permission`, which:

1. authenticates the caller (access JWT or API key),
2. re-reads the user's *current* organization membership from the database
   (so revoked members lose access immediately, regardless of token lifetime),
3. checks the requested permission.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import API_KEY_PREFIX, decode_token, oauth2_scheme, parse_uuid, resolve_api_key
from app.database import get_db
from app.models.organization import Organization, OrganizationMember, OrganizationRole
from app.models.user import User


@dataclass
class TenantContext:
    user: User
    organization: Organization
    role: OrganizationRole
    permissions: set[str]
    is_api_key: bool = False


class Permission:
    VIEW_SCANS = "view_scans"
    UPLOAD_SCANS = "upload_scans"
    DELETE_SCANS = "delete_scans"
    VIEW_GRAPH = "view_graph"
    MANAGE_INVESTIGATIONS = "manage_investigations"
    GENERATE_REPORTS = "generate_reports"
    USE_COPILOT = "use_copilot"
    MANAGE_USERS = "manage_users"
    MANAGE_ORGANIZATION = "manage_organization"
    EXPORT_DATA = "export_data"

    @classmethod
    def all(cls) -> set[str]:
        return {v for k, v in vars(cls).items() if k.isupper() and isinstance(v, str)}


_ALL = Permission.all()

ROLE_PERMISSIONS: dict[OrganizationRole, set[str]] = {
    OrganizationRole.platform_admin: set(_ALL),
    OrganizationRole.org_admin: set(_ALL),
    OrganizationRole.soc_manager: {
        Permission.VIEW_SCANS, Permission.UPLOAD_SCANS, Permission.DELETE_SCANS, Permission.VIEW_GRAPH,
        Permission.MANAGE_INVESTIGATIONS, Permission.GENERATE_REPORTS,
        Permission.USE_COPILOT, Permission.EXPORT_DATA,
    },
    OrganizationRole.soc_analyst: {
        Permission.VIEW_SCANS, Permission.UPLOAD_SCANS, Permission.VIEW_GRAPH,
        Permission.USE_COPILOT, Permission.MANAGE_INVESTIGATIONS, Permission.GENERATE_REPORTS,
    },
    OrganizationRole.read_only: {Permission.VIEW_SCANS, Permission.VIEW_GRAPH},
}

# Roles ordered by privilege — used to stop admins granting roles above their own.
ROLE_RANK: dict[OrganizationRole, int] = {
    OrganizationRole.read_only: 0,
    OrganizationRole.soc_analyst: 1,
    OrganizationRole.soc_manager: 2,
    OrganizationRole.org_admin: 3,
    OrganizationRole.platform_admin: 4,
}

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


async def _membership(db: AsyncSession, user_id, org_id) -> Optional[OrganizationMember]:
    res = await db.execute(
        select(OrganizationMember).where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == org_id,
            OrganizationMember.is_active.is_(True),
        )
    )
    return res.scalar_one_or_none()


async def get_tenant_context(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> TenantContext:
    if not token:
        raise _UNAUTH

    # ── API key ──────────────────────────────────────────────────────────
    if token.startswith(API_KEY_PREFIX):
        api_key = await resolve_api_key(token, db)
        if api_key is None:
            raise _UNAUTH
        org = await db.get(Organization, api_key.organization_id)
        if not org or not org.is_active:
            raise _UNAUTH
        if api_key.user_id is None:
            raise _UNAUTH
        user = await db.get(User, api_key.user_id)
        if not user or not user.is_active:
            raise _UNAUTH
        # The key's owner must still be a member; key permissions are capped
        # by what the owner's role currently allows.
        membership = await _membership(db, user.id, org.id)
        if membership is None:
            raise _UNAUTH
        owner_perms = ROLE_PERMISSIONS.get(membership.role, set())
        key_perms = set(api_key.permissions or []) & owner_perms
        request.state.user_id = str(user.id)
        request.state.org_id = str(org.id)
        return TenantContext(user=user, organization=org, role=membership.role, permissions=key_perms, is_api_key=True)

    # ── Access JWT ───────────────────────────────────────────────────────
    payload = decode_token(token)
    user_id = parse_uuid(payload.get("sub"))
    org_id = parse_uuid(payload.get("org"))
    if user_id is None:
        raise _UNAUTH
    if org_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not a member of any organization yet. Ask an administrator for an invitation.",
        )

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise _UNAUTH
    org = await db.get(Organization, org_id)
    if not org or not org.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization is inactive")

    membership = await _membership(db, user.id, org.id)
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")

    request.state.user_id = str(user.id)
    request.state.org_id = str(org.id)
    return TenantContext(
        user=user,
        organization=org,
        role=membership.role,
        permissions=set(ROLE_PERMISSIONS.get(membership.role, set())),
    )


def requires_permission(permission: str):
    """FastAPI dependency factory enforcing a tenant permission."""
    if permission not in _ALL:
        raise RuntimeError(f"Unknown permission: {permission}")

    async def _guard(tenant: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if permission not in tenant.permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")
        return tenant

    return _guard
