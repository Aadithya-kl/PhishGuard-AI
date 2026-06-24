from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, case
from datetime import datetime, timezone, timedelta
from typing import Any

from app.database import get_db
from app.models.user import User
from app.core.tenant_context import TenantContext, requires_permission, Permission
from app.models.scan import EmailScan, RiskLevel, UrlAnalysis
from app.schemas.dashboard import (
    DashboardStats, 
    RiskDistribution, 
    TrendsResponse, 
    TrendPoint,
    AttackCategoriesResponse,
    AttackCategory,
    TopDomainsResponse,
    TopDomain,
    AutomationMetricsResponse
)
from app.schemas.scan import ScanSummaryResponse

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Total scans
    total_scans_result = await db.execute(select(func.count(EmailScan.id)).where(EmailScan.organization_id == tenant.organization.id))
    total_scans = total_scans_result.scalar() or 0
    
    # Scans today
    scans_today_result = await db.execute(select(func.count(EmailScan.id)).where(EmailScan.organization_id == tenant.organization.id, EmailScan.scanned_at >= today_start))
    scans_today = scans_today_result.scalar() or 0
    
    # Risk counts
    risk_counts = await db.execute(
        select(EmailScan.risk_level, func.count(EmailScan.id))
        .where(EmailScan.organization_id == tenant.organization.id)
        .group_by(EmailScan.risk_level)
    )
    counts = dict(risk_counts.all())
    high_risk_count = counts.get(RiskLevel.high, 0)
    suspicious_count = counts.get(RiskLevel.suspicious, 0)
    safe_count = counts.get(RiskLevel.safe, 0)
    
    # Threats detected = high + suspicious
    threats_detected = high_risk_count + suspicious_count
    
    # Avg risk score
    avg_score_result = await db.execute(select(func.avg(EmailScan.overall_risk_score)).where(EmailScan.organization_id == tenant.organization.id))
    avg_risk_score = avg_score_result.scalar() or 0.0
    
    # Scanned URLs
    urls_scanned_result = await db.execute(
        select(func.count(UrlAnalysis.id))
        .join(EmailScan)
        .where(EmailScan.organization_id == tenant.organization.id)
    )
    urls_scanned = urls_scanned_result.scalar() or 0
    
    # Playbook Metrics
    from app.models.playbook import ActionRecommendation, ActionStatus
    recs_result = await db.execute(
        select(ActionRecommendation.status, func.count(ActionRecommendation.id))
        .where(ActionRecommendation.organization_id == tenant.organization.id)
        .group_by(ActionRecommendation.status)
    )
    recs_counts = dict(recs_result.all())
    
    gen = sum(recs_counts.values())
    appr = recs_counts.get(ActionStatus.approved, 0) + recs_counts.get(ActionStatus.executed, 0)
    rej = recs_counts.get(ActionStatus.rejected, 0)
    
    acceptance_rate = (appr / (appr + rej) * 100) if (appr + rej) > 0 else 0.0
    
    return DashboardStats(
        total_scans=total_scans,
        threats_detected=threats_detected,
        scans_today=scans_today,
        avg_risk_score=round(avg_risk_score, 1),
        urls_scanned=urls_scanned,
        risk_distribution={
            "safe": safe_count,
            "low": counts.get(RiskLevel.low, 0),
            "suspicious": suspicious_count,
            "high": high_risk_count
        },
        recommendations_generated=gen,
        recommendations_approved=appr,
        recommendations_rejected=rej,
        automation_acceptance_rate=round(acceptance_rate, 1)
    )

@router.get("/trends", response_model=TrendsResponse)
async def get_trends(days: int = 7, db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)
    
    # Group by date
    result = await db.execute(
        select(
            func.date(EmailScan.scanned_at).label('date'),
            func.count(EmailScan.id).label('total'),
            func.sum(case((EmailScan.risk_level == RiskLevel.high, 1), else_=0)).label('threats')
        )
        .where(EmailScan.organization_id == tenant.organization.id, EmailScan.scanned_at >= start_date)
        .group_by(func.date(EmailScan.scanned_at))
        .order_by(func.date(EmailScan.scanned_at))
    )
    
    points = []
    for row in result.all():
        points.append(TrendPoint(
            date=row.date.strftime("%Y-%m-%d"),
            scans=row.total,
            threats=row.threats or 0
        ))
        
    return TrendsResponse(points=points)

