"""Knowledge-graph relationship ORM models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RelationshipConfidence(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class EntityType(str, enum.Enum):
    domain = "Domain"
    url = "URL"
    ip = "IP"
    hash = "Hash"
    sender = "Sender"
    campaign = "Campaign"
    scan = "Scan"
    ioc = "IOC"


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False)
    source_value: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    target_type: Mapped[EntityType] = mapped_column(Enum(EntityType), nullable=False)
    target_value: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    confidence: Mapped[RelationshipConfidence] = mapped_column(Enum(RelationshipConfidence), default=RelationshipConfidence.medium)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
