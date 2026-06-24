"""Audit logging middleware and helper."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.audit import AuditLog


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
    """Persist an audit log entry to the database."""
    try:
        async with async_session_factory() as session:
            entry = AuditLog(
                organization_id=organization_id,
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                correlation_id=correlation_id,
                details=details or {},
                ip_address=ip_address,
            )
            session.add(entry)
            await session.commit()
    except Exception as exc:
        logger.warning(f"Failed to write audit log: {exc}")


class AuditMiddleware:
    """Starlette middleware that logs every API request to the audit_logs table."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        client_ip = request.client.host if request.client else "0.0.0.0"
        method = request.method
        path = request.url.path

        # Skip health and docs endpoints
        skip_paths = {"/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}
        if path in skip_paths or path.startswith("/static"):
            await self.app(scope, receive, send)
            return

        # Capture response status
        response_status = 0

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 0)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        # Fire-and-forget audit log (don't block response)
        try:
            user_id_str = None
            org_id_str = None
            
            # Try to extract user_id and org_id from the auth token (best-effort)
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                if token.startswith("pg_"):
                    # For API keys, we'd need a DB lookup. To keep middleware fast, 
                    # we might skip org-level audit for API keys in middleware, 
                    # or do a quick lookup.
                    from app.database import async_session_factory
                    from sqlalchemy import select
                    from app.models.user import ApiKey
                    from passlib.context import CryptContext
                    
                    prefix = token[:8]
                    async with async_session_factory() as session:
                        result = await session.execute(select(ApiKey).where(ApiKey.prefix == prefix))
                        keys = result.scalars().all()
                        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                        for k in keys:
                            if pwd_context.verify(token, k.key_hash):
                                org_id_str = str(k.organization_id)
                                user_id_str = str(k.user_id) if k.user_id else None
                                break
                else:
                    try:
                        from app.core.auth import decode_token
                        payload = decode_token(token)
                        user_id_str = payload.get("sub")
                        org_id_str = payload.get("org")
                    except Exception:
                        pass
                        
            # Use request ID or generate a correlation ID
            corr_id = request.headers.get("x-request-id", str(uuid.uuid4()))

            if org_id_str:
                await log_audit_event(
                    action=f"{method} {path}",
                    organization_id=uuid.UUID(org_id_str),
                    entity_type="api",
                    correlation_id=corr_id,
                    details={"status_code": response_status, "method": method, "path": path},
                    user_id=uuid.UUID(user_id_str) if user_id_str else None,
                    ip_address=client_ip,
                )
        except Exception as exc:
            logger.debug(f"Audit middleware error (non-fatal): {exc}")
