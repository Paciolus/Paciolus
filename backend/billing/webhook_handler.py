"""
Stripe webhook event handler — Sprint 366.

Processes Stripe webhook events to keep local subscription state in sync.
Signature verification ensures events come from Stripe.
"""

import logging

from sqlalchemy.orm import Session

from billing.subscription_manager import get_subscription, sync_subscription_from_stripe
from models import User, UserTier
from subscription_model import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)


def _resolve_user_id(db: Session, event_data: dict) -> int | None:
    """Extract Paciolus user_id from webhook event metadata or customer lookup."""
    # Try metadata first
    metadata = event_data.get("metadata", {})
    user_id = metadata.get("paciolus_user_id")
    if user_id:
        return int(user_id)

    # Try customer ID lookup
    customer_id = event_data.get("customer")
    if customer_id:
        sub = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()
        if sub:
            return sub.user_id

    return None


def _resolve_tier_from_price(price_id: str) -> str:
    """Map a Stripe Price ID to a Paciolus tier.

    Falls back to the price's metadata or product lookup.
    In production, STRIPE_PRICE_IDS would be populated.
    """
    from billing.price_config import STRIPE_PRICE_IDS

    for tier, intervals in STRIPE_PRICE_IDS.items():
        if price_id in intervals.values():
            return tier

    # Default fallback — will be resolved when price IDs are configured
    return "professional"


def handle_checkout_completed(db: Session, event_data: dict) -> None:
    """Handle checkout.session.completed — new subscription created."""
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("checkout.session.completed: could not resolve user_id")
        return

    subscription_id = event_data.get("subscription")
    customer_id = event_data.get("customer")

    if not subscription_id or not customer_id:
        logger.warning("checkout.session.completed: missing subscription or customer ID")
        return

    # Fetch the full subscription from Stripe
    from billing.stripe_client import get_stripe
    stripe = get_stripe()
    stripe_sub = stripe.Subscription.retrieve(subscription_id)

    # Resolve tier from the price
    items = stripe_sub.get("items", {}).get("data", [])
    tier = "professional"
    if items:
        price_id = items[0].get("price", {}).get("id", "")
        tier = _resolve_tier_from_price(price_id)

    sync_subscription_from_stripe(db, user_id, stripe_sub, customer_id, tier)
    logger.info("checkout.session.completed: synced user %d to tier %s", user_id, tier)


def handle_subscription_updated(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.updated — plan change, renewal, etc."""
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("customer.subscription.updated: could not resolve user_id")
        return

    customer_id = event_data.get("customer")

    # Resolve tier
    items = event_data.get("items", {}).get("data", [])
    tier = "professional"
    if items:
        price_id = items[0].get("price", {}).get("id", "")
        tier = _resolve_tier_from_price(price_id)

    sync_subscription_from_stripe(db, user_id, event_data, customer_id, tier)
    logger.info("customer.subscription.updated: synced user %d", user_id)


def handle_subscription_deleted(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.deleted — subscription canceled."""
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("customer.subscription.deleted: could not resolve user_id")
        return

    sub = get_subscription(db, user_id)
    if sub:
        sub.status = SubscriptionStatus.CANCELED
        sub.cancel_at_period_end = False
        db.commit()

    # Downgrade user to free tier
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.tier = UserTier.FREE
        db.commit()

    logger.info("customer.subscription.deleted: user %d downgraded to free", user_id)


def handle_invoice_payment_failed(db: Session, event_data: dict) -> None:
    """Handle invoice.payment_failed — payment issue."""
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    if sub:
        sub.status = SubscriptionStatus.PAST_DUE
        db.commit()
        logger.warning("invoice.payment_failed: user %d is now past_due", sub.user_id)


def handle_invoice_paid(db: Session, event_data: dict) -> None:
    """Handle invoice.paid — successful payment (renewal or recovery)."""
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    if sub and sub.status == SubscriptionStatus.PAST_DUE:
        sub.status = SubscriptionStatus.ACTIVE
        db.commit()
        logger.info("invoice.paid: user %d recovered to active", sub.user_id)


# Event type → handler mapping
WEBHOOK_HANDLERS: dict[str, callable] = {
    "checkout.session.completed": handle_checkout_completed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.payment_failed": handle_invoice_payment_failed,
    "invoice.paid": handle_invoice_paid,
}


def process_webhook_event(db: Session, event_type: str, event_data: dict) -> bool:
    """Process a Stripe webhook event.

    Returns True if the event was handled, False if ignored.
    """
    handler = WEBHOOK_HANDLERS.get(event_type)
    if handler is None:
        logger.debug("Ignoring unhandled webhook event: %s", event_type)
        return False

    handler(db, event_data)
    return True
