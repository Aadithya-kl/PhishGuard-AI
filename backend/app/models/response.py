"""Active Response ORM models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ResponseRiskTier(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GlobalAutomationState(str, enum.Enum):
    DISABLED = "DISABLED"
    OBSERVATION = "OBSERVATION"
    LIMITED_ACTIVE = "LIMITED_ACTIVE"
    FULL_ACTIVE = "FULL_ACTIVE"


class ProviderTrustLevel(str, enum.Enum):
    LAB = "LAB"
    TESTED = "TESTED"
    PRODUCTION = "PRODUCTION"


class AutomationLevel(str, enum.Enum):
    OBSERVATION_ONLY = "OBSERVATION_ONLY"
    ANALYST_APPROVAL_REQUIRED = "ANALYST_APPROVAL_REQUIRED"
    MANAGER_APPROVAL_REQUIRED = "MANAGER_APPROVAL_REQUIRED"
    FULLY_AUTOMATED = "FULLY_AUTOMATED"


class OrganizationAutomationPolicy(Base):
    __tablename__ = "organization_automation_policies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(255), nullable=False)
    
    automation_level: Mapped[AutomationLevel] = mapped_column(Enum(AutomationLevel), nullable=False, default=AutomationLevel.ANALYST_APPROVAL_REQUIRED)
    risk_threshold: Mapped[float] = mapped_column(Float, default=0.0)
    requires_manager_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ResponseApproval(Base):
    __tablename__ = "response_approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(255), nullable=False)
    
    approver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    approver_role: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. Analyst, Manager, OrgAdmin
    
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reason: Mapped[str] = mapped_column(Text, nullable=True)


class ExecutedAction(Base):
    __tablename__ = "executed_actions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(255), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(255), nullable=False)
    
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    rollback_available: Mapped[bool] = mapped_column(Boolean, default=False)
    rollback_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rolled_back: Mapped[bool] = mapped_column(Boolean, default=False)


class ResponseAuditRecord(Base):
    __tablename__ = "response_audit_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True) # None if automated
    
    action_type: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_tier: Mapped[ResponseRiskTier] = mapped_column(Enum(ResponseRiskTier), nullable=False)
    
    approval_chain: Mapped[list | None] = mapped_column(JSON, nullable=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    
    rollback_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    
    status: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. EXECUTED, BLOCKED, DRY_RUN_FAILED
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GlobalAutomationSettings(Base):
    __tablename__ = "global_automation_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state: Mapped[GlobalAutomationState] = mapped_column(Enum(GlobalAutomationState), nullable=False, default=GlobalAutomationState.OBSERVATION)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
