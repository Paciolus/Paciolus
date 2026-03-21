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
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models import User


class SubscriptionStatus(str, PyEnum):
    """Stripe-aligned subscription lifecycle status.

    All 8 Stripe-documented subscription statuses mapped 1:1.
    AUDIT-08-F1: extended from 4 to 8 statuses; unknown defaults to PAUSED (fail closed).
    """

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"
    PAUSED = "paused"


class BillingInterval(str, PyEnum):
    """Billing frequency."""

    MONTHLY = "monthly"
    ANNUAL = "annual"


class BillingEventType(str, PyEnum):
    """Billing lifecycle event taxonomy.

    11 event types covering the complete subscription lifecycle.
    Used for post-launch decision metrics (Phase LX).
    """

    # Trial lifecycle
    TRIAL_STARTED = "trial_started"
    TRIAL_CONVERTED = "trial_converted"
    TRIAL_ENDING = "trial_ending"  # 3-day warning before trial end (trial_will_end)
    TRIAL_EXPIRED = "trial_expired"  # Trial actually ended (subscription status change)

    # Subscription lifecycle
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPGRADED = "subscription_upgraded"
    SUBSCRIPTION_DOWNGRADED = "subscription_downgraded"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    SUBSCRIPTION_CHURNED = "subscription_churned"

    # Payment lifecycle
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_RECOVERED = "payment_recovered"
    PAYMENT_SUCCEEDED = "payment_succeeded"

    # Invoice lifecycle (AUDIT-08-F6)
    INVOICE_CREATED = "invoice_created"

    # Dispute lifecycle (AUDIT-08-F5)
    DISPUTE_CREATED = "dispute_created"
    DISPUTE_RESOLVED_WON = "dispute_resolved_won"
    DISPUTE_RESOLVED_LOST = "dispute_resolved_lost"
    DISPUTE_CLOSED_OTHER = "dispute_closed_other"


class Subscription(Base):
    """
    Subscription model — links a user to their billing state.

    One subscription per user (unique constraint on user_id).
    Stripe is the source of truth; this table is a local cache
    synced via webhooks.
    """

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # One subscription per user
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user: Mapped["User"] = relationship("User", backref="subscription")

    # Plan details
    tier: Mapped[str] = mapped_column(
        Enum("free", "solo", "professional", "enterprise", name="subscription_tier"),
        nullable=False,
        default="free",
    )
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE)
    billing_interval: Mapped[BillingInterval | None] = mapped_column(Enum(BillingInterval), nullable=True)

    # Stripe references
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)

    # Billing period (synced from Stripe)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Seat management (Phase LIX Sprint B)
    seat_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Base seats from plan
    additional_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Add-on seats purchased

    # Upload quota tracking (Phase LXIX — billing-cycle-aligned)
    uploads_used_current_period: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Seat mutation versioning (AUDIT-06 FIX 1 — optimistic concurrency + idempotency)
    seat_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Cancellation
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # DPA acceptance (Sprint 459 — PI1.3 / C2.1)
    # Timestamps when the customer accepted the Data Processing Addendum, and which version.
    dpa_accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dpa_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
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
            "uploads_used_current_period": self.uploads_used_current_period or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProcessedWebhookEvent(Base):
    """Deduplication table for Stripe webhook events.

    Stores processed event IDs to prevent replay/duplicate processing.
    Stripe retries on network timeout can deliver the same event multiple times;
    this table ensures idempotent handling.
    """

    __tablename__ = "processed_webhook_events"

    stripe_event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())

    def __repr__(self) -> str:
        return f"<ProcessedWebhookEvent(id={self.stripe_event_id})>"


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Who (nullable — webhook events may lack user context)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # What happened
    event_type: Mapped[BillingEventType] = mapped_column(
        Enum(BillingEventType),
        nullable=False,
        index=True,
    )

    # Context at time of event
    tier: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)  # solo, team
    interval: Mapped[str | None] = mapped_column(String(10), nullable=True)  # monthly, annual
    seat_count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # total seats at event time

    # Flexible metadata (JSON string) — cancellation reason, promo code used, etc.
    # Example: {"reason": "too_expensive"}, {"promo_code": "MONTHLY20"}
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # When
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<BillingEvent(id={self.id}, type={self.event_type}, tier={self.tier})>"
