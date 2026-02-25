"""
Price configuration — Phase LIX + Billing Launch.

Sprint A: Flat price table (A/B variant system retired).
Sprint B: Tiered add-on seat pricing.
Sprint C: Trial period + promotional coupon configuration.
Billing Launch: Env-var loading for base plan Stripe Price IDs + startup validation.

Maps (tier, interval) → price in cents.
Stripe Price IDs loaded from env vars at runtime (lazy-loaded to avoid circular imports).
"""

# Price table: {tier: {interval: price_cents}}
# Annual prices embed ~17% discount vs 12x monthly.
PRICE_TABLE: dict[str, dict[str, int]] = {
    "free": {"monthly": 0, "annual": 0},
    "solo": {"monthly": 5000, "annual": 50000},  # Solo: $50/mo, $500/yr
    "team": {"monthly": 13000, "annual": 130000},  # Team: $130/mo, $1,300/yr
    "enterprise": {"monthly": 40000, "annual": 400000},  # Organization: $400/mo, $4,000/yr
}

# Stripe Price IDs — loaded from env vars at runtime.
# Env var pattern: STRIPE_PRICE_{TIER}_MONTHLY, STRIPE_PRICE_{TIER}_ANNUAL
# Tiers: SOLO, TEAM, ENTERPRISE (free tier has no Stripe Price).
_PAID_TIERS = ("solo", "team", "enterprise")


def _load_stripe_price_ids() -> dict[str, dict[str, str]]:
    """Lazy-load base plan Stripe Price IDs from env vars."""
    from config import _load_optional

    result: dict[str, dict[str, str]] = {}
    for tier in _PAID_TIERS:
        monthly = _load_optional(f"STRIPE_PRICE_{tier.upper()}_MONTHLY", "")
        annual = _load_optional(f"STRIPE_PRICE_{tier.upper()}_ANNUAL", "")
        if monthly or annual:
            result[tier] = {}
            if monthly:
                result[tier]["monthly"] = monthly
            if annual:
                result[tier]["annual"] = annual
    return result


# ---------------------------------------------------------------------------
# Add-on seat pricing (Phase LIX Sprint B)
# ---------------------------------------------------------------------------
# Tiered per-seat pricing for Team and Organization plans.
# Seats 1–3 (base) are included in the plan price.
# Seats 4+ are billed as add-ons at tiered rates.

SEAT_PRICE_TIERS: list[tuple[int, int, dict[str, int]]] = [
    # (min_seat, max_seat, {interval: price_cents_per_seat})
    (4, 10, {"monthly": 8000, "annual": 80000}),  # $80/mo, $800/yr per seat
    (11, 25, {"monthly": 7000, "annual": 70000}),  # $70/mo, $700/yr per seat
    # 26+ = contact sales (not purchasable via self-serve)
]

# Maximum self-serve seats before requiring sales contact
MAX_SELF_SERVE_SEATS = 25


def get_seat_price_cents(seat_number: int, interval: str = "monthly") -> int | None:
    """Get the per-seat price in cents for a given seat position.

    Seats 1-3 are included in the base plan (returns 0).
    Seats 4-25 are tiered add-ons (returns per-seat price).
    Seats 26+ require sales contact (returns None).
    """
    if seat_number <= 3:
        return 0  # Included in base plan
    for min_seat, max_seat, prices in SEAT_PRICE_TIERS:
        if min_seat <= seat_number <= max_seat:
            return prices.get(interval, 0)
    return None  # Beyond self-serve — contact sales


def calculate_additional_seats_cost(additional_seats: int, interval: str = "monthly") -> int | None:
    """Calculate total cost for a number of additional seats (above the base 3).

    Returns total cost in cents, or None if any seat exceeds self-serve limit.
    Each seat is priced at its tier rate (not blended).
    """
    if additional_seats <= 0:
        return 0
    total = 0
    for i in range(additional_seats):
        seat_number = 4 + i  # First add-on seat is seat #4
        price = get_seat_price_cents(seat_number, interval)
        if price is None:
            return None  # Exceeds self-serve limit
        total += price
    return total


# ---------------------------------------------------------------------------
# Trial period (Phase LIX Sprint C)
# ---------------------------------------------------------------------------
# All paid plans include a 7-day free trial for new subscriptions.
TRIAL_PERIOD_DAYS = 7

# Tiers eligible for trial (not free — already free)
TRIAL_ELIGIBLE_TIERS: frozenset[str] = frozenset({"solo", "team", "enterprise"})


# ---------------------------------------------------------------------------
# Promotional coupons (Phase LIX Sprint C)
# ---------------------------------------------------------------------------
# Stripe Coupon IDs loaded from config. Created in Stripe Dashboard:
#   MONTHLY_20_3MO: 20% off for first 3 months (duration=repeating, months=3)
#   ANNUAL_10_1YR: 10% off first annual invoice (duration=once)
# Best single discount only — no stacking.


def _load_coupon_ids() -> dict[str, str]:
    """Lazy-load Stripe Coupon IDs from config to avoid circular import."""
    from config import _load_optional

    return {
        "monthly": _load_optional("STRIPE_COUPON_MONTHLY_20", ""),
        "annual": _load_optional("STRIPE_COUPON_ANNUAL_10", ""),
    }


# Promo code labels to interval mapping (user-facing promo code → interval)
PROMO_CODES: dict[str, str] = {
    "MONTHLY20": "monthly",  # 20% off first 3 months
    "ANNUAL10": "annual",  # 10% off first annual invoice
}


