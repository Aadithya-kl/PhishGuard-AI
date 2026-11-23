"""Threat hunting: IOC search, pivoting, campaign clustering.

Every query is scoped to the caller's organization. (Previously ``/ioc/{value}``
and ``/campaigns`` were unauthenticated and returned data from every tenant.)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import user_limiter
from app.core.tenant_context import Permission, TenantContext, requires_permission
from app.database import get_db
from app.models.graph import EntityType, Relationship
from app.models.investigation import Investigation, InvestigationStatus
from app.models.ioc import EmailIoc, IocType
from app.models.preferences import SavedSearch, TrackedEntity, TrackedEntityType
from app.models.scan import EmailScan, RiskLevel
from app.schemas.threat_hunting import (
    CampaignCluster,
    CampaignClusteringResponse,
    IocInvestigationResponse,
    IocRelationships,
    IocTimelineEvent,
    ThreatSearchItem,
    ThreatSearchResponse,
)

router = APIRouter()
_view = requires_permission(Permission.VIEW_SCANS)


def _like(q: str) -> str:
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _org_iocs(org_id):
    return select(EmailIoc).join(EmailScan, EmailIoc.scan_id == EmailScan.id).where(EmailScan.organization_id == org_id)


@router.get("/statistics", response_model=dict)
async def get_statistics(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_view)):
    org = tenant.organization.id

    async def top_iocs(ioc_type: IocType):
        rows = await db.execute(
            select(EmailIoc.value, func.count(EmailIoc.id))
            .join(EmailScan, EmailIoc.scan_id == EmailScan.id)
            .where(EmailScan.organization_id == org, EmailIoc.ioc_type == ioc_type, EmailIoc.threat_score >= 70.0)
            .group_by(EmailIoc.value)
            .order_by(desc(func.count(EmailIoc.id)))
            .limit(5)
        )
        return [{"domain": v, "count": c} for v, c in rows.all()]

    ioc_count = await db.scalar(
        select(func.count(EmailIoc.id))
        .join(EmailScan, EmailIoc.scan_id == EmailScan.id)
        .where(EmailScan.organization_id == org, EmailIoc.threat_score >= 70.0)
    )
    attack_rows = await db.execute(
        select(EmailScan.attack_type, func.count(EmailScan.id))
        .where(EmailScan.organization_id == org, EmailScan.attack_type.is_not(None), EmailScan.attack_type != "Benign")
        .group_by(EmailScan.attack_type)
        .order_by(desc(func.count(EmailScan.id)))
        .limit(5)
    )
    open_invs = await db.scalar(
        select(func.count(Investigation.id)).where(Investigation.organization_id == org, Investigation.status == InvestigationStatus.open)
    )
    escalated = await db.scalar(
        select(func.count(Investigation.id)).where(
            Investigation.organization_id == org, Investigation.status == InvestigationStatus.escalated
        )
    )
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    new_threats = await db.scalar(
        select(func.count(EmailScan.id)).where(
            EmailScan.organization_id == org, EmailScan.risk_level == RiskLevel.high, EmailScan.scanned_at >= since
        )
    )
    avg_risk = await db.scalar(select(func.avg(EmailScan.overall_risk_score)).where(EmailScan.organization_id == org))

    return {
        "top_domains": await top_iocs(IocType.domain),
        "top_senders": await top_iocs(IocType.sender_domain),
        "common_attacks": [{"type": t, "count": c} for t, c in attack_rows.all() if t],
        "high_risk_ioc_count": ioc_count or 0,
        "soc_metrics": {
            "open_investigations": open_invs or 0,
            "escalated_investigations": escalated or 0,
            "critical_iocs": ioc_count or 0,
            "new_threats_24h": new_threats or 0,
            "average_risk_score": round(avg_risk or 0, 1),
        },
    }


@router.get("/search", response_model=ThreatSearchResponse)
@user_limiter.limit("120/minute")
async def search_threats(
    request: Request,
    q: Optional[str] = Query(None, min_length=2, max_length=200),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(_view),
):
    results: list[ThreatSearchItem] = []
    if q:
        like = _like(q)
        iocs = await db.execute(_org_iocs(tenant.organization.id).where(EmailIoc.value.ilike(like, escape="\\")).limit(25))
        seen: set[str] = set()
        for ioc in iocs.scalars():
            if ioc.value in seen:
                continue
            seen.add(ioc.value)
            results.append(ThreatSearchItem(
                id=ioc.id,
                type="ioc",
                value=ioc.value,
                risk_level="critical" if ioc.threat_score > 80 else "high" if ioc.threat_score > 60 else "low",
                classification=ioc.ioc_type.value,
            ))
        scans = await db.execute(
            select(EmailScan).where(
                EmailScan.organization_id == tenant.organization.id,
                or_(EmailScan.sender_address.ilike(like, escape="\\"), EmailScan.subject.ilike(like, escape="\\")),
            ).order_by(EmailScan.scanned_at.desc()).limit(25)
        )
        for scan in scans.scalars():
            results.append(ThreatSearchItem(
                id=scan.id,
                type="scan",
                value=scan.subject,
                risk_level=scan.risk_level.value,
                classification=scan.attack_type,
                first_seen=scan.scanned_at,
                last_seen=scan.scanned_at,
            ))
    return ThreatSearchResponse(total=len(results), results=results)


@router.get("/ioc/{value:path}", response_model=IocInvestigationResponse)
async def get_ioc_details(value: str, db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_view)):
    org = tenant.organization.id
    ioc_records = list(
        (await db.execute(_org_iocs(org).where(EmailIoc.value == value).order_by(EmailIoc.threat_score.desc()))).scalars()
    )
    if not ioc_records:
        raise HTTPException(status_code=404, detail="IOC not found")
    primary = ioc_records[0]

    scans = list(
        (
            await db.execute(
                select(EmailScan)
                .where(EmailScan.id.in_({i.scan_id for i in ioc_records}), EmailScan.organization_id == org)
                .order_by(EmailScan.scanned_at.asc())
            )
        ).scalars()
    )
    now = datetime.now(timezone.utc)
    first_seen = scans[0].scanned_at if scans else now
    last_seen = scans[-1].scanned_at if scans else now

    timeline = [IocTimelineEvent(date=first_seen, description="First observed in environment")]
    if len(scans) > 1:
        timeline.append(IocTimelineEvent(date=last_seen, description=f"Observed in {len(scans)} scans"))
    if primary.threat_score > 50:
        timeline.append(IocTimelineEvent(date=last_seen, description="Flagged by threat intelligence"))

    rels = (
        await db.execute(
            select(Relationship).where(
                Relationship.organization_id == org,
                or_(Relationship.source_value == value, Relationship.target_value == value),
            ).limit(500)
        )
    ).scalars().all()

    buckets: dict[EntityType, set[str]] = {}
    for r in rels:
        other_type, other_val = (r.target_type, r.target_value) if r.source_value == value else (r.source_type, r.source_value)
        buckets.setdefault(other_type, set()).add(other_val)

    def take(t: EntityType) -> list[str]:
        return sorted(buckets.get(t, set()))[:10]

    return IocInvestigationResponse(
        id=primary.id,
        value=primary.value,
        ioc_type=primary.ioc_type.value,
        threat_score=primary.threat_score,
        first_seen=first_seen,
        last_seen=last_seen,
        timeline=timeline,
        relationships=IocRelationships(
            related_domains=take(EntityType.domain),
            related_ips=take(EntityType.ip),
            related_urls=take(EntityType.url),
            related_senders=take(EntityType.sender),
            related_hashes=take(EntityType.hash),
            related_campaigns=take(EntityType.campaign),
            related_scans=take(EntityType.scan),
            relationship_count=len(rels),
            risk_summary={"max_score": primary.threat_score, "is_critical": primary.threat_score >= 80},
        ),
        linked_scans=[
            {
                "id": str(s.id),
                "subject": s.subject,
                "date": s.scanned_at.isoformat() if s.scanned_at else None,
                "risk": s.risk_level.value,
            }
            for s in scans[:50]
        ],
    )


@router.get("/campaigns", response_model=CampaignClusteringResponse)
async def get_campaigns(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_view)):
    """Cluster high-risk scans by shared infrastructure (hash > sender domain > IP)."""
    org = tenant.organization.id
    scans = list(
        (
            await db.execute(
                select(EmailScan)
                .where(EmailScan.organization_id == org, EmailScan.risk_level.in_([RiskLevel.high, RiskLevel.suspicious]))
                .order_by(EmailScan.scanned_at.desc())
                .limit(2000)
            )
        ).scalars()
    )
    scan_iocs: dict = {}
    if scans:
        for ioc in (await db.execute(select(EmailIoc).where(EmailIoc.scan_id.in_([s.id for s in scans])))).scalars():
            scan_iocs.setdefault(ioc.scan_id, []).append(ioc)

    clusters: dict[str, dict] = {}
    for scan in scans:
        s_iocs = scan_iocs.get(scan.id, [])
        sender_domains = [i.value for i in s_iocs if i.ioc_type == IocType.sender_domain]
        ips = [i.value for i in s_iocs if i.ioc_type == IocType.ip]
        hashes = [i.value for i in s_iocs if i.ioc_type in (IocType.md5, IocType.sha256)]
        urls = [i.value for i in s_iocs if i.ioc_type == IocType.url]
        if not (sender_domains or ips or hashes):
            continue
        key = hashes[0] if hashes else (sender_domains[0] if sender_domains else ips[0])
        score = 40 * bool(sender_domains) + 30 * bool(ips) + 50 * bool(hashes) + 40 * bool(urls)
        indicators = list(dict.fromkeys([*(sender_domains[:1]), *(ips[:1]), *(hashes[:1]), *(urls[:1])]))
        c = clusters.setdefault(key, {
            "name": f"Campaign pivot: {key}",
            "confidence": "High" if score >= 80 else "Medium" if score >= 50 else "Low",
            "shared_indicators": indicators,
            "scans": [],
            "dates": [],
        })
        c["scans"].append(scan)
        if scan.scanned_at:
            c["dates"].append(scan.scanned_at)

    campaigns = []
    for c in clusters.values():
        if len(c["scans"]) > 1 and c["dates"]:
            c["dates"].sort()
            campaigns.append(CampaignCluster(
                name=c["name"],
                confidence=c["confidence"],
                affected_scans_count=len(c["scans"]),
                shared_indicators=c["shared_indicators"],
                first_seen=c["dates"][0],
                last_seen=c["dates"][-1],
                scans=[{"id": str(s.id), "subject": s.subject} for s in c["scans"][:50]],
            ))
    campaigns.sort(key=lambda x: x.affected_scans_count, reverse=True)
    return CampaignClusteringResponse(total_campaigns=len(campaigns), campaigns=campaigns)


# ── Per-user preferences ─────────────────────────────────────────────────

@router.post("/saved-searches", response_model=dict)
async def create_saved_search(
    name: str = Query(..., min_length=1, max_length=255),
    query: str = Query(..., min_length=1, max_length=500),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(_view),
):
    ss = SavedSearch(user_id=tenant.user.id, name=name, query=query)
    db.add(ss)
    await db.commit()
    return {"id": str(ss.id), "status": "success"}


@router.get("/saved-searches", response_model=list)
async def get_saved_searches(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_view)):
    res = await db.execute(select(SavedSearch).where(SavedSearch.user_id == tenant.user.id).limit(100))
    return [{"id": str(s.id), "name": s.name, "query": s.query} for s in res.scalars()]


@router.post("/tracked-entities", response_model=dict)
async def create_tracked_entity(
    entity_type: TrackedEntityType,
    entity_value: str = Query(..., min_length=1, max_length=2048),
    db: AsyncSession = Depends(get_db),
    tenant: TenantContext = Depends(_view),
):
    te = TrackedEntity(user_id=tenant.user.id, entity_type=entity_type, entity_value=entity_value)
    db.add(te)
    await db.commit()
    return {"id": str(te.id), "status": "success"}


@router.get("/tracked-entities", response_model=list)
async def get_tracked_entities(db: AsyncSession = Depends(get_db), tenant: TenantContext = Depends(_view)):
    res = await db.execute(select(TrackedEntity).where(TrackedEntity.user_id == tenant.user.id).limit(200))
    return [{"id": str(s.id), "type": s.entity_type.value, "value": s.entity_value} for s in res.scalars()]
