from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from app.models.playbook import ConfidenceLevel, ActionStatus

class PlaybookAction(BaseModel):
    action_type: str
    title: str
    description: str

class ActionRecommendationCreate(BaseModel):
    playbook_name: str
    recommendation_type: str
    reasoning: str
    confidence_score: float
    confidence_level: ConfidenceLevel
    triggering_detections: List[str]
    triggering_mitre_ids: List[str]
    triggering_iocs: List[str]
    affected_users_count: int = 1

    scan_id: Optional[uuid.UUID] = None
    investigation_id: Optional[uuid.UUID] = None
    campaign_id: Optional[uuid.UUID] = None
    actor_id: Optional[uuid.UUID] = None

class ActionRecommendationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    playbook_name: str
    recommendation_type: str
    recommendation_fingerprint: str
    status: ActionStatus
    confidence_score: float
    confidence_level: ConfidenceLevel
    reasoning: str
    triggering_detections: List[str]
    triggering_mitre_ids: List[str]
    triggering_iocs: List[str]
    affected_users_count: int
    analyst_feedback: Optional[str] = None
    analyst_notes: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True
