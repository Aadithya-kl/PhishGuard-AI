import logging
import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.playbook import ActionRecommendation, ActionStatus
from app.services.trust_analysis import TrustAnalysisService

logger = logging.getLogger(__name__)

class DriftDetectionService:
    @staticmethod
    async def run_drift_detection(db: AsyncSession):
        """
        Scan playbook performance metrics and generate review recommendations
        for playbooks that are deteriorating.
        """
        logger.info("Starting drift detection scan.")
        
        # Since we might have multiple organizations, we would query organizations first
        # For simplicity, we assume we get org_id as parameter or iterate over all
        # Let's iterate over organizations that have telemetry
        result = await db.execute(select(ActionRecommendation.organization_id).distinct())
        org_ids = result.scalars().all()
        
        for org_id in org_ids:
            trends = await TrustAnalysisService.analyze_trends(db, org_id)
            
            pb_metrics_7 = trends["7_days"].get("playbooks", {})
            pb_metrics_14 = trends["14_days"].get("playbooks", {})
            
            for pb_name, metrics_7 in pb_metrics_7.items():
                if metrics_7["total"] < 20:
                    continue
                    
                metrics_14 = pb_metrics_14.get(pb_name, {"acceptance_rate": 0})
                
                needs_review = False
                reasons = []
                
                # Check for >10% drop between 14 day and 7 day window
                # Wait, 14 days window includes the last 7 days. 
                # Let's just compare the rates we got.
                # A more precise way would be 7-14 vs 0-7, but using the existing windows:
                # If acceptance rate in 7 days is 10% lower than the broader 14 day average:
                if metrics_7["acceptance_rate"] < metrics_14["acceptance_rate"] - 10.0:
                    needs_review = True
                    reasons.append(f"Acceptance rate dropped >10% (from {metrics_14['acceptance_rate']:.1f}% to {metrics_7['acceptance_rate']:.1f}%) with volume {metrics_7['total']}")
                    
                if metrics_7["false_action_rate"] > 5.0:
                    needs_review = True
                    reasons.append(f"False action rate spiked to {metrics_7['false_action_rate']:.1f}%")
                    
                if needs_review:
                    reason_str = " | ".join(reasons)
                    
                    fingerprint = hashlib.sha256(
                        f"{org_id}:playbook_review:{pb_name}:{datetime.now(timezone.utc).strftime('%Y-%m')}".encode()
                    ).hexdigest()
                
                    # Check if we already created one this month
                    existing = await db.execute(
                        select(ActionRecommendation).where(
                            ActionRecommendation.recommendation_fingerprint == fingerprint
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue
                        
                    rec = ActionRecommendation(
                        organization_id=org_id,
                        playbook_name="Platform Operations",
                        recommendation_type="playbook_review",
                        status=ActionStatus.pending,
                        confidence_score=100.0,
                        confidence_level="HIGH",
                        reasoning=f"Playbook '{pb_name}' requires review: {reason_str}",
                        triggering_detections=["Playbook Drift"],
                        triggering_mitre_ids=[],
                        triggering_iocs=[],
                        recommendation_fingerprint=fingerprint
                    )
                    db.add(rec)
                
        await db.commit()
        logger.info("Drift detection scan complete.")
