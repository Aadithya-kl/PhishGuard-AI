from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database import get_db
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.services.executive_metrics import ExecutiveMetricsEngine
from app.services.security_posture import SecurityPostureService
from app.services.mitre_analytics import MitreAnalyticsService
from app.services.readiness_gate import ReadinessGateService
from app.api.dashboard import get_trends, get_automation_metrics

router = APIRouter()

@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))) -> Any:
    return await ExecutiveMetricsEngine.get_overview_metrics(db, tenant.organization.id)

@router.get("/threat-trends")
async def get_threat_trends(days: int = 30, db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))) -> Any:
    # Use the existing dashboard trends logic, but default to 30 days
    return await get_trends(days=days, db=db, tenant=tenant)

@router.get("/mitre-coverage")
async def get_mitre_coverage(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))) -> Any:
    return await MitreAnalyticsService.get_coverage(db, tenant.organization.id)

@router.get("/automation")
async def get_automation(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))) -> Any:
    return await get_automation_metrics(db=db, tenant=tenant)

@router.get("/copilot")
async def get_copilot_analytics(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))) -> Any:
    return await ExecutiveMetricsEngine.get_copilot_metrics(db, tenant.organization.id)

@router.get("/posture")
async def get_security_posture(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))) -> Any:
    return await SecurityPostureService.calculate_posture(db, tenant.organization.id)

@router.get("/readiness")
async def get_readiness_status(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))) -> Any:
    return await ReadinessGateService.evaluate_readiness(db, tenant.organization.id)
