"""Investigation Workbench ORM models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InvestigationStatus(str, enum.Enum):
    open = "Open"
    in_progress = "In Progress"
    escalated = "Escalated"
    closed = "Closed"


class InvestigationPriority(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class InvestigationSeverity(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class Investigation(Base):
    __tablename__ = "investigations"

    __table_args__ = (
        Index("ix_inv_org_created_at", "organization_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InvestigationStatus] = mapped_column(Enum(InvestigationStatus), default=InvestigationStatus.open, index=True)
    priority: Mapped[InvestigationPriority] = mapped_column(Enum(InvestigationPriority), default=InvestigationPriority.medium, index=True)
    severity: Mapped[InvestigationSeverity] = mapped_column(Enum(InvestigationSeverity), default=InvestigationSeverity.medium, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    artifacts: Mapped[list["InvestigationArtifact"]] = relationship("InvestigationArtifact", back_populates="investigation", cascade="all, delete-orphan")
    notes: Mapped[list["InvestigationNote"]] = relationship("InvestigationNote", back_populates="investigation", cascade="all, delete-orphan")
    timeline: Mapped[list["InvestigationTimelineEvent"]] = relationship("InvestigationTimelineEvent", back_populates="investigation", cascade="all, delete-orphan")
    owner = relationship("User")


class ArtifactType(str, enum.Enum):
    ioc = "IOC"
    domain = "Domain"
    ip = "IP"
    url = "URL"
    hash = "Hash"
    sender = "Sender"
    campaign = "Campaign"
    scan = "Scan"
    attachment = "Attachment"
    threat_intel = "ThreatIntelRecord"


class InvestigationArtifact(Base):
    __tablename__ = "investigation_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(Enum(ArtifactType), nullable=False)
    artifact_value: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    added_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="artifacts")


class InvestigationNote(Base):
    __tablename__ = "investigation_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="notes")
    author = relationship("User")


class TimelineEventType(str, enum.Enum):
    created = "Investigation Created"
    ioc_added = "IOC Added"
    campaign_added = "Campaign Added"
    note_added = "Note Added"
    status_changed = "Status Changed"
    priority_changed = "Priority Changed"
    severity_changed = "Severity Changed"
    artifact_removed = "Artifact Removed"
    scan_added = "Scan Added"


class InvestigationTimelineEvent(Base):
    __tablename__ = "investigation_timeline"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[TimelineEventType] = mapped_column(Enum(TimelineEventType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="timeline")
