"""
Stripe webhook event handler — Sprint 366 + Phase LIX Sprint C + Self-Serve Checkout.
Phase LX: BillingEvent recording for post-launch analytics.

Processes Stripe webhook events to keep local subscription state in sync.
Signature verification ensures events come from Stripe.
Sprint C adds: customer.subscription.trial_will_end handler.
Self-Serve Checkout: multi-item subscription handling, seat add-on filtering.
Phase LX: Each handler records a BillingEvent for decision metrics.
"""

import logging

from sqlalchemy.orm import Session

from billing.subscription_manager import get_subscription, sync_subscription_from_stripe
from models import User, UserTier
from subscription_model import BillingEventType, Subscription, SubscriptionStatus

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
        sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
        if sub:
            return sub.user_id

    return None


def _resolve_tier_from_price(price_id: str) -> str | None:
    """Map a Stripe Price ID to a Paciolus tier.

    Returns None if the price ID is unrecognized or is a seat add-on price.
    Callers must handle None (log + skip sync) — never silently default.
    """
    from billing.price_config import _load_stripe_price_ids, get_all_seat_price_ids

    # Skip seat add-on prices — they don't map to a tier
    if price_id in get_all_seat_price_ids():
        return None

    for tier, intervals in _load_stripe_price_ids().items():
        if price_id in intervals.values():
            return tier

    logger.warning("Unrecognized Stripe Price ID: %s — cannot resolve tier", price_id)
    return None


def _find_base_plan_item(items: list[dict]) -> dict | None:
    """Find the base plan line item (not a seat add-on) from subscription items.

    Returns the first item whose price ID is NOT a seat add-on.
    Falls back to the first item if all items are unrecognized (backward compat).
    """
    from billing.price_config import get_all_seat_price_ids

    seat_ids = get_all_seat_price_ids()
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        if price_id not in seat_ids:
            return item
    return items[0] if items else None


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

    # Resolve tier from the base plan item (skip seat add-ons)
    items = stripe_sub.get("items", {}).get("data", [])
    base_item = _find_base_plan_item(items)
    tier: str | None = None
    if base_item:
        price_id = base_item.get("price", {}).get("id", "")
        tier = _resolve_tier_from_price(price_id)

    if tier is None:
        logger.error(
            "checkout.session.completed: could not resolve tier for user %d (subscription %s)",
            user_id,
            subscription_id,
        )
        return

    sync_subscription_from_stripe(db, user_id, stripe_sub, customer_id, tier)
    logger.info("checkout.session.completed: synced user %d to tier %s", user_id, tier)

    # Phase LX: Record billing event
    from billing.analytics import record_billing_event

    stripe_status = stripe_sub.get("status", "")
    interval = stripe_sub.get("items", {}).get("data", [{}])[0].get("plan", {}).get("interval", "")
    interval_mapped = "annual" if interval == "year" else "monthly"

    if stripe_status == "trialing":
        record_billing_event(
            db,
            BillingEventType.TRIAL_STARTED,
            user_id=user_id,
            tier=tier,
            interval=interval_mapped,
        )
    else:
        record_billing_event(
            db,
            BillingEventType.SUBSCRIPTION_CREATED,
            user_id=user_id,
            tier=tier,
            interval=interval_mapped,
        )


