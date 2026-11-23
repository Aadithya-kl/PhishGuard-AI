import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session_factory
from app.models.organization import Organization
from app.models.user import User
from app.models.playbook import ActionRecommendation, ActionStatus
from app.models.recommendation_feedback import RecommendationOutcome, OutcomeType, PlaybookPerformanceMetrics, FeedbackCategory

async def generate_telemetry():
    print("Starting operational telemetry generation...")
    
    async with async_session_factory() as db:
        org_id = uuid.uuid4()
        org = Organization(id=org_id, name="Telemetry Corp", slug=f"telemetry-{uuid.uuid4().hex[:8]}")
        db.add(org)
        user_id = uuid.uuid4()
        user = User(id=user_id, email=f"analyst{uuid.uuid4().hex[:4]}@ta.com", hashed_password="pw", full_name="Analyst")
        db.add(user)
        await db.commit()
        
        playbooks = [
            "Credential Harvesting",
            "Malware Delivery",
            "Business Email Compromise",
            "Spam Campaign",
            "Data Exfiltration"
        ]
        
        now = datetime.now(timezone.utc)
        
        for pb in playbooks:
            # We want > 25 per playbook. We'll do ~250 each to total ~1250 globally.
            volume = random.randint(200, 300)
            
            # Setup Playbook Metrics
            metrics = PlaybookPerformanceMetrics(
                organization_id=org_id,
                playbook_name=pb,
                recommendations_generated=volume,
                recommendations_approved=int(volume * 0.85),
                recommendations_rejected=int(volume * 0.10),
                acceptance_rate=85.0,
                false_action_rate=1.5,
                analyst_override_rate=5.0,
                trust_score=92.0,
                average_approval_latency=120
            )
            db.add(metrics)
            
            for i in range(volume):
                # Spread over 40 days
                days_ago = random.randint(0, 40)
                rec_date = now - timedelta(days=days_ago, hours=random.randint(0, 23))
                
                rec_id = uuid.uuid4()
                rec = ActionRecommendation(
                    id=rec_id,
                    organization_id=org_id,
                    playbook_name=pb,
                    recommendation_type="block_sender",
                    status=ActionStatus.approved,
                    confidence_score=random.uniform(85.0, 99.0),
                    confidence_level="HIGH",
                    recommendation_fingerprint=uuid.uuid4().hex,
                    reasoning="Telemetry simulation"
                )
                db.add(rec)
                
                # We need ~100 feedback records globally. 
                # Let's generate outcome for about 50% of recommendations.
                if random.random() < 0.5:
                    outcome_choice = random.choices(
                        [OutcomeType.approved, OutcomeType.modified, OutcomeType.rejected, OutcomeType.ignored],
                        weights=[80, 10, 5, 5]
                    )[0]
                    
                    fc = None
                    if outcome_choice == OutcomeType.rejected:
                        fc = random.choices([FeedbackCategory.FALSE_POSITIVE, FeedbackCategory.BUSINESS_EXCEPTION], weights=[20, 80])[0]
                    
                    outcome = RecommendationOutcome(
                        organization_id=org_id,
                        recommendation_id=rec_id,
                        analyst_id=user_id,
                        outcome_type=outcome_choice,
                        feedback_category=fc,
                        created_at=rec_date
                    )
                    db.add(outcome)
                    
        await db.commit()
    print("Telemetry generation complete.")
    return org_id

if __name__ == "__main__":
    asyncio.run(generate_telemetry())
