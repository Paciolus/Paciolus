"""
Subscription lifecycle management — Sprint 365 + Phase LIX Sprint E.

Syncs Stripe subscription state to the local Subscription model.
Stripe is the source of truth; this module keeps the local DB in sync.
Sprint E adds: add_seats() and remove_seats() for seat management.
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


def _extract_seat_quantity(stripe_subscription: dict) -> int:
    """Extract seat quantity from Stripe subscription items.

    Stripe subscriptions can have quantity > 1 for seat-based plans.
    Returns the quantity from the first subscription item, defaulting to 1.
    """
    items = stripe_subscription.get("items", {}).get("data", [])
    if items:
        return items[0].get("quantity", 1)
    return 1


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
    Extracts seat quantity from Stripe subscription items (Phase LIX Sprint B).
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

    # Extract seat quantity (Phase LIX Sprint B)
    seat_quantity = _extract_seat_quantity(stripe_subscription)

    # Convert timestamps
    period_start = None
    period_end = None
    if stripe_subscription.get("current_period_start"):
        period_start = datetime.fromtimestamp(stripe_subscription["current_period_start"], tz=UTC)
    if stripe_subscription.get("current_period_end"):
        period_end = datetime.fromtimestamp(stripe_subscription["current_period_end"], tz=UTC)

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
            seat_count=seat_quantity,
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
        sub.seat_count = seat_quantity

    # Also update the User.tier column
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        try:
            user.tier = UserTier(tier)
        except ValueError:
            logger.warning("Unknown tier value '%s' for user %d, keeping current", tier, user_id)

    db.commit()
    logger.info(
        "Synced subscription for user %d: tier=%s, status=%s, seats=%d",
        user_id,
        tier,
        status.value,
        seat_quantity,
    )
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


def add_seats(db: Session, user_id: int, seats_to_add: int) -> Subscription | None:
    """Add seats to an existing subscription via Stripe.

    Updates the Stripe subscription item quantity and syncs locally.
    Returns the updated Subscription or None if not found.
    Phase LIX Sprint E.
    """
    from billing.price_config import MAX_SELF_SERVE_SEATS

    sub = get_subscription(db, user_id)
    if sub is None or not sub.stripe_subscription_id:
        return None

    new_additional = (sub.additional_seats or 0) + seats_to_add
    new_total = (sub.seat_count or 1) + new_additional
    if new_total > MAX_SELF_SERVE_SEATS:
        return None  # Exceeds self-serve limit

    stripe = get_stripe()

    # Get current subscription items from Stripe
    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
    items = stripe_sub.get("items", {}).get("data", [])
    if not items:
        return None

    item_id = items[0].get("id")
    current_quantity = items[0].get("quantity", 1)
    new_quantity = current_quantity + seats_to_add

    # Update Stripe subscription item quantity (proration handled by Stripe)
    stripe.SubscriptionItem.modify(item_id, quantity=new_quantity)

    # Sync locally
    sub.additional_seats = new_additional
    db.commit()

    logger.info(
        "Added %d seats for user %d: additional_seats=%d, total=%d",
        seats_to_add,
        user_id,
        new_additional,
        sub.total_seats,
    )
    return sub


def remove_seats(db: Session, user_id: int, seats_to_remove: int) -> Subscription | None:
    """Remove seats from an existing subscription via Stripe.

    Cannot go below the plan's base seats (additional_seats cannot go below 0).
    Returns the updated Subscription or None if not found or invalid.
    Phase LIX Sprint E.
    """
    sub = get_subscription(db, user_id)
    if sub is None or not sub.stripe_subscription_id:
        return None

    current_additional = sub.additional_seats or 0
    new_additional = current_additional - seats_to_remove
    if new_additional < 0:
        return None  # Can't go below base seats

    stripe = get_stripe()

    # Get current subscription items from Stripe
    stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
    items = stripe_sub.get("items", {}).get("data", [])
    if not items:
        return None

    item_id = items[0].get("id")
    current_quantity = items[0].get("quantity", 1)
    new_quantity = max(1, current_quantity - seats_to_remove)

    # Update Stripe subscription item quantity
    stripe.SubscriptionItem.modify(item_id, quantity=new_quantity)

    # Sync locally
    sub.additional_seats = new_additional
    db.commit()

    logger.info(
        "Removed %d seats for user %d: additional_seats=%d, total=%d",
        seats_to_remove,
        user_id,
        new_additional,
        sub.total_seats,
    )
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
