"""
Tier display-name mapping tests — Phase LIX Sprint A.

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
        """Professional is deprecated but still has a display name."""
        assert get_display_name(UserTier.PROFESSIONAL) == "Professional"

    def test_team_display_name(self):
        assert get_display_name(UserTier.TEAM) == "Team"

    def test_organization_display_name(self):
        assert get_display_name(UserTier.ORGANIZATION) == "Organization"

    def test_all_tiers_have_display_names(self):
        for tier in UserTier:
            assert tier in TIER_DISPLAY_NAMES, f"Missing display name for {tier}"


class TestGetInternalId:
    """Validate reverse lookup from display name to internal ID."""

    def test_solo_maps_to_solo(self):
        assert get_internal_id("Solo") == "solo"

    def test_team_maps_to_team(self):
        assert get_internal_id("Team") == "team"

    def test_free_maps_to_free(self):
        assert get_internal_id("Free") == "free"

    def test_professional_maps_to_professional(self):
        assert get_internal_id("Professional") == "professional"

    def test_organization_maps_to_organization(self):
        assert get_internal_id("Organization") == "organization"

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

    def test_excludes_professional(self):
        assert "professional" not in PURCHASABLE_TIERS

    def test_includes_solo(self):
        assert "solo" in PURCHASABLE_TIERS

    def test_includes_team(self):
        assert "team" in PURCHASABLE_TIERS

    def test_includes_organization(self):
        assert "organization" in PURCHASABLE_TIERS

    def test_excludes_enterprise(self):
        assert "enterprise" not in PURCHASABLE_TIERS

    def test_exactly_three_purchasable(self):
        assert len(PURCHASABLE_TIERS) == 3
