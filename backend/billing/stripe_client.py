"""
Stripe client singleton — Sprint 364.

Lazy-initializes the Stripe SDK and guards on STRIPE_ENABLED.
All billing modules should call get_stripe() instead of importing stripe directly.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

_stripe_module: Any | None = None


def get_stripe() -> Any:
    """Return the configured stripe module, or raise if Stripe is disabled.

    Lazy import avoids requiring the stripe package when billing is off.
    """
    global _stripe_module

    from config import STRIPE_ENABLED, STRIPE_SECRET_KEY

    if not STRIPE_ENABLED:
        raise RuntimeError("Stripe is not configured. Set STRIPE_SECRET_KEY in .env to enable billing.")

    if _stripe_module is None:
        import stripe

        stripe.api_key = STRIPE_SECRET_KEY
        _stripe_module = stripe
        logger.info("Stripe SDK initialized")

    return _stripe_module


def is_stripe_enabled() -> bool:
    """Check if Stripe is configured without raising."""
    from config import STRIPE_ENABLED

    return STRIPE_ENABLED


def to_plain_dict(obj: Any) -> dict[str, Any]:
    """Return a Stripe response as a plain, recursively-converted ``dict``.

    Since stripe-python 15 (#1762), ``StripeObject`` no longer inherits from
    ``dict``: ``.get()`` raises ``AttributeError`` and ``.items()`` is not the
    dict method. All billing code reads Stripe payloads with the ``.get(...)``
    chain, so every object coming back from the SDK (``Webhook.construct_event``,
    ``Subscription.retrieve``) is converted here, once, at the boundary.

    A value that is already a ``dict`` (test doubles, pre-parsed payloads)
    passes through unchanged.
    """
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        result = to_dict()
        if isinstance(result, dict):
            return result
    raise TypeError(f"Expected a Stripe object or dict, got {type(obj).__name__}")
