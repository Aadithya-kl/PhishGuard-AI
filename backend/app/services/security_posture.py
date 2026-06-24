import logging
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.investigation import Investigation, InvestigationStatus, InvestigationSeverity
from app.models.threat import ThreatCampaign
from app.models.recommendation_feedback import PlaybookPerformanceMetrics
from app.models.scan import EmailScan, RiskLevel

logger = logging.getLogger(__name__)

class SecurityPostureService:
    @staticmethod
    async def calculate_posture(db: AsyncSession, organization_id: uuid.UUID) -> dict:
        score = 100
        
        # 1. Critical Open Investigations
        critical_open = await db.scalar(
            select(func.count(Investigation.id)).where(
                Investigation.organization_id == organization_id,
                Investigation.status != InvestigationStatus.closed,
                Investigation.severity == InvestigationSeverity.critical
            )
        ) or 0
        score -= (critical_open * 5)
        
        # 2. High Open Investigations
        high_open = await db.scalar(
            select(func.count(Investigation.id)).where(
                Investigation.organization_id == organization_id,
                Investigation.status != InvestigationStatus.closed,
                Investigation.severity == InvestigationSeverity.high
            )
        ) or 0
        score -= (high_open * 2)
        
        # 3. Active Campaigns
        active_campaigns = await db.scalar(
            select(func.count(ThreatCampaign.id)).where(
                ThreatCampaign.organization_id == organization_id,
                ThreatCampaign.status == "active"
            )
        ) or 0
        score -= (active_campaigns * 3)
        
        # 4. Automation Trust Below 80
        playbook_metrics = (await db.execute(
            select(PlaybookPerformanceMetrics).where(PlaybookPerformanceMetrics.organization_id == organization_id)
        )).scalars().all()
        
        trust_score = sum(m.trust_score for m in playbook_metrics) / len(playbook_metrics) if playbook_metrics else 100.0
        if trust_score < 80.0:
            score -= 10
            
        # 5. False Action Rate Above 5%
        generated = sum(m.recommendations_generated for m in playbook_metrics)
        total_false_actions = sum(m.false_action_rate / 100.0 * m.recommendations_generated for m in playbook_metrics)
        far_rate = (total_false_actions / generated * 100.0) if generated > 0 else 0.0
        if far_rate > 5.0:
            score -= 15
            
        # 6. Investigation Backlog > 25
        open_invs = await db.scalar(
            select(func.count(Investigation.id)).where(
                Investigation.organization_id == organization_id,
                Investigation.status != InvestigationStatus.closed
            )
        ) or 0
        if open_invs > 25:
            score -= 10
            
        # 7. Risk Trend Increasing
        now = datetime.now(timezone.utc)
        last_7_days = now - timedelta(days=7)
        prev_7_days = now - timedelta(days=14)
        
        recent_threats = await db.scalar(
            select(func.count(EmailScan.id)).where(
                EmailScan.organization_id == organization_id,
                EmailScan.risk_level.in_([RiskLevel.high, RiskLevel.suspicious]),
                EmailScan.scanned_at >= last_7_days
            )
        ) or 0
        
        past_threats = await db.scalar(
            select(func.count(EmailScan.id)).where(
                EmailScan.organization_id == organization_id,
                EmailScan.risk_level.in_([RiskLevel.high, RiskLevel.suspicious]),
                EmailScan.scanned_at >= prev_7_days,
                EmailScan.scanned_at < last_7_days
            )
        ) or 0
        
        if recent_threats > past_threats:
            score -= 10
            
        # Clamp
        score = max(0, min(100, score))
        
        # Rating Band
        if score >= 90: rating = "Excellent"
        elif score >= 75: rating = "Good"
        elif score >= 60: rating = "Fair"
        elif score >= 40: rating = "Poor"
        else: rating = "Critical"
        
        return {
            "score": score,
            "rating": rating,
            "factors": {
                "critical_open": critical_open,
                "high_open": high_open,
                "active_campaigns": active_campaigns,
                "automation_trust": round(trust_score, 1),
                "false_action_rate": round(far_rate, 1),
                "backlog": open_invs,
                "risk_trend_increasing": recent_threats > past_threats
            }
        }
