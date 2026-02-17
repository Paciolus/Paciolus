"""
Tests for Statistical Sampling Engine — Sprint 268
Phase XXXVI: Tool 12

Covers:
- MUS sample size calculation
- MUS interval-based selection
- Random selection (Fisher-Yates)
- 2-tier stratification
- Stringer bound evaluation
- Integration (design_sample, evaluate_sample)
"""

import pytest

from sampling_engine import (
    CONFIDENCE_FACTORS,
    PopulationItem,
    SampleError,
    SamplingConfig,
    apply_stratification,
    calculate_mus_sample_size,
    design_sample,
    evaluate_mus_sample_stringer,
    evaluate_sample,
    get_confidence_factor,
    select_mus_sample,
    select_random_sample,
)

# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _make_items(amounts: list[float]) -> list[PopulationItem]:
    """Create PopulationItem list from a list of amounts."""
    return [
        PopulationItem(
            row_index=i + 1,
            item_id=str(i + 1),
            description=f"Item {i + 1}",
            recorded_amount=amt,
        )
        for i, amt in enumerate(amounts)
    ]


def _make_csv(rows: list[dict], columns: list[str]) -> bytes:
    """Create CSV bytes from rows and columns."""
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(str(row.get(c, "")) for c in columns))
    return "\n".join(lines).encode("utf-8")


# ═══════════════════════════════════════════════════════════════
# Confidence Factor Lookup
# ═══════════════════════════════════════════════════════════════

class TestConfidenceFactors:
    """Test confidence factor lookup."""

    def test_exact_lookup_95(self):
        assert get_confidence_factor(0.95) == 3.00

    def test_exact_lookup_90(self):
        assert get_confidence_factor(0.90) == 2.31

    def test_exact_lookup_99(self):
        assert get_confidence_factor(0.99) == 4.61

    def test_nearest_fallback(self):
        """Non-standard level falls back to nearest."""
        factor = get_confidence_factor(0.93)
        # 0.93 is nearest to 0.95 (diff 0.02) vs 0.90 (diff 0.03)
        assert factor == CONFIDENCE_FACTORS[0.95]

    def test_all_factors_positive(self):
        for level, factor in CONFIDENCE_FACTORS.items():
            assert factor > 0, f"Factor for {level} should be positive"


# ═══════════════════════════════════════════════════════════════
# MUS Sample Size Calculation
# ═══════════════════════════════════════════════════════════════

class TestMUSSampleSize:
    """Test MUS sample size formula."""

    def test_basic_calculation_zero_expected(self):
        """Standard case: 95% confidence, $50K tolerable, zero expected, $1M population."""
        size, interval, factor = calculate_mus_sample_size(
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            expected_misstatement=0,
            population_value=1_000_000,
        )
        # interval = 50000 / 3.0 = 16666.67
        # size = ceil(1000000 / 16666.67) = 60
        assert factor == 3.00
        assert abs(interval - 16666.67) < 1
        assert size == 60

    def test_with_expected_misstatement(self):
        """Expected misstatement increases sample size."""
        size_zero, _, _ = calculate_mus_sample_size(
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            expected_misstatement=0,
            population_value=1_000_000,
        )
        size_with, _, _ = calculate_mus_sample_size(
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            expected_misstatement=10_000,
            population_value=1_000_000,
        )
        assert size_with > size_zero

    def test_higher_confidence_larger_sample(self):
        """Higher confidence = larger sample."""
        size_90, _, _ = calculate_mus_sample_size(
            confidence_level=0.90,
            tolerable_misstatement=50_000,
            expected_misstatement=0,
            population_value=1_000_000,
        )
        size_95, _, _ = calculate_mus_sample_size(
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            expected_misstatement=0,
            population_value=1_000_000,
        )
        assert size_95 > size_90

    def test_invalid_zero_tolerable(self):
        with pytest.raises(ValueError, match="Tolerable misstatement must be positive"):
            calculate_mus_sample_size(0.95, 0, 0, 1_000_000)

    def test_invalid_negative_expected(self):
        with pytest.raises(ValueError, match="Expected misstatement cannot be negative"):
            calculate_mus_sample_size(0.95, 50_000, -1, 1_000_000)

    def test_invalid_expected_ge_tolerable(self):
        with pytest.raises(ValueError, match="Expected misstatement must be less"):
            calculate_mus_sample_size(0.95, 50_000, 50_000, 1_000_000)

    def test_invalid_zero_population(self):
        with pytest.raises(ValueError, match="Population value must be positive"):
            calculate_mus_sample_size(0.95, 50_000, 0, 0)

    def test_minimum_sample_size_is_one(self):
        """Even with huge tolerable, sample size is at least 1."""
        size, _, _ = calculate_mus_sample_size(
            confidence_level=0.80,
            tolerable_misstatement=10_000_000,
            expected_misstatement=0,
            population_value=100,
        )
        assert size >= 1


