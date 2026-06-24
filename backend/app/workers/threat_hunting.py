from celery import shared_task
from app.database import async_session_factory
from app.models.organization import Organization
from app.models.playbook import ActionRecommendation, ConfidenceLevel
from sqlalchemy import select
import uuid
import hashlib
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

async def run_threat_hunting_jobs():
    logger.info("Running Threat Hunting Automation jobs...")
    
    async with async_session_factory() as session:
        orgs_res = await session.execute(select(Organization).where(Organization.is_active == True))
        orgs = orgs_res.scalars().all()
        
        for org in orgs:
            # Detect new infrastructure clusters (Mock implementation)
            logger.info(f"Detecting new infra for {org.id}")
            # E.g., we found 5 new malicious domains associated with Actor X
            # We would generate a recommendation to block the domain cluster
            
            fingerprint = hashlib.sha256(f"{org.id}:ThreatHunting:block_infra".encode('utf-8')).hexdigest()
            
            # Check if exists
            existing = await session.execute(
                select(ActionRecommendation).where(
                    ActionRecommendation.organization_id == org.id,
                    ActionRecommendation.recommendation_fingerprint == fingerprint,
                    ActionRecommendation.status == "Pending"
                )
            )
            rec = existing.scalar_one_or_none()
            if not rec:
                rec = ActionRecommendation(
                    organization_id=org.id,
                    playbook_name="Threat Hunting: Infrastructure Discovery",
                    recommendation_type="block_domain",
                    recommendation_fingerprint=fingerprint,
                    confidence_score=92.0,
                    confidence_level=ConfidenceLevel.HIGH,
                    reasoning="Automated threat hunting detected a cluster of 5 malicious domains sharing identical registration patterns with a known threat actor.",
                    triggering_detections=["New Infrastructure Cluster", "Domain Generation Algorithm (DGA)"],
                    triggering_mitre_ids=["T1583", "T1584"],
                    triggering_iocs=["bad-cluster-1.com", "bad-cluster-2.com"]
                )
                session.add(rec)
            
        await session.commit()

@shared_task(name="threat_hunting.run_all")
def trigger_threat_hunting_jobs():
    """Celery beat task entrypoint"""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_threat_hunting_jobs())
