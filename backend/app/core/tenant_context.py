"""Tenant context and multi-tenancy dependency injection."""

from dataclasses import dataclass
from typing import Optional
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import decode_token, oauth2_scheme
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


# ── Phase 8 Permission Matrix ──────────────────────────────────────────

class Permission:
    VIEW_SCANS = "view_scans"
    UPLOAD_SCANS = "upload_scans"
    VIEW_GRAPH = "view_graph"
    MANAGE_INVESTIGATIONS = "manage_investigations"
    GENERATE_REPORTS = "generate_reports"
    USE_COPILOT = "use_copilot"
    MANAGE_USERS = "manage_users"
    MANAGE_ORGANIZATION = "manage_organization"
    EXPORT_DATA = "export_data"


ROLE_PERMISSIONS: dict[OrganizationRole, set[str]] = {
    OrganizationRole.platform_admin: {
        Permission.VIEW_SCANS, Permission.UPLOAD_SCANS, Permission.VIEW_GRAPH,
        Permission.MANAGE_INVESTIGATIONS, Permission.GENERATE_REPORTS,
        Permission.USE_COPILOT, Permission.MANAGE_USERS,
        Permission.MANAGE_ORGANIZATION, Permission.EXPORT_DATA
    },
    OrganizationRole.org_admin: {
        Permission.VIEW_SCANS, Permission.UPLOAD_SCANS, Permission.VIEW_GRAPH,
        Permission.MANAGE_INVESTIGATIONS, Permission.GENERATE_REPORTS,
        Permission.USE_COPILOT, Permission.MANAGE_USERS,
        Permission.MANAGE_ORGANIZATION, Permission.EXPORT_DATA
    },
    OrganizationRole.soc_manager: {
        Permission.VIEW_SCANS, Permission.UPLOAD_SCANS, Permission.VIEW_GRAPH,
        Permission.MANAGE_INVESTIGATIONS, Permission.GENERATE_REPORTS,
        Permission.USE_COPILOT, Permission.EXPORT_DATA
    },
    OrganizationRole.soc_analyst: {
        Permission.VIEW_SCANS, Permission.UPLOAD_SCANS, Permission.VIEW_GRAPH,
        Permission.USE_COPILOT, Permission.MANAGE_INVESTIGATIONS
    },
    OrganizationRole.read_only: {
        Permission.VIEW_SCANS, Permission.VIEW_GRAPH
    }
}


async def get_tenant_context(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> TenantContext:
    """Resolve the current tenant context from JWT or API key.
    
    For JWTs, we expect an 'org' claim in the payload indicating the active organization.
    For API keys, the key belongs directly to the organization.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if it's an API key
    if token.startswith("pg_"):
        # We need to resolve the organization and permissions of the API key
        from passlib.context import CryptContext
        from app.models.user import ApiKey
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        prefix = token[:8]
        result = await db.execute(select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.is_active.is_(True)))
        api_keys = result.scalars().all()
        for api_key in api_keys:
            if pwd_context.verify(token, api_key.key_hash):
                from datetime import datetime, timezone
                if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")
                
                # Retrieve organization
                org_result = await db.execute(select(Organization).where(Organization.id == api_key.organization_id))
                org = org_result.scalar_one_or_none()
                if not org or not org.is_active:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization inactive")
                
                # Retrieve user if api key is bound to one, otherwise a dummy user
                user = None
                if api_key.user_id:
                    user_result = await db.execute(select(User).where(User.id == api_key.user_id))
                    user = user_result.scalar_one_or_none()
                
                if not user:
                    # Fallback to the organization's platform admin
                    admin_member = await db.execute(
                        select(OrganizationMember)
                        .where(
                            OrganizationMember.organization_id == org.id,
                            OrganizationMember.role == OrganizationRole.platform_admin,
                            OrganizationMember.is_active.is_(True)
                        )
                        .limit(1)
                    )
                    admin = admin_member.scalar_one_or_none()
                    if admin:
                        user_result = await db.execute(select(User).where(User.id == admin.user_id))
                        user = user_result.scalar_one_or_none()
                    
                    if not user:
                        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization has no active admins to proxy API key")

                permissions = set(api_key.permissions) if api_key.permissions else set()
                return TenantContext(
                    user=user,
                    organization=org,
                    role=OrganizationRole.soc_analyst, # API keys use explicit permissions
                    permissions=permissions,
                    is_api_key=True
                )
                
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    # Otherwise treat as JWT
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    org_id = payload.get("org")

    if not user_id or not org_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user or organization in token")

    # Fetch User
    user_result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Fetch Organization
    org_result = await db.execute(select(Organization).where(Organization.id == uuid.UUID(org_id)))
    org = org_result.scalar_one_or_none()
    if not org or not org.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization not found or inactive")

    # Verify Membership
    member_result = await db.execute(
        select(OrganizationMember)
        .where(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == org.id,
            OrganizationMember.is_active.is_(True)
        )
    )
    membership = member_result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")

    permissions = ROLE_PERMISSIONS.get(membership.role, set())
    
    return TenantContext(
        user=user,
        organization=org,
        role=membership.role,
        permissions=permissions,
        is_api_key=False
    )


def requires_permission(permission: str):
    """FastAPI dependency to enforce tenant permissions."""
    def _guard(tenant: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if permission not in tenant.permissions:
            # If the user is a platform admin, allow it implicitly?
            if Permission.MANAGE_ORGANIZATION in tenant.permissions and tenant.role == OrganizationRole.platform_admin:
                pass # Or just explicitly check tenant.permissions
            
            if permission not in tenant.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permission: {permission}"
                )
        return tenant
    return _guard