# ═══════════════════════════════════════════════════════════════
# MUS Selection
# ═══════════════════════════════════════════════════════════════

class TestMUSSelection:
    """Test MUS interval-based selection."""

    def test_basic_selection_count(self):
        """Selection should produce approximately expected count."""
        items = _make_items([1000] * 100)  # 100 items, $1000 each = $100K
        interval = 10_000  # Should select ~10 items
        selected, start = select_mus_sample(items, interval, random_start=5000)
        assert len(selected) >= 8
        assert len(selected) <= 12

    def test_deterministic_with_fixed_start(self):
        """Same random start produces same selection."""
        items = _make_items([500, 1000, 1500, 2000, 2500])
        sel1, _ = select_mus_sample(items, 2000, random_start=500)
        sel2, _ = select_mus_sample(items, 2000, random_start=500)
        ids1 = [s.item.row_index for s in sel1]
        ids2 = [s.item.row_index for s in sel2]
        assert ids1 == ids2

    def test_no_duplicates(self):
        """Same item should not appear twice in selection."""
        items = _make_items([100] * 50)
        selected, _ = select_mus_sample(items, 500)
        row_indices = [s.item.row_index for s in selected]
        assert len(row_indices) == len(set(row_indices))

    def test_large_item_always_selected(self):
        """An item larger than the interval is always selected."""
        items = _make_items([100, 200, 50_000, 300])
        selected, _ = select_mus_sample(items, 5000, random_start=100)
        selected_amounts = [s.item.recorded_amount for s in selected]
        assert 50_000 in selected_amounts

    def test_zero_amount_items_skipped(self):
        """Items with zero amount are skipped."""
        items = _make_items([0, 0, 1000, 0, 2000])
        selected, _ = select_mus_sample(items, 500)
        for s in selected:
            assert s.item.recorded_amount != 0

    def test_invalid_interval(self):
        with pytest.raises(ValueError, match="Sampling interval must be positive"):
            select_mus_sample([], 0)

    def test_full_population_when_interval_tiny(self):
        """When interval is very small, most items get selected."""
        items = _make_items([1000, 2000, 3000, 4000, 5000])
        selected, _ = select_mus_sample(items, 1.0, random_start=0.5)
        # With interval=1, all items should be selected
        assert len(selected) == 5


# ═══════════════════════════════════════════════════════════════
# Random Selection
# ═══════════════════════════════════════════════════════════════

class TestRandomSelection:
    """Test random selection (Fisher-Yates)."""

    def test_correct_count(self):
        items = _make_items([100] * 50)
        selected = select_random_sample(items, 10)
        assert len(selected) == 10

    def test_no_duplicates(self):
        items = _make_items([100] * 100)
        selected = select_random_sample(items, 20)
        row_indices = [s.item.row_index for s in selected]
        assert len(row_indices) == len(set(row_indices))

    def test_full_population_when_oversized(self):
        """Request more than population → return entire population."""
        items = _make_items([100] * 5)
        selected = select_random_sample(items, 100)
        assert len(selected) == 5

    def test_selection_method_tag(self):
        items = _make_items([100] * 10)
        selected = select_random_sample(items, 3)
        for s in selected:
            assert s.selection_method == "random"

    def test_invalid_zero_size(self):
        with pytest.raises(ValueError, match="Sample size must be positive"):
            select_random_sample([], 0)


