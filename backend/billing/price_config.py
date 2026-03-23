"""
Price configuration — Phase LXIX Pricing v3.

Maps (tier, interval) → price in cents.
Stripe Price IDs loaded from env vars at runtime (lazy-loaded to avoid circular imports).

Pricing v3:
- Solo: $100/mo, $1,000/yr
- Professional: $500/mo, $5,000/yr
- Enterprise: $1,000/mo, $10,000/yr

Seat pricing:
- Professional: $65/mo, $650/yr per additional seat (max 20 total)
- Enterprise: $45/mo, $450/yr per additional seat (max 100 total)
"""

# Price table: {tier: {interval: price_cents}}
# Annual prices embed ~17% discount vs 12x monthly.
PRICE_TABLE: dict[str, dict[str, int]] = {
    "free": {"monthly": 0, "annual": 0},
    "solo": {"monthly": 10000, "annual": 100000},  # $100/mo, $1,000/yr
    "professional": {"monthly": 50000, "annual": 500000},  # $500/mo, $5,000/yr
    "enterprise": {"monthly": 100000, "annual": 1000000},  # $1,000/mo, $10,000/yr
}

# Stripe Price IDs — loaded from env vars at runtime.
_PAID_TIERS = ("solo", "professional", "enterprise")


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
# Add-on seat pricing (Phase LXIX — per-tier flat pricing)
# ---------------------------------------------------------------------------

# Professional tier: $65/mo, $650/yr per additional seat
PROFESSIONAL_SEAT_PRICE: dict[str, int] = {"monthly": 6500, "annual": 65000}
MAX_SELF_SERVE_SEATS_PROFESSIONAL = 20

# Enterprise tier: $45/mo, $450/yr per additional seat
ENTERPRISE_SEAT_PRICE: dict[str, int] = {"monthly": 4500, "annual": 45000}
MAX_SELF_SERVE_SEATS_ENTERPRISE = 100


def get_max_self_serve_seats(tier: str) -> int:
    """Get the maximum self-serve seat count for a tier."""
    if tier == "enterprise":
        return MAX_SELF_SERVE_SEATS_ENTERPRISE
    if tier == "professional":
        return MAX_SELF_SERVE_SEATS_PROFESSIONAL
    return 1  # Solo and Free have no team features


def get_seat_price_cents(seat_number: int, interval: str = "monthly", tier: str = "professional") -> int | None:
    """Get the per-seat price in cents for a given seat position.

    Professional tier: Seats 1-7 included, seats 8-20 at $65/mo.
    Enterprise tier: Seats 1-20 included, seats 21-100 at $45/mo.
    """
    from models import UserTier
    from shared.entitlements import get_entitlements

    entitlements = get_entitlements(UserTier(tier))
    seats_included = entitlements.seats_included

    if seat_number <= seats_included:
        return 0  # Included in base plan

    max_seats = get_max_self_serve_seats(tier)
    if seat_number > max_seats:
        return None  # Beyond self-serve — contact sales

    if tier == "enterprise":
        return ENTERPRISE_SEAT_PRICE.get(interval, 0)

    if tier == "professional":
        return PROFESSIONAL_SEAT_PRICE.get(interval, 0)

    return None  # Solo/Free don't have seats


def calculate_additional_seats_cost(
    additional_seats: int, interval: str = "monthly", tier: str = "professional"
) -> int | None:
    """Calculate total cost for a number of additional seats (above included seats).

    Returns total cost in cents, or None if any seat exceeds self-serve limit.
    Each seat is priced at the flat tier rate.
    """
    if additional_seats <= 0:
        return 0

    from models import UserTier
    from shared.entitlements import get_entitlements

    entitlements = get_entitlements(UserTier(tier))
    seats_included = entitlements.seats_included

    total = 0
    for i in range(additional_seats):
        seat_number = seats_included + 1 + i
        price = get_seat_price_cents(seat_number, interval, tier)
        if price is None:
            return None  # Exceeds self-serve limit
        total += price
    return total


# ---------------------------------------------------------------------------
# Trial period
# ---------------------------------------------------------------------------
TRIAL_PERIOD_DAYS = 7

# Tiers eligible for trial (not free — already free)
TRIAL_ELIGIBLE_TIERS: frozenset[str] = frozenset({"solo", "professional", "enterprise"})


# ---------------------------------------------------------------------------
# Promotional coupons
# ---------------------------------------------------------------------------


def _load_coupon_ids() -> dict[str, str]:
    """Lazy-load Stripe Coupon IDs from config to avoid circular import."""
    from config import _load_optional

    return {
        "monthly": _load_optional("STRIPE_COUPON_MONTHLY_20", ""),
        "annual": _load_optional("STRIPE_COUPON_ANNUAL_10", ""),
    }


