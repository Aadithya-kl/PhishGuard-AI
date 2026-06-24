from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uuid
import time
from loguru import logger
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.core.rate_limit import limiter

from app.api.auth import router as auth_router
from app.api.scans import router as scans_router
from app.api.dashboard import router as dashboard_router
from app.api.threat_hunting import router as threat_hunting_router
from app.api.investigations import router as investigations_router
from app.api.graph import router as graph_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="PhishGuard AI Backend API - Hardened",
    lifespan=lifespan
)

# Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_instrument_requests_inprogress=True,
    inprogress_name="inprogress",
    inprogress_labels=True,
).instrument(app).expose(app, endpoint="/metrics")

# SlowAPI setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID and Request Logging Middleware
@app.middleware("http")
async def add_correlation_id_and_log(request: Request, call_next):
    corr_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Pass correlation id to log context or request state
    request.state.correlation_id = corr_id
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Correlation-ID"] = corr_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as exc:
        logger.error(f"CorrelationId={corr_id} | Unhandled Exception: {str(exc)}")
        # Do not leak stack traces to client
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "correlation_id": corr_id,
                "message": "An unexpected error occurred. Please contact support."
            }
        )

# Include routers
api_prefix = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=f"{api_prefix}/auth", tags=["auth"])
app.include_router(scans_router, prefix=f"{api_prefix}/scans", tags=["scans"])
app.include_router(dashboard_router, prefix=f"{api_prefix}/dashboard", tags=["dashboard"])
app.include_router(threat_hunting_router, prefix=f"{api_prefix}/threat-hunting", tags=["threat-hunting"])
app.include_router(investigations_router, prefix=f"{api_prefix}/investigations", tags=["investigations"])
from app.api.routers.reports import router as reports_router
from app.api.routers.copilot import router as copilot_router
from app.api.routers.api_keys import router as api_keys_router
from app.api.routers.organizations import router as organizations_router
from app.api.routers.playbooks import router as playbooks_router
from app.api.routers.executive import router as executive_router

app.include_router(graph_router, prefix=f"{api_prefix}/graph", tags=["graph"])
app.include_router(reports_router, prefix=f"{api_prefix}/reports", tags=["reports"])
app.include_router(copilot_router, prefix=f"{api_prefix}/copilot", tags=["copilot"])
app.include_router(api_keys_router, prefix=f"{api_prefix}/api-keys", tags=["api-keys"])
app.include_router(organizations_router, prefix=f"{api_prefix}/organizations", tags=["organizations"])
app.include_router(playbooks_router, prefix=f"{api_prefix}/playbooks", tags=["playbooks"])
app.include_router(executive_router, prefix=f"{api_prefix}/executive", tags=["executive"])

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}

@app.get("/ready", tags=["health"])
async def readiness_check():
    # In production, check DB, Redis, etc.
    return {"status": "ready"}