# ═══════════════════════════════════════════════════════════════
# Stratification
# ═══════════════════════════════════════════════════════════════

class TestStratification:
    """Test 2-tier stratification."""

    def test_basic_split(self):
        items = _make_items([100, 500, 1000, 5000, 10000, 50])
        high, remainder = apply_stratification(items, 1000)
        assert len(high) == 3  # 1000, 5000, 10000
        assert len(remainder) == 3  # 100, 500, 50

    def test_all_high_value(self):
        items = _make_items([5000, 10000, 20000])
        high, remainder = apply_stratification(items, 1000)
        assert len(high) == 3
        assert len(remainder) == 0

    def test_all_remainder(self):
        items = _make_items([100, 200, 300])
        high, remainder = apply_stratification(items, 1000)
        assert len(high) == 0
        assert len(remainder) == 3

    def test_stratum_labels(self):
        items = _make_items([500, 5000])
        high, remainder = apply_stratification(items, 1000)
        assert all(i.stratum == "high_value" for i in high)
        assert all(i.stratum == "remainder" for i in remainder)

    def test_threshold_boundary(self):
        """Items exactly at threshold go to high value."""
        items = _make_items([1000])
        high, remainder = apply_stratification(items, 1000)
        assert len(high) == 1
        assert len(remainder) == 0

    def test_negative_amounts(self):
        """Stratification uses absolute value."""
        items = _make_items([-5000, -100, 3000])
        high, remainder = apply_stratification(items, 2000)
        assert len(high) == 2  # |-5000| >= 2000, |3000| >= 2000
        assert len(remainder) == 1


# ═══════════════════════════════════════════════════════════════
# Stringer Bound Evaluation
# ═══════════════════════════════════════════════════════════════

class TestStringerBound:
    """Test Stringer bound evaluation."""

    def test_zero_errors(self):
        """No errors → UEL = basic precision only."""
        result = evaluate_mus_sample_stringer(
            errors=[],
            sampling_interval=10_000,
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            population_value=600_000,
            sample_size=60,
        )
        assert result.errors_found == 0
        assert result.projected_misstatement == 0.0
        assert result.incremental_allowance == 0.0
        # Basic precision = 10000 * 3.0 = 30000
        assert abs(result.basic_precision - 30_000) < 1
        assert result.upper_error_limit == result.basic_precision
        assert result.conclusion == "pass"  # 30000 < 50000

    def test_one_error(self):
        """Single error with 50% tainting."""
        errors = [SampleError(
            row_index=1, item_id="1",
            recorded_amount=10_000, audited_amount=5_000,
            misstatement=5_000, tainting=0.5,
        )]
        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=10_000,
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            population_value=600_000,
            sample_size=60,
        )
        assert result.errors_found == 1
        # Projected = 0.5 * 10000 = 5000
        assert abs(result.projected_misstatement - 5_000) < 1
        # Incremental = 0.5 * 10000 * (1.58 - 1.0) = 2900
        assert abs(result.incremental_allowance - 2_900) < 1
        # UEL = 30000 + 5000 + 2900 = 37900
        assert abs(result.upper_error_limit - 37_900) < 1
        assert result.conclusion == "pass"  # 37900 < 50000

    def test_multiple_errors_fail(self):
        """Multiple errors push UEL above tolerable."""
        errors = [
            SampleError(1, "1", 10_000, 2_000, 8_000, 0.8),
            SampleError(2, "2", 10_000, 3_000, 7_000, 0.7),
            SampleError(3, "3", 10_000, 5_000, 5_000, 0.5),
        ]
        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=10_000,
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            population_value=600_000,
            sample_size=60,
        )
        assert result.errors_found == 3
        assert result.conclusion == "fail"
        assert result.upper_error_limit > 50_000

    def test_taintings_ranked_descending(self):
        """Taintings should be sorted largest first."""
        errors = [
            SampleError(1, "1", 10_000, 8_000, 2_000, 0.2),
            SampleError(2, "2", 10_000, 2_000, 8_000, 0.8),
            SampleError(3, "3", 10_000, 5_000, 5_000, 0.5),
        ]
        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=10_000,
            confidence_level=0.95,
            tolerable_misstatement=100_000,
            population_value=600_000,
            sample_size=60,
        )
        assert result.taintings_ranked == [0.8, 0.5, 0.2]

    def test_100_percent_tainting(self):
        """Full misstatement (100% tainting)."""
        errors = [SampleError(
            row_index=1, item_id="1",
            recorded_amount=10_000, audited_amount=0,
            misstatement=10_000, tainting=1.0,
        )]
        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=10_000,
            confidence_level=0.95,
            tolerable_misstatement=50_000,
            population_value=600_000,
            sample_size=60,
        )
        assert result.taintings_ranked == [1.0]
        # Projected = 1.0 * 10000 = 10000
        assert abs(result.projected_misstatement - 10_000) < 1


