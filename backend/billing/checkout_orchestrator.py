"""
Checkout orchestration — Sprint 519 Phase 5

Extracts checkout business logic from the billing route layer.
The route keeps HTTP concerns (request parsing, error→HTTPException mapping).

Saga pattern: Each Stripe step has a compensating action.
- Customer creation → delete customer on later failure
- Checkout session creation → no compensation needed (sessions expire automatically)
- DB commit failure → log Stripe resource IDs for manual reconciliation

Sprint 881 (AZ-09): a new-subscription checkout is admitted only when the
account has no subscription Stripe may still bill (``billing.purchase_admission``);
plan and interval changes update the existing subscription (``change_plan``).
Input validation now runs before any Stripe call, so a refused request never
creates a customer.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from subscription_model import Subscription

logger = logging.getLogger(__name__)

ALREADY_SUBSCRIBED_MESSAGE = (
    "This account already has a subscription. Change your plan or billing interval from Billing settings "
    "instead of starting a new checkout."
)
PURCHASE_IN_PROGRESS_MESSAGE = (
    "A checkout for this account has just been paid and is being set up. Refresh in a minute before trying again."
)
CHECKOUT_BEING_OPENED_MESSAGE = "A checkout for this account is already being opened. Try again in a moment."


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


class CheckoutTierNotSelfServeError(Exception):
    """Raised when the tier is sold by arrangement only (→ 403). Sprint 858."""

    pass


class CheckoutConflictError(Exception):
    """Raised when the account already has, or is completing, a subscription (→ 409). Sprint 881."""

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
    """Validate inputs, admit the purchase, create the checkout session.

    Returns the checkout URL string.
    Raises CheckoutValidationError, CheckoutProviderError, CheckoutUnavailableError,
    CheckoutTierNotSelfServeError or CheckoutConflictError.
    """
    from billing import purchase_admission as admission
    from billing.checkout import create_or_get_stripe_customer, open_checkout_session
    from billing.price_config import (
        SALES_ONLY_MESSAGE,
        TRIAL_ELIGIBLE_TIERS,
        TRIAL_PERIOD_DAYS,
        get_max_self_serve_seats,
        get_stripe_coupon_id,
        get_stripe_price_id,
        get_stripe_seat_price_id,
        is_self_serve_purchasable,
        validate_promo_for_interval,
    )
    from billing.stripe_client import is_stripe_enabled
    from billing.subscription_manager import get_subscription
    from models import UserTier
    from shared.entitlements import get_entitlements
    from subscription_model import CheckoutAttemptStatus

    # 0. Sprint 858: Professional/Enterprise are sales-only until Sprint 853.
    #    Checked before any Stripe call, so no customer is created for a refused tier.
    if not is_self_serve_purchasable(tier):
        raise CheckoutTierNotSelfServeError(SALES_ONLY_MESSAGE)

    # 1. Check billing enabled
    if not is_stripe_enabled():
        raise CheckoutUnavailableError("Billing is not currently available. Please contact sales.")

    # 2. Resolve price
    price_id = get_stripe_price_id(tier, interval)
    if not price_id:
        raise CheckoutValidationError(f"No price configured for {tier}/{interval}. Please contact support.")

    # 3. Seat validation (no Stripe call yet)
    if seat_count > 0 and tier == "solo":
        raise CheckoutValidationError("Solo plan does not support additional seats.")

    entitlements = get_entitlements(UserTier(tier))
    total_seats = entitlements.seats_included + seat_count
    max_seats = get_max_self_serve_seats(tier)
    if total_seats > max_seats:
        raise CheckoutValidationError(f"Maximum {max_seats} seats via self-serve. Contact sales for more.")

    additional_seats = seat_count
    seat_price_id: str | None = None
    if additional_seats > 0:
        seat_price_id = get_stripe_seat_price_id(interval, tier)
        if not seat_price_id:
            raise CheckoutValidationError("Seat pricing not configured. Contact support.")

    # 4. Validate and resolve promo code (no Stripe call yet)
    stripe_coupon_id: str | None = None
    if promo_code:
        promo_error = validate_promo_for_interval(promo_code, interval)
        if promo_error:
            raise CheckoutValidationError(promo_error)
        stripe_coupon_id = get_stripe_coupon_id(promo_code)
        if not stripe_coupon_id:
            raise CheckoutValidationError("Promo code is not currently available. Please contact support.")
        # Sprint 881 (AZ-16): each code works once per account.
        if admission.promo_already_redeemed(db, user_id, promo_code):
            raise CheckoutValidationError(f"Promo code '{promo_code.upper()}' has already been used on this account.")

    # 5. Purchase admission (Sprint 881, AZ-09): serialized on the user row; refuse a
    #    second subscription; expire any earlier checkout still payable.
    purchaser = admission.lock_purchaser(db, user_id)
    existing_sub = get_subscription(db, user_id)
    customer_ids = admission.known_customer_ids(db, user_id, existing_sub)
    try:
        admission.refuse_if_subscribed(existing_sub, customer_ids)
        admission.refuse_if_checkout_being_opened(db, user_id)
        admission.close_open_checkouts(db, user_id, customer_ids)
    except admission.CheckoutBeingOpenedError as exc:
        db.rollback()
        logger.info("Checkout refused for user %d: attempt %s is still opening", user_id, exc)
        raise CheckoutConflictError(CHECKOUT_BEING_OPENED_MESSAGE)
    except admission.AlreadySubscribedError as exc:
        db.rollback()
        logger.info("Checkout refused for user %d: %s", user_id, exc)
        raise CheckoutConflictError(ALREADY_SUBSCRIBED_MESSAGE)
    except admission.PurchaseInProgressError as exc:
        db.rollback()
        logger.warning("Checkout refused for user %d: session %s already completed", user_id, exc)
        raise CheckoutConflictError(PURCHASE_IN_PROGRESS_MESSAGE)
    except Exception:
        db.rollback()
        logger.exception("Checkout admission failed for user %d", user_id)
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    # 6. Get or create the Stripe customer (saga step 1) — one per account, reused
    stripe_customer_id = customer_ids[0] if customer_ids else None
    created_new_customer = False
    try:
        customer_id = create_or_get_stripe_customer(user_id, user_email, stripe_customer_id)
        created_new_customer = customer_id != stripe_customer_id
    except Exception:
        db.rollback()
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    if existing_sub and not existing_sub.stripe_customer_id:
        existing_sub.stripe_customer_id = customer_id

    # 7. Trial eligibility — one introductory trial per account (Sprint 881, AZ-16). Stored
    #    on the account when Stripe confirms a trialing subscription, so cancelling and
    #    buying again does not restart it.
    trial_days = 0
    if tier in TRIAL_ELIGIBLE_TIERS and purchaser.trial_used_at is None:
        trial_days = TRIAL_PERIOD_DAYS

    # 8. DPA acceptance (committed with the attempt row)
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

    # 9. Durable checkout identity: committed before Stripe is called (releases the lock)
    try:
        attempt = admission.begin_attempt(
            db,
            user_id,
            tier,
            interval,
            customer_id,
            trial_offered=trial_days > 0,
            promo_code=promo_code.upper() if promo_code else None,
        )
    except Exception:
        db.rollback()
        if created_new_customer:
            _rollback_stripe_customer(customer_id, user_id)
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    # 10. Create checkout session, keyed by the attempt (saga step 2)
    try:
        session = open_checkout_session(
            customer_id=customer_id,
            plan_price_id=price_id,
            user_id=user_id,
            trial_period_days=trial_days,
            stripe_coupon_id=stripe_coupon_id,
            seat_price_id=seat_price_id,
            additional_seats=additional_seats,
            dpa_accepted_at=dpa_accepted_at_str,
            dpa_version=dpa_version_str,
            idempotency_key=f"checkout-attempt-{attempt.id}",
            checkout_attempt_id=attempt.id,
            expires_at=admission.session_expiry_epoch(attempt),
            promo_code=promo_code,
        )
    except Exception:
        db.rollback()
        attempt.status = CheckoutAttemptStatus.FAILED.value
        if created_new_customer:
            _rollback_stripe_customer(customer_id, user_id)
            attempt.stripe_customer_id = None
        try:
            db.commit()
        except Exception:
            db.rollback()
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    # 11. Record the session on the attempt
    attempt.stripe_checkout_session_id = session.session_id
    attempt.status = CheckoutAttemptStatus.OPEN.value
    try:
        db.commit()
    except Exception:
        db.rollback()
        # The session exists and the attempt row (with its customer) is already
        # committed, so the next checkout still finds and expires it.
        logger.critical(
            "MANUAL RECONCILIATION REQUIRED: DB commit failed after Stripe "
            "resources were created. stripe_customer_id=%s, user_id=%d, "
            "tier=%s, checkout_attempt=%d. Verify in Stripe dashboard whether the customer "
            "completed checkout; clean up if not.",
            customer_id,
            user_id,
            tier,
            attempt.id,
        )
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    return session.url


def change_plan(db: Session, user_id: int, tier: str, interval: str) -> Subscription:
    """Move an existing subscription to another plan or interval (Sprint 881, AZ-09).

    Updates the existing Stripe subscription — the price change takes effect now
    and Stripe prorates it on the next invoice (CEO 2026-11-18). Never opens a
    Checkout Session, so it cannot create a second subscription.
    """
    from billing import purchase_admission as admission
    from billing.price_config import (
        SALES_ONLY_MESSAGE,
        get_max_self_serve_seats,
        get_stripe_price_id,
        get_stripe_seat_price_id,
        is_self_serve_purchasable,
    )
    from billing.stripe_client import get_stripe, is_stripe_enabled, to_plain_dict
    from billing.subscription_manager import (
        _find_base_item,
        _find_seat_addon_item,
        get_subscription,
        included_seats_for_tier,
        sync_subscription_from_stripe,
    )
    from subscription_model import SubscriptionStatus

    if not is_self_serve_purchasable(tier):
        raise CheckoutTierNotSelfServeError(SALES_ONLY_MESSAGE)
    if not is_stripe_enabled():
        raise CheckoutUnavailableError("Billing is not currently available. Please contact sales.")
    price_id = get_stripe_price_id(tier, interval)
    if not price_id:
        raise CheckoutValidationError(f"No price configured for {tier}/{interval}. Please contact support.")

    admission.lock_purchaser(db, user_id)
    sub = get_subscription(db, user_id)
    if (
        sub is None
        or not sub.stripe_subscription_id
        or sub.status not in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)
    ):
        db.rollback()
        raise CheckoutValidationError(
            "There is no active subscription to change. Update your payment method in Billing settings first, "
            "or start a new subscription if the previous one has ended."
        )
    current_interval = sub.billing_interval.value if sub.billing_interval else "monthly"
    if sub.tier == tier and current_interval == interval:
        db.rollback()
        raise CheckoutValidationError("Your subscription is already on this plan and billing interval.")

    stripe = get_stripe()
    try:
        stripe_sub = to_plain_dict(stripe.Subscription.retrieve(sub.stripe_subscription_id))
    except Exception:
        db.rollback()
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    items = stripe_sub.get("items", {}).get("data", [])
    base_item = _find_base_item(items)
    if base_item is None:
        db.rollback()
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")
    changes: list[dict] = [{"id": base_item.get("id"), "price": price_id}]

    seat_item = _find_seat_addon_item(items)
    if seat_item is not None:
        if tier not in ("professional", "enterprise"):
            db.rollback()
            raise CheckoutValidationError("Remove your add-on seats before moving to a plan without them.")
        new_seat_price = get_stripe_seat_price_id(interval, tier)
        if not new_seat_price:
            db.rollback()
            raise CheckoutValidationError("Seat pricing not configured. Contact support.")
        max_seats = get_max_self_serve_seats(tier)
        if included_seats_for_tier(tier) + int(seat_item.get("quantity", 0)) > max_seats:
            db.rollback()
            raise CheckoutValidationError(f"Maximum {max_seats} seats via self-serve. Contact sales for more.")
        changes.append({"id": seat_item.get("id"), "price": new_seat_price})

    try:
        updated = to_plain_dict(
            stripe.Subscription.modify(
                sub.stripe_subscription_id,
                items=changes,
                proration_behavior="create_prorations",
            )
        )
    except Exception:
        db.rollback()
        logger.exception("Plan change failed in Stripe for user %d", user_id)
        raise CheckoutProviderError("Payment provider error. Please try again or contact support.")

    synced = sync_subscription_from_stripe(db, user_id, updated, sub.stripe_customer_id or "", tier)
    db.commit()
    logger.info("Plan changed for user %d to %s/%s (prorated)", user_id, tier, interval)
    return synced
