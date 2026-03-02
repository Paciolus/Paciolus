"""
Tier display-name mapping — Phase LXIX Pricing v3.

Maps internal tier IDs to public-facing plan names.
Internal IDs (free, solo, professional, enterprise) are used in DB/API.
This module provides the canonical presentation layer.
"""

from models import UserTier

# Internal tier ID → public display name
TIER_DISPLAY_NAMES: dict[UserTier, str] = {
    UserTier.FREE: "Free",
    UserTier.SOLO: "Solo",
    UserTier.PROFESSIONAL: "Professional",
    UserTier.ENTERPRISE: "Enterprise",
}

# Reverse mapping: display name → internal tier
_DISPLAY_TO_TIER: dict[str, UserTier] = {name: tier for tier, name in TIER_DISPLAY_NAMES.items()}

# Tiers available for new subscriptions (excludes free)
PURCHASABLE_TIERS: frozenset[str] = frozenset({"solo", "professional", "enterprise"})


def get_display_name(tier: UserTier) -> str:
    """Get the public-facing display name for a tier.

    Returns the tier's value (lowercase) if not found in the mapping.
    """
    return TIER_DISPLAY_NAMES.get(tier, tier.value)


def get_internal_id(display_name: str) -> str | None:
    """Get the internal tier ID for a display name.

    Returns None if the display name is not recognized.
    """
    tier = _DISPLAY_TO_TIER.get(display_name)
    return tier.value if tier else None
