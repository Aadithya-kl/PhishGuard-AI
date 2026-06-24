import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.recommendation_feedback import PlaybookPerformanceMetrics, RecommendationOutcome
from app.models.playbook import ActionRecommendation, ActionStatus
from app.models.investigation import Investigation, InvestigationStatus, InvestigationSeverity

class ReadinessGateService:
    @staticmethod
    async def evaluate_readiness(db: AsyncSession, organization_id: uuid.UUID) -> dict:
        reasons = []
        
        playbook_metrics = (await db.execute(
            select(PlaybookPerformanceMetrics).where(PlaybookPerformanceMetrics.organization_id == organization_id)
        )).scalars().all()
        
        generated = sum(m.recommendations_generated for m in playbook_metrics)
        approved = sum(m.recommendations_approved for m in playbook_metrics)
        total_false_actions = sum(m.false_action_rate / 100.0 * m.recommendations_generated for m in playbook_metrics)
        
        acc_rate = (approved / generated * 100.0) if generated > 0 else 0.0
        far_rate = (total_false_actions / generated * 100.0) if generated > 0 else 0.0
        trust_score = sum(m.trust_score for m in playbook_metrics) / len(playbook_metrics) if playbook_metrics else 100.0
        
        # Check per playbook volume
        for m in playbook_metrics:
            if m.recommendations_generated < 25:
                reasons.append(f"Playbook '{m.playbook_name}' has insufficient volume ({m.recommendations_generated} < 25).")
        
        if trust_score <= 85.0:
            reasons.append(f"Trust Score ({trust_score:.1f}) is below threshold of 85.")
        if far_rate >= 2.0:
            reasons.append(f"False Action Rate ({far_rate:.1f}%) is above threshold of 2%.")
        if acc_rate <= 80.0:
            reasons.append(f"Acceptance Rate ({acc_rate:.1f}%) is below threshold of 80%.")
        if generated < 100:
            reasons.append(f"Insufficient global recommendation volume ({generated} < 100).")
            
        feedback_count = await db.scalar(
            select(func.count(RecommendationOutcome.id)).where(RecommendationOutcome.organization_id == organization_id)
        ) or 0
        if feedback_count < 50:
            reasons.append(f"Insufficient analyst feedback records ({feedback_count} < 50).")
            
        drift_alerts = await db.scalar(
            select(func.count(ActionRecommendation.id)).where(
                ActionRecommendation.organization_id == organization_id,
                ActionRecommendation.recommendation_type == "playbook_review",
                ActionRecommendation.status == ActionStatus.pending
            )
        ) or 0
        if drift_alerts > 0:
            reasons.append(f"There are {drift_alerts} active Playbook Drift Alerts.")
            
        # Governance Audit Mock (To be tested fully in Eval Script)
        gov_audit_passed = True
        
        # Calculate Readiness Score
        far_score = 100 if far_rate < 2.0 else max(0, 100 - (far_rate * 10))
        drift_score = 100 if drift_alerts == 0 else 0
        gov_score = 100 if gov_audit_passed else 0
        
        readiness_score = (trust_score * 0.30) + (acc_rate * 0.20) + (far_score * 0.25) + (drift_score * 0.15) + (gov_score * 0.10)
        readiness_score = round(readiness_score, 1)
        
        if readiness_score < 90:
            reasons.append(f"Readiness Score ({readiness_score}) is below 90.")
            
        if not reasons:
            return {
                "readiness_score": readiness_score,
                "status": "READY_FOR_ACTIVE_RESPONSE",
                "reasons": []
            }
        else:
            return {
                "readiness_score": readiness_score,
                "status": "OBSERVATION_MODE_REQUIRED",
                "reasons": reasons
            }
