"""
Checkout orchestration — Sprint 519 Phase 5

Extracts checkout business logic from the billing route layer.
The route keeps HTTP concerns (request parsing, error→HTTPException mapping).

Saga pattern: Each Stripe step has a compensating action.
- Customer creation → delete customer on later failure
- Checkout session creation → no compensation needed (sessions expire automatically)
- DB commit failure → log Stripe resource IDs for manual reconciliation
"""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _rollback_stripe_customer(customer_id: str, user_id: int) -> None:
    """Compensating action: delete an orphaned Stripe customer.

    Best-effort — if this also fails, we log for manual reconciliation.
    """
    from billing.stripe_client import get_stripe

    try:
        stripe = get_stripe()
        stripe.Customer.delete(customer_id)
        logger.info(
            "Saga rollback: deleted orphaned Stripe customer %s (user %d)",
            customer_id,
            user_id,
        )
    except Exception:
        logger.critical(
            "MANUAL RECONCILIATION REQUIRED: Failed to delete orphaned Stripe "
            "customer %s for user %d. Delete manually in the Stripe dashboard.",
            customer_id,
            user_id,
            exc_info=True,
        )


class CheckoutValidationError(Exception):
    """Raised when checkout input validation fails (→ 400)."""

    pass


class CheckoutProviderError(Exception):
    """Raised when Stripe API call fails (→ 502)."""

    pass


class CheckoutUnavailableError(Exception):
    """Raised when billing is not enabled (→ 503)."""

    pass


@dataclass
class CheckoutParams:
    """Validated checkout parameters ready for Stripe session creation."""

    customer_id: str
    plan_price_id: str
    user_id: int
    trial_period_days: int = 0
    stripe_coupon_id: Optional[str] = None
    seat_price_id: Optional[str] = None
    additional_seats: int = 0
    dpa_accepted_at: Optional[str] = None
    dpa_version: Optional[str] = None


