"""
Subscription lifecycle management — Sprint 365 + Phase LIX Sprint E + Self-Serve Checkout.

Syncs Stripe subscription state to the local Subscription model.
Stripe is the source of truth; this module keeps the local DB in sync.
Sprint E adds: add_seats() and remove_seats() for seat management.
Self-Serve Checkout: multi-item seat extraction from seat add-on line item.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from billing.stripe_client import get_stripe, to_plain_dict
from models import User, UserTier
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)

# Map Stripe subscription status to our enum — 1:1, no collapsing (AUDIT-08-F1)
_STATUS_MAP: dict[str, SubscriptionStatus] = {
    "active": SubscriptionStatus.ACTIVE,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "trialing": SubscriptionStatus.TRIALING,
    "incomplete": SubscriptionStatus.INCOMPLETE,
    "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
    "unpaid": SubscriptionStatus.UNPAID,
    "paused": SubscriptionStatus.PAUSED,
}

# Only these statuses grant paid-tier access (AUDIT-08-F1)
_ENTITLED_STATUSES = {SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING}

# Map Stripe interval to our enum
_INTERVAL_MAP: dict[str, BillingInterval] = {
    "month": BillingInterval.MONTHLY,
    "year": BillingInterval.ANNUAL,
}


def get_subscription(db: Session, user_id: int) -> Subscription | None:
    """Get the subscription for a user, or None."""
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()


def _extract_seat_quantity(stripe_subscription: dict) -> int:
    """Extract base seat quantity from the base plan subscription item.

    Returns the quantity from the base plan item (not seat add-on), defaulting to 1.
    For dual-line-item subscriptions, the base plan always has quantity=1.
    """
    from billing.price_config import get_all_seat_price_ids

    seat_ids = get_all_seat_price_ids()
    items = stripe_subscription.get("items", {}).get("data", [])
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        if price_id not in seat_ids:
            return int(item.get("quantity", 1))
    # Fallback for single-item subscriptions (backward compat)
    if items:
        return int(items[0].get("quantity", 1))
    return 1


def _extract_additional_seats(stripe_subscription: dict) -> int:
    """Extract additional seat count from the seat add-on subscription item.

    For dual-line-item subscriptions, the seat add-on item's quantity
    represents the number of additional seats beyond the plan base.
    Returns 0 if no seat add-on item is found (single-item subscription).
    """
    from billing.price_config import get_all_seat_price_ids

    seat_ids = get_all_seat_price_ids()
    items = stripe_subscription.get("items", {}).get("data", [])
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        if price_id in seat_ids:
            return int(item.get("quantity", 0))
    return 0


def _extract_billing_interval(items: list[dict]) -> BillingInterval:
    """Extract billing interval from the base plan line item.

    Identifies the base plan item (non-seat-add-on) and reads its interval.
    Uses the same seat-price-ID exclusion logic as _extract_seat_quantity
    for consistency. Falls back to MONTHLY if no items are present.
    """
    from billing.price_config import get_all_seat_price_ids

    seat_ids = get_all_seat_price_ids()
    # Find the base plan item (not a seat add-on)
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        if price_id not in seat_ids:
            stripe_interval = item.get("plan", {}).get("interval", "month")
            return _INTERVAL_MAP.get(stripe_interval, BillingInterval.MONTHLY)
    # Fallback for single-item subscriptions (backward compat)
    if items:
        stripe_interval = items[0].get("plan", {}).get("interval", "month")
        return _INTERVAL_MAP.get(stripe_interval, BillingInterval.MONTHLY)
    return BillingInterval.MONTHLY


def _extract_period_bounds(stripe_subscription: dict, items: list[dict]) -> tuple[datetime | None, datetime | None]:
    """Return the billing period (start, end) as aware UTC datetimes.

    Sprint 786b: Stripe API ``2025-03-31.basil`` moved ``current_period_start``
    / ``current_period_end`` off the Subscription and onto each Subscription
    Item. Every SDK this code has shipped on since then (stripe 15 pins
    ``2026-04-22.dahlia``, stripe 16 pins ``2026-09-30.endive``) sends a basil-or-
    later ``Stripe-Version``, so ``stripe.Subscription.retrieve()`` responses
    carry the period only on the items. Webhook payloads follow the *endpoint's*
    API version (set in the Stripe Dashboard), so they may still carry the
    legacy top-level fields.

    Read the top-level field when present (pre-basil payloads), else the base
    plan item's: its renewal is what defines the plan period.
    """

    def _ts(value: Any) -> datetime | None:
        return datetime.fromtimestamp(int(value), tz=UTC) if value else None

    start = stripe_subscription.get("current_period_start")
    end = stripe_subscription.get("current_period_end")
    if not start or not end:
        base_item = _find_base_item(items)
        if base_item is not None:
            start = start or base_item.get("current_period_start")
            end = end or base_item.get("current_period_end")
    return _ts(start), _ts(end)


def _find_base_item(items: list[dict]) -> dict | None:
    """Return the base plan item (first non-seat-add-on), else the first item."""
    from billing.price_config import get_all_seat_price_ids

    seat_ids = get_all_seat_price_ids()
    for item in items:
        if item.get("price", {}).get("id", "") not in seat_ids:
            return item
    return items[0] if items else None


def _period_advanced(old_start: datetime | None, new_start: datetime | None) -> bool:
    """True when ``new_start`` begins a later billing period than ``old_start``.

    SQLite (tests) hands back naive datetimes for a column Postgres returns
    aware, so both sides are normalised to naive UTC before comparing.
    """
    if new_start is None:
        return False
    if old_start is None:
        return True

    def _naive_utc(dt: datetime) -> datetime:
        return dt.astimezone(UTC).replace(tzinfo=None) if dt.tzinfo else dt

    return _naive_utc(new_start) > _naive_utc(old_start)


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
    status = _STATUS_MAP.get(stripe_status)
    if status is None:
        logger.error(
            "Unknown Stripe subscription status '%s' for subscription %s. Failing closed to PAUSED.",
            stripe_status,
            stripe_subscription.get("id", "unknown"),
        )
        status = SubscriptionStatus.PAUSED

    # Extract billing interval from the base plan item (not seat add-on)
    items = stripe_subscription.get("items", {}).get("data", [])
    interval = _extract_billing_interval(items)

    # Extract seat counts (Self-Serve Checkout: dual line item support)
    seat_quantity = _extract_seat_quantity(stripe_subscription)
    additional_seats = _extract_additional_seats(stripe_subscription)

    # Convert timestamps
    period_start, period_end = _extract_period_bounds(stripe_subscription, items)

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
            additional_seats=additional_seats,
        )
        db.add(sub)
    else:
        # Sprint 790: a new billing period starts a new upload allowance.
        # reset_upload_quotas (hourly) only zeroes a row whose period_end is
        # already past when it runs, but Stripe's renewal webhook advances the
        # period within seconds — so for a renewal that lands between two runs
        # the job never sees an expired row and the counter carried over into
        # the next month. Harmless while the counter never moved; a lockout
        # once it meters every run. Reset here when the period start moves
        # forward (or is first learned); an out-of-order older event does not.
        # This write may move updated_at: it *is* the processing of a Stripe
        # event, which is what the webhook ordering check is meant to see.
        period_advanced = _period_advanced(sub.current_period_start, period_start)
        sub.tier = tier
        sub.status = status
        sub.billing_interval = interval
        sub.stripe_customer_id = stripe_customer_id
        sub.stripe_subscription_id = stripe_subscription.get("id")
        sub.current_period_start = period_start
        sub.current_period_end = period_end
        sub.cancel_at_period_end = stripe_subscription.get("cancel_at_period_end", False)
        sub.seat_count = seat_quantity
        sub.additional_seats = additional_seats
        if period_advanced:
            from shared.entitlement_checks import upload_window_start

            sub.uploads_used_current_period = 0
            # Open the new period's monthly window explicitly (computed from the
            # period fields just assigned) so the zero is attributed to it.
            sub.uploads_window_start = upload_window_start(sub)

    # Also update the User.tier column — only grant plan tier if status is entitled (AUDIT-08-F1)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if status in _ENTITLED_STATUSES:
            try:
                user.tier = UserTier(tier)
            except ValueError:
                logger.warning("Unknown tier value '%s' for user %d, keeping current", tier, user_id)
        else:
            user.tier = UserTier.FREE

    db.flush()
    logger.info(
        "Synced subscription for user %d: tier=%s, status=%s, seats=%d, add_seats=%d",
        user_id,
        tier,
        status.value,
        seat_quantity,
        additional_seats,
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


def _find_seat_addon_item(items: list[dict]) -> dict | None:
    """Find the seat add-on line item from Stripe subscription items.

    Returns the item whose price ID matches a known seat add-on price,
    or None if no seat add-on item is found (single-item subscription).
    """
    from billing.price_config import get_all_seat_price_ids

    seat_ids = get_all_seat_price_ids()
    for item in items:
        price_id = item.get("price", {}).get("id", "")
        if price_id in seat_ids:
            return item
    return None


def add_seats(db: Session, user_id: int, seats_to_add: int) -> Subscription | None:
    """Add seats to an existing subscription via Stripe.

    Uses optimistic concurrency to minimize DB lock duration:
    1. Read local state WITHOUT lock (snapshot)
    2. Perform Stripe API calls (no lock held — network latency doesn't block DB)
    3. Re-acquire row with FOR UPDATE (short lock window)
    4. Verify seat_version unchanged (detects concurrent mutations)
    5. Update local state and commit (releases lock)

    The Stripe idempotency key (derived from seat_version) prevents duplicate
    billing if two callers snapshot the same version — Stripe deduplicates,
    and the version check ensures only one caller commits locally.

    Returns the updated Subscription or None if not found.
    Phase LIX Sprint E. AUDIT-06 FIX 1: concurrency-safe.
    """
    from billing.price_config import get_all_seat_price_ids, get_max_self_serve_seats

    # ── Step 1: Read local state WITHOUT lock ────────────────────────
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub is None or not sub.stripe_subscription_id:
        return None

    # Snapshot values for validation and post-Stripe staleness check
    snap_additional = sub.additional_seats or 0
    snap_version = sub.seat_version or 0
    snap_stripe_sub_id = sub.stripe_subscription_id
    snap_sub_id = sub.id

    max_seats = get_max_self_serve_seats(sub.tier)
    new_additional = snap_additional + seats_to_add
    new_total = (sub.seat_count or 1) + new_additional
    if new_total > max_seats:
        return None  # Exceeds self-serve limit

    # ── Step 2: Stripe API calls (no DB lock held) ───────────────────
    stripe = get_stripe()

    # Get current subscription items from Stripe
    stripe_sub = to_plain_dict(stripe.Subscription.retrieve(snap_stripe_sub_id))
    items = stripe_sub.get("items", {}).get("data", [])
    if not items:
        return None

    # Find the correct item to modify — seat add-on item by price ID, not position
    seat_item = _find_seat_addon_item(items)
    if seat_item:
        item_id = seat_item.get("id")
        current_quantity = seat_item.get("quantity", 0)
    elif len(items) == 1:
        # Single-item subscription (backward compat) — only item is the plan
        item_id = items[0].get("id")
        current_quantity = items[0].get("quantity", 1)
    else:
        raise ValueError(
            f"Cannot identify seat add-on item in subscription {snap_stripe_sub_id} "
            f"with {len(items)} line items. No item matched known seat price IDs: "
            f"{get_all_seat_price_ids()}"
        )

    new_quantity = current_quantity + seats_to_add

    # Increment version and generate idempotency key
    new_version = snap_version + 1
    idempotency_key = f"seat-mutation-{snap_sub_id}-v{new_version}"

    # Update Stripe with idempotency key (proration handled by Stripe)
    try:
        stripe.SubscriptionItem.modify(item_id, quantity=new_quantity, idempotency_key=idempotency_key)
    except Exception:
        db.rollback()
        raise

    # ── Step 3: Re-acquire with FOR UPDATE (short lock window) ───────
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).with_for_update().populate_existing().first()
    if sub is None:
        db.rollback()
        raise RuntimeError(f"Subscription for user {user_id} disappeared during seat mutation")

    # ── Step 4: Verify no concurrent modification ────────────────────
    if (sub.seat_version or 0) != snap_version:
        db.rollback()
        raise RuntimeError(
            f"Concurrent seat modification detected for user {user_id} "
            f"(expected version {snap_version}, found {sub.seat_version})"
        )

    # ── Step 5: Sync locally and commit ──────────────────────────────
    sub.additional_seats = new_additional
    sub.seat_version = new_version
    db.commit()

    logger.info(
        "Added %d seats for user %d: additional_seats=%d, total=%d, seat_version=%d",
        seats_to_add,
        user_id,
        new_additional,
        sub.total_seats,
        new_version,
    )
    return sub


def remove_seats(db: Session, user_id: int, seats_to_remove: int) -> Subscription | None:
    """Remove seats from an existing subscription via Stripe.

    Uses optimistic concurrency to minimize DB lock duration (same pattern
    as add_seats — see its docstring for the full protocol description).

    Cannot go below the plan's base seats (additional_seats cannot go below 0).
    Returns the updated Subscription or None if not found or invalid.
    Phase LIX Sprint E. AUDIT-06 FIX 1: concurrency-safe.
    """
    from billing.price_config import get_all_seat_price_ids

    # ── Step 1: Read local state WITHOUT lock ────────────────────────
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    if sub is None or not sub.stripe_subscription_id:
        return None

    # Snapshot values for validation and post-Stripe staleness check
    snap_additional = sub.additional_seats or 0
    snap_version = sub.seat_version or 0
    snap_stripe_sub_id = sub.stripe_subscription_id
    snap_sub_id = sub.id

    new_additional = snap_additional - seats_to_remove
    if new_additional < 0:
        return None  # Can't go below base seats

    # ── Step 2: Stripe API calls (no DB lock held) ───────────────────
    stripe = get_stripe()

    # Get current subscription items from Stripe
    stripe_sub = to_plain_dict(stripe.Subscription.retrieve(snap_stripe_sub_id))
    items = stripe_sub.get("items", {}).get("data", [])
    if not items:
        return None

    # Find the correct item to modify — seat add-on item by price ID, not position
    seat_item = _find_seat_addon_item(items)
    if seat_item:
        item_id = seat_item.get("id")
        current_quantity = seat_item.get("quantity", 0)
    elif len(items) == 1:
        # Single-item subscription (backward compat) — only item is the plan
        item_id = items[0].get("id")
        current_quantity = items[0].get("quantity", 1)
    else:
        raise ValueError(
            f"Cannot identify seat add-on item in subscription {snap_stripe_sub_id} "
            f"with {len(items)} line items. No item matched known seat price IDs: "
            f"{get_all_seat_price_ids()}"
        )

    new_quantity = current_quantity - seats_to_remove

    # Increment version and generate idempotency key
    new_version = snap_version + 1
    idempotency_key = f"seat-mutation-{snap_sub_id}-v{new_version}"

    # If quantity reaches 0, delete the subscription item entirely
    # (Stripe does not allow quantity=0 on most price types)
    try:
        if new_quantity <= 0:
            stripe.SubscriptionItem.delete(item_id, idempotency_key=idempotency_key)
        else:
            stripe.SubscriptionItem.modify(item_id, quantity=new_quantity, idempotency_key=idempotency_key)
    except Exception:
        db.rollback()
        raise

    # ── Step 3: Re-acquire with FOR UPDATE (short lock window) ───────
    sub = db.query(Subscription).filter(Subscription.user_id == user_id).with_for_update().populate_existing().first()
    if sub is None:
        db.rollback()
        raise RuntimeError(f"Subscription for user {user_id} disappeared during seat mutation")

    # ── Step 4: Verify no concurrent modification ────────────────────
    if (sub.seat_version or 0) != snap_version:
        db.rollback()
        raise RuntimeError(
            f"Concurrent seat modification detected for user {user_id} "
            f"(expected version {snap_version}, found {sub.seat_version})"
        )

    # ── Step 5: Sync locally and commit ──────────────────────────────
    sub.additional_seats = new_additional
    sub.seat_version = new_version
    db.commit()

    logger.info(
        "Removed %d seats for user %d: additional_seats=%d, total=%d, seat_version=%d",
        seats_to_remove,
        user_id,
        new_additional,
        sub.total_seats,
        new_version,
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
    return str(session.url)
