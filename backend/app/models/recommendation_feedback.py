"""Recommendation Feedback and Playbook Performance ORM models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Float, Index
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OutcomeType(str, enum.Enum):
    approved = "Approved"
    rejected = "Rejected"
    modified = "Modified"
    ignored = "Ignored"
    expired = "Expired"


class FeedbackCategory(str, enum.Enum):
    # Intelligence Failures (Negative)
    INTELLIGENCE_ERROR = "INTELLIGENCE_ERROR"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    INCORRECT_ATTRIBUTION = "INCORRECT_ATTRIBUTION"
    INCORRECT_PLAYBOOK = "INCORRECT_PLAYBOOK"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INCORRECT_RISK_ASSESSMENT = "INCORRECT_RISK_ASSESSMENT"

    # Business/Workflow outcomes (Neutral)
    BUSINESS_EXCEPTION = "BUSINESS_EXCEPTION"
    DUPLICATE = "DUPLICATE"
    ALREADY_REMEDIATED = "ALREADY_REMEDIATED"
    ANALYST_OVERRIDE = "ANALYST_OVERRIDE"
    OTHER = "OTHER"


class RecommendationOutcome(Base):
    __tablename__ = "recommendation_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("action_recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    analyst_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    outcome_type: Mapped[OutcomeType] = mapped_column(Enum(OutcomeType), nullable=False)
    
    feedback_category: Mapped[FeedbackCategory | None] = mapped_column(Enum(FeedbackCategory), nullable=True)
    feedback_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    feedback_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    recommendation = relationship("ActionRecommendation")
    analyst = relationship("User")


class PlaybookPerformanceMetrics(Base):
    __tablename__ = "playbook_performance_metrics"

    __table_args__ = (
        Index("ix_playbook_metrics_org_name", "organization_id", "playbook_name", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    playbook_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Volumes
    recommendations_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommendations_approved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommendations_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommendations_modified: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    recommendations_ignored: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Measured rates
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rejection_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    false_action_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    analyst_override_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_approval_latency: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # In seconds

    # Trust Engine
    trust_score: Mapped[float] = mapped_column(Float, default=100.0, nullable=False) # Max 100

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