# ═══════════════════════════════════════════════════════════════
# Integration: design_sample
# ═══════════════════════════════════════════════════════════════

class TestDesignSample:
    """Integration tests for the design_sample entry point."""

    def _make_population_csv(self, count: int = 50) -> bytes:
        """Generate a simple population CSV."""
        lines = ["ID,Description,Amount"]
        for i in range(1, count + 1):
            lines.append(f"{i},Item {i},{i * 100}")
        return "\n".join(lines).encode("utf-8")

    def test_mus_design_basic(self):
        csv_data = self._make_population_csv(50)
        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=10_000,
            expected_misstatement=0,
        )
        result = design_sample(csv_data, "test.csv", config)
        assert result.method == "mus"
        assert result.population_size == 50
        assert result.actual_sample_size > 0
        assert len(result.selected_items) == result.actual_sample_size
        assert result.sampling_interval is not None
        assert result.sampling_interval > 0

    def test_random_design_with_override(self):
        csv_data = self._make_population_csv(50)
        config = SamplingConfig(
            method="random",
            confidence_level=0.95,
            tolerable_misstatement=10_000,
            sample_size_override=15,
        )
        result = design_sample(csv_data, "test.csv", config)
        assert result.method == "random"
        assert result.actual_sample_size == 15
        assert len(result.selected_items) == 15

    def test_stratified_design(self):
        """Stratification splits high-value from remainder."""
        lines = ["ID,Description,Amount"]
        for i in range(1, 41):
            lines.append(f"{i},Small Item {i},{100}")
        for i in range(41, 51):
            lines.append(f"{i},Large Item {i},{10000}")
        csv_data = "\n".join(lines).encode("utf-8")

        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=20_000,
            expected_misstatement=0,
            stratification_threshold=5000,
        )
        result = design_sample(csv_data, "test.csv", config)
        assert result.high_value_count == 10
        assert result.remainder_count == 40
        assert len(result.strata_summary) == 2
        # High-value items are always selected
        hv_selected = [
            s for s in result.selected_items
            if s.selection_method == "high_value_100pct"
        ]
        assert len(hv_selected) == 10

    def test_column_mapping_override(self):
        """Manual column mapping should override auto-detection."""
        lines = ["Ref,Note,Value"]
        for i in range(1, 21):
            lines.append(f"R{i},Note {i},{i * 50}")
        csv_data = "\n".join(lines).encode("utf-8")

        config = SamplingConfig(
            method="random",
            confidence_level=0.95,
            tolerable_misstatement=5_000,
            sample_size_override=5,
        )
        mapping = {"item_id": "Ref", "description": "Note", "recorded_amount": "Value"}
        result = design_sample(csv_data, "test.csv", config, column_mapping=mapping)
        assert result.population_size == 20
        assert result.actual_sample_size == 5

    def test_empty_population_raises(self):
        """CSV with no numeric amounts should raise."""
        csv_data = b"ID,Description,Amount\n1,Test,abc\n2,Test,xyz\n"
        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=1000,
        )
        with pytest.raises(ValueError, match="No valid items"):
            design_sample(csv_data, "test.csv", config)


