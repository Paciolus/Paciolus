"""
Stripe checkout session creation — Sprint 365 + Phase LIX Sprint C.

Creates Stripe Checkout Sessions for new subscriptions.
Sprint C adds: 7-day trial period + promotional coupon support.
"""

import logging

from billing.stripe_client import get_stripe

logger = logging.getLogger(__name__)


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
    return customer.id


def create_checkout_session(
    customer_id: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
    user_id: int,
    trial_period_days: int = 0,
    stripe_coupon_id: str | None = None,
    seat_quantity: int = 1,
) -> str:
    """Create a Stripe Checkout Session and return the URL.

    Args:
        customer_id: Stripe Customer ID
        price_id: Stripe Price ID for the plan
        success_url: URL to redirect on successful payment
        cancel_url: URL to redirect on cancellation
        user_id: Internal user ID for metadata
        trial_period_days: Free trial period (0 = no trial). Phase LIX Sprint C.
        stripe_coupon_id: Stripe Coupon ID for promotional discount. Phase LIX Sprint C.
        seat_quantity: Number of seats for subscription item. Phase LIX Sprint E.

    Returns:
        Checkout session URL for client redirect.
    """
    stripe = get_stripe()

    subscription_data: dict = {
        "metadata": {"paciolus_user_id": str(user_id)},
    }

    # Add trial period for new subscriptions (Phase LIX Sprint C)
    if trial_period_days > 0:
        subscription_data["trial_period_days"] = trial_period_days

    quantity = max(1, seat_quantity)

    session_params: dict = {
        "customer": customer_id,
        "payment_method_types": ["card"],
        "line_items": [{"price": price_id, "quantity": quantity}],
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {"paciolus_user_id": str(user_id)},
        "subscription_data": subscription_data,
    }

    # Apply promotional coupon (Phase LIX Sprint C)
    # Stripe allows only one coupon per checkout — no stacking by design.
    if stripe_coupon_id:
        session_params["discounts"] = [{"coupon": stripe_coupon_id}]

    session = stripe.checkout.Session.create(**session_params)
    logger.info(
        "Created checkout session %s for user %d (trial=%d, coupon=%s, seats=%d)",
        session.id,
        user_id,
        trial_period_days,
        stripe_coupon_id or "none",
        quantity,
    )
    return session.url
