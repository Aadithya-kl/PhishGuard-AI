from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
from app.models.playbook import ConfidenceLevel, ActionStatus

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
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

from app.models.recommendation_feedback import FeedbackCategory

class ActionFeedback(BaseModel):
    feedback_category: Optional[FeedbackCategory] = None
    analyst_feedback: Optional[str] = None
    analyst_notes: Optional[str] = None
