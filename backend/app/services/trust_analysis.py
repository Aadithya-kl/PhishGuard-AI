import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.recommendation_feedback import RecommendationOutcome, OutcomeType, FeedbackCategory
from app.models.playbook import ActionRecommendation

class TrustAnalysisService:
    @staticmethod
    async def analyze_trends(db: AsyncSession, organization_id: uuid.UUID) -> dict:
        now = datetime.now(timezone.utc)
        windows = {
            "7_days": now - timedelta(days=7),
            "14_days": now - timedelta(days=14),
            "30_days": now - timedelta(days=30)
        }
        
        results = {}
        for w_name, w_start in windows.items():
            # Get outcomes within this window
            stmt = (
                select(RecommendationOutcome, ActionRecommendation.playbook_name)
                .join(ActionRecommendation, RecommendationOutcome.recommendation_id == ActionRecommendation.id)
                .where(RecommendationOutcome.organization_id == organization_id, RecommendationOutcome.created_at >= w_start)
            )
            outcomes = (await db.execute(stmt)).all()
            
            total = len(outcomes)
            approved = sum(1 for o, _ in outcomes if o.outcome_type == OutcomeType.approved)
            modified = sum(1 for o, _ in outcomes if o.outcome_type == OutcomeType.modified)
            false_actions = sum(1 for o, _ in outcomes if o.outcome_type == OutcomeType.rejected and o.feedback_category in [FeedbackCategory.FALSE_POSITIVE, FeedbackCategory.INCORRECT_ATTRIBUTION, FeedbackCategory.INCORRECT_PLAYBOOK, FeedbackCategory.INSUFFICIENT_EVIDENCE, FeedbackCategory.INCORRECT_RISK_ASSESSMENT])
            
            acc_rate = (approved / total * 100.0) if total > 0 else 0.0
            far_rate = (false_actions / total * 100.0) if total > 0 else 0.0
            override_rate = (modified / total * 100.0) if total > 0 else 0.0
            
            # Playbook specific metrics within this window
            pb_metrics = {}
            for o, pb in outcomes:
                if pb not in pb_metrics:
                    pb_metrics[pb] = {"total": 0, "approved": 0, "false_actions": 0}
                pb_metrics[pb]["total"] += 1
                if o.outcome_type == OutcomeType.approved:
                    pb_metrics[pb]["approved"] += 1
                if o.outcome_type == OutcomeType.rejected and o.feedback_category in [FeedbackCategory.FALSE_POSITIVE, FeedbackCategory.INCORRECT_ATTRIBUTION, FeedbackCategory.INCORRECT_PLAYBOOK, FeedbackCategory.INSUFFICIENT_EVIDENCE, FeedbackCategory.INCORRECT_RISK_ASSESSMENT]:
                    pb_metrics[pb]["false_actions"] += 1
                    
            for pb, m in pb_metrics.items():
                m["acceptance_rate"] = (m["approved"] / m["total"] * 100.0) if m["total"] > 0 else 0.0
                m["false_action_rate"] = (m["false_actions"] / m["total"] * 100.0) if m["total"] > 0 else 0.0
                
            results[w_name] = {
                "total": total,
                "acceptance_rate": acc_rate,
                "override_rate": override_rate,
                "false_action_rate": far_rate,
                "playbooks": pb_metrics
            }
            
        # Overall trend classification (Improving, Stable, Degrading)
        # Comparing 7 days vs 14 days
        trend = "Stable"
        if results["7_days"]["total"] > 0 and results["14_days"]["total"] > 0:
            if results["7_days"]["acceptance_rate"] > results["14_days"]["acceptance_rate"] + 5:
                trend = "Improving"
            elif results["7_days"]["acceptance_rate"] < results["14_days"]["acceptance_rate"] - 5:
                trend = "Degrading"
                
        results["overall_trend"] = trend
        return results
