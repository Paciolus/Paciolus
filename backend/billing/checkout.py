"""
Stripe checkout session creation — Sprint 365.

Creates Stripe Checkout Sessions for new subscriptions.
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
) -> str:
    """Create a Stripe Checkout Session and return the URL.

    Args:
        customer_id: Stripe Customer ID
        price_id: Stripe Price ID for the plan
        success_url: URL to redirect on successful payment
        cancel_url: URL to redirect on cancellation
        user_id: Internal user ID for metadata

    Returns:
        Checkout session URL for client redirect.
    """
    stripe = get_stripe()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"paciolus_user_id": str(user_id)},
        subscription_data={
            "metadata": {"paciolus_user_id": str(user_id)},
        },
    )
    logger.info("Created checkout session %s for user %d", session.id, user_id)
    return session.url
