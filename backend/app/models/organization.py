"""Organization and multi-tenant ORM models."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlanTier(str, enum.Enum):
    free = "Free"
    pro = "Pro"
    enterprise = "Enterprise"


class OrganizationRole(str, enum.Enum):
    platform_admin = "Platform Admin"
    org_admin = "Organization Admin"
    soc_manager = "SOC Manager"
    soc_analyst = "SOC Analyst"
    read_only = "Read Only Analyst"


class InvitationStatus(str, enum.Enum):
    pending = "Pending"
    accepted = "Accepted"
    revoked = "Revoked"
    expired = "Expired"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan: Mapped[PlanTier] = mapped_column(Enum(PlanTier), default=PlanTier.free, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    members: Mapped[list["OrganizationMember"]] = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    settings: Mapped["OrganizationSettings"] = relationship("OrganizationSettings", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    invitations: Mapped[list["OrganizationInvitation"]] = relationship("OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[OrganizationRole] = mapped_column(Enum(OrganizationRole), default=OrganizationRole.soc_analyst, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization: Mapped["Organization"] = relationship("Organization", back_populates="members")
    user = relationship("User", back_populates="memberships")


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role: Mapped[OrganizationRole] = mapped_column(Enum(OrganizationRole), default=OrganizationRole.soc_analyst, nullable=False)
    invitation_token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    status: Mapped[InvitationStatus] = mapped_column(Enum(InvitationStatus), default=InvitationStatus.pending, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization: Mapped["Organization"] = relationship("Organization", back_populates="invitations")


class OrganizationSettings(Base):
    __tablename__ = "organization_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False)
    branding_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notification_prefs_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    retention_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="settings")
