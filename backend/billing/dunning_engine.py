"""
Dunning engine — Sprint 591: Failed payment state machine.

Manages the lifecycle of payment failure episodes:
  FIRST_ATTEMPT_FAILED → SECOND → THIRD → GRACE_PERIOD → CANCELED
  Any dunning state → RESOLVED (when payment succeeds)

All state transitions are idempotent — duplicate webhooks will not
cause duplicate emails or state corruption.

Email sends are non-blocking (fire-and-forget with error logging).
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from billing.price_config import PRICE_TABLE
from dunning_model import DunningEpisode, DunningResolution, DunningState
from models import User, UserTier
from subscription_model import (
    Subscription,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)

# Retry schedule: days after each failure before Stripe's next retry
_RETRY_DELAYS = {
    DunningState.FIRST_ATTEMPT_FAILED: 3,  # Wait 3 days
    DunningState.SECOND_ATTEMPT_FAILED: 5,  # Wait 5 more days
    DunningState.THIRD_ATTEMPT_FAILED: 7,  # 7-day grace period
}

# Grace period: days after 3rd failure before cancellation
GRACE_PERIOD_DAYS = 7


# ---------------------------------------------------------------------------
# Public API — called from webhook handlers
# ---------------------------------------------------------------------------


def handle_payment_failed(db: Session, sub: Subscription, stripe_invoice_id: str | None = None) -> DunningEpisode:
    """Process a payment failure for a subscription.

    Creates or advances a dunning episode, triggers the appropriate email.
    Idempotent: if the episode is already at or past the expected state for
    this failure count, no state change or email is sent.

    Returns the dunning episode.
    """
    episode = _get_or_create_episode(db, sub, stripe_invoice_id)

    # Determine the new state based on failure count
    old_state = episode.state
    episode.failure_count += 1
    episode.last_failed_at = datetime.now(UTC)

    if episode.failure_count == 1:
        new_state = DunningState.FIRST_ATTEMPT_FAILED
    elif episode.failure_count == 2:
        new_state = DunningState.SECOND_ATTEMPT_FAILED
    elif episode.failure_count >= 3:
        new_state = DunningState.THIRD_ATTEMPT_FAILED
    else:
        new_state = old_state

    # Idempotency: only advance state forward, never backward.
    # Skip this check for newly created episodes (first failure).
    is_new = getattr(episode, "_is_new", False)
    if is_new:
        episode._is_new = False  # type: ignore[attr-defined]
    else:
        state_order = _state_order()
        if state_order.get(new_state, 0) <= state_order.get(old_state, 0):
            logger.debug(
                "Dunning idempotent skip: episode %d already at %s, not moving to %s",
                episode.id,
                old_state.value,
                new_state.value,
            )
            db.flush()
            return episode

    episode.state = new_state

    # Set next retry date (for display purposes — Stripe handles actual retries)
    retry_days = _RETRY_DELAYS.get(new_state)
    if retry_days:
        episode.next_retry_at = datetime.now(UTC) + timedelta(days=retry_days)

    db.flush()

    logger.info(
        "Dunning transition: episode %d, sub %d: %s → %s (failure #%d)",
        episode.id,
        sub.id,
        old_state.value,
        new_state.value,
        episode.failure_count,
    )

    # Fire email (non-blocking)
    _send_dunning_email_for_state(db, sub, episode, new_state)

    return episode


def handle_payment_recovered(db: Session, sub: Subscription) -> DunningEpisode | None:
    """Mark active dunning episode as resolved when payment succeeds.

    Returns the resolved episode, or None if no active episode existed.
    """
    episode = _get_active_episode(db, sub.id)
    if not episode:
        return None

    old_state = episode.state
    episode.state = DunningState.RESOLVED
    episode.resolved_at = datetime.now(UTC)
    episode.resolution = DunningResolution.PAID
    episode.next_retry_at = None
    db.flush()

    logger.info(
        "Dunning resolved (paid): episode %d, sub %d, was %s",
        episode.id,
        sub.id,
        old_state.value,
    )

    # Send recovery email
    _send_recovery_email(db, sub)

    return episode


def process_grace_period_expirations(db: Session) -> int:
    """Cancel subscriptions whose grace period has expired.

    Called hourly by the scheduler. Queries episodes in
    THIRD_ATTEMPT_FAILED state where last_failed_at + 7 days < now.

    Returns count of episodes canceled.
    """
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=GRACE_PERIOD_DAYS)

    expired = (
        db.query(DunningEpisode)
        .filter(
            DunningEpisode.state == DunningState.THIRD_ATTEMPT_FAILED,
            DunningEpisode.last_failed_at <= cutoff,
        )
        .all()
    )

    canceled_count = 0
    for episode in expired:
        sub = db.query(Subscription).filter(Subscription.id == episode.subscription_id).first()
        if not sub:
            continue

        # Cancel the subscription
        sub.status = SubscriptionStatus.CANCELED
        user = db.query(User).filter(User.id == sub.user_id).first()
        if user:
            user.tier = UserTier.FREE

        # Transition episode to CANCELED
        episode.state = DunningState.CANCELED
        episode.resolved_at = now
        episode.resolution = DunningResolution.CANCELED
        episode.next_retry_at = None

        db.flush()

        # Record billing event
        from billing.analytics import record_billing_event
        from subscription_model import BillingEventType

        record_billing_event(
            db,
            BillingEventType.SUBSCRIPTION_CHURNED,
            user_id=sub.user_id,
            tier=sub.tier,
            metadata={"reason": "dunning_grace_period_expired", "dunning_episode_id": episode.id},
        )

        # Send suspension email
        _send_suspension_email(db, sub)

        canceled_count += 1

        logger.info(
            "Dunning grace expired: episode %d, sub %d canceled",
            episode.id,
            sub.id,
        )

    return canceled_count


def resolve_manually(db: Session, episode_id: int, reason: str | None = None) -> DunningEpisode | None:
    """Manually resolve a dunning episode (admin action).

    Returns the resolved episode, or None if not found/already resolved.
    """
    episode = db.query(DunningEpisode).filter(DunningEpisode.id == episode_id).first()
    if not episode or not episode.is_active:
        return None

    episode.state = DunningState.RESOLVED
    episode.resolved_at = datetime.now(UTC)
    episode.resolution = DunningResolution.MANUAL_OVERRIDE
    episode.next_retry_at = None
    db.flush()

    logger.info("Dunning manually resolved: episode %d, reason=%s", episode.id, reason)

    return episode


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_or_create_episode(db: Session, sub: Subscription, stripe_invoice_id: str | None) -> DunningEpisode:
    """Get the active dunning episode for a subscription, or create one.

    If an active episode exists, return it (even if for a different invoice).
    If no active episode, create a new one.
    """
    active = _get_active_episode(db, sub.id)
    if active:
        # Update invoice ID if provided (Stripe may send a new invoice on retry)
        if stripe_invoice_id and active.stripe_invoice_id != stripe_invoice_id:
            active.stripe_invoice_id = stripe_invoice_id
        return active

    # Create new episode. failure_count starts at 0; handle_payment_failed
    # will increment it and set the real state.  We temporarily use
    # FIRST_ATTEMPT_FAILED as a placeholder but mark _is_new so the caller
    # knows to bypass the idempotency guard on the first transition.
    now = datetime.now(UTC)
    episode = DunningEpisode(
        subscription_id=sub.id,
        org_id=_resolve_org_id(db, sub.user_id),
        stripe_invoice_id=stripe_invoice_id,
        state=DunningState.FIRST_ATTEMPT_FAILED,
        failure_count=0,  # Will be incremented by caller
        first_failed_at=now,
        last_failed_at=now,
    )
    episode._is_new = True  # type: ignore[attr-defined]
    db.add(episode)
    db.flush()
    return episode


def _get_active_episode(db: Session, subscription_id: int) -> DunningEpisode | None:
    """Get the active (non-resolved, non-canceled) dunning episode for a subscription."""
    return (
        db.query(DunningEpisode)
        .filter(
            DunningEpisode.subscription_id == subscription_id,
            DunningEpisode.state.notin_([DunningState.CANCELED, DunningState.RESOLVED]),
        )
        .first()
    )


def _resolve_org_id(db: Session, user_id: int) -> int | None:
    """Resolve the org_id for a user."""
    user = db.query(User).filter(User.id == user_id).first()
    return user.organization_id if user else None


def _state_order() -> dict[DunningState, int]:
    """Numeric ordering of states for idempotency checks."""
    return {
        DunningState.FIRST_ATTEMPT_FAILED: 1,
        DunningState.SECOND_ATTEMPT_FAILED: 2,
        DunningState.THIRD_ATTEMPT_FAILED: 3,
        DunningState.GRACE_PERIOD: 4,
        DunningState.CANCELED: 5,
        DunningState.RESOLVED: 5,
    }


def _format_amount(sub: Subscription) -> str:
    """Format subscription price as dollar string."""
    tier = sub.tier or "free"
    interval = sub.billing_interval.value if sub.billing_interval else "monthly"
    cents = PRICE_TABLE.get(tier, {}).get(interval, 0)
    return f"${cents / 100:.2f}"


def _format_plan_name(sub: Subscription) -> str:
    """Format plan name for email."""
    tier = (sub.tier or "free").capitalize()
    interval = sub.billing_interval.value if sub.billing_interval else "monthly"
    return f"Paciolus {tier} ({interval})"


def _get_portal_url(sub: Subscription) -> str:
    """Get the Stripe billing portal URL for payment method updates."""
    from config import FRONTEND_URL

    # Direct users to the billing settings page (which has a portal link)
    return f"{FRONTEND_URL}/settings/billing"


def _send_dunning_email_for_state(db: Session, sub: Subscription, episode: DunningEpisode, state: DunningState) -> None:
    """Send the appropriate dunning email for a state transition. Non-blocking."""
    user = db.query(User).filter(User.id == sub.user_id).first()
    if not user:
        return

    portal_url = _get_portal_url(sub)
    amount = _format_amount(sub)
    plan_name = _format_plan_name(sub)

    try:
        from email_service import (
            send_dunning_final_notice,
            send_dunning_first_failure,
            send_dunning_second_failure,
        )

        if state == DunningState.FIRST_ATTEMPT_FAILED:
            send_dunning_first_failure(user.email, amount, plan_name, portal_url)
        elif state == DunningState.SECOND_ATTEMPT_FAILED:
            send_dunning_second_failure(user.email, amount, portal_url)
        elif state == DunningState.THIRD_ATTEMPT_FAILED:
            suspension_date = (datetime.now(UTC) + timedelta(days=GRACE_PERIOD_DAYS)).strftime("%B %d, %Y")
            send_dunning_final_notice(user.email, suspension_date, portal_url)
    except Exception:
        logger.exception("Failed to send dunning email for episode %d", episode.id)


def _send_recovery_email(db: Session, sub: Subscription) -> None:
    """Send payment recovered email. Non-blocking."""
    user = db.query(User).filter(User.id == sub.user_id).first()
    if not user:
        return

    try:
        from email_service import send_dunning_recovered

        send_dunning_recovered(user.email, _format_amount(sub))
    except Exception:
        logger.exception("Failed to send recovery email for sub %d", sub.id)


def _send_suspension_email(db: Session, sub: Subscription) -> None:
    """Send account suspended email. Non-blocking."""
    user = db.query(User).filter(User.id == sub.user_id).first()
    if not user:
        return

    try:
        from config import FRONTEND_URL
        from email_service import send_dunning_suspended

        send_dunning_suspended(user.email, f"{FRONTEND_URL}/pricing")
    except Exception:
        logger.exception("Failed to send suspension email for sub %d", sub.id)
