import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.recommendation_feedback import PlaybookPerformanceMetrics

class RecommendationQualityService:
    @staticmethod
    async def analyze_quality(db: AsyncSession, organization_id: uuid.UUID) -> dict:
        playbooks = (await db.execute(
            select(PlaybookPerformanceMetrics).where(PlaybookPerformanceMetrics.organization_id == organization_id)
        )).scalars().all()
        
        best_performing = []
        average = []
        needs_review = []
        
        details = {}
        for pb in playbooks:
            details[pb.playbook_name] = {
                "volume": pb.recommendations_generated,
                "acceptance_rate": pb.acceptance_rate,
                "modification_rate": pb.analyst_override_rate,
                "false_positive_rate": pb.false_action_rate,
                "time_to_approval": pb.average_approval_latency
            }
            
            if pb.recommendations_generated < 25:
                # Not enough volume to rank properly, treat as needs review or unranked
                needs_review.append(pb.playbook_name)
                continue
                
            if pb.acceptance_rate >= 90.0 and pb.false_action_rate <= 1.0:
                best_performing.append(pb.playbook_name)
            elif pb.acceptance_rate < 80.0 or pb.false_action_rate > 5.0:
                needs_review.append(pb.playbook_name)
            else:
                average.append(pb.playbook_name)
                
        return {
            "best_performing": best_performing,
            "average": average,
            "needs_review": needs_review,
            "details": details
        }
