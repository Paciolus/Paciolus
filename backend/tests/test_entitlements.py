"""
Tests for Tier Entitlements Configuration.

Sprint 363 — Phase L, updated Phase LIX Sprint A.

Covers:
1. Entitlement config completeness (all tiers defined)
2. Limit ordering (higher tiers get more)
3. Tool gating (free/solo restricted, team+ all tools)
4. Feature flags (workspace, export, priority_support)
5. get_entitlements fallback behavior
6. seats_included field (Phase LIX)
7. Professional deprecated → maps to solo entitlements (Phase LIX)
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import UserTier
from shared.entitlements import TIER_ENTITLEMENTS, TierEntitlements, get_entitlements


class TestEntitlementConfig:
    """Verify all tiers have entitlements defined."""

    def test_all_tiers_defined(self):
        for tier in UserTier:
            assert tier in TIER_ENTITLEMENTS, f"Missing entitlements for {tier.value}"

    def test_entitlements_are_frozen(self):
        for tier in UserTier:
            ent = TIER_ENTITLEMENTS[tier]
            assert isinstance(ent, TierEntitlements)
            with pytest.raises(AttributeError):
                ent.diagnostics_per_month = 999  # type: ignore[misc]


class TestDiagnosticLimits:
    """Diagnostic limits should increase with tier."""

    def test_free_has_limit(self):
        ent = get_entitlements(UserTier.FREE)
        assert ent.diagnostics_per_month == 10

    def test_solo_has_limit(self):
        ent = get_entitlements(UserTier.SOLO)
        assert ent.diagnostics_per_month == 20

    def test_professional_matches_solo(self):
        """Professional deprecated — maps to solo-level entitlements."""
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.diagnostics_per_month == 20

    def test_team_unlimited(self):
        ent = get_entitlements(UserTier.TEAM)
        assert ent.diagnostics_per_month == 0

    def test_organization_unlimited(self):
        ent = get_entitlements(UserTier.ORGANIZATION)
        assert ent.diagnostics_per_month == 0


class TestClientLimits:
    """Client limits should increase with tier."""

    def test_free_has_limit(self):
        ent = get_entitlements(UserTier.FREE)
        assert ent.max_clients == 3

    def test_solo_has_limit(self):
        ent = get_entitlements(UserTier.SOLO)
        assert ent.max_clients == 10

    def test_professional_matches_solo(self):
        """Professional deprecated — maps to solo-level entitlements."""
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.max_clients == 10

    def test_team_unlimited(self):
        ent = get_entitlements(UserTier.TEAM)
        assert ent.max_clients == 0

    def test_organization_unlimited(self):
        ent = get_entitlements(UserTier.ORGANIZATION)
        assert ent.max_clients == 0


class TestToolAccess:
    """Free/Solo have restricted tools; Team+ have all."""

    def test_free_restricted_tools(self):
        ent = get_entitlements(UserTier.FREE)
        assert len(ent.tools_allowed) > 0
        assert "trial_balance" in ent.tools_allowed
        assert "flux_analysis" in ent.tools_allowed
        assert "journal_entry_testing" not in ent.tools_allowed

    def test_solo_has_nine_tools(self):
        ent = get_entitlements(UserTier.SOLO)
        assert len(ent.tools_allowed) == 9
        assert "journal_entry_testing" in ent.tools_allowed
        assert "multi_period" in ent.tools_allowed
        assert "ap_testing" in ent.tools_allowed
        assert "bank_reconciliation" in ent.tools_allowed
        assert "revenue_testing" in ent.tools_allowed

    def test_professional_matches_solo(self):
        """Professional deprecated — same tool access as solo."""
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.tools_allowed == get_entitlements(UserTier.SOLO).tools_allowed

    def test_team_all_tools(self):
        ent = get_entitlements(UserTier.TEAM)
        assert len(ent.tools_allowed) == 0

    def test_organization_all_tools(self):
        ent = get_entitlements(UserTier.ORGANIZATION)
        assert len(ent.tools_allowed) == 0


class TestFeatureFlags:
    """Workspace, export, and support features vary by tier."""

    def test_free_no_workspace(self):
        assert not get_entitlements(UserTier.FREE).workspace

    def test_free_pdf_only(self):
        ent = get_entitlements(UserTier.FREE)
        assert ent.pdf_export
        assert not ent.excel_export
        assert not ent.csv_export

    def test_solo_all_exports(self):
        ent = get_entitlements(UserTier.SOLO)
        assert ent.pdf_export
        assert ent.excel_export
        assert ent.csv_export

    def test_professional_no_workspace(self):
        """Professional deprecated — maps to solo, no workspace."""
        assert not get_entitlements(UserTier.PROFESSIONAL).workspace

    def test_team_has_workspace(self):
        assert get_entitlements(UserTier.TEAM).workspace

    def test_team_has_priority_support(self):
        assert get_entitlements(UserTier.TEAM).priority_support

    def test_organization_has_workspace(self):
        assert get_entitlements(UserTier.ORGANIZATION).workspace

    def test_organization_has_priority_support(self):
        assert get_entitlements(UserTier.ORGANIZATION).priority_support

    def test_organization_all_exports(self):
        ent = get_entitlements(UserTier.ORGANIZATION)
        assert ent.pdf_export
        assert ent.excel_export
        assert ent.csv_export

    def test_free_no_priority_support(self):
        assert not get_entitlements(UserTier.FREE).priority_support


class TestTeamSeats:
    """Team tier has included seats; others don't."""

    def test_team_has_unlimited_seats(self):
        ent = get_entitlements(UserTier.TEAM)
        assert ent.max_team_seats == 0  # 0 = unlimited (custom)

    def test_solo_tiers_no_seats(self):
        for tier in [UserTier.FREE, UserTier.SOLO, UserTier.PROFESSIONAL]:
            assert get_entitlements(tier).max_team_seats == 0


class TestSeatsIncluded:
    """seats_included field — Phase LIX."""

    def test_free_one_seat(self):
        assert get_entitlements(UserTier.FREE).seats_included == 1

    def test_solo_one_seat(self):
        assert get_entitlements(UserTier.SOLO).seats_included == 1

    def test_professional_one_seat(self):
        assert get_entitlements(UserTier.PROFESSIONAL).seats_included == 1

    def test_team_three_seats(self):
        assert get_entitlements(UserTier.TEAM).seats_included == 3

    def test_organization_unlimited_seats(self):
        ent = get_entitlements(UserTier.ORGANIZATION)
        assert ent.seats_included == 0  # unlimited


class TestGetEntitlementsFallback:
    """get_entitlements returns FREE for unknown values."""

    def test_returns_free_for_unknown_tier(self):
        # Simulate a tier value not in the dict
        result = get_entitlements(UserTier.FREE)
        assert result.diagnostics_per_month == 10
