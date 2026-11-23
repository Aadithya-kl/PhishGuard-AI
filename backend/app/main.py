"""PhishGuard AI — FastAPI application factory."""

from __future__ import annotations

import hmac
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.core.audit import AuditMiddleware
from app.core.rate_limit import limiter
from app.core.token_store import token_store
from app.database import engine

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.graph import router as graph_router
from app.api.investigations import router as investigations_router
from app.api.scans import router as scans_router
from app.api.threat_hunting import router as threat_hunting_router
from app.api.routers.api_keys import router as api_keys_router
from app.api.routers.copilot import router as copilot_router
from app.api.routers.executive import router as executive_router
from app.api.routers.organizations import router as organizations_router
from app.api.routers.playbooks import router as playbooks_router
from app.api.routers.reports import router as reports_router

_CORRELATION_RE = re.compile(r"^[A-Za-z0-9\-]{8,64}$")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.using_dev_secret:
        logger.warning("SECRET_KEY is not set — using an INSECURE development key. Never deploy like this.")
    if settings.ALLOW_PUBLIC_REGISTRATION and settings.is_production:
        logger.warning("Public self-registration is enabled in production.")
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="PhishGuard AI — email threat analysis API",
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# ── Metrics (optional, token-protected) ──────────────────────────────────
try:
    from prometheus_fastapi_instrumentator import Instrumentator

    _instrumentator = Instrumentator(should_group_status_codes=False, should_ignore_untemplated=True).instrument(app)

    @app.get("/metrics", include_in_schema=False)
    async def metrics(request: Request):
        if settings.METRICS_TOKEN:
            supplied = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
            if not hmac.compare_digest(supplied, settings.METRICS_TOKEN):
                return PlainTextResponse("Forbidden", status_code=403)
        elif settings.is_production:
            return PlainTextResponse("Not found", status_code=404)
        from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

        return PlainTextResponse(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
except ImportError:  # pragma: no cover
    logger.info("prometheus instrumentation not installed; /metrics disabled")

# ── Rate limiting ────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── Audit trail for state-changing requests ──────────────────────────────
app.add_middleware(AuditMiddleware)

# ── CORS (explicit origins only; credentials needed for refresh cookie) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID", "X-Token-Delivery"],
    expose_headers=["X-Correlation-ID"],
    max_age=600,
)

# ── Host header validation ───────────────────────────────────────────────
if settings.trusted_hosts_list != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)


@app.middleware("http")
async def security_and_correlation(request: Request, call_next):
    supplied = request.headers.get("X-Correlation-ID", "")
    corr_id = supplied if _CORRELATION_RE.match(supplied) else str(uuid.uuid4())
    request.state.correlation_id = corr_id
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(f"Unhandled error correlation_id={corr_id} path={request.url.path}")
        response = JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred.", "correlation_id": corr_id},
        )
    response.headers["X-Correlation-ID"] = corr_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if not request.url.path.startswith(("/docs", "/redoc")):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    if request.url.path.startswith(settings.API_V1_PREFIX):
        response.headers.setdefault("Cache-Control", "no-store")
    logger.debug(f"{request.method} {request.url.path} {response.status_code} {(time.perf_counter() - start) * 1000:.1f}ms")
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    # Do not echo submitted values (could contain passwords) back to the client.
    errors = [{"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


# ── Routers ──────────────────────────────────────────────────────────────
p = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=f"{p}/auth", tags=["auth"])
app.include_router(scans_router, prefix=f"{p}/scans", tags=["scans"])
app.include_router(dashboard_router, prefix=f"{p}/dashboard", tags=["dashboard"])
app.include_router(threat_hunting_router, prefix=f"{p}/threat-hunting", tags=["threat-hunting"])
app.include_router(investigations_router, prefix=f"{p}/investigations", tags=["investigations"])
app.include_router(graph_router, prefix=f"{p}/graph", tags=["graph"])
app.include_router(reports_router, prefix=f"{p}/reports", tags=["reports"])
app.include_router(copilot_router, prefix=f"{p}/copilot", tags=["copilot"])
app.include_router(api_keys_router, prefix=f"{p}/api-keys", tags=["api-keys"])
app.include_router(organizations_router, prefix=f"{p}/organizations", tags=["organizations"])
app.include_router(playbooks_router, prefix=f"{p}/playbooks", tags=["playbooks"])
app.include_router(executive_router, prefix=f"{p}/executive", tags=["executive"])


@app.get("/health", tags=["health"], include_in_schema=False)
@limiter.exempt
async def health_check():
    return {"status": "ok"}


@app.get("/ready", tags=["health"], include_in_schema=False)
@limiter.exempt
async def readiness_check():
    checks = {"database": False, "redis": False}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:
        logger.error(f"Readiness: database unavailable: {exc}")
    checks["redis"] = await token_store.ping()
    ok = all(checks.values())
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ready" if ok else "degraded", **checks})
