"""
Subscription model for billing lifecycle management.

Sprint 363: Phase L — Pricing Strategy & Billing Infrastructure.

ZERO-STORAGE EXCEPTION: This module stores ONLY:
- Subscription metadata (tier, status, billing interval, period dates)
- Stripe references (customer_id, subscription_id) for payment lifecycle

No financial data, no account numbers, no PII beyond what Stripe requires.
"""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from database import Base


class SubscriptionStatus(str, PyEnum):
    """Stripe-aligned subscription lifecycle status."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"


class BillingInterval(str, PyEnum):
    """Billing frequency."""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class Subscription(Base):
    """
    Subscription model — links a user to their billing state.

    One subscription per user (unique constraint on user_id).
    Stripe is the source of truth; this table is a local cache
    synced via webhooks.
    """
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    # One subscription per user
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user = relationship("User", backref="subscription")

    # Plan details
    tier = Column(Enum("free", "starter", "professional", "team", "enterprise", name="subscription_tier"), nullable=False, default="free")
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    billing_interval = Column(Enum(BillingInterval), nullable=True)

    # Stripe references
    stripe_customer_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)

    # Billing period (synced from Stripe)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier={self.tier}, status={self.status})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tier": self.tier,
            "status": self.status.value if self.status else None,
            "billing_interval": self.billing_interval.value if self.billing_interval else None,
            "stripe_customer_id": self.stripe_customer_id,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "cancel_at_period_end": self.cancel_at_period_end,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