@router.get("/attack-categories", response_model=AttackCategoriesResponse)
async def get_attack_categories(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    result = await db.execute(
        select(EmailScan.attack_type, func.count(EmailScan.id))
        .where(EmailScan.organization_id == tenant.organization.id, EmailScan.attack_type.is_not(None), EmailScan.attack_type != "Benign")
        .group_by(EmailScan.attack_type)
        .order_by(func.count(EmailScan.id).desc())
        .limit(5)
    )
    
    categories = []
    for row in result.all():
        categories.append(AttackCategory(
            name=row.attack_type,
            count=row.count
        ))
        
    return AttackCategoriesResponse(categories=categories)

@router.get("/recent-threats", response_model=list[ScanSummaryResponse])
async def get_recent_threats(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    result = await db.execute(
        select(EmailScan)
        .where(EmailScan.organization_id == tenant.organization.id, EmailScan.risk_level.in_([RiskLevel.high, RiskLevel.suspicious]))
        .order_by(EmailScan.scanned_at.desc())
        .limit(5)
    )
    
    scans = result.scalars().all()
    return [ScanSummaryResponse.model_validate(scan) for scan in scans]

@router.get("/top-domains", response_model=TopDomainsResponse)
async def get_top_domains(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    # Very basic domain extraction from sender_address
    # In production, we'd query the IOC table instead
    result = await db.execute(
        select(
            func.split_part(EmailScan.sender_address, '@', 2).label('domain'),
            func.count(EmailScan.id).label('count')
        )
        .where(EmailScan.organization_id == tenant.organization.id, EmailScan.risk_level.in_([RiskLevel.high, RiskLevel.suspicious]))
        .group_by('domain')
        .order_by(func.count(EmailScan.id).desc())
        .limit(5)
    )
    
    domains = []
    for row in result.all():
        if row.domain:
            domains.append(TopDomain(
                domain=row.domain,
                count=row.count
            ))
            
    return TopDomainsResponse(domains=domains)


@router.get("/automation-metrics", response_model=AutomationMetricsResponse)
async def get_automation_metrics(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(requires_permission(Permission.VIEW_SCANS))):
    from app.models.recommendation_feedback import PlaybookPerformanceMetrics
    from app.models.playbook import ActionRecommendation
    
    result = await db.execute(
        select(PlaybookPerformanceMetrics)
        .where(PlaybookPerformanceMetrics.organization_id == tenant.organization.id)
    )
    metrics_list = result.scalars().all()
    
    # Calculate coverage
    # Find total scans
    scans_result = await db.execute(
        select(func.count(EmailScan.id))
        .where(EmailScan.organization_id == tenant.organization.id, EmailScan.risk_level.in_([RiskLevel.high, RiskLevel.suspicious]))
    )
    malicious_scans = scans_result.scalar() or 0
    
    total_generated = sum(m.recommendations_generated for m in metrics_list)
    total_approved = sum(m.recommendations_approved for m in metrics_list)
    total_rejected = sum(m.recommendations_rejected for m in metrics_list)
    
    # Recalculate global rates
    coverage = (total_generated / malicious_scans * 100.0) if malicious_scans > 0 else 0.0
    
    # We can average the rates from playbooks or compute overall from raw counts
    total_override = sum(m.recommendations_modified for m in metrics_list)
    
    # To compute total false actions accurately, we need the sum of false actions, which is metrics.false_action_rate * metrics.generated
    total_false_actions = sum(int(m.false_action_rate / 100.0 * m.recommendations_generated) for m in metrics_list)
    
    acceptance_rate = (total_approved / total_generated * 100.0) if total_generated > 0 else 0.0
    false_action_rate = (total_false_actions / total_generated * 100.0) if total_generated > 0 else 0.0
    override_rate = (total_override / total_generated * 100.0) if total_generated > 0 else 0.0
    
    avg_latency = sum(m.average_approval_latency for m in metrics_list) / len(metrics_list) if metrics_list else 0.0
    
    high_trust = [m.playbook_name for m in metrics_list if m.trust_score >= 80.0]
    low_trust = [m.playbook_name for m in metrics_list if m.trust_score < 40.0]
    
    return AutomationMetricsResponse(
        recommendations_generated=total_generated,
        recommendations_approved=total_approved,
        recommendations_rejected=total_rejected,
        acceptance_rate=round(acceptance_rate, 1),
        false_action_rate=round(false_action_rate, 1),
        analyst_override_rate=round(override_rate, 1),
        recommendation_coverage=round(coverage, 1),
        average_approval_latency=round(avg_latency, 1),
        high_trust_playbooks=high_trust,
        low_trust_playbooks=low_trust
    )
