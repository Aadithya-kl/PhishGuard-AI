from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc
from datetime import datetime, timezone
from typing import List, Optional
import uuid

from app.database import get_db
from app.models.scan import EmailScan, RiskLevel, AiAnalysis
from app.models.ioc import EmailIoc, IocType
from app.models.graph import Relationship, EntityType
from app.models.investigation import Investigation, InvestigationStatus
from app.models.preferences import SavedSearch, RecentSearch, TrackedEntity, TrackedEntityType
from app.models.user import User
from app.core.auth import get_current_user

from app.schemas.threat_hunting import (
    ThreatStatistics, ThreatSearchResponse, ThreatSearchItem,
    IocInvestigationResponse, IocTimelineEvent, IocRelationships,
    CampaignClusteringResponse, CampaignCluster
)

router = APIRouter()

@router.get("/statistics", response_model=dict)
async def get_statistics(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # High risk IOC count
    ioc_count = await db.scalar(
        select(func.count(EmailIoc.id))
        .join(EmailScan)
        .where(EmailScan.user_id == user.id, EmailIoc.threat_score >= 70.0)
    )
    
    # Top attack types
    attack_counts = await db.execute(
        select(EmailScan.attack_type, func.count(EmailScan.id))
        .where(EmailScan.user_id == user.id, EmailScan.attack_type != "Benign")
        .group_by(EmailScan.attack_type)
        .order_by(desc(func.count(EmailScan.id)))
        .limit(5)
    )
    attacks = [{"type": a[0], "count": a[1]} for a in attack_counts if a[0]]

    # Top malicious senders
    sender_counts = await db.execute(
        select(EmailIoc.value, func.count(EmailIoc.id))
        .join(EmailScan)
        .where(EmailScan.user_id == user.id, EmailIoc.ioc_type == IocType.sender_domain, EmailIoc.threat_score >= 70.0)
        .group_by(EmailIoc.value)
        .order_by(desc(func.count(EmailIoc.id)))
        .limit(5)
    )
    senders = [{"domain": s[0], "count": s[1]} for s in sender_counts]
    
    # Top domains
    domain_counts = await db.execute(
        select(EmailIoc.value, func.count(EmailIoc.id))
        .join(EmailScan)
        .where(EmailScan.user_id == user.id, EmailIoc.ioc_type == IocType.domain, EmailIoc.threat_score >= 70.0)
        .group_by(EmailIoc.value)
        .order_by(desc(func.count(EmailIoc.id)))
        .limit(5)
    )
    domains = [{"domain": d[0], "count": d[1]} for d in domain_counts]
    
    # Dashboard SOC Metrics
    open_invs = await db.scalar(select(func.count(Investigation.id)).where(Investigation.created_by == user.id, Investigation.status == InvestigationStatus.open))
    escalated_invs = await db.scalar(select(func.count(Investigation.id)).where(Investigation.created_by == user.id, Investigation.status == InvestigationStatus.escalated))
    recent_scans = await db.scalar(select(func.count(EmailScan.id)).where(EmailScan.user_id == user.id, EmailScan.risk_level == RiskLevel.high))
    avg_risk = await db.scalar(select(func.avg(EmailScan.overall_risk_score)).where(EmailScan.user_id == user.id))
    
    return {
        "top_domains": domains,
        "top_senders": senders,
        "common_attacks": attacks,
        "high_risk_ioc_count": ioc_count or 0,
        "soc_metrics": {
            "open_investigations": open_invs or 0,
            "escalated_investigations": escalated_invs or 0,
            "critical_iocs": ioc_count or 0,
            "new_threats_24h": recent_scans or 0,
            "average_risk_score": round(avg_risk or 0, 1) if avg_risk else 0
        }
    }


from app.core.rate_limit import user_limiter
from fastapi import Request

@router.get("/search", response_model=ThreatSearchResponse)
@user_limiter.limit("120/minute")
async def search_threats(
    request: Request,
    q: Optional[str] = Query(None, description="Global search query"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    results = []
    
    if q:
        # Search IOCs
        iocs = await db.execute(
            select(EmailIoc).where(EmailIoc.value.ilike(f"%{q}%")).limit(20)
        )
        for ioc in iocs.scalars():
            results.append(ThreatSearchItem(
                id=ioc.id,
                type="ioc",
                value=ioc.value,
                risk_level="Critical" if ioc.threat_score > 80 else "High" if ioc.threat_score > 60 else "Low",
                classification=ioc.ioc_type.value
            ))
            
        # Search Scans
        scans = await db.execute(
            select(EmailScan).where(
                EmailScan.user_id == user.id,
                or_(
                    EmailScan.sender_address.ilike(f"%{q}%"),
                    EmailScan.subject.ilike(f"%{q}%")
                )
            ).limit(20)
        )
        for scan in scans.scalars():
            results.append(ThreatSearchItem(
                id=scan.id,
                type="scan",
                value=scan.subject,
                risk_level=scan.risk_level.value,
                classification=scan.attack_type,
                first_seen=scan.scanned_at,
                last_seen=scan.scanned_at
            ))

    return ThreatSearchResponse(total=len(results), results=results)


@router.get("/ioc/{value}", response_model=IocInvestigationResponse)
async def get_ioc_details(value: str, db: AsyncSession = Depends(get_db)):
    iocs = await db.execute(
        select(EmailIoc).where(EmailIoc.value == value).order_by(EmailIoc.threat_score.desc())
    )
    ioc_records = list(iocs.scalars())
    if not ioc_records:
        raise HTTPException(status_code=404, detail="IOC not found")
        
    primary_ioc = ioc_records[0]
    
    # Scans directly linked
    scan_ids = [ioc.scan_id for ioc in ioc_records]
    scans_result = await db.execute(
        select(EmailScan).where(EmailScan.id.in_(scan_ids)).order_by(EmailScan.scanned_at.asc())
    )
    scans = list(scans_result.scalars())
    
    first_seen = scans[0].scanned_at if scans else datetime.now(timezone.utc)
    last_seen = scans[-1].scanned_at if scans else datetime.now(timezone.utc)
    
    timeline = []
    timeline.append(IocTimelineEvent(date=first_seen, description="First observed in environment"))
    if len(scans) > 1:
        timeline.append(IocTimelineEvent(date=last_seen, description=f"Observed in {len(scans)} independent scans"))
    if primary_ioc.threat_score > 50:
        timeline.append(IocTimelineEvent(date=last_seen, description="Threat score escalated due to malicious indicators"))

    # Pivot Engine using Relationship table
    rels_res = await db.execute(
        select(Relationship).where(
            or_(Relationship.source_value == value, Relationship.target_value == value)
        )
    )
    rels = rels_res.scalars().all()
    
    domains, ips, urls, senders, hashes, campaigns, rel_scans = set(), set(), set(), set(), set(), set(), set()
    
    for r in rels:
        other_type = r.target_type if r.source_value == value else r.source_type
        other_val = r.target_value if r.source_value == value else r.source_value
        
        if other_type == EntityType.domain: domains.add(other_val)
        elif other_type == EntityType.ip: ips.add(other_val)
        elif other_type == EntityType.url: urls.add(other_val)
        elif other_type == EntityType.sender: senders.add(other_val)
        elif other_type == EntityType.hash: hashes.add(other_val)
        elif other_type == EntityType.campaign: campaigns.add(other_val)
        elif other_type == EntityType.scan: rel_scans.add(other_val)

    relationships = IocRelationships(
        related_domains=list(domains)[:10],
        related_ips=list(ips)[:10],
        related_urls=list(urls)[:10],
        related_senders=list(senders)[:10],
        related_hashes=list(hashes)[:10],
        related_campaigns=list(campaigns)[:10],
        related_scans=list(rel_scans)[:10],
        relationship_count=len(rels),
        risk_summary={"max_score": primary_ioc.threat_score, "is_critical": primary_ioc.threat_score >= 80}
    )

    linked_scans = [
        {
            "id": str(s.id),
            "subject": s.subject,
            "date": s.scanned_at.isoformat() if s.scanned_at else None,
            "risk": s.risk_level.value
        } for s in scans
    ]

    return IocInvestigationResponse(
        id=primary_ioc.id,
        value=primary_ioc.value,
        ioc_type=primary_ioc.ioc_type.value,
        threat_score=primary_ioc.threat_score,
        first_seen=first_seen,
        last_seen=last_seen,
        timeline=timeline,
        relationships=relationships,
        linked_scans=linked_scans
    )


@router.get("/campaigns", response_model=CampaignClusteringResponse)
async def get_campaigns(db: AsyncSession = Depends(get_db)):
    # V2 Clustering Logic: Weighted clustering
    
    scans_res = await db.execute(select(EmailScan).where(EmailScan.risk_level == RiskLevel.high))
    scans = list(scans_res.scalars())
    
    scan_ids = [s.id for s in scans]
    iocs_res = await db.execute(select(EmailIoc).where(EmailIoc.scan_id.in_(scan_ids)))
    iocs = list(iocs_res.scalars())
    
    scan_iocs = {}
    for ioc in iocs:
        if ioc.scan_id not in scan_iocs:
            scan_iocs[ioc.scan_id] = []
        scan_iocs[ioc.scan_id].append(ioc)
        
    clusters = {}
    for scan in scans:
        s_iocs = scan_iocs.get(scan.id, [])
        sender_domains = [i.value for i in s_iocs if i.ioc_type == IocType.sender_domain]
        ips = [i.value for i in s_iocs if i.ioc_type == IocType.ip]
        hashes = [i.value for i in s_iocs if i.ioc_type == IocType.md5 or ioc.ioc_type == IocType.sha256]
        urls = [i.value for i in s_iocs if i.ioc_type == IocType.url]
        
        # Determine pivot point
        if not sender_domains and not ips and not hashes:
            continue
            
        primary_pivot = hashes[0] if hashes else (sender_domains[0] if sender_domains else ips[0])
        cluster_key = primary_pivot
        
        # Calculate cluster score
        score = 0
        indicators = []
        if sender_domains:
            score += 40
            indicators.append(sender_domains[0])
        if ips:
            score += 30
            if ips[0] not in indicators: indicators.append(ips[0])
        if hashes:
            score += 50
            if hashes[0] not in indicators: indicators.append(hashes[0])
        if urls:
            score += 40
            if urls[0] not in indicators: indicators.append(urls[0])
            
        if scan.sender_address:
            score += 30
            
        if score < 50: conf = "Low"
        elif score < 80: conf = "Medium"
        else: conf = "High"
            
        if cluster_key not in clusters:
            clusters[cluster_key] = {
                "name": f"Campaign Pivot: {cluster_key}",
                "confidence": conf,
                "shared_indicators": indicators,
                "scans": [],
                "dates": []
            }
            
        clusters[cluster_key]["scans"].append(scan)
        if scan.scanned_at:
            clusters[cluster_key]["dates"].append(scan.scanned_at)
            
    campaigns = []
    for c in clusters.values():
        if len(c["scans"]) > 1:
            c["dates"].sort()
            campaigns.append(CampaignCluster(
                name=c["name"],
                confidence=c["confidence"],
                affected_scans_count=len(c["scans"]),
                shared_indicators=c["shared_indicators"],
                first_seen=c["dates"][0],
                last_seen=c["dates"][-1],
                scans=[{"id": str(s.id), "subject": s.subject} for s in c["scans"]]
            ))
            
    campaigns.sort(key=lambda x: x.affected_scans_count, reverse=True)
    return CampaignClusteringResponse(total_campaigns=len(campaigns), campaigns=campaigns)


# --- User Preferences ---
@router.post("/saved-searches", response_model=dict)
async def create_saved_search(name: str, query: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    ss = SavedSearch(user_id=user.id, name=name, query=query)
    db.add(ss)
    await db.commit()
    return {"id": str(ss.id), "status": "success"}

@router.get("/saved-searches", response_model=list)
async def get_saved_searches(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    res = await db.execute(select(SavedSearch).where(SavedSearch.user_id == user.id))
    return [{"id": str(s.id), "name": s.name, "query": s.query} for s in res.scalars()]

@router.post("/tracked-entities", response_model=dict)
async def create_tracked_entity(entity_type: TrackedEntityType, entity_value: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    te = TrackedEntity(user_id=user.id, entity_type=entity_type, entity_value=entity_value)
    db.add(te)
    await db.commit()
    return {"id": str(te.id), "status": "success"}

@router.get("/tracked-entities", response_model=list)
async def get_tracked_entities(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    res = await db.execute(select(TrackedEntity).where(TrackedEntity.user_id == user.id))
    return [{"id": str(s.id), "type": s.entity_type.value, "value": s.entity_value} for s in res.scalars()]