# Promo code labels to interval mapping (user-facing promo code → interval)
PROMO_CODES: dict[str, str] = {
    "MONTHLY20": "monthly",
    "ANNUAL10": "annual",
}


def get_stripe_coupon_id(promo_code: str) -> str | None:
    """Resolve a user-facing promo code to a Stripe Coupon ID."""
    interval = PROMO_CODES.get(promo_code.upper())
    if interval is None:
        return None
    coupon_ids = _load_coupon_ids()
    coupon_id = coupon_ids.get(interval, "")
    return coupon_id if coupon_id else None


def validate_promo_for_interval(promo_code: str, interval: str) -> str | None:
    """Validate that a promo code is compatible with the billing interval."""
    target_interval = PROMO_CODES.get(promo_code.upper())
    if target_interval is None:
        return f"Unknown promo code: {promo_code}"
    if target_interval != interval:
        return f"Promo code '{promo_code}' is only valid for {target_interval} plans"
    return None


# ---------------------------------------------------------------------------
# Stripe Seat Add-On Price IDs
# ---------------------------------------------------------------------------


def _load_pro_seat_price_ids() -> dict[str, str]:
    """Lazy-load Professional seat add-on Stripe Price IDs from env vars."""
    from config import _load_optional

    return {
        "monthly": _load_optional("STRIPE_SEAT_PRICE_PRO_MONTHLY", ""),
        "annual": _load_optional("STRIPE_SEAT_PRICE_PRO_ANNUAL", ""),
    }


def _load_ent_seat_price_ids() -> dict[str, str]:
    """Lazy-load Enterprise seat add-on Stripe Price IDs from env vars."""
    from config import _load_optional

    return {
        "monthly": _load_optional("STRIPE_SEAT_PRICE_ENT_MONTHLY", ""),
        "annual": _load_optional("STRIPE_SEAT_PRICE_ENT_ANNUAL", ""),
    }


def get_stripe_seat_price_id(interval: str, tier: str = "professional") -> str | None:
    """Get the Stripe Price ID for seat add-ons at the given tier and interval."""
    if tier == "enterprise":
        ids = _load_ent_seat_price_ids()
    else:
        ids = _load_pro_seat_price_ids()
    pid = ids.get(interval, "")
    return pid if pid else None


def get_all_seat_price_ids() -> set[str]:
    """Return the set of all configured seat add-on Stripe Price IDs."""
    pro_ids = _load_pro_seat_price_ids()
    ent_ids = _load_ent_seat_price_ids()
    return {v for v in [*pro_ids.values(), *ent_ids.values()] if v}


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
    """Return the set of all configured base plan Stripe Price IDs."""
    ids = _load_stripe_price_ids()
    return {v for tier_ids in ids.values() for v in tier_ids.values() if v}


# ---------------------------------------------------------------------------
# Startup billing config validation
# ---------------------------------------------------------------------------


def validate_billing_config() -> list[str]:
    """Validate billing configuration at startup."""
    import logging
    import sys

    from config import ENV_MODE, STRIPE_WEBHOOK_SECRET

    logger = logging.getLogger(__name__)
    issues: list[str] = []
    price_ids = _load_stripe_price_ids()

    for tier in _PAID_TIERS:
        for interval in ("monthly", "annual"):
            env_var = f"STRIPE_PRICE_{tier.upper()}_{interval.upper()}"
            if not price_ids.get(tier, {}).get(interval):
                issues.append(f"Missing {env_var} — {tier}/{interval} checkout will fail")

    if not STRIPE_WEBHOOK_SECRET:
        issues.append("Missing STRIPE_WEBHOOK_SECRET — webhook signature verification will fail")

    # Non-critical warnings: gate by environment to reduce dev noise
    _log = logger.warning if ENV_MODE == "production" else logger.debug

    pro_seat_ids = _load_pro_seat_price_ids()
    if not pro_seat_ids.get("monthly") or not pro_seat_ids.get("annual"):
        _log("Billing config: Professional seat price IDs incomplete — seat add-ons won't work")

    ent_seat_ids = _load_ent_seat_price_ids()
    if not ent_seat_ids.get("monthly") or not ent_seat_ids.get("annual"):
        _log("Billing config: Enterprise seat price IDs incomplete — seat add-ons won't work")

    coupon_ids = _load_coupon_ids()
    if not coupon_ids.get("monthly") or not coupon_ids.get("annual"):
        _log("Billing config: coupon IDs incomplete — promo codes won't work")

    if issues and ENV_MODE == "production":
        for issue in issues:
            logger.error("CRITICAL billing config: %s", issue)
        logger.error(
            "Billing is enabled (STRIPE_SECRET_KEY set) but critical config is missing. "
            "Set all required env vars or disable billing by unsetting STRIPE_SECRET_KEY."
        )
        sys.exit(1)

    return issues
