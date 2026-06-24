"""Dashboard analytics schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_scans: int = 0
    threats_detected: int = 0
    avg_risk_score: float = 0.0
    scans_today: int = 0
    high_risk_count: int = 0
    suspicious_count: int = 0
    safe_count: int = 0
    urls_scanned: int = 0
    risk_distribution: dict = {}
    
    # Playbook Metrics
    recommendations_generated: int = 0
    recommendations_approved: int = 0
    recommendations_rejected: int = 0
    automation_acceptance_rate: float = 0.0


class TrendPoint(BaseModel):
    date: str
    total: int = 0
    high: int = 0
    suspicious: int = 0
    low: int = 0
    safe: int = 0


class TrendsResponse(BaseModel):
    trends: list[TrendPoint]


class RiskDistribution(BaseModel):
    safe: int = 0
    low: int = 0
    suspicious: int = 0
    high: int = 0


class AttackCategory(BaseModel):
    category: str
    count: int


class TopDomain(BaseModel):
    domain: str
    count: int
    avg_risk: float


class DashboardTrends(BaseModel):
    trends: list[TrendPoint]


class AttackCategoriesResponse(BaseModel):
    categories: list[AttackCategory]


class TopDomainsResponse(BaseModel):
    domains: list[TopDomain]


class AutomationMetricsResponse(BaseModel):
    recommendations_generated: int = 0
    recommendations_approved: int = 0
    recommendations_rejected: int = 0
    acceptance_rate: float = 0.0
    false_action_rate: float = 0.0
    analyst_override_rate: float = 0.0
    recommendation_coverage: float = 0.0
    average_approval_latency: float = 0.0
    high_trust_playbooks: list[str] = []
    low_trust_playbooks: list[str] = []

