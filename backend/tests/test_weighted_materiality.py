"""
Tests for Sprint 32: Weighted Materiality by Account Type

Tests the WeightedMaterialityConfig and MaterialityCalculator.calculate_weighted
functionality for applying different materiality thresholds to different
account categories.
"""

import pytest

from practice_settings import (
    MaterialityCalculator,
    MaterialityConfig,
    MaterialityFormula,
    MaterialityFormulaType,
    PracticeSettings,
    WeightedMaterialityConfig,
    resolve_materiality_config,
)


class TestWeightedMaterialityConfig:
    """Tests for WeightedMaterialityConfig model."""

    def test_default_weights(self):
        """Test that default weights are applied correctly."""
        config = WeightedMaterialityConfig()

        assert config.account_weights["asset"] == 1.0
        assert config.account_weights["liability"] == 1.2
        assert config.account_weights["equity"] == 1.5
        assert config.account_weights["revenue"] == 1.3
        assert config.account_weights["expense"] == 0.8
        assert config.account_weights["unknown"] == 1.0

    def test_disabled_by_default(self):
        """Test that weighted materiality is disabled by default."""
        config = WeightedMaterialityConfig()
        assert config.enabled is False

    def test_get_effective_weight_disabled(self):
        """Test that effective weight is 1.0 when disabled."""
        config = WeightedMaterialityConfig(enabled=False)

        assert config.get_effective_weight("asset") == 1.0
        assert config.get_effective_weight("equity") == 1.0
        assert config.get_effective_weight("expense") == 1.0

    def test_get_effective_weight_enabled(self):
        """Test effective weight calculation when enabled."""
        config = WeightedMaterialityConfig(enabled=True)

        # Asset: 1.0 * 1.0 (balance_sheet_weight) = 1.0
        assert config.get_effective_weight("asset") == 1.0

        # Equity: 1.5 * 1.0 = 1.5
        assert config.get_effective_weight("equity") == 1.5

        # Expense: 0.8 * 0.9 (income_statement_weight) = 0.72
        assert config.get_effective_weight("expense") == pytest.approx(0.72, rel=0.01)

    def test_calculate_threshold_disabled(self):
        """Test threshold calculation when disabled returns base threshold."""
        config = WeightedMaterialityConfig(enabled=False)

        assert config.calculate_threshold(1000.0, "asset") == 1000.0
        assert config.calculate_threshold(1000.0, "equity") == 1000.0
        assert config.calculate_threshold(1000.0, "expense") == 1000.0

    def test_calculate_threshold_enabled(self):
        """Test threshold calculation with weights applied."""
        config = WeightedMaterialityConfig(enabled=True)
        base_threshold = 1000.0

        # Asset: 1.0 weight -> 1000 / 1.0 = 1000
        assert config.calculate_threshold(base_threshold, "asset") == 1000.0

        # Equity: 1.5 weight -> 1000 / 1.5 = 666.67
        assert config.calculate_threshold(base_threshold, "equity") == pytest.approx(666.67, rel=0.01)

        # Expense: 0.72 weight -> 1000 / 0.72 = 1388.89
        assert config.calculate_threshold(base_threshold, "expense") == pytest.approx(1388.89, rel=0.01)

    def test_custom_weights(self):
        """Test with custom weight configuration."""
        custom_weights = {
            "asset": 2.0,      # Very high scrutiny
            "liability": 1.0,
            "equity": 1.0,
            "revenue": 1.0,
            "expense": 0.5,    # Low scrutiny
            "unknown": 1.0,
        }
        config = WeightedMaterialityConfig(
            account_weights=custom_weights,
            enabled=True,
            balance_sheet_weight=1.0,
            income_statement_weight=1.0
        )

        # Asset: 2.0 -> 500 / 2.0 = 250 (more items flagged)
        assert config.calculate_threshold(500.0, "asset") == 250.0

        # Expense: 0.5 -> 500 / 0.5 = 1000 (fewer items flagged)
        assert config.calculate_threshold(500.0, "expense") == 1000.0

    def test_to_dict_from_dict(self):
        """Test serialization and deserialization."""
        config = WeightedMaterialityConfig(
            enabled=True,
            balance_sheet_weight=1.2,
            income_statement_weight=0.8
        )

        data = config.to_dict()
        restored = WeightedMaterialityConfig.from_dict(data)

        assert restored.enabled == config.enabled
        assert restored.balance_sheet_weight == config.balance_sheet_weight
        assert restored.income_statement_weight == config.income_statement_weight
        assert restored.account_weights == config.account_weights

    def test_display_summary_disabled(self):
        """Test display summary when disabled."""
        config = WeightedMaterialityConfig(enabled=False)
        summary = config.get_display_summary()
        assert "disabled" in summary.lower()

    def test_display_summary_enabled(self):
        """Test display summary when enabled."""
        config = WeightedMaterialityConfig(enabled=True)
        summary = config.get_display_summary()
        assert "Equity" in summary  # Highest default weight
        assert "Expense" in summary  # Lowest default weight

    def test_weight_validation_bounds(self):
        """Test that weights must be within bounds."""
        with pytest.raises(ValueError):
            WeightedMaterialityConfig(
                account_weights={"asset": 0.05}  # Below 0.1 minimum
            )

        with pytest.raises(ValueError):
            WeightedMaterialityConfig(
                account_weights={"asset": 6.0}  # Above 5.0 maximum
            )


