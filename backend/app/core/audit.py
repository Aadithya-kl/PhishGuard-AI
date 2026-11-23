"""Audit logging helper and middleware.

The middleware records every *state-changing* API request (POST/PUT/PATCH/DELETE)
for authenticated tenants. Reads are not logged to keep the table useful and the
hot path fast. Identity is taken from ``request.state`` which the tenant
dependency populates after successful authentication — tokens are never
re-parsed here.
"""

from __future__ import annotations

import uuid
from typing import Optional

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import async_session_factory
from app.models.audit import AuditLog

_MUTATING = {"POST", "PUT", "PATCH", "DELETE"}
_SKIP_PREFIXES = ("/health", "/ready", "/metrics", "/docs", "/redoc", "/openapi.json")


async def log_audit_event(
    action: str,
    organization_id: uuid.UUID,
    entity_type: str = "",
    entity_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    details: Optional[dict] = None,
    user_id: Optional[uuid.UUID] = None,
    ip_address: str = "0.0.0.0",
) -> None:
    """Persist an audit log entry. Failures are logged, never raised."""
    try:
        async with async_session_factory() as session:
            session.add(
                AuditLog(
                    organization_id=organization_id,
                    user_id=user_id,
                    action=action[:100],
                    entity_type=entity_type[:100],
                    entity_id=entity_id,
                    correlation_id=(correlation_id or "")[:36] or None,
                    details=details or {},
                    ip_address=ip_address,
                )
            )
            await session.commit()
    except Exception as exc:  # pragma: no cover
        logger.warning(f"Failed to write audit log: {exc}")


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.method not in _MUTATING or request.url.path.startswith(_SKIP_PREFIXES):
            return response
        org_id = getattr(request.state, "org_id", None)
        if not org_id:
            return response
        try:
            user_id = getattr(request.state, "user_id", None)
            await log_audit_event(
                action=f"{request.method} {request.scope.get('route').path if request.scope.get('route') else request.url.path}",
                organization_id=uuid.UUID(org_id),
                entity_type="api",
                correlation_id=getattr(request.state, "correlation_id", None),
                details={"status_code": response.status_code, "path": request.url.path},
                user_id=uuid.UUID(user_id) if user_id else None,
                ip_address=request.client.host if request.client else "0.0.0.0",
            )
        except Exception as exc:  # pragma: no cover
            logger.debug(f"Audit middleware error (non-fatal): {exc}")
        return response
