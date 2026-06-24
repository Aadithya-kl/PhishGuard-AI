from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# --- Statistics ---

class ThreatStatistics(BaseModel):
    top_domains: List[Dict[str, Any]]
    top_senders: List[Dict[str, Any]]
    common_attacks: List[Dict[str, Any]]
    recent_campaigns: List[Dict[str, Any]]
    high_risk_ioc_count: int

# --- Search Responses ---

class ThreatSearchItem(BaseModel):
    id: UUID
    type: str  # 'scan', 'ioc', 'campaign'
    value: str
    classification: Optional[str] = None
    risk_level: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

class ThreatSearchResponse(BaseModel):
    total: int
    results: List[ThreatSearchItem]

# --- IOC Investigation & Relationships ---

class IocTimelineEvent(BaseModel):
    date: datetime
    description: str

class IocRelationships(BaseModel):
    related_domains: List[str]
    related_ips: List[str]
    related_urls: List[str]
    related_campaigns: List[str]
    related_senders: List[str]
    related_hashes: List[str]
    related_scans: List[str]
    relationship_count: int
    risk_summary: Dict[str, Any]

class IocInvestigationResponse(BaseModel):
    id: UUID
    value: str
    ioc_type: str
    threat_score: float
    first_seen: datetime
    last_seen: datetime
    timeline: List[IocTimelineEvent]
    relationships: IocRelationships
    linked_scans: List[Dict[str, Any]] # Brief scan details
    
    model_config = ConfigDict(from_attributes=True)

# --- Campaign Clustering ---

class CampaignCluster(BaseModel):
    name: str
    confidence: str # Low, Medium, High
    affected_scans_count: int
    shared_indicators: List[str]
    first_seen: datetime
    last_seen: datetime
    scans: List[Dict[str, Any]] # Brief scan details

class CampaignClusteringResponse(BaseModel):
    total_campaigns: int
    campaigns: List[CampaignCluster]