class TestMaterialityCalculatorWeighted:
    """Tests for MaterialityCalculator.calculate_weighted method."""

    def test_calculate_weighted_no_config(self):
        """Test weighted calculation without weighted config."""
        formula = MaterialityFormula(type=MaterialityFormulaType.FIXED, value=500.0)
        config = MaterialityConfig(formula=formula, weighted_config=None)

        result = MaterialityCalculator.calculate_weighted(config, "asset")
        assert result == 500.0

    def test_calculate_weighted_disabled(self):
        """Test weighted calculation with disabled config."""
        formula = MaterialityFormula(type=MaterialityFormulaType.FIXED, value=500.0)
        weighted = WeightedMaterialityConfig(enabled=False)
        config = MaterialityConfig(formula=formula, weighted_config=weighted)

        result = MaterialityCalculator.calculate_weighted(config, "equity")
        assert result == 500.0  # No adjustment

    def test_calculate_weighted_enabled(self):
        """Test weighted calculation with enabled config."""
        formula = MaterialityFormula(type=MaterialityFormulaType.FIXED, value=1000.0)
        weighted = WeightedMaterialityConfig(enabled=True)
        config = MaterialityConfig(formula=formula, weighted_config=weighted)

        # Equity has 1.5 weight -> 1000 / 1.5 = 666.67
        equity_threshold = MaterialityCalculator.calculate_weighted(config, "equity")
        assert equity_threshold == pytest.approx(666.67, rel=0.01)

        # Asset has 1.0 weight -> 1000 / 1.0 = 1000
        asset_threshold = MaterialityCalculator.calculate_weighted(config, "asset")
        assert asset_threshold == 1000.0

    def test_calculate_weighted_percentage_based(self):
        """Test weighted calculation with percentage-based formula."""
        formula = MaterialityFormula(
            type=MaterialityFormulaType.PERCENTAGE_OF_REVENUE,
            value=1.0  # 1% of revenue
        )
        weighted = WeightedMaterialityConfig(enabled=True)
        config = MaterialityConfig(formula=formula, weighted_config=weighted)

        # 1% of $100,000 = $1,000 base
        # Equity: 1000 / 1.5 = 666.67
        result = MaterialityCalculator.calculate_weighted(
            config, "equity", total_revenue=100000.0
        )
        assert result == pytest.approx(666.67, rel=0.01)

    def test_preview_weighted(self):
        """Test preview_weighted returns all category thresholds."""
        formula = MaterialityFormula(type=MaterialityFormulaType.FIXED, value=1000.0)
        weighted = WeightedMaterialityConfig(enabled=True)
        config = MaterialityConfig(formula=formula, weighted_config=weighted)

        preview = MaterialityCalculator.preview_weighted(config)

        assert preview["base_threshold"] == 1000.0
        assert preview["weighted_enabled"] is True
        assert "asset" in preview["thresholds_by_category"]
        assert "liability" in preview["thresholds_by_category"]
        assert "equity" in preview["thresholds_by_category"]
        assert "revenue" in preview["thresholds_by_category"]
        assert "expense" in preview["thresholds_by_category"]
        assert preview["weighted_config"] is not None


