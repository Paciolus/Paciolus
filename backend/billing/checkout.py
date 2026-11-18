"""
Stripe checkout session creation — Sprint 365 + Phase LIX Sprint C + Self-Serve Checkout.

Creates Stripe Checkout Sessions for new subscriptions.
Sprint C adds: 7-day trial period + promotional coupon support.
Self-Serve Checkout: Base Plan + Seat Add-On dual line items.
Redirect URLs are always derived server-side from FRONTEND_URL — never user-supplied.
"""

import logging
from typing import NamedTuple

from billing.stripe_client import get_stripe

logger = logging.getLogger(__name__)


class CheckoutSessionRef(NamedTuple):
    """The Stripe Checkout Session just opened: its ID (kept on the attempt row) and URL."""

    session_id: str
    url: str


def create_or_get_stripe_customer(user_id: int, email: str, stripe_customer_id: str | None = None) -> str:
    """Get existing or create new Stripe Customer.

    Returns the Stripe Customer ID.
    """
    stripe = get_stripe()

    if stripe_customer_id:
        return stripe_customer_id

    customer = stripe.Customer.create(
        email=email,
        metadata={"paciolus_user_id": str(user_id)},
    )
    logger.info("Created Stripe customer %s for user %d", customer.id, user_id)
    return str(customer.id)


def create_checkout_session(
    customer_id: str,
    plan_price_id: str,
    user_id: int,
    trial_period_days: int = 0,
    stripe_coupon_id: str | None = None,
    seat_price_id: str | None = None,
    additional_seats: int = 0,
    dpa_accepted_at: str | None = None,
    dpa_version: str | None = None,
    idempotency_key: str | None = None,
) -> str:
    """Create a Stripe Checkout Session and return its URL (see ``open_checkout_session``)."""
    return open_checkout_session(
        customer_id=customer_id,
        plan_price_id=plan_price_id,
        user_id=user_id,
        trial_period_days=trial_period_days,
        stripe_coupon_id=stripe_coupon_id,
        seat_price_id=seat_price_id,
        additional_seats=additional_seats,
        dpa_accepted_at=dpa_accepted_at,
        dpa_version=dpa_version,
        idempotency_key=idempotency_key,
    ).url


def open_checkout_session(
    customer_id: str,
    plan_price_id: str,
    user_id: int,
    trial_period_days: int = 0,
    stripe_coupon_id: str | None = None,
    seat_price_id: str | None = None,
    additional_seats: int = 0,
    dpa_accepted_at: str | None = None,
    dpa_version: str | None = None,
    idempotency_key: str | None = None,
    checkout_attempt_id: int | None = None,
    expires_at: int | None = None,
) -> CheckoutSessionRef:
    """Create a Stripe Checkout Session and return its ID and URL.

    Redirect URLs are derived server-side from FRONTEND_URL — never user-supplied.

    Builds 1 or 2 line items:
      - Base plan price (qty=1) — always present.
      - Seat add-on price (qty=additional_seats) — only when seats > 0.

    Args:
        customer_id: Stripe Customer ID
        plan_price_id: Stripe Price ID for the base plan
        user_id: Internal user ID for metadata
        trial_period_days: Free trial period (0 = no trial). Phase LIX Sprint C.
        stripe_coupon_id: Stripe Coupon ID for promotional discount. Phase LIX Sprint C.
        seat_price_id: Stripe Price ID for the seat add-on (graduated pricing).
        additional_seats: Number of add-on seats beyond plan base.
        dpa_accepted_at: ISO timestamp of DPA acceptance (Sprint 459 — PI1.3 / C2.1).
        dpa_version: Version string of accepted DPA (e.g. "1.0").
        idempotency_key: Sent to Stripe so a retried create returns the same session.
        checkout_attempt_id: Sprint 881 — the ``checkout_attempts`` row this session belongs
            to; sent as ``client_reference_id`` and in both metadata blocks.
        expires_at: Sprint 881 — Unix time after which Stripe expires the session unpaid.

    Returns:
        The session's ID and its URL for client redirect.
    """
    from config import FRONTEND_URL

    if not FRONTEND_URL:
        raise ValueError("FRONTEND_URL must be configured")

    success_url = f"{FRONTEND_URL}/checkout/success"
    cancel_url = f"{FRONTEND_URL}/pricing"

    stripe = get_stripe()

    sub_metadata: dict = {
        "paciolus_user_id": str(user_id),
        "paciolus_additional_seats": str(additional_seats),
    }
    # Sprint 459: Carry DPA acceptance into subscription metadata for webhook pickup
    if dpa_accepted_at:
        sub_metadata["dpa_accepted_at"] = dpa_accepted_at
    if dpa_version:
        sub_metadata["dpa_version"] = dpa_version

    session_metadata: dict = {"paciolus_user_id": str(user_id)}
    if checkout_attempt_id is not None:
        sub_metadata["paciolus_checkout_attempt_id"] = str(checkout_attempt_id)
        session_metadata["paciolus_checkout_attempt_id"] = str(checkout_attempt_id)

    subscription_data: dict = {"metadata": sub_metadata}

    # Add trial period for new subscriptions (Phase LIX Sprint C)
    if trial_period_days > 0:
        subscription_data["trial_period_days"] = trial_period_days

    # Build line items: base plan (qty=1) + optional seat add-on
    line_items: list[dict] = [{"price": plan_price_id, "quantity": 1}]
    if seat_price_id and additional_seats > 0:
        line_items.append({"price": seat_price_id, "quantity": additional_seats})

    session_params: dict = {
        "customer": customer_id,
        # Sprint 786b: API 2026-09-30.endive (pinned by stripe 16) rejects
        # `payment_method_types` on Checkout Session create with a 400. The
        # replacement `allowed_payment_method_types` keeps the card-only intent
        # in code rather than handing it to the Dashboard's dynamic payment
        # method settings.
        "allowed_payment_method_types": ["card"],
        "line_items": line_items,
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": session_metadata,
        "subscription_data": subscription_data,
    }
    if checkout_attempt_id is not None:
        session_params["client_reference_id"] = str(checkout_attempt_id)
    if expires_at is not None:
        session_params["expires_at"] = expires_at

    # Apply promotional coupon (Phase LIX Sprint C)
    # Stripe allows only one coupon per checkout — no stacking by design.
    if stripe_coupon_id:
        session_params["discounts"] = [{"coupon": stripe_coupon_id}]

    # The idempotency key was accepted but never sent before Sprint 881.
    if idempotency_key:
        session = stripe.checkout.Session.create(**session_params, idempotency_key=idempotency_key)
    else:
        session = stripe.checkout.Session.create(**session_params)
    logger.info(
        "Created checkout session %s for user %d (trial=%d, coupon=%s, add_seats=%d)",
        session.id,
        user_id,
        trial_period_days,
        stripe_coupon_id or "none",
        additional_seats,
    )
    return CheckoutSessionRef(session_id=str(session.id), url=str(session.url))
