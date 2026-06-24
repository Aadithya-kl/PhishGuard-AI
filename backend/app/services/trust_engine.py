import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.playbook import ActionRecommendation
from app.models.recommendation_feedback import (
    RecommendationOutcome, 
    PlaybookPerformanceMetrics, 
    OutcomeType, 
    FeedbackCategory
)

logger = logging.getLogger(__name__)

class AutomationTrustEngine:
    INTELLIGENCE_FAILURES = {
        FeedbackCategory.FALSE_POSITIVE,
        FeedbackCategory.INCORRECT_ATTRIBUTION,
        FeedbackCategory.INCORRECT_PLAYBOOK,
        FeedbackCategory.INSUFFICIENT_EVIDENCE,
        FeedbackCategory.INCORRECT_RISK_ASSESSMENT
    }
    
    NEUTRAL_OUTCOMES = {
        FeedbackCategory.BUSINESS_EXCEPTION,
        FeedbackCategory.DUPLICATE,
        FeedbackCategory.ALREADY_REMEDIATED,
        FeedbackCategory.OTHER
    }

    @staticmethod
    async def _get_or_create_metrics(db: AsyncSession, organization_id: uuid.UUID, playbook_name: str) -> PlaybookPerformanceMetrics:
        result = await db.execute(
            select(PlaybookPerformanceMetrics).where(
                PlaybookPerformanceMetrics.organization_id == organization_id,
                PlaybookPerformanceMetrics.playbook_name == playbook_name
            )
        )
        metrics = result.scalar_one_or_none()
        if not metrics:
            metrics = PlaybookPerformanceMetrics(
                organization_id=organization_id,
                playbook_name=playbook_name
            )
            db.add(metrics)
        return metrics

    @staticmethod
    async def process_outcome(db: AsyncSession, outcome: RecommendationOutcome):
        """
        Process a recommendation outcome and update the PlaybookPerformanceMetrics.
        """
        logger.info(f"TrustEngine processing outcome {outcome.id} for playbook.")
        
        # We need the playbook name to update metrics
        await db.refresh(outcome, ["recommendation"])
        rec = outcome.recommendation
        
        if not rec:
            return
            
        metrics = await AutomationTrustEngine._get_or_create_metrics(db, outcome.organization_id, rec.playbook_name)
        
        # Ensure we count it as generated if it's the first time we see metrics for this playbook
        # In a real system, the PlaybookEngine should increment `recommendations_generated` upon creation.
        # But for Phase 9.5 we'll just track it via the sum of outcomes or explicitly query the count.
        
        # Calculate new totals
        result = await db.execute(
            select(ActionRecommendation).where(
                ActionRecommendation.organization_id == outcome.organization_id,
                ActionRecommendation.playbook_name == rec.playbook_name
            )
        )
        total_recs = len(result.scalars().all())
        metrics.recommendations_generated = total_recs
        
        # Calculate approvals, rejections, etc.
        outcomes_res = await db.execute(
            select(RecommendationOutcome).join(ActionRecommendation).where(
                ActionRecommendation.organization_id == outcome.organization_id,
                ActionRecommendation.playbook_name == rec.playbook_name
            )
        )
        all_outcomes = outcomes_res.scalars().all()
        
        approved_count = 0
        rejected_count = 0
        modified_count = 0
        intelligence_failures = 0
        
        total_latency = 0.0
        latency_count = 0
        
        for o in all_outcomes:
            if o.outcome_type == OutcomeType.approved:
                approved_count += 1
                # Calculate latency if possible
                latency = (o.created_at - o.recommendation.created_at).total_seconds()
                total_latency += latency
                latency_count += 1
            elif o.outcome_type == OutcomeType.rejected:
                rejected_count += 1
                if o.feedback_category in AutomationTrustEngine.INTELLIGENCE_FAILURES:
                    intelligence_failures += 1
            elif o.outcome_type == OutcomeType.modified:
                modified_count += 1
                
        metrics.recommendations_approved = approved_count
        metrics.recommendations_rejected = rejected_count
        metrics.recommendations_modified = modified_count
        
        if latency_count > 0:
            metrics.average_approval_latency = total_latency / latency_count
            
        if metrics.recommendations_generated > 0:
            metrics.acceptance_rate = (approved_count / metrics.recommendations_generated) * 100.0
            metrics.false_action_rate = (intelligence_failures / metrics.recommendations_generated) * 100.0
            metrics.analyst_override_rate = (modified_count / metrics.recommendations_generated) * 100.0
            
        # Trust Score Calculation
        # Positive: Approved, Modified
        # Negative: Intelligence Failures
        # Neutral: everything else
        total_scoreable = approved_count + modified_count + intelligence_failures
        if total_scoreable == 0:
            metrics.trust_score = 100.0 # Default high trust
        else:
            positive_score = approved_count + modified_count
            # False actions hurt the score heavily
            metrics.trust_score = max(0.0, min(100.0, (positive_score / total_scoreable) * 100.0))
            
        db.add(metrics)
        await db.commit()
