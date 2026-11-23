from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
from app.models.investigation import InvestigationPriority, InvestigationSeverity, InvestigationStatus, ArtifactType, TimelineEventType

class ArtifactCreate(BaseModel):
    artifact_type: ArtifactType
    artifact_value: str = Field(..., min_length=1, max_length=2048)

class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    priority: Optional[InvestigationPriority] = None
    severity: Optional[InvestigationSeverity] = None
    status: Optional[InvestigationStatus] = None

class InvestigationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10000)
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
    timestamp: datetime
    triggered_by: Optional[uuid.UUID] = None
    
    class Config:
        from_attributes = True

class InvestigationResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
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
