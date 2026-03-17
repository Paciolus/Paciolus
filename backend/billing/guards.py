"""
Billing guards — reusable dependency-injectable policy functions.

Provides the stripe_endpoint_guard context manager that wraps common Stripe
API call patterns with availability checks and standardized error handling.
Extracted from routes/billing.py during the bounded-domain split (Refactor 4).
"""

import logging
from collections.abc import Generator
from contextlib import contextmanager

from fastapi import HTTPException

logger = logging.getLogger(__name__)


@contextmanager
def stripe_endpoint_guard(user_id: int, operation: str) -> Generator[None, None, None]:
    """Context manager that wraps the common Stripe endpoint pattern:

    1. Check is_stripe_enabled() -> 503 if not
    2. Yield for the provider call
    3. Catch Exception -> log + raise 502
    """
    from billing.stripe_client import is_stripe_enabled

    if not is_stripe_enabled():
        raise HTTPException(status_code=503, detail="Billing is not available.")

    try:
        yield
    except Exception as e:
        logger.error("Stripe %s failed for user %d: %s", operation, user_id, type(e).__name__)
        raise HTTPException(
            status_code=502,
            detail="Payment provider error. Please try again or contact support.",
        )
