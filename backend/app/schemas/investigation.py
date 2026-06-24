from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
from app.models.investigation import InvestigationPriority, InvestigationSeverity, InvestigationStatus, ArtifactType, TimelineEventType

class ArtifactCreate(BaseModel):
    artifact_type: ArtifactType
    artifact_value: str

class NoteCreate(BaseModel):
    content: str
    priority: Optional[InvestigationPriority] = None
    severity: Optional[InvestigationSeverity] = None
    status: Optional[InvestigationStatus] = None

class InvestigationCreate(BaseModel):
    title: str
    description: str
    priority: InvestigationPriority = InvestigationPriority.medium
    severity: InvestigationSeverity = InvestigationSeverity.medium

class InvestigationArtifactResponse(BaseModel):
    id: uuid.UUID
    artifact_type: ArtifactType
    artifact_value: str
    added_at: datetime
    
    class Config:
        from_attributes = True

class InvestigationNoteResponse(BaseModel):
    id: uuid.UUID
    content: str
    created_at: datetime
    author_id: uuid.UUID
    
    class Config:
        from_attributes = True

class InvestigationTimelineEventResponse(BaseModel):
    id: uuid.UUID
    event_type: TimelineEventType
    description: str
    created_at: datetime
    user_id: uuid.UUID
    
    class Config:
        from_attributes = True

class InvestigationResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    priority: InvestigationPriority
    severity: InvestigationSeverity
    status: InvestigationStatus
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID
    
    class Config:
        from_attributes = True

class InvestigationDetailResponse(InvestigationResponse):
    artifacts: List[InvestigationArtifactResponse] = []
    notes: List[InvestigationNoteResponse] = []
    timeline: List[InvestigationTimelineEventResponse] = []