class TestPracticeSettingsIntegration:
    """Tests for weighted materiality integration with PracticeSettings."""

    def test_practice_settings_includes_weighted(self):
        """Test that PracticeSettings includes weighted materiality config."""
        settings = PracticeSettings()

        assert hasattr(settings, 'weighted_materiality')
        assert isinstance(settings.weighted_materiality, WeightedMaterialityConfig)

    def test_practice_settings_json_roundtrip(self):
        """Test JSON serialization/deserialization with weighted config."""
        settings = PracticeSettings(
            weighted_materiality=WeightedMaterialityConfig(
                enabled=True,
                balance_sheet_weight=1.1,
                income_statement_weight=0.9
            )
        )

        json_str = settings.to_json()
        restored = PracticeSettings.from_json(json_str)

        assert restored.weighted_materiality.enabled is True
        assert restored.weighted_materiality.balance_sheet_weight == 1.1
        assert restored.weighted_materiality.income_statement_weight == 0.9

    def test_resolve_materiality_config_includes_weighted(self):
        """Test that resolve_materiality_config includes weighted config."""
        practice_settings = PracticeSettings(
            weighted_materiality=WeightedMaterialityConfig(enabled=True)
        )

        config = resolve_materiality_config(practice_settings=practice_settings)

        assert config.weighted_config is not None
        assert config.weighted_config.enabled is True


class TestEdgeCases:
    """Edge case tests for weighted materiality."""

    def test_zero_base_threshold(self):
        """Test handling of zero base threshold."""
        config = WeightedMaterialityConfig(enabled=True)
        result = config.calculate_threshold(0.0, "equity")
        assert result == 0.0

    def test_unknown_category(self):
        """Test handling of unknown category."""
        config = WeightedMaterialityConfig(enabled=True)
        # Unknown uses 1.0 weight
        result = config.calculate_threshold(1000.0, "unknown")
        assert result == 1000.0

    def test_case_insensitive_category(self):
        """Test that category matching is case insensitive."""
        config = WeightedMaterialityConfig(enabled=True)

        assert config.get_effective_weight("ASSET") == config.get_effective_weight("asset")
        assert config.get_effective_weight("Equity") == config.get_effective_weight("equity")

    def test_unrecognized_category(self):
        """Test handling of completely unrecognized category."""
        config = WeightedMaterialityConfig(enabled=True)

        # Should default to 1.0 weight
        weight = config.get_effective_weight("nonexistent")
        assert weight == 1.0  # Falls back to 1.0 account weight * 1.0 statement weight

    def test_session_override_bypasses_weights(self):
        """Test that session override takes priority over weighted calculation."""
        formula = MaterialityFormula(type=MaterialityFormulaType.FIXED, value=1000.0)
        weighted = WeightedMaterialityConfig(enabled=True)
        config = MaterialityConfig(
            formula=formula,
            weighted_config=weighted,
            session_override=250.0  # Direct override
        )

        # Session override should be returned directly (base calculation)
        # Then weight should be applied
        result = MaterialityCalculator.calculate_weighted(config, "equity")
        # 250 / 1.5 = 166.67
        assert result == pytest.approx(166.67, rel=0.01)
