"""Role-based access control (RBAC) dependency factories."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_user
from app.models.user import User, UserRole

# ── Permissions matrix ───────────────────────────────────────────────────
PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.admin: {
        "scan", "view", "delete", "hunt", "report", "copilot",
        "manage_users", "manage_api_keys", "view_audit", "admin",
    },
    UserRole.analyst: {
        "scan", "view", "hunt", "report", "copilot", "manage_api_keys",
    },
    UserRole.viewer: {
        "view",
    },
}


def require_role(*roles: UserRole) -> Callable:
    """FastAPI dependency that enforces the user has one of the specified roles.

    Usage::

        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.admin))])
        async def admin_only(): ...
    """

    async def _guard(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in roles]}",
            )
        return current_user

    return _guard


def require_permission(permission: str) -> Callable:
    """FastAPI dependency that enforces the user has a specific permission.

    Usage::

        @router.post("/scan", dependencies=[Depends(require_permission("scan"))])
        async def create_scan(): ...
    """

    async def _guard(current_user: User = Depends(get_current_user)) -> User:
        user_perms = PERMISSIONS.get(current_user.role, set())
        if permission not in user_perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return current_user

    return _guard
