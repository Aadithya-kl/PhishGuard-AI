"""Report ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReportType(str, enum.Enum):
    scan = "scan"
    investigation = "investigation"
    campaign = "campaign"
    threat_actor = "threat_actor"
    executive = "executive"


class ReportFormat(str, enum.Enum):
    pdf = "pdf"
    json = "json"
    html = "html"

class ReportStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Report(Base):
    __tablename__ = "reports"

    __table_args__ = (
        Index("ix_reports_org_created_at", "organization_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Optional foreign keys for different report scopes
    scan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("email_scans.id", ondelete="SET NULL"), nullable=True)
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True) # Assuming campaign table doesn't exist yet or is part of threat graph
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), default=ReportStatus.pending, nullable=False)
    
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="reports")  # type: ignore[name-defined]
    scan: Mapped["EmailScan"] = relationship(back_populates="reports")  # type: ignore[name-defined]
