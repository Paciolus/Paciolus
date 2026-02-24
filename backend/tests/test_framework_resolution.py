"""
Tests for Framework Resolution Engine — Sprint 1

Full branch coverage of resolve_reporting_framework():
- Explicit FASB/GASB overrides
- Entity type → framework mapping
- Jurisdiction-based defaults
- Fallback with warnings
- Edge cases (whitespace, case, empty strings)
"""

import sys

import pytest

sys.path.insert(0, "..")

from shared.framework_resolution import (
    ResolutionReason,
    ResolvedFramework,
    resolve_reporting_framework,
)

# =============================================================================
# Precedence 1: Explicit Framework Override
# =============================================================================


class TestExplicitFramework:
    """Tests for explicit FASB/GASB selection (highest precedence)."""

    def test_explicit_fasb(self):
        result = resolve_reporting_framework(
            reporting_framework="fasb",
            entity_type="for_profit",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.EXPLICIT_FASB
        assert len(result.warnings) == 0

    def test_explicit_fasb_overrides_governmental(self):
        """FASB explicit beats governmental entity_type."""
        result = resolve_reporting_framework(
            reporting_framework="fasb",
            entity_type="governmental",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.EXPLICIT_FASB

    def test_explicit_gasb_governmental(self):
        result = resolve_reporting_framework(
            reporting_framework="gasb",
            entity_type="governmental",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert result.resolution_reason == ResolutionReason.EXPLICIT_GASB
        assert len(result.warnings) == 0

    def test_explicit_gasb_non_governmental_warns(self):
        """GASB with non-governmental entity_type emits a warning."""
        result = resolve_reporting_framework(
            reporting_framework="gasb",
            entity_type="for_profit",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert result.resolution_reason == ResolutionReason.EXPLICIT_GASB
        assert len(result.warnings) == 1
        assert "not 'governmental'" in result.warnings[0]

    def test_explicit_gasb_nonprofit_warns(self):
        result = resolve_reporting_framework(
            reporting_framework="gasb",
            entity_type="nonprofit",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert len(result.warnings) == 1

    def test_explicit_gasb_other_warns(self):
        result = resolve_reporting_framework(
            reporting_framework="gasb",
            entity_type="other",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert len(result.warnings) == 1


# =============================================================================
# Precedence 2-4: AUTO Resolution by Entity Type
# =============================================================================


class TestAutoEntityType:
    """Tests for AUTO mode resolving by entity_type."""

    def test_governmental_resolves_gasb(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="governmental",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_GOVERNMENTAL
        assert len(result.warnings) == 0

    def test_for_profit_resolves_fasb(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="for_profit",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_FOR_PROFIT
        assert len(result.warnings) == 0

    def test_nonprofit_us_resolves_fasb(self):
        """US nonprofits follow FASB ASC 958."""
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="nonprofit",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_NONPROFIT_US
        assert len(result.warnings) == 0

    def test_nonprofit_non_us_falls_through(self):
        """Non-US nonprofit doesn't match ENTITY_TYPE_NONPROFIT_US rule."""
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="nonprofit",
            jurisdiction_country="GB",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.FALLBACK_FASB
        assert len(result.warnings) == 1

    def test_governmental_non_us(self):
        """Governmental entity type resolves to GASB regardless of country."""
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="governmental",
            jurisdiction_country="CA",
        )
        assert result.framework == ResolvedFramework.GASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_GOVERNMENTAL


# =============================================================================
# Precedence 5: Jurisdiction-Based Default
# =============================================================================


class TestJurisdictionDefault:
    """Tests for US jurisdiction fallback."""

    def test_other_entity_us_defaults_fasb_with_warning(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="other",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.JURISDICTION_US_DEFAULT
        assert len(result.warnings) == 1
        assert "Entity type is 'other'" in result.warnings[0]

    def test_us_jurisdiction_with_state(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="other",
            jurisdiction_country="US",
            jurisdiction_state="California",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.JURISDICTION_US_DEFAULT


# =============================================================================
# Precedence 6: Fallback
# =============================================================================


class TestFallback:
    """Tests for non-US, non-deterministic fallback."""

    def test_non_us_other_falls_back_fasb(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="other",
            jurisdiction_country="DE",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.FALLBACK_FASB
        assert len(result.warnings) == 1
        assert "No deterministic rule matched" in result.warnings[0]

    def test_non_us_for_profit(self):
        """For-profit in non-US still resolves to FASB via entity_type rule."""
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="for_profit",
            jurisdiction_country="JP",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_FOR_PROFIT
        assert len(result.warnings) == 0


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases: case sensitivity, whitespace, empty strings."""

    def test_case_insensitive_framework(self):
        result = resolve_reporting_framework(
            reporting_framework="FASB",
            entity_type="for_profit",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.EXPLICIT_FASB

    def test_case_insensitive_entity_type(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="GOVERNMENTAL",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_GOVERNMENTAL

    def test_whitespace_trimmed(self):
        result = resolve_reporting_framework(
            reporting_framework="  gasb  ",
            entity_type="governmental",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert result.resolution_reason == ResolutionReason.EXPLICIT_GASB

    def test_empty_framework_treated_as_auto(self):
        result = resolve_reporting_framework(
            reporting_framework="",
            entity_type="governmental",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.GASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_GOVERNMENTAL

    def test_empty_entity_type_treated_as_other(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="",
            jurisdiction_country="US",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.JURISDICTION_US_DEFAULT

    def test_empty_country_defaults_to_us(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="for_profit",
            jurisdiction_country="",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.ENTITY_TYPE_FOR_PROFIT

    def test_lowercase_country_normalized(self):
        result = resolve_reporting_framework(
            reporting_framework="auto",
            entity_type="other",
            jurisdiction_country="us",
        )
        assert result.framework == ResolvedFramework.FASB
        assert result.resolution_reason == ResolutionReason.JURISDICTION_US_DEFAULT

    def test_result_is_frozen(self):
        result = resolve_reporting_framework(
            reporting_framework="fasb",
            entity_type="for_profit",
            jurisdiction_country="US",
        )
        with pytest.raises(AttributeError):
            result.framework = ResolvedFramework.GASB  # type: ignore[misc]

    def test_is_fasb_property(self):
        result = resolve_reporting_framework(
            reporting_framework="fasb",
            entity_type="for_profit",
            jurisdiction_country="US",
        )
        assert result.is_fasb is True
        assert result.is_gasb is False

    def test_is_gasb_property(self):
        result = resolve_reporting_framework(
            reporting_framework="gasb",
            entity_type="governmental",
            jurisdiction_country="US",
        )
        assert result.is_gasb is True
        assert result.is_fasb is False
