"""Threat intelligence and campaign ORM models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text, Float, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

class IndicatorType(str, enum.Enum):
    url = "url"
    domain = "domain"
    ip = "ip"
    hash = "hash"


class CampaignStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    monitoring = "monitoring"


class ThreatIntelCache(Base):
    __tablename__ = "threat_intel_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    indicator_type: Mapped[IndicatorType] = mapped_column(Enum(IndicatorType), nullable=False)
    indicator_value: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ThreatCampaign(Base):
    __tablename__ = "threat_campaigns"

    __table_args__ = (
        Index("ix_campaign_org_created_at", "organization_id", "first_seen"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attack_type: Mapped[str] = mapped_column(String(100), nullable=False, default="phishing")
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    scan_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indicators: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.active, nullable=False)
