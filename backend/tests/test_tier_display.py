"""
Tier display-name mapping tests — Phase LIX Sprint A.
Updated Pricing v3: 4-tier system (Free/Solo/Professional/Enterprise).

Validates the presentation layer that maps internal tier IDs to public plan names.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from shared.tier_display import (
    PURCHASABLE_TIERS,
    TIER_DISPLAY_NAMES,
    get_display_name,
    get_internal_id,
)


class TestTierDisplayNames:
    """Validate the display name mapping."""

    def test_free_display_name(self):
        assert get_display_name(UserTier.FREE) == "Free"

    def test_solo_displays_as_solo(self):
        assert get_display_name(UserTier.SOLO) == "Solo"

    def test_professional_display_name(self):
        assert get_display_name(UserTier.PROFESSIONAL) == "Professional"

    def test_enterprise_display_name(self):
        assert get_display_name(UserTier.ENTERPRISE) == "Enterprise"

    def test_all_tiers_have_display_names(self):
        for tier in UserTier:
            assert tier in TIER_DISPLAY_NAMES, f"Missing display name for {tier}"


class TestGetInternalId:
    """Validate reverse lookup from display name to internal ID."""

    def test_solo_maps_to_solo(self):
        assert get_internal_id("Solo") == "solo"

    def test_professional_maps_to_professional(self):
        assert get_internal_id("Professional") == "professional"

    def test_enterprise_maps_to_enterprise(self):
        assert get_internal_id("Enterprise") == "enterprise"

    def test_free_maps_to_free(self):
        assert get_internal_id("Free") == "free"

    def test_unknown_name_returns_none(self):
        assert get_internal_id("Platinum") is None

    def test_case_sensitive(self):
        """Display name lookup is case-sensitive."""
        assert get_internal_id("solo") is None
        assert get_internal_id("SOLO") is None


class TestPurchasableTiers:
    """Validate the set of tiers available for new subscriptions."""

    def test_excludes_free(self):
        assert "free" not in PURCHASABLE_TIERS

    def test_includes_solo(self):
        assert "solo" in PURCHASABLE_TIERS

    def test_includes_professional(self):
        assert "professional" in PURCHASABLE_TIERS

    def test_includes_enterprise(self):
        assert "enterprise" in PURCHASABLE_TIERS

    def test_exactly_three_purchasable(self):
        assert len(PURCHASABLE_TIERS) == 3
