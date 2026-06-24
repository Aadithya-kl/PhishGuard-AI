"""Usage and Plan Limits ORM models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrganizationUsage(Base):
    __tablename__ = "organization_usage"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    scans_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    copilot_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reports_generated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    investigations_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    graph_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    storage_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    reset_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organization = relationship("Organization")
