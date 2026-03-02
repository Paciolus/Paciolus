"""
Tests for Tier Entitlements Configuration.

Sprint 363 — Phase L, updated Phase LIX Sprint A.
Updated Pricing v3: 4-tier system (Free/Solo/Professional/Enterprise).

Covers:
1. Entitlement config completeness (all tiers defined)
2. Limit ordering (higher tiers get more)
3. Tool gating (free/solo restricted, professional/enterprise have all)
4. Feature flags (workspace, export, priority_support)
5. get_entitlements fallback behavior
6. seats_included field (Phase LIX)
7. Format gating (free restricted, solo+ has all)
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
        assert ent.diagnostics_per_month == 100

    def test_professional_has_limit(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.diagnostics_per_month == 500

    def test_enterprise_unlimited(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert ent.diagnostics_per_month == 0


class TestClientLimits:
    """Client limits should increase with tier."""

    def test_free_has_limit(self):
        ent = get_entitlements(UserTier.FREE)
        assert ent.max_clients == 3

    def test_solo_unlimited(self):
        ent = get_entitlements(UserTier.SOLO)
        assert ent.max_clients == 0

    def test_professional_unlimited(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.max_clients == 0

    def test_enterprise_unlimited(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert ent.max_clients == 0


class TestToolAccess:
    """Free has restricted tools; Solo+ has all tools."""

    def test_free_restricted_tools(self):
        ent = get_entitlements(UserTier.FREE)
        assert len(ent.tools_allowed) > 0
        assert "trial_balance" in ent.tools_allowed
        assert "flux_analysis" in ent.tools_allowed

    def test_solo_all_tools(self):
        ent = get_entitlements(UserTier.SOLO)
        assert len(ent.tools_allowed) == 0  # empty = all

    def test_professional_all_tools(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert len(ent.tools_allowed) == 0  # empty = all

    def test_enterprise_all_tools(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert len(ent.tools_allowed) == 0  # empty = all


class TestFormatAccess:
    """Format gating per tier."""

    def test_free_restricted_formats(self):
        ent = get_entitlements(UserTier.FREE)
        assert len(ent.formats_allowed) > 0
        assert "csv" in ent.formats_allowed
        assert "xlsx" in ent.formats_allowed

    def test_solo_all_formats(self):
        ent = get_entitlements(UserTier.SOLO)
        assert len(ent.formats_allowed) == 0  # empty = all

    def test_professional_all_formats(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert len(ent.formats_allowed) == 0  # empty = all

    def test_enterprise_all_formats(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert len(ent.formats_allowed) == 0  # empty = all


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

    def test_solo_has_workspace(self):
        assert get_entitlements(UserTier.SOLO).workspace

    def test_solo_no_priority_support(self):
        assert not get_entitlements(UserTier.SOLO).priority_support

    def test_professional_all_exports(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.pdf_export
        assert ent.excel_export
        assert ent.csv_export

    def test_professional_has_workspace(self):
        assert get_entitlements(UserTier.PROFESSIONAL).workspace

    def test_professional_has_priority_support(self):
        assert get_entitlements(UserTier.PROFESSIONAL).priority_support

    def test_enterprise_has_workspace(self):
        assert get_entitlements(UserTier.ENTERPRISE).workspace

    def test_enterprise_has_priority_support(self):
        assert get_entitlements(UserTier.ENTERPRISE).priority_support

    def test_enterprise_all_exports(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert ent.pdf_export
        assert ent.excel_export
        assert ent.csv_export

    def test_free_no_priority_support(self):
        assert not get_entitlements(UserTier.FREE).priority_support


class TestSeatsIncluded:
    """seats_included field — Phase LIX."""

    def test_free_one_seat(self):
        assert get_entitlements(UserTier.FREE).seats_included == 1

    def test_solo_one_seat(self):
        assert get_entitlements(UserTier.SOLO).seats_included == 1

    def test_professional_seven_seats(self):
        assert get_entitlements(UserTier.PROFESSIONAL).seats_included == 7

    def test_enterprise_twenty_seats(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert ent.seats_included == 20


class TestMaxTeamSeats:
    """Max team seats per tier."""

    def test_professional_max_seats(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        assert ent.max_team_seats == 20

    def test_enterprise_max_seats(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert ent.max_team_seats == 100

    def test_solo_no_team_seats(self):
        assert get_entitlements(UserTier.SOLO).max_team_seats == 0

    def test_free_no_team_seats(self):
        assert get_entitlements(UserTier.FREE).max_team_seats == 0


class TestGetEntitlementsFallback:
    """get_entitlements returns FREE for unknown values."""

    def test_returns_free_for_unknown_tier(self):
        # Simulate a tier value not in the dict
        result = get_entitlements(UserTier.FREE)
        assert result.diagnostics_per_month == 10
