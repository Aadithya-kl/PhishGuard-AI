import asyncio
from sqlalchemy import select, update
from app.database import async_session_factory
from app.models.threat import ThreatCampaign as Campaign
from app.models.graph import Relationship, EntityType, RelationshipConfidence
from app.models.scan import EmailScan
import uuid

async def setup_campaign_relationships():
    async with async_session_factory() as db:
        # Create some mock campaigns if none exist
        res = await db.execute(select(Campaign))
        campaigns = res.scalars().all()
        
        if not campaigns:
            print("No campaigns found. Creating mock campaigns...")
            c1 = Campaign(id=uuid.uuid4(), name="Operation Crimson Phish", description="Targeting execs")
            c2 = Campaign(id=uuid.uuid4(), name="Invoice Fraud Ring", description="Fake invoices")
            db.add_all([c1, c2])
            await db.commit()
            campaigns = [c1, c2]
            
        print(f"Found {len(campaigns)} campaigns.")
        
        # Link 20 random scans to c1, 20 to c2
        res = await db.execute(select(EmailScan.id).limit(40))
        scan_ids = res.scalars().all()
        
        for i, scan_id in enumerate(scan_ids):
            c_id = campaigns[0].id if i < 20 else campaigns[1].id
            
            # Create a Relationship: Campaign -> Scan
            rel = Relationship(
                source_type=EntityType.campaign,
                source_value=str(c_id),
                target_type=EntityType.scan,
                target_value=str(scan_id),
                relationship_type="includes_scan",
                confidence=RelationshipConfidence.high
            )
            db.add(rel)
            
            # Also link the Campaign directly to the infrastructure discovered in that scan
            # to trigger Actor Clustering (which looks for shared infrastructure across campaigns)
            from app.models.ioc import EmailIoc
            ioc_res = await db.execute(select(EmailIoc.value, EmailIoc.ioc_type).where(EmailIoc.scan_id == scan_id))
            for ioc_val, ioc_type in ioc_res:
                try:
                    e_type = EntityType[ioc_type.name]
                except KeyError:
                    e_type = EntityType.ioc
                    
                rel_ioc = Relationship(
                    source_type=EntityType.campaign,
                    source_value=str(c_id),
                    target_type=e_type,
                    target_value=ioc_val,
                    relationship_type="uses_infrastructure",
                    confidence=RelationshipConfidence.high
                )
                db.add(rel_ioc)

        await db.commit()
        print("Campaign relationships seeded successfully.")

if __name__ == "__main__":
    asyncio.run(setup_campaign_relationships())