def get_stripe_coupon_id(promo_code: str) -> str | None:
    """Resolve a user-facing promo code to a Stripe Coupon ID.

    Returns None if the promo code is unknown or the coupon ID isn't configured.
    """
    interval = PROMO_CODES.get(promo_code.upper())
    if interval is None:
        return None
    coupon_ids = _load_coupon_ids()
    coupon_id = coupon_ids.get(interval, "")
    return coupon_id if coupon_id else None


def validate_promo_for_interval(promo_code: str, interval: str) -> str | None:
    """Validate that a promo code is compatible with the billing interval.

    Returns an error message if invalid, None if valid.
    Monthly promos only apply to monthly plans, annual promos to annual plans.
    """
    target_interval = PROMO_CODES.get(promo_code.upper())
    if target_interval is None:
        return f"Unknown promo code: {promo_code}"
    if target_interval != interval:
        return f"Promo code '{promo_code}' is only valid for {target_interval} plans"
    return None


# ---------------------------------------------------------------------------
# Base plan pricing helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Stripe Seat Add-On Price IDs (Self-Serve Checkout)
# ---------------------------------------------------------------------------
# Graduated seat pricing is configured in Stripe Dashboard.
# These Price IDs use "graduated" billing mode in Stripe:
#   seats 1-7 @ $80/mo, seats 8-22 @ $70/mo.
# Set via env vars: STRIPE_SEAT_PRICE_MONTHLY, STRIPE_SEAT_PRICE_ANNUAL.


def _load_seat_price_ids() -> dict[str, str]:
    """Lazy-load seat add-on Stripe Price IDs from env vars."""
    from config import _load_optional

    return {
        "monthly": _load_optional("STRIPE_SEAT_PRICE_MONTHLY", ""),
        "annual": _load_optional("STRIPE_SEAT_PRICE_ANNUAL", ""),
    }


def get_stripe_seat_price_id(interval: str) -> str | None:
    """Get the Stripe Price ID for the seat add-on at the given billing interval.

    Returns None if the seat price is not configured.
    """
    ids = _load_seat_price_ids()
    pid = ids.get(interval, "")
    return pid if pid else None


def get_all_seat_price_ids() -> set[str]:
    """Return the set of all configured seat add-on Stripe Price IDs.

    Used by the webhook handler to distinguish seat items from base plan items.
    """
    ids = _load_seat_price_ids()
    return {v for v in ids.values() if v}


# ---------------------------------------------------------------------------
# Base plan pricing helpers
# ---------------------------------------------------------------------------


def get_price_cents(tier: str, interval: str = "monthly") -> int:
    """Get the price in cents for a given tier and interval."""
    return PRICE_TABLE.get(tier, {}).get(interval, 0)


def get_annual_savings_percent(tier: str) -> int:
    """Calculate annual savings percentage vs 12x monthly."""
    monthly = get_price_cents(tier, "monthly")
    annual = get_price_cents(tier, "annual")
    if monthly == 0:
        return 0
    annual_at_monthly = monthly * 12
    if annual_at_monthly == 0:
        return 0
    savings = ((annual_at_monthly - annual) / annual_at_monthly) * 100
    return round(savings)


def get_stripe_price_id(tier: str, interval: str) -> str | None:
    """Get the Stripe Price ID for a tier and interval. Returns None if not configured."""
    ids = _load_stripe_price_ids()
    return ids.get(tier, {}).get(interval)


def get_all_base_price_ids() -> set[str]:
    """Return the set of all configured base plan Stripe Price IDs.

    Used by the webhook handler to distinguish base plan items from seat add-ons.
    """
    ids = _load_stripe_price_ids()
    return {v for tier_ids in ids.values() for v in tier_ids.values() if v}


# ---------------------------------------------------------------------------
# Startup billing config validation
# ---------------------------------------------------------------------------


def validate_billing_config() -> list[str]:
    """Validate billing configuration at startup.

    Returns a list of issue messages (empty = all good).
    In production (ENV_MODE=production), missing critical config causes sys.exit(1).
    In development, issues are returned as warnings only.
    """
    import logging
    import sys

    from config import ENV_MODE, STRIPE_WEBHOOK_SECRET

    logger = logging.getLogger(__name__)
    issues: list[str] = []
    price_ids = _load_stripe_price_ids()

    # Critical: all 6 base price IDs must be set
    for tier in _PAID_TIERS:
        for interval in ("monthly", "annual"):
            env_var = f"STRIPE_PRICE_{tier.upper()}_{interval.upper()}"
            if not price_ids.get(tier, {}).get(interval):
                issues.append(f"Missing {env_var} — {tier}/{interval} checkout will fail")

    # Critical: webhook secret must be set
    if not STRIPE_WEBHOOK_SECRET:
        issues.append("Missing STRIPE_WEBHOOK_SECRET — webhook signature verification will fail")

    # Warning: seat price IDs (non-critical — seats are V2 only)
    seat_ids = _load_seat_price_ids()
    if not seat_ids.get("monthly") or not seat_ids.get("annual"):
        logger.warning("Billing config: seat price IDs incomplete — seat add-ons won't work")

    # Warning: coupon IDs (non-critical — promos are optional)
    coupon_ids = _load_coupon_ids()
    if not coupon_ids.get("monthly") or not coupon_ids.get("annual"):
        logger.warning("Billing config: coupon IDs incomplete — promo codes won't work")

    # Production hard fail on critical issues
    if issues and ENV_MODE == "production":
        for issue in issues:
            logger.error("CRITICAL billing config: %s", issue)
        logger.error(
            "Billing is enabled (STRIPE_SECRET_KEY set) but critical config is missing. "
            "Set all required env vars or disable billing by unsetting STRIPE_SECRET_KEY."
        )
        sys.exit(1)

    return issues
