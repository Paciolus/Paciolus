"""
Subscription model for billing lifecycle management.

Sprint 363: Phase L — Pricing Strategy & Billing Infrastructure.
Phase LIX Sprint B: seat_count + additional_seats columns.
Phase LX: BillingEvent append-only event log for post-launch analytics.

ZERO-STORAGE EXCEPTION: This module stores ONLY:
- Subscription metadata (tier, status, billing interval, period dates, seat counts)
- Stripe references (customer_id, subscription_id) for payment lifecycle
- Billing lifecycle events (event type, tier, interval — no financial data)

No financial data, no account numbers, no PII beyond what Stripe requires.
"""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, func
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


class BillingEventType(str, PyEnum):
    """Billing lifecycle event taxonomy.

    10 event types covering the complete subscription lifecycle.
    Used for post-launch decision metrics (Phase LX).
    """

    # Trial lifecycle
    TRIAL_STARTED = "trial_started"
    TRIAL_CONVERTED = "trial_converted"
    TRIAL_EXPIRED = "trial_expired"

    # Subscription lifecycle
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    SUBSCRIPTION_CHURNED = "subscription_churned"

    # Payment lifecycle
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_RECOVERED = "payment_recovered"


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
    tier = Column(
        Enum("free", "solo", "professional", "team", "organization", name="subscription_tier"),
        nullable=False,
        default="free",
    )
    status = Column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    billing_interval = Column(Enum(BillingInterval), nullable=True)

    # Stripe references
    stripe_customer_id = Column(String(255), nullable=True, unique=True, index=True)
    stripe_subscription_id = Column(String(255), nullable=True, unique=True, index=True)

    # Billing period (synced from Stripe)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)

    # Seat management (Phase LIX Sprint B)
    seat_count = Column(Integer, default=1, nullable=False)  # Base seats from plan
    additional_seats = Column(Integer, default=0, nullable=False)  # Add-on seats purchased

    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)

    # DPA acceptance (Sprint 459 — PI1.3 / C2.1)
    # Timestamps when the customer accepted the Data Processing Addendum, and which version.
    dpa_accepted_at = Column(DateTime, nullable=True)
    dpa_version = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), server_default=func.now()
    )

    @property
    def total_seats(self) -> int:
        """Total seats = base plan seats + additional purchased seats."""
        return (self.seat_count or 1) + (self.additional_seats or 0)

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
            "seat_count": self.seat_count or 1,
            "additional_seats": self.additional_seats or 0,
            "total_seats": self.total_seats,
            "dpa_accepted_at": self.dpa_accepted_at.isoformat() if self.dpa_accepted_at else None,
            "dpa_version": self.dpa_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BillingEvent(Base):
    """
    Append-only billing lifecycle event log — Phase LX.

    Records key decision metrics for founder weekly review:
    - Trial starts / conversions / expirations
    - Subscription creation / upgrade / downgrade / cancellation / churn
    - Payment failures / recoveries

    ZERO-STORAGE COMPLIANT: No financial data. Only event type, tier,
    interval, seat count, and optional metadata (e.g., cancellation reason).
    """

    __tablename__ = "billing_events"

    id = Column(Integer, primary_key=True, index=True)

    # Who (nullable — webhook events may lack user context)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # What happened
    event_type = Column(
        Enum(BillingEventType),
        nullable=False,
        index=True,
    )

    # Context at time of event
    tier = Column(String(20), nullable=True, index=True)  # solo, team
    interval = Column(String(10), nullable=True)  # monthly, annual
    seat_count = Column(Integer, nullable=True)  # total seats at event time

    # Flexible metadata (JSON string) — cancellation reason, promo code used, etc.
    # Example: {"reason": "too_expensive"}, {"promo_code": "MONTHLY20"}
    metadata_json = Column(Text, nullable=True)

    # When
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<BillingEvent(id={self.id}, type={self.event_type}, tier={self.tier})>"
