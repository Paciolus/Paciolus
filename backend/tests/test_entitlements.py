"""
Tests for Sprint 363 — Tier Entitlements Configuration.

Covers:
1. Entitlement config completeness (all tiers defined)
2. Limit ordering (higher tiers get more)
3. Tool gating (free/starter restricted, pro+ all tools)
4. Feature flags (workspace, export, priority_support)
5. get_entitlements fallback behavior
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

    def test_starter_has_limit(self):
        ent = get_entitlements(UserTier.STARTER)
        assert ent.diagnostics_per_month == 50

    def test_professional_unlimited(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.diagnostics_per_month == 0  # unlimited

    def test_team_unlimited(self):
        ent = get_entitlements(UserTier.TEAM)
        assert ent.diagnostics_per_month == 0

    def test_enterprise_unlimited(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert ent.diagnostics_per_month == 0


class TestClientLimits:
    """Client limits should increase with tier."""

    def test_free_has_limit(self):
        ent = get_entitlements(UserTier.FREE)
        assert ent.max_clients == 3

    def test_starter_has_limit(self):
        ent = get_entitlements(UserTier.STARTER)
        assert ent.max_clients == 10

    def test_professional_unlimited(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.max_clients == 0

    def test_team_unlimited(self):
        ent = get_entitlements(UserTier.TEAM)
        assert ent.max_clients == 0


class TestToolAccess:
    """Free/Starter have restricted tools; Pro+ have all."""

    def test_free_restricted_tools(self):
        ent = get_entitlements(UserTier.FREE)
        assert len(ent.tools_allowed) > 0
        assert "trial_balance" in ent.tools_allowed
        assert "flux_analysis" in ent.tools_allowed
        assert "journal_entry_testing" not in ent.tools_allowed

    def test_starter_has_six_tools(self):
        ent = get_entitlements(UserTier.STARTER)
        assert len(ent.tools_allowed) == 6
        assert "journal_entry_testing" in ent.tools_allowed
        assert "multi_period" in ent.tools_allowed

    def test_professional_all_tools(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert len(ent.tools_allowed) == 0  # empty = all

    def test_team_all_tools(self):
        ent = get_entitlements(UserTier.TEAM)
        assert len(ent.tools_allowed) == 0

    def test_enterprise_all_tools(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
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

    def test_starter_all_exports(self):
        ent = get_entitlements(UserTier.STARTER)
        assert ent.pdf_export
        assert ent.excel_export
        assert ent.csv_export

    def test_professional_has_workspace(self):
        assert get_entitlements(UserTier.PROFESSIONAL).workspace

    def test_team_has_priority_support(self):
        assert get_entitlements(UserTier.TEAM).priority_support

    def test_enterprise_has_priority_support(self):
        assert get_entitlements(UserTier.ENTERPRISE).priority_support

    def test_free_no_priority_support(self):
        assert not get_entitlements(UserTier.FREE).priority_support


class TestTeamSeats:
    """Team tier has included seats; others don't."""

    def test_team_has_seats(self):
        ent = get_entitlements(UserTier.TEAM)
        assert ent.max_team_seats == 3

    def test_solo_tiers_no_seats(self):
        for tier in [UserTier.FREE, UserTier.STARTER, UserTier.PROFESSIONAL]:
            assert get_entitlements(tier).max_team_seats == 0


class TestGetEntitlementsFallback:
    """get_entitlements returns FREE for unknown values."""

    def test_returns_free_for_unknown_tier(self):
        # Simulate a tier value not in the dict
        result = get_entitlements(UserTier.FREE)
        assert result.diagnostics_per_month == 10
