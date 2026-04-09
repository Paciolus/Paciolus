"""
Dunning episode model — Sprint 591: Failed payment workflow.

Tracks payment failure episodes through a state machine:
  NONE → FIRST_ATTEMPT_FAILED → SECOND_ATTEMPT_FAILED →
  THIRD_ATTEMPT_FAILED → GRACE_PERIOD → CANCELED

Each episode is bound to a subscription + Stripe invoice.
Resolution is terminal — no re-entry without a new episode.

ZERO-STORAGE COMPLIANT: No financial data. Only state, counts, timestamps.
"""

from datetime import UTC, datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class DunningState(str, PyEnum):
    """Dunning episode lifecycle states."""

    FIRST_ATTEMPT_FAILED = "first_attempt_failed"
    SECOND_ATTEMPT_FAILED = "second_attempt_failed"
    THIRD_ATTEMPT_FAILED = "third_attempt_failed"
    GRACE_PERIOD = "grace_period"
    CANCELED = "canceled"
    RESOLVED = "resolved"


class DunningResolution(str, PyEnum):
    """How a dunning episode was resolved."""

    PAID = "paid"
    CANCELED = "canceled"
    MANUAL_OVERRIDE = "manual_override"


class DunningEpisode(Base):
    """Tracks a payment failure episode through the dunning state machine.

    One active episode per subscription at a time. Resolution (paid,
    canceled, manual_override) is terminal — a new failure creates a
    new episode.
    """

    __tablename__ = "dunning_episodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Links
    subscription_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    org_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    stripe_invoice_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # State machine
    state: Mapped[DunningState] = mapped_column(
        Enum(DunningState), nullable=False, default=DunningState.FIRST_ATTEMPT_FAILED
    )
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Timestamps
    first_failed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    last_failed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Resolution
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution: Mapped[DunningResolution | None] = mapped_column(Enum(DunningResolution), nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_dunning_sub_state", "subscription_id", "state"),
        Index("ix_dunning_state_last_failed", "state", "last_failed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<DunningEpisode(id={self.id}, sub={self.subscription_id}, "
            f"state={self.state}, failures={self.failure_count})>"
        )

    @property
    def is_active(self) -> bool:
        """True if episode is still in progress (not resolved/canceled)."""
        return self.state not in (DunningState.CANCELED, DunningState.RESOLVED)
