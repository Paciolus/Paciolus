"""
Price configuration for A/B testing — Sprint 364.

Maps (tier, variant, interval) → price in cents.
STRIPE_PRICE_IDS maps to actual Stripe Price objects (set after creating products).
"""

from enum import Enum as PyEnum


class PriceVariant(str, PyEnum):
    """A/B price experiment variant."""
    CONTROL = "control"
    EXPERIMENT = "experiment"


# Price table: {tier: {variant: {interval: price_cents}}}
# Annual prices embed ~17% discount vs 12x monthly.
PRICE_TABLE: dict[str, dict[str, dict[str, int]]] = {
    "free": {
        "control": {"monthly": 0, "annual": 0},
        "experiment": {"monthly": 0, "annual": 0},
    },
    "starter": {
        "control": {"monthly": 4900, "annual": 49900},       # $49/mo, $499/yr
        "experiment": {"monthly": 5900, "annual": 59900},     # $59/mo, $599/yr
    },
    "professional": {
        "control": {"monthly": 12900, "annual": 130900},     # $129/mo, $1,309/yr
        "experiment": {"monthly": 14900, "annual": 151900},   # $149/mo, $1,519/yr
    },
    "team": {
        "control": {"monthly": 39900, "annual": 399900},     # $399/mo, $3,999/yr
        "experiment": {"monthly": 44900, "annual": 449900},   # $449/mo, $4,499/yr
    },
    "enterprise": {
        "control": {"monthly": 0, "annual": 0},   # Custom pricing
        "experiment": {"monthly": 0, "annual": 0},
    },
}

# Stripe Price IDs — populate after creating products in Stripe Dashboard.
# Format: {tier: {interval: stripe_price_id}}
# These should be loaded from env vars in production.
STRIPE_PRICE_IDS: dict[str, dict[str, str]] = {
    # Example:
    # "starter": {
    #     "monthly": "price_1234567890abcdef",
    #     "annual": "price_abcdef1234567890",
    # },
}


def get_price_cents(tier: str, variant: str = "control", interval: str = "monthly") -> int:
    """Get the price in cents for a given tier, variant, and interval."""
    tier_prices = PRICE_TABLE.get(tier, {})
    variant_prices = tier_prices.get(variant, tier_prices.get("control", {}))
    return variant_prices.get(interval, 0)


def get_annual_savings_percent(tier: str, variant: str = "control") -> int:
    """Calculate annual savings percentage vs 12x monthly."""
    monthly = get_price_cents(tier, variant, "monthly")
    annual = get_price_cents(tier, variant, "annual")
    if monthly == 0:
        return 0
    annual_at_monthly = monthly * 12
    if annual_at_monthly == 0:
        return 0
    savings = ((annual_at_monthly - annual) / annual_at_monthly) * 100
    return round(savings)


def get_stripe_price_id(tier: str, interval: str) -> str | None:
    """Get the Stripe Price ID for a tier and interval. Returns None if not configured."""
    return STRIPE_PRICE_IDS.get(tier, {}).get(interval)