def orchestrate_checkout(
    tier: str,
    interval: str,
    seat_count: int,
    promo_code: Optional[str],
    dpa_accepted: bool,
    user_id: int,
    user_email: str,
    db: Session,
) -> str:
    """Validate inputs, resolve Stripe entities, create checkout session.

    Returns the checkout URL string.
    Raises CheckoutValidationError, CheckoutProviderError, or CheckoutUnavailableError.
    """
    from billing.checkout import create_checkout_session, create_or_get_stripe_customer
    from billing.price_config import (
        TRIAL_ELIGIBLE_TIERS,
        TRIAL_PERIOD_DAYS,
        get_max_self_serve_seats,
        get_stripe_coupon_id,
        get_stripe_price_id,
        get_stripe_seat_price_id,
        validate_promo_for_interval,
    )
    from billing.stripe_client import is_stripe_enabled
    from billing.subscription_manager import get_subscription
    from models import UserTier
    from shared.entitlements import get_entitlements

    # 1. Check billing enabled
    if not is_stripe_enabled():
        raise CheckoutUnavailableError("Billing is not currently available. Please contact sales.")

    # 2. Resolve price
    price_id = get_stripe_price_id(tier, interval)
    if not price_id:
        raise CheckoutValidationError(f"No price configured for {tier}/{interval}. Please contact support.")

    # 3. Get or create Stripe customer (saga step 1)
    existing_sub = get_subscription(db, user_id)
    stripe_customer_id = existing_sub.stripe_customer_id if existing_sub else None
    created_new_customer = False

    try:
        customer_id = create_or_get_stripe_customer(user_id, user_email, stripe_customer_id)
        created_new_customer = customer_id != stripe_customer_id
    except Exception:
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    # Save customer ID if new (deferred commit — atomic with session creation)
    if existing_sub and not existing_sub.stripe_customer_id:
        existing_sub.stripe_customer_id = customer_id

    # 4. Validate and resolve promo code
    stripe_coupon_id: str | None = None
    if promo_code:
        promo_error = validate_promo_for_interval(promo_code, interval)
        if promo_error:
            if created_new_customer:
                _rollback_stripe_customer(customer_id, user_id)
            raise CheckoutValidationError(promo_error)
        stripe_coupon_id = get_stripe_coupon_id(promo_code)
        if not stripe_coupon_id:
            if created_new_customer:
                _rollback_stripe_customer(customer_id, user_id)
            raise CheckoutValidationError("Promo code is not currently available. Please contact support.")

    # 5. Trial eligibility
    trial_days = 0
    is_new_subscription = existing_sub is None or existing_sub.status.value == "canceled"
    if is_new_subscription and tier in TRIAL_ELIGIBLE_TIERS:
        trial_days = TRIAL_PERIOD_DAYS

    # 6. Seat validation
    if seat_count > 0 and tier == "solo":
        if created_new_customer:
            _rollback_stripe_customer(customer_id, user_id)
        raise CheckoutValidationError("Solo plan does not support additional seats.")

    entitlements = get_entitlements(UserTier(tier))
    seats_included = entitlements.seats_included
    total_seats = seats_included + seat_count
    max_seats = get_max_self_serve_seats(tier)
    if total_seats > max_seats:
        if created_new_customer:
            _rollback_stripe_customer(customer_id, user_id)
        raise CheckoutValidationError(f"Maximum {max_seats} seats via self-serve. Contact sales for more.")

    additional_seats = seat_count
    seat_price_id: str | None = None
    if additional_seats > 0:
        seat_price_id = get_stripe_seat_price_id(interval, tier)
        if not seat_price_id:
            if created_new_customer:
                _rollback_stripe_customer(customer_id, user_id)
            raise CheckoutValidationError("Seat pricing not configured. Contact support.")

    # 7. DPA acceptance (deferred commit — atomic with session creation)
    from datetime import UTC, datetime

    dpa_accepted_at_str: str | None = None
    dpa_version_str: str | None = None

    if dpa_accepted and tier in ("professional", "enterprise"):
        now_utc = datetime.now(UTC)
        dpa_accepted_at_str = now_utc.isoformat()
        dpa_version_str = "1.0"
        if existing_sub:
            existing_sub.dpa_accepted_at = now_utc
            existing_sub.dpa_version = dpa_version_str
            logger.info("DPA v%s accepted by user %d (existing sub)", dpa_version_str, user_id)

    # 8. Create checkout session with idempotency key (saga step 2)
    import time as _time

    idempotency_key = f"checkout-{user_id}-{price_id}-{int(_time.time() // 60)}"
    try:
        checkout_url = create_checkout_session(
            customer_id=customer_id,
            plan_price_id=price_id,
            user_id=user_id,
            trial_period_days=trial_days,
            stripe_coupon_id=stripe_coupon_id,
            seat_price_id=seat_price_id,
            additional_seats=additional_seats,
            dpa_accepted_at=dpa_accepted_at_str,
            dpa_version=dpa_version_str,
            idempotency_key=idempotency_key,
        )
    except Exception:
        db.rollback()
        # Saga compensation: clean up the Stripe customer we just created
        if created_new_customer:
            _rollback_stripe_customer(customer_id, user_id)
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    # 9. Atomic DB commit: customer_id + DPA persisted together
    try:
        db.commit()
    except Exception:
        db.rollback()
        # Stripe resources (customer + checkout session) already exist.
        # Do NOT auto-delete in production — the checkout session may still be
        # completed by the user. Log for manual reconciliation instead.
        logger.critical(
            "MANUAL RECONCILIATION REQUIRED: DB commit failed after Stripe "
            "resources were created. stripe_customer_id=%s, user_id=%d, "
            "tier=%s. Verify in Stripe dashboard whether the customer "
            "completed checkout; clean up if not.",
            customer_id,
            user_id,
            tier,
        )
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    return checkout_url
