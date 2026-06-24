import uuid
import hashlib
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.playbook import ActionRecommendation
from app.playbooks.registry import registry
from app.playbooks.models import ActionRecommendationCreate
import logging

logger = logging.getLogger(__name__)

class PlaybookEngine:
    @staticmethod
    def _generate_fingerprint(org_id: uuid.UUID, playbook_name: str, recommendation_type: str, trigger_context: dict) -> str:
        """
        Generates a deterministic fingerprint for deduplication.
        If a recommendation has the exact same action intent and playbook within the organization,
        it yields the same fingerprint.
        We group by org_id, playbook_name, and recommendation_type.
        """
        base = f"{org_id}:{playbook_name}:{recommendation_type}"
        return hashlib.sha256(base.encode('utf-8')).hexdigest()

    @staticmethod
    async def process_scan(db: AsyncSession, organization_id: uuid.UUID, scan_id: uuid.UUID, scan_data: dict) -> list[ActionRecommendation]:
        """
        Evaluate a completed scan against all registered playbooks.
        Creates and deduplicates ActionRecommendations.
        """
        logger.info(f"Running PlaybookEngine for Scan {scan_id}")
        created_actions = []
        
        all_playbooks = registry.get_all()
        for name, playbook_func in all_playbooks.items():
            # Get recommended actions from playbook logic
            actions: list[ActionRecommendationCreate] = playbook_func(scan_data)
            
            for action_create in actions:
                fingerprint = PlaybookEngine._generate_fingerprint(
                    organization_id, 
                    action_create.playbook_name, 
                    action_create.recommendation_type,
                    {}
                )
                
                # Deduplication logic
                # Check if a pending or approved recommendation with this fingerprint already exists
                result = await db.execute(
                    select(ActionRecommendation)
                    .where(
                        ActionRecommendation.organization_id == organization_id,
                        ActionRecommendation.recommendation_fingerprint == fingerprint,
                        ActionRecommendation.status.in_(["Pending", "Approved"])
                    )
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing recommendation
                    existing.affected_users_count += 1
                    
                    # Merge reasoning or detections if they differ
                    for det in action_create.triggering_detections:
                        if det not in existing.triggering_detections:
                            existing.triggering_detections.append(det)
                            
                    for ioc in action_create.triggering_iocs:
                        if ioc not in existing.triggering_iocs:
                            existing.triggering_iocs.append(ioc)
                            
                    # Optionally upgrade confidence if new signals are stronger
                    if action_create.confidence_score > existing.confidence_score:
                        existing.confidence_score = action_create.confidence_score
                        existing.confidence_level = action_create.confidence_level
                    
                    db.add(existing)
                    created_actions.append(existing)
                    logger.info(f"Deduplicated recommendation: {fingerprint}")
                else:
                    # Create new
                    new_rec = ActionRecommendation(
                        organization_id=organization_id,
                        scan_id=scan_id,
                        playbook_name=action_create.playbook_name,
                        recommendation_type=action_create.recommendation_type,
                        recommendation_fingerprint=fingerprint,
                        confidence_score=action_create.confidence_score,
                        confidence_level=action_create.confidence_level,
                        reasoning=action_create.reasoning,
                        triggering_detections=action_create.triggering_detections,
                        triggering_mitre_ids=action_create.triggering_mitre_ids,
                        triggering_iocs=action_create.triggering_iocs,
                        affected_users_count=action_create.affected_users_count
                    )
                    db.add(new_rec)
                    created_actions.append(new_rec)
                    
        await db.commit()
        return created_actions
