"""
Organization model for team/firm management.

Phase LXIX: Pricing Restructure v3 — Organization entity model.

Supports Professional (7 seats) and Enterprise (20 seats) tiers.
Organization owns a single subscription; members inherit the org's tier.

ZERO-STORAGE EXCEPTION: This module stores ONLY:
- Organization metadata (name, slug)
- Membership records (user_id, role, joined date)
- Invite tokens (SHA-256 hashed, 72h expiry)

No financial data, no account numbers, no PII beyond email for invites.
"""

from datetime import UTC, datetime, timedelta
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class OrgRole(str, PyEnum):
    """Role within an organization."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class InviteStatus(str, PyEnum):
    """Status of an organization invite."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Organization(Base):
    """Organization entity — a firm or team that owns a subscription.

    One organization per subscription (unique constraint on subscription_id).
    Auto-created on Professional/Enterprise checkout.
    """

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)

    # Owner (the user who created the org / subscribed)
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Link to subscription (one org = one subscription)
    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id"),
        unique=True,
        nullable=True,
        index=True,
    )

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now()
    )

    # Relationships
    members = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    invites = relationship("OrganizationInvite", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "owner_user_id": self.owner_user_id,
            "subscription_id": self.subscription_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class OrganizationMember(Base):
    """Membership record linking a user to an organization.

    A user can belong to at most one organization (unique on user_id).
    """

    __tablename__ = "organization_members"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="members")

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)

    role = Column(Enum(OrgRole), default=OrgRole.MEMBER, nullable=False)
    joined_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    # Who invited this member (nullable for owner — self-created)
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<OrganizationMember(id={self.id}, org_id={self.organization_id}, user_id={self.user_id}, role={self.role})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "role": self.role.value if self.role else None,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "invited_by_user_id": self.invited_by_user_id,
        }


# Default invite expiry: 72 hours
INVITE_EXPIRY_HOURS = 72


class OrganizationInvite(Base):
    """Pending invitation to join an organization.

    Tokens are stored as SHA-256 hashes (never plaintext).
    Expires after 72 hours.
    """

    __tablename__ = "organization_invites"

    id = Column(Integer, primary_key=True, index=True)

    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    organization = relationship("Organization", back_populates="invites")

    # Token stored as SHA-256 hash
    invite_token_hash = Column(String(64), unique=True, index=True, nullable=False)

    # Invitee info
    invitee_email = Column(String(255), nullable=False, index=True)
    role = Column(Enum(OrgRole), default=OrgRole.MEMBER, nullable=False)

    # Status lifecycle
    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    expires_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC) + timedelta(hours=INVITE_EXPIRY_HOURS),
        nullable=False,
    )
    accepted_at = Column(DateTime, nullable=True)
    accepted_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Who sent the invite
    invited_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<OrganizationInvite(id={self.id}, org_id={self.organization_id}, email={self.invitee_email[:10]}...)>"

    @property
    def is_expired(self) -> bool:
        """Check if invite has expired."""
        now = datetime.now(UTC)
        if self.expires_at.tzinfo is None:
            from datetime import timezone

            expires = self.expires_at.replace(tzinfo=timezone.utc)
        else:
            expires = self.expires_at
        return now > expires

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "invitee_email": self.invitee_email,
            "role": self.role.value if self.role else None,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
        }
