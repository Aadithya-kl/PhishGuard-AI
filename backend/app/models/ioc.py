"""Indicators of Compromise (IOC) ORM models."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IocType(str, enum.Enum):
    domain = "domain"
    subdomain = "subdomain"
    url = "url"
    ip = "ip"
    email = "email"
    md5 = "md5"
    sha1 = "sha1"
    sha256 = "sha256"
    attachment_name = "attachment_name"
    attachment_extension = "attachment_extension"
    sender_domain = "sender_domain"
    reply_to_domain = "reply_to_domain"
    message_id = "message_id"
    phone_number = "phone_number"
    cryptocurrency_wallet = "cryptocurrency_wallet"


class EmailIoc(Base):
    __tablename__ = "email_iocs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("email_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    ioc_type: Mapped[IocType] = mapped_column(Enum(IocType), nullable=False)
    value: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    threat_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reputation_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    scan: Mapped["EmailScan"] = relationship(back_populates="iocs")
