import uuid
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.scan import EmailScan
from app.models.ioc import EmailIoc, IocType
from app.models.graph import Relationship, EntityType, RelationshipConfidence

class RelationshipEngine:
    async def process_scan(self, db: AsyncSession, scan_id: uuid.UUID):
        """
        Execute relationship engine automatically at the end of every completed scan.
        Reads the scan and its extracted IOCs to generate and persist relationships.
        """
        try:
            # 1. Fetch scan
            scan_res = await db.execute(select(EmailScan).where(EmailScan.id == scan_id))
            scan = scan_res.scalar_one_or_none()
            if not scan:
                return
            
            # 2. Fetch IOCs associated with scan
            iocs_res = await db.execute(select(EmailIoc).where(EmailIoc.scan_id == scan_id))
            iocs = list(iocs_res.scalars())

            new_relationships = []
            
            def add_rel(src_t, src_v, tgt_t, tgt_v, rel_type, conf=RelationshipConfidence.high):
                # Avoid duplicates in memory
                new_relationships.append(Relationship(
                    user_id=scan.user_id,
                    source_type=src_t,
                    source_value=src_v,
                    target_type=tgt_t,
                    target_value=tgt_v,
                    relationship_type=rel_type,
                    confidence=conf
                ))

            # Domain relationships
            sender_domain = None
            
            # Identify sender_domain from IOCs or scan
            for ioc in iocs:
                if ioc.ioc_type == IocType.sender_domain:
                    sender_domain = ioc.value
                    break
            
            # Create Scan -> Sender
            if scan.sender_address:
                add_rel(EntityType.scan, str(scan.id), EntityType.sender, scan.sender_address, "Sent By")
                if sender_domain:
                    add_rel(EntityType.sender, scan.sender_address, EntityType.domain, sender_domain, "Hosted On")
                    
            for ioc in iocs:
                # Scan -> IOC
                tgt_type = EntityType.ioc
                if ioc.ioc_type == IocType.domain: tgt_type = EntityType.domain
                elif ioc.ioc_type == IocType.ip: tgt_type = EntityType.ip
                elif ioc.ioc_type == IocType.url: tgt_type = EntityType.url
                elif ioc.ioc_type == IocType.md5 or ioc.ioc_type == IocType.sha256: tgt_type = EntityType.hash
                elif ioc.ioc_type == IocType.sender_domain: tgt_type = EntityType.domain

                add_rel(EntityType.scan, str(scan.id), tgt_type, ioc.value, "Contains")
                
                # Domain -> URL
                if ioc.ioc_type == IocType.url:
                    parts = ioc.value.split('/')
                    if len(parts) > 2:
                        url_domain = parts[2] if "//" in ioc.value else parts[0]
                        add_rel(EntityType.domain, url_domain, EntityType.url, ioc.value, "Hosts")
                        
                # Sender -> IOC (if not sender domain)
                if scan.sender_address and ioc.value != scan.sender_address:
                    add_rel(EntityType.sender, scan.sender_address, tgt_type, ioc.value, "Delivered")
            
            # Persist
            if new_relationships:
                db.add_all(new_relationships)
                await db.commit()
                logger.info(f"RelationshipEngine: Persisted {len(new_relationships)} relationships for scan {scan_id}")
                
        except Exception as e:
            logger.exception(f"RelationshipEngine failed for scan {scan_id}")
            await db.rollback()
