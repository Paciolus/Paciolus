"""
Subscription lifecycle management — Sprint 365.

Syncs Stripe subscription state to the local Subscription model.
Stripe is the source of truth; this module keeps the local DB in sync.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from billing.stripe_client import get_stripe
from models import User, UserTier
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)

# Map Stripe subscription status to our enum
_STATUS_MAP: dict[str, SubscriptionStatus] = {
    "active": SubscriptionStatus.ACTIVE,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "trialing": SubscriptionStatus.TRIALING,
    "incomplete": SubscriptionStatus.PAST_DUE,  # treat incomplete as past_due
    "incomplete_expired": SubscriptionStatus.CANCELED,
    "unpaid": SubscriptionStatus.PAST_DUE,
}

# Map Stripe interval to our enum
_INTERVAL_MAP: dict[str, BillingInterval] = {
    "month": BillingInterval.MONTHLY,
    "year": BillingInterval.ANNUAL,
}


def get_subscription(db: Session, user_id: int) -> Subscription | None:
    """Get the subscription for a user, or None."""
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()


def sync_subscription_from_stripe(
    db: Session,
    user_id: int,
    stripe_subscription: dict,
    stripe_customer_id: str,
    tier: str,
) -> Subscription:
    """Sync a Stripe subscription to the local DB.

    Creates or updates the local Subscription record.
    Also updates the User.tier to match.
    """
    sub = get_subscription(db, user_id)

    stripe_status = stripe_subscription.get("status", "active")
    status = _STATUS_MAP.get(stripe_status, SubscriptionStatus.ACTIVE)

    # Extract billing interval from the first item
    items = stripe_subscription.get("items", {}).get("data", [])
    interval = BillingInterval.MONTHLY
    if items:
        stripe_interval = items[0].get("plan", {}).get("interval", "month")
        interval = _INTERVAL_MAP.get(stripe_interval, BillingInterval.MONTHLY)

    # Convert timestamps
    period_start = None
    period_end = None
    if stripe_subscription.get("current_period_start"):
        period_start = datetime.fromtimestamp(
            stripe_subscription["current_period_start"], tz=UTC
        )
    if stripe_subscription.get("current_period_end"):
        period_end = datetime.fromtimestamp(
            stripe_subscription["current_period_end"], tz=UTC
        )

    if sub is None:
        sub = Subscription(
            user_id=user_id,
            tier=tier,
            status=status,
            billing_interval=interval,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription.get("id"),
            current_period_start=period_start,
            current_period_end=period_end,
            cancel_at_period_end=stripe_subscription.get("cancel_at_period_end", False),
        )
        db.add(sub)
    else:
        sub.tier = tier
        sub.status = status
        sub.billing_interval = interval
        sub.stripe_customer_id = stripe_customer_id
        sub.stripe_subscription_id = stripe_subscription.get("id")
        sub.current_period_start = period_start
        sub.current_period_end = period_end
        sub.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)

    # Also update the User.tier column
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        try:
            user.tier = UserTier(tier)
        except ValueError:
            logger.warning("Unknown tier value '%s' for user %d, keeping current", tier, user_id)

    db.commit()
    logger.info("Synced subscription for user %d: tier=%s, status=%s", user_id, tier, status.value)
    return sub


def cancel_subscription(db: Session, user_id: int) -> Subscription | None:
    """Cancel a subscription at period end via Stripe.

    Returns the updated Subscription or None if not found.
    """
    sub = get_subscription(db, user_id)
    if sub is None or not sub.stripe_subscription_id:
        return None

    stripe = get_stripe()
    stripe.Subscription.modify(
        sub.stripe_subscription_id,
        cancel_at_period_end=True,
    )

    sub.cancel_at_period_end = True
    db.commit()
    logger.info("Subscription cancellation scheduled for user %d", user_id)
    return sub


def reactivate_subscription(db: Session, user_id: int) -> Subscription | None:
    """Reactivate a subscription that was set to cancel at period end.

    Returns the updated Subscription or None if not found.
    """
    sub = get_subscription(db, user_id)
    if sub is None or not sub.stripe_subscription_id:
        return None

    stripe = get_stripe()
    stripe.Subscription.modify(
        sub.stripe_subscription_id,
        cancel_at_period_end=False,
    )

    sub.cancel_at_period_end = False
    db.commit()
    logger.info("Subscription reactivated for user %d", user_id)
    return sub


def create_portal_session(stripe_customer_id: str, return_url: str) -> str:
    """Create a Stripe Billing Portal session for self-service management.

    Returns the portal session URL.
    """
    stripe = get_stripe()
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url
