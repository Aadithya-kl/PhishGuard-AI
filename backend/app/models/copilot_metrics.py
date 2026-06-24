import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base

class CopilotUsageStat(Base):
    __tablename__ = "copilot_usage_stats"
    __table_args__ = (
        CheckConstraint('avg_confidence >= 0 AND avg_confidence <= 100', name='check_confidence_range'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    query_count = Column(Integer, default=0, nullable=False)
    tool_invocation_count = Column(Integer, default=0, nullable=False)
    avg_confidence = Column(Float, default=0.0, nullable=False)
    avg_response_time = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class CopilotEvaluationStat(Base):
    __tablename__ = "copilot_evaluation_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    evaluation_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    citation_rate = Column(Float, default=0.0, nullable=False)
    hallucination_rate = Column(Float, default=0.0, nullable=False)
    precision = Column(Float, default=0.0, nullable=False)
    recall = Column(Float, default=0.0, nullable=False)
    f1_score = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