# ═══════════════════════════════════════════════════════════════
# Integration: evaluate_sample
# ═══════════════════════════════════════════════════════════════

class TestEvaluateSample:
    """Integration tests for the evaluate_sample entry point."""

    def _make_evaluation_csv(self, errors: list[tuple[float, float]], clean: int = 10) -> bytes:
        """Generate evaluation CSV with recorded/audited amounts.

        errors: list of (recorded, audited) pairs for misstatement rows
        clean: number of matching rows (recorded == audited)
        """
        lines = ["ID,Description,Amount,Audited Amount"]
        idx = 1
        for recorded, audited in errors:
            lines.append(f"{idx},Error Item {idx},{recorded},{audited}")
            idx += 1
        for i in range(clean):
            amt = (i + 1) * 100
            lines.append(f"{idx},Clean Item {idx},{amt},{amt}")
            idx += 1
        return "\n".join(lines).encode("utf-8")

    def test_zero_errors_pass(self):
        """All amounts match → pass. Basic precision = interval * factor must < tolerable."""
        csv_data = self._make_evaluation_csv(errors=[], clean=20)
        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=50_000,
        )
        # interval=10000 → basic_precision = 10000 * 3.0 = 30000 < 50000
        result = evaluate_sample(
            csv_data, "sample.csv", config,
            population_value=200_000,
            sample_size=20,
            sampling_interval=10_000,
        )
        assert result.errors_found == 0
        assert result.conclusion == "pass"
        assert result.upper_error_limit > 0  # Basic precision

    def test_one_error_pass(self):
        """Single small error → still pass."""
        csv_data = self._make_evaluation_csv(
            errors=[(10_000, 9_500)],  # $500 misstatement, 5% tainting
            clean=19,
        )
        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=200_000,
        )
        result = evaluate_sample(
            csv_data, "sample.csv", config,
            population_value=1_000_000,
            sample_size=20,
            sampling_interval=50_000,
        )
        assert result.errors_found == 1
        assert result.conclusion == "pass"

    def test_large_errors_fail(self):
        """Large misstatements → fail."""
        csv_data = self._make_evaluation_csv(
            errors=[
                (10_000, 2_000),   # 80% tainting
                (8_000, 1_000),    # 87.5% tainting
            ],
            clean=8,
        )
        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=20_000,
        )
        result = evaluate_sample(
            csv_data, "sample.csv", config,
            population_value=500_000,
            sample_size=10,
            sampling_interval=10_000,
        )
        assert result.errors_found == 2
        assert result.conclusion == "fail"
        assert result.upper_error_limit > 20_000

    def test_random_evaluation(self):
        """Random method uses ratio projection."""
        csv_data = self._make_evaluation_csv(
            errors=[(1_000, 900)],  # $100 misstatement
            clean=19,
        )
        config = SamplingConfig(
            method="random",
            confidence_level=0.95,
            tolerable_misstatement=50_000,
        )
        result = evaluate_sample(
            csv_data, "sample.csv", config,
            population_value=1_000_000,
            sample_size=20,
        )
        assert result.method == "random"
        assert result.errors_found == 1
        assert result.projected_misstatement > 0

    def test_blank_audited_amounts_skipped(self):
        """Rows with blank audited amount are not errors."""
        lines = [
            "ID,Description,Amount,Audited Amount",
            "1,Item 1,1000,1000",
            "2,Item 2,2000,",         # Blank → skip
            "3,Item 3,3000,3000",
        ]
        csv_data = "\n".join(lines).encode("utf-8")

        config = SamplingConfig(method="mus", confidence_level=0.95, tolerable_misstatement=50_000)
        result = evaluate_sample(
            csv_data, "sample.csv", config,
            population_value=100_000, sample_size=3, sampling_interval=10_000,
        )
        assert result.errors_found == 0