def handle_subscription_updated(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.updated — plan change, renewal, etc."""
    user_id = _resolve_user_id(db, event_data)
    if user_id is None:
        logger.warning("customer.subscription.updated: could not resolve user_id")
        return

    customer_id = event_data.get("customer")

    # Resolve tier from the base plan item (skip seat add-ons)
    items = event_data.get("items", {}).get("data", [])
    base_item = _find_base_plan_item(items)
    tier: str | None = None
    if base_item:
        price_id = base_item.get("price", {}).get("id", "")
        tier = _resolve_tier_from_price(price_id)

    if tier is None:
        logger.error(
            "customer.subscription.updated: could not resolve tier for user %d",
            user_id,
        )
        return

    # Phase LX: Detect trial→paid conversion or tier change before sync
    from billing.analytics import record_billing_event

    existing_sub = get_subscription(db, user_id)
    old_status = existing_sub.status if existing_sub else None
    old_tier = existing_sub.tier if existing_sub else None
    new_status = event_data.get("status", "")

    sync_subscription_from_stripe(db, user_id, event_data, customer_id, tier)
    logger.info("customer.subscription.updated: synced user %d to tier %s", user_id, tier)

    # Trial → paid conversion
    if old_status == SubscriptionStatus.TRIALING and new_status == "active":
        record_billing_event(
            db,
            BillingEventType.TRIAL_CONVERTED,
            user_id=user_id,
            tier=tier,
        )
    # Tier upgrade/downgrade (only if both old and new tier are known)
    elif old_tier and old_tier != tier:
        _TIER_RANK = {"free": 0, "solo": 1, "professional": 1, "team": 2, "enterprise": 3}
        old_rank = _TIER_RANK.get(old_tier, 0)
        new_rank = _TIER_RANK.get(tier, 0)
        if new_rank > old_rank:
            record_billing_event(
                db,
                BillingEventType.SUBSCRIPTION_UPGRADED,
                user_id=user_id,
                tier=tier,
                metadata={"from_tier": old_tier},
            )
        elif new_rank < old_rank:
            record_billing_event(
                db,
                BillingEventType.SUBSCRIPTION_DOWNGRADED,
                user_id=user_id,
                tier=tier,
                metadata={"from_tier": old_tier},
            )


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

    # Phase LX: Record churn event (subscription actually ended)
    from billing.analytics import record_billing_event

    old_tier = sub.tier if sub else None
    record_billing_event(
        db,
        BillingEventType.SUBSCRIPTION_CHURNED,
        user_id=user_id,
        tier=old_tier,
    )


def handle_invoice_payment_failed(db: Session, event_data: dict) -> None:
    """Handle invoice.payment_failed — payment issue."""
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    if sub:
        sub.status = SubscriptionStatus.PAST_DUE
        db.commit()
        logger.warning("invoice.payment_failed: user %d is now past_due", sub.user_id)

        # Phase LX: Record payment failure event
        from billing.analytics import record_billing_event

        record_billing_event(
            db,
            BillingEventType.PAYMENT_FAILED,
            user_id=sub.user_id,
            tier=sub.tier,
        )


def handle_invoice_paid(db: Session, event_data: dict) -> None:
    """Handle invoice.paid — successful payment (renewal or recovery)."""
    customer_id = event_data.get("customer")
    if not customer_id:
        return

    sub = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    if sub and sub.status == SubscriptionStatus.PAST_DUE:
        sub.status = SubscriptionStatus.ACTIVE
        db.commit()
        logger.info("invoice.paid: user %d recovered to active", sub.user_id)

        # Phase LX: Record payment recovery event
        from billing.analytics import record_billing_event

        record_billing_event(
            db,
            BillingEventType.PAYMENT_RECOVERED,
            user_id=sub.user_id,
            tier=sub.tier,
        )


def handle_subscription_trial_will_end(db: Session, event_data: dict) -> None:
    """Handle customer.subscription.trial_will_end — 3 days before trial expires.

    Phase LIX Sprint C. Logs the event for monitoring.
    Notification email infrastructure deferred to a future sprint.
    """
    user_id = _resolve_user_id(db, event_data)
    trial_end = event_data.get("trial_end")

    if user_id is None:
        logger.warning("customer.subscription.trial_will_end: could not resolve user_id")
        return

    logger.info(
        "customer.subscription.trial_will_end: user %d trial ends at %s",
        user_id,
        trial_end,
    )

    # Phase LX: Record trial expiration warning (used for tracking non-converters)
    from billing.analytics import record_billing_event

    sub = get_subscription(db, user_id)
    record_billing_event(
        db,
        BillingEventType.TRIAL_EXPIRED,
        user_id=user_id,
        tier=sub.tier if sub else None,
    )


# Event type → handler mapping
WEBHOOK_HANDLERS: dict[str, callable] = {
    "checkout.session.completed": handle_checkout_completed,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "customer.subscription.trial_will_end": handle_subscription_trial_will_end,
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
