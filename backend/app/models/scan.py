"""Email scan and analysis ORM models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RiskLevel(str, enum.Enum):
    safe = "safe"
    low = "low"
    suspicious = "suspicious"
    high = "high"


class ScanStatus(str, enum.Enum):
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


class SeverityLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class EmailScan(Base):
    __tablename__ = "email_scans"

    __table_args__ = (
        Index("ix_email_scans_org_scanned_at", "organization_id", "scanned_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String(1000), nullable=False, default="(no subject)")
    sender_address: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    sender_display_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    recipient: Mapped[str] = mapped_column(String(320), nullable=False, default="")
    reply_to: Mapped[str | None] = mapped_column(String(320), nullable=True)
    return_path: Mapped[str | None] = mapped_column(String(320), nullable=True)
    raw_headers: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    body_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parsed_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    mime_structure: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    detections: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    overall_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.safe, nullable=False)
    attack_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    risk_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    investigation_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.pending, nullable=False, index=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="scans")  # type: ignore[name-defined]
    header_analysis: Mapped["HeaderAnalysis | None"] = relationship(back_populates="scan", uselist=False, cascade="all, delete-orphan")
    url_analyses: Mapped[list["UrlAnalysis"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    attachment_analyses: Mapped[list["AttachmentAnalysis"]] = relationship(back_populates="scan", cascade="all, delete-orphan")
    ai_analysis: Mapped["AiAnalysis | None"] = relationship(back_populates="scan", uselist=False, cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="scan", cascade="all, delete-orphan")  # type: ignore[name-defined]
    iocs: Mapped[list["EmailIoc"]] = relationship(back_populates="scan", cascade="all, delete-orphan")  # type: ignore[name-defined]


class HeaderAnalysis(Base):
    __tablename__ = "header_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("email_scans.id", ondelete="CASCADE"), unique=True, nullable=False)
    spf_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    spf_result: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    dkim_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dkim_result: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    dmarc_pass: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    dmarc_result: Mapped[str] = mapped_column(String(50), nullable=False, default="none")
    sender_spoofed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_name_impersonation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    domain_mismatch: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    relay_chain: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    forged_headers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    bec_indicators: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    scan: Mapped["EmailScan"] = relationship(back_populates="header_analysis")


class UrlAnalysis(Base):
    __tablename__ = "url_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("email_scans.id", ondelete="CASCADE"), nullable=False)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    final_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    registrar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    whois_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    redirect_chain: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_shortened: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_homoglyph: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_typosquatting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_ip_based: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tld: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    threat_intel_results: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    scan: Mapped["EmailScan"] = relationship(back_populates="url_analyses")


class AttachmentAnalysis(Base):
    __tablename__ = "attachment_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("email_scans.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    md5_hash: Mapped[str] = mapped_column(String(32), nullable=False, default="", index=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="", index=True)
    is_executable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_macros: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_double_extension: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    file_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    threat_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    scan: Mapped["EmailScan"] = relationship(back_populates="attachment_analyses")


class AiAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("email_scans.id", ondelete="CASCADE"), unique=True, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False, default="rule-ensemble")
    attack_classification: Mapped[str] = mapped_column(String(100), nullable=False, default="unknown")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    severity_level: Mapped[SeverityLevel] = mapped_column(Enum(SeverityLevel), default=SeverityLevel.low, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tactics_detected: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    structured_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ioc_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    investigation_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    technical_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    attack_chain: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recommended_actions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    analyst_notes: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    scan: Mapped["EmailScan"] = relationship(back_populates="ai_analysis")
