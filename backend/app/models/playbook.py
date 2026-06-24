"""Playbook and Automated Response ORM models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ActionStatus(str, enum.Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"
    executed = "Executed"
    failed = "Failed"


class ConfidenceLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionRecommendation(Base):
    __tablename__ = "action_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Optional references (at least one must be set in practice)
    scan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("email_scans.id", ondelete="CASCADE"), nullable=True, index=True)
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=True, index=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("threat_campaigns.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    recommendation_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    playbook_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(255), nullable=False)
    
    status: Mapped[ActionStatus] = mapped_column(Enum(ActionStatus), default=ActionStatus.pending, nullable=False)
    
    # Confidence metrics
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(Enum(ConfidenceLevel), default=ConfidenceLevel.LOW, nullable=False)
    
    # Explainability
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    triggering_detections: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    triggering_mitre_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    triggering_iocs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    affected_users_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Analyst Feedback
    analyst_feedback: Mapped[str | None] = mapped_column(String(50), nullable=True) # e.g. "False Positive", "Approved"
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps & Auditing
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    organization = relationship("Organization")
    scan = relationship("EmailScan")
    investigation = relationship("Investigation")
    campaign = relationship("ThreatCampaign")
    approver = relationship("User")
