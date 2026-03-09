"""
Checkout orchestration — Sprint 519 Phase 5

Extracts checkout business logic from the billing route layer.
The route keeps HTTP concerns (request parsing, error→HTTPException mapping).
"""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


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

    # 3. Get or create Stripe customer
    existing_sub = get_subscription(db, user_id)
    stripe_customer_id = existing_sub.stripe_customer_id if existing_sub else None

    try:
        customer_id = create_or_get_stripe_customer(user_id, user_email, stripe_customer_id)
    except Exception:
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    # Save customer ID if new
    if existing_sub and not existing_sub.stripe_customer_id:
        existing_sub.stripe_customer_id = customer_id
        db.commit()

    # 4. Validate and resolve promo code
    stripe_coupon_id: str | None = None
    if promo_code:
        promo_error = validate_promo_for_interval(promo_code, interval)
        if promo_error:
            raise CheckoutValidationError(promo_error)
        stripe_coupon_id = get_stripe_coupon_id(promo_code)
        if not stripe_coupon_id:
            raise CheckoutValidationError("Promo code is not currently available. Please contact support.")

    # 5. Trial eligibility
    trial_days = 0
    is_new_subscription = existing_sub is None or existing_sub.status.value == "canceled"
    if is_new_subscription and tier in TRIAL_ELIGIBLE_TIERS:
        trial_days = TRIAL_PERIOD_DAYS

    # 6. Seat validation
    if seat_count > 0 and tier == "solo":
        raise CheckoutValidationError("Solo plan does not support additional seats.")

    entitlements = get_entitlements(UserTier(tier))
    seats_included = entitlements.seats_included
    total_seats = seats_included + seat_count
    max_seats = get_max_self_serve_seats(tier)
    if total_seats > max_seats:
        raise CheckoutValidationError(f"Maximum {max_seats} seats via self-serve. Contact sales for more.")

    additional_seats = seat_count
    seat_price_id: str | None = None
    if additional_seats > 0:
        seat_price_id = get_stripe_seat_price_id(interval, tier)
        if not seat_price_id:
            raise CheckoutValidationError("Seat pricing not configured. Contact support.")

    # 7. DPA acceptance
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
            db.commit()
            logger.info("DPA v%s accepted by user %d (existing sub)", dpa_version_str, user_id)

    # 8. Create checkout session
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
        )
    except Exception:
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    return checkout_url
