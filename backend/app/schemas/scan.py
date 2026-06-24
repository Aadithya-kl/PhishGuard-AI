"""Scan-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Sub-models ───────────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    type: str
    description: str
    severity: str = "info"
    impact_on_score: float = 0.0


class HeaderAnalysisResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    spf_pass: Optional[bool] = None
    spf_result: str = "none"
    dkim_pass: Optional[bool] = None
    dkim_result: str = "none"
    dmarc_pass: Optional[bool] = None
    dmarc_result: str = "none"
    sender_spoofed: bool = False
    display_name_impersonation: bool = False
    domain_mismatch: bool = False
    relay_chain: Optional[list[dict[str, Any]]] = None
    forged_headers: Optional[list[dict[str, Any]]] = None
    bec_indicators: Optional[dict[str, Any]] = None
    trust_score: float = 100.0
    evidence: Optional[list[dict[str, Any]]] = None


class UrlAnalysisResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    original_url: str
    final_url: Optional[str] = None
    domain: str
    domain_age_days: Optional[int] = None
    registrar: Optional[str] = None
    is_shortened: bool = False
    is_homoglyph: bool = False
    is_typosquatting: bool = False
    is_ip_based: bool = False
    tld: str = ""
    risk_score: float = 0.0
    threat_intel_results: Optional[dict[str, Any]] = None
    evidence: Optional[list[dict[str, Any]]] = None


class AttachmentAnalysisResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    filename: str
    content_type: str
    file_size: int
    md5_hash: str
    sha256_hash: str
    is_executable: bool = False
    has_macros: bool = False
    is_double_extension: bool = False
    threat_score: float = 0.0
    evidence: Optional[list[dict[str, Any]]] = None


class AiAnalysisResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    model_used: str
    attack_classification: str
    confidence_score: float
    severity_level: str
    reasoning: str
    tactics_detected: Optional[list[dict[str, Any]]] = None
    structured_output: Optional[dict[str, Any]] = None
    evidence: Optional[list[dict[str, Any]]] = None
    ioc_summary: Optional[list[dict[str, Any]]] = None
    investigation_summary: str = ""
    executive_summary: str = ""
    technical_summary: str = ""
    attack_chain: Optional[list[str]] = None
    recommended_actions: Optional[list[str]] = None
    analyst_notes: Optional[list[str]] = None


class IocResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    ioc_type: str
    value: str
    threat_score: float
    reputation_data: Optional[dict[str, Any]] = None


class RiskBreakdown(BaseModel):
    header_score: float = 0.0
    url_score: float = 0.0
    attachment_score: float = 0.0
    ai_score: float = 0.0
    overall_score: float = 0.0
    risk_level: str = "safe"
    reasoning: list[str] = Field(default_factory=list)


# ── Requests ─────────────────────────────────────────────────────────────

class PasteEmailRequest(BaseModel):
    raw_content: str = Field(..., min_length=10)
    content_type: str = Field(default="raw", pattern=r"^(raw|headers_only)$")


class HeadersOnlyRequest(BaseModel):
    raw_headers: str = Field(..., min_length=10)


# ── Responses ────────────────────────────────────────────────────────────

class ScanSummaryResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    subject: str
    sender_address: str
    sender_display_name: str
    recipient: str
    overall_risk_score: float
    risk_level: str
    attack_type: Optional[str] = None
    status: str
    scanned_at: datetime


class ScanDetailResponse(ScanSummaryResponse):
    reply_to: Optional[str] = None
    return_path: Optional[str] = None
    body_text: str = ""
    risk_breakdown: Optional[dict[str, Any]] = None
    investigation_report: Optional[dict[str, Any]] = None
    header_analysis: Optional[HeaderAnalysisResponse] = None
    url_analyses: Optional[list[UrlAnalysisResponse]] = None
    attachment_analyses: Optional[list[AttachmentAnalysisResponse]] = None
    ai_analysis: Optional[AiAnalysisResponse] = None
    detections: Optional[list[dict[str, Any]]] = None
    iocs: Optional[list[IocResponse]] = None


class ScanListResponse(BaseModel):
    items: list[ScanSummaryResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SandboxResponse(BaseModel):
    sanitized_html: str
    warnings: list[str]
