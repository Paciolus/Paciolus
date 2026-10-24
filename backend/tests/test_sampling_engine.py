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

    def test_untabulated_level_is_refused_not_snapped(self):
        """
        Sprint 805 (finding A-1). This used to snap to the nearest tabulated
        level, which is how a 97% or 99% engagement came to be planned and
        evaluated on 95% figures — the published 99% rank-1 increment is 2.03
        against 95%'s 1.75. Substituting the nearest table misstates the upper
        error limit, so the engine now refuses.
        """
        with pytest.raises(ValueError, match="No published reliability-factor series"):
            get_confidence_factor(0.93)

    def test_every_tabulated_level_keeps_its_own_factor(self):
        """97% and 99% must not resolve to the 95% factor."""
        assert get_confidence_factor(0.97) == 3.51
        assert get_confidence_factor(0.99) == 4.61
        assert get_confidence_factor(0.95) == 3.00
        assert len({get_confidence_factor(lvl) for lvl in (0.90, 0.95, 0.97, 0.99)}) == 4

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
# Sprint 684: AICPA Table A-1 expansion factors
# ═══════════════════════════════════════════════════════════════


class TestSprint805ExpansionFactor:
    """
    Sprint 805 (finding A-2) replaced Sprint 684's two-dimensional expansion
    factor table.

    The published AICPA expansion factor depends on the **risk of incorrect
    acceptance alone** — 1.9 / 1.6 / 1.5 / 1.4 / 1.3 / 1.25 / 1.2 / 1.15 / 1.0
    for 1%…50% — and it scales *expected misstatement* in the denominator:

        n = BV x RF / (TM - EM x EF)

    Sprint 684 had tabulated it by `(confidence_level, expected/tolerable)`,
    rising to 3.00, and multiplied it into the reliability factor. Sample sizes
    ran up to 1.40x the size the standard requires. Conservative, so no audit
    conclusion was endangered — but the client paid for up to 40% more items
    than the method calls for, under a citation that does not support the figure.

    The tests this class replaces asserted the two-dimensional values, so they
    are not adjusted: they were pinning the defect.
    """

    def test_expansion_factor_depends_only_on_risk_of_incorrect_acceptance(self):
        from shared.aicpa_tables import expansion_factor

        assert expansion_factor(0.99) == pytest.approx(1.9)
        assert expansion_factor(0.95) == pytest.approx(1.6)
        assert expansion_factor(0.90) == pytest.approx(1.5)
        assert expansion_factor(0.85) == pytest.approx(1.4)
        assert expansion_factor(0.80) == pytest.approx(1.3)

    def test_expansion_factor_does_not_vary_with_expected_over_tolerable(self):
        """
        The defect, asserted directly: the expected/tolerable ratio is not an
        input to the published table. The signature no longer accepts it.
        """
        import inspect

        from shared.aicpa_tables import expansion_factor

        params = inspect.signature(expansion_factor).parameters
        assert list(params) == ["confidence_level"]

    def test_sample_size_matches_the_published_aicpa_formula(self):
        """
        Reproduces the review's measured table. Pre-fix, the product returned
        70 / 84 / 140 / 360 against the AICPA formula's 66 / 72 / 100 / 300.
        """
        import math

        from shared.audit_figure_registry import expansion_factor, reliability_factor

        population, tolerable = 10_000_000.0, 500_000.0
        for ratio, expected_n in ((0.05, 66), (0.10, 72), (0.25, 100), (0.50, 300)):
            expected_misstatement = tolerable * ratio
            size, _interval, _cf = calculate_mus_sample_size(
                confidence_level=0.95,
                tolerable_misstatement=tolerable,
                expected_misstatement=expected_misstatement,
                population_value=population,
            )
            formula_n = math.ceil(
                population * reliability_factor(0.95) / (tolerable - expected_misstatement * expansion_factor(0.95))
            )
            assert size == formula_n == expected_n, f"e/TM={ratio}: got {size}, AICPA {formula_n}"

    def test_the_expansion_factor_scales_expected_misstatement_not_the_reliability_factor(self):
        """
        Structural. The interval must be `(TM - EM x EF) / RF`. Under Sprint
        684's placement it was `(TM - EM) / (RF x EF)`, which is a different
        number for every non-zero expected misstatement.
        """
        _size, interval, cf = calculate_mus_sample_size(
            confidence_level=0.95,
            tolerable_misstatement=500_000,
            expected_misstatement=100_000,
            population_value=10_000_000,
        )
        assert interval == pytest.approx((500_000 - 100_000 * 1.6) / 3.0)
        # And emphatically not the Sprint 684 placement.
        assert interval != pytest.approx((500_000 - 100_000) / (3.0 * 1.6))
        assert cf == 3.0

    def test_zero_expected_misstatement_leaves_tolerable_untouched(self):
        _size, interval, _cf = calculate_mus_sample_size(
            confidence_level=0.95,
            tolerable_misstatement=100_000,
            expected_misstatement=0,
            population_value=1_000_000,
        )
        assert interval == pytest.approx(100_000 / 3.0)


# ═══════════════════════════════════════════════════════════════
# Sprint 684: Negative-balance MUS rejection
# ═══════════════════════════════════════════════════════════════


class TestSprint684NegativeBalanceRejection:
    """Sprint 684: MUS excludes negative-balance items (AICPA §5.06).

    Returns a third tuple element with the excluded items so the memo
    can disclose the stratification decision to the auditor.
    """

    def test_negative_items_excluded_from_selection(self):
        items = _make_items([1000, 2000, -500, 3000, -1500, 4000])
        selected, _start, negatives = select_mus_sample(items, sampling_interval=2_000, random_start=500)
        # Two negative items should be excluded from selection.
        assert len(negatives) == 2
        # No selected item has a negative amount.
        assert all(s.item.recorded_amount >= 0 for s in selected)

    def test_all_positive_returns_empty_negative_list(self):
        items = _make_items([1000, 2000, 3000])
        _selected, _start, negatives = select_mus_sample(items, sampling_interval=1_000, random_start=500)
        assert negatives == []


# ═══════════════════════════════════════════════════════════════
# MUS Selection
# ═══════════════════════════════════════════════════════════════


class TestMUSSelection:
    """Test MUS interval-based selection."""

    def test_basic_selection_count(self):
        """Selection should produce approximately expected count."""
        items = _make_items([1000] * 100)  # 100 items, $1000 each = $100K
        interval = 10_000  # Should select ~10 items
        selected, start, _neg = select_mus_sample(items, interval, random_start=5000)
        assert len(selected) >= 8
        assert len(selected) <= 12

    def test_deterministic_with_fixed_start(self):
        """Same random start produces same selection."""
        items = _make_items([500, 1000, 1500, 2000, 2500])
        sel1, _, _ = select_mus_sample(items, 2000, random_start=500)
        sel2, _, _ = select_mus_sample(items, 2000, random_start=500)
        ids1 = [s.item.row_index for s in sel1]
        ids2 = [s.item.row_index for s in sel2]
        assert ids1 == ids2

    def test_no_duplicates(self):
        """Same item should not appear twice in selection."""
        items = _make_items([100] * 50)
        selected, _, _ = select_mus_sample(items, 500)
        row_indices = [s.item.row_index for s in selected]
        assert len(row_indices) == len(set(row_indices))

    def test_large_item_always_selected(self):
        """An item larger than the interval is always selected."""
        items = _make_items([100, 200, 50_000, 300])
        selected, _, _ = select_mus_sample(items, 5000, random_start=100)
        selected_amounts = [s.item.recorded_amount for s in selected]
        assert 50_000 in selected_amounts

    def test_zero_amount_items_skipped(self):
        """Items with zero amount are skipped."""
        items = _make_items([0, 0, 1000, 0, 2000])
        selected, _, _ = select_mus_sample(items, 500)
        for s in selected:
            assert s.item.recorded_amount != 0

    def test_invalid_interval(self):
        with pytest.raises(ValueError, match="Sampling interval must be positive"):
            select_mus_sample([], 0)

    def test_full_population_when_interval_tiny(self):
        """When interval is very small, most items get selected."""
        items = _make_items([1000, 2000, 3000, 4000, 5000])
        selected, _, _ = select_mus_sample(items, 1.0, random_start=0.5)
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
        errors = [
            SampleError(
                row_index=1,
                item_id="1",
                recorded_amount=5_000,  # below the interval: a sampled item (Sprint 824)
                audited_amount=2_500,
                misstatement=2_500,
                tainting=0.5,
            )
        ]
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
        # Sprint 805 (A-1): the rank-1 increment is the first difference of the
        # published 95% Poisson series, 4.75 - 3.00 = 1.75 — not the 1.58 that
        # was tabulated here, which is the *90%* rank-1 increment.
        # Incremental = 0.5 * 10000 * (1.75 - 1.0) = 3750
        assert abs(result.incremental_allowance - 3_750) < 1
        # UEL = 30000 + 5000 + 3750 = 38750
        assert abs(result.upper_error_limit - 38_750) < 1
        assert result.conclusion == "pass"  # 38750 < 50000

    def test_multiple_errors_fail(self):
        """Multiple errors push UEL above tolerable."""
        errors = [
            SampleError(1, "1", 5_000, 1_000, 4_000, 0.8),
            SampleError(2, "2", 5_000, 1_500, 3_500, 0.7),
            SampleError(3, "3", 5_000, 2_500, 2_500, 0.5),
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
            SampleError(1, "1", 5_000, 4_000, 1_000, 0.2),
            SampleError(2, "2", 5_000, 1_000, 4_000, 0.8),
            SampleError(3, "3", 5_000, 2_500, 2_500, 0.5),
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
        errors = [
            SampleError(
                row_index=1,
                item_id="1",
                recorded_amount=5_000,
                audited_amount=0,
                misstatement=5_000,
                tainting=1.0,
            )
        ]
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
        hv_selected = [s for s in result.selected_items if s.selection_method == "high_value_100pct"]
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
            csv_data,
            "sample.csv",
            config,
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
            csv_data,
            "sample.csv",
            config,
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
                (10_000, 2_000),  # 80% tainting
                (8_000, 1_000),  # 87.5% tainting
            ],
            clean=8,
        )
        config = SamplingConfig(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=20_000,
        )
        result = evaluate_sample(
            csv_data,
            "sample.csv",
            config,
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
            csv_data,
            "sample.csv",
            config,
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
            "2,Item 2,2000,",  # Blank → skip
            "3,Item 3,3000,3000",
        ]
        csv_data = "\n".join(lines).encode("utf-8")

        config = SamplingConfig(method="mus", confidence_level=0.95, tolerable_misstatement=50_000)
        result = evaluate_sample(
            csv_data,
            "sample.csv",
            config,
            population_value=100_000,
            sample_size=3,
            sampling_interval=10_000,
        )
        assert result.errors_found == 0


class TestSprint824Evaluation:
    """Sprint 823 discovery findings S1, S2, S4, S5, S7, S8."""

    def test_top_stratum_error_counts_its_actual_misstatement(self):
        """S1: a $250,000 item at a $70,000 interval is examined, not sampled.
        Its $50,000 error is added as-is — projecting it as tainting x interval
        ($14,000 + allowance) reported $234,500 "pass" against $250,000 TM."""
        errors = [SampleError(1, "BIG", 250_000, 200_000, 50_000, 0.2)]
        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=70_000,
            confidence_level=0.95,
            tolerable_misstatement=250_000,
            population_value=5_000_000,
            sample_size=72,
        )
        assert result.basic_precision == pytest.approx(210_000)
        assert result.projected_misstatement == pytest.approx(50_000)
        assert result.incremental_allowance == 0.0
        assert result.upper_error_limit == pytest.approx(260_000)
        assert result.conclusion == "fail"
        assert result.taintings_ranked == []

    def test_mus_echoes_the_expected_misstatement_it_was_given(self):
        """S8: the MUS result always reported expected_misstatement 0.0."""
        result = evaluate_mus_sample_stringer(
            errors=[],
            sampling_interval=70_000,
            confidence_level=0.95,
            tolerable_misstatement=250_000,
            population_value=5_000_000,
            sample_size=72,
            expected_misstatement=25_000,
        )
        assert result.expected_misstatement == 25_000

    @staticmethod
    def _evaluate(csv: str, method: str = "mus"):
        from sampling_engine import evaluate_sample

        config = SamplingConfig(method=method, confidence_level=0.95, tolerable_misstatement=250_000)
        return evaluate_sample(csv.encode(), "sample.csv", config, 5_000_000, 4, sampling_interval=70_000)

    def test_sample_value_covers_the_whole_evaluated_sample(self):
        """S2/S7: sample value and the random ratio used only the error rows."""
        csv = "item_id,recorded_amount,audited_amount\nA,8372,7372\nB,50000,50000\nC,40000,40000\nD,1628,1628\n"
        mus = self._evaluate(csv)
        assert mus.sample_value == pytest.approx(100_000)

        random_result = self._evaluate(csv, method="random")
        assert random_result.sample_value == pytest.approx(100_000)
        # 1,000 / 100,000 of a $5M population — not 1,000 / 8,372 of it.
        assert random_result.projected_misstatement == pytest.approx(50_000)

    @pytest.mark.parametrize("audited", ["see note", "Infinity", "-infinity"])
    def test_unreadable_audited_amount_is_unassessed_not_a_full_misstatement(self, audited):
        """S4/S5: these became $0 (a 100% misstatement) or Decimal('Infinity')."""
        csv = f'item_id,recorded_amount,audited_amount\nA,4000,{audited}\nB,"$5,000.00",5000\n'
        result = self._evaluate(csv)
        assert result.errors_found == 0
        assert result.skipped_missing_audited == 1
        assert result.evaluated_count == 1

    @pytest.mark.parametrize("method", ["mus", "random"])
    def test_a_sample_with_nothing_assessable_is_refused_not_passed(self, method):
        """PR #205 review: with every audited amount unreadable, both methods
        evaluated an empty sample and concluded "pass"."""
        with pytest.raises(ValueError, match="No sample item could be evaluated"):
            self._evaluate("item_id,recorded_amount,audited_amount\nA,50000,see note\n", method=method)


class TestSprint825Methodology:
    """Sprint 825 — CEO methodology decision on findings S3 and S6
    (reports/sprint-823-discovery-2026-10-23.md): the tool must never report
    more assurance than the data supports."""

    @staticmethod
    def _csv(rows: list[tuple]) -> bytes:
        """rows: (recorded, audited); audited may be '' for an unassessed item."""
        lines = ["item_id,recorded_amount,audited_amount"]
        lines += [f"R{i},{rec},{aud}" for i, (rec, aud) in enumerate(rows, 1)]
        return "\n".join(lines).encode()

    def _random(self, rows, *, sample_size, tm=50_000, population_value=1_000_000):
        config = SamplingConfig(method="random", confidence_level=0.95, tolerable_misstatement=tm)
        return evaluate_sample(self._csv(rows), "s.csv", config, population_value, sample_size)

    # ── S3: zero-error samples ──────────────────────────────────

    def test_s3_small_clean_random_sample_fails(self):
        """S3. Population $1,000,000, TM $50,000, 95% (zero-error confidence
        factor 3.00), 20 items tested, no misstatements.

        Basic precision = population x CF / n = 1,000,000 x 3.00 / 20 = $150,000.
        UEL = $150,000 > TM $50,000 -> fail.

        Before Sprint 825: precision = projected x CF / sqrt(n) = 0 x ... = $0,
        so the result was UEL $0, "pass"."""
        result = self._random([(1_000, 1_000)] * 20, sample_size=20)
        assert result.errors_found == 0
        assert result.basic_precision == pytest.approx(150_000)
        assert result.upper_error_limit == pytest.approx(150_000)
        assert result.understatement_upper_error_limit == pytest.approx(150_000)
        assert result.conclusion == "fail"

    def test_s3_clean_sample_of_the_designed_size_passes(self):
        """S3. The same engagement's designed random sample size is
        n = BV x CF / TM = 1,000,000 x 3.00 / 50,000 = 60. A clean sample of
        60 gives basic precision 1,000,000 x 3.00 / 60 = $50,000 = TM -> pass
        (the engine passes at UEL <= TM)."""
        n, _, _ = calculate_mus_sample_size(0.95, 50_000, 0, 1_000_000)
        assert n == 60
        result = self._random([(1_000, 1_000)] * 60, sample_size=60)
        assert result.basic_precision == pytest.approx(50_000)
        assert result.conclusion == "pass"

    def test_s3_a_clean_sample_of_5_does_not_read_like_one_of_200(self):
        five = self._random([(1_000, 1_000)] * 5, sample_size=5)
        two_hundred = self._random([(1_000, 1_000)] * 200, sample_size=200)
        # 1,000,000 x 3 / 5 and 1,000,000 x 3 / 200
        assert five.upper_error_limit == pytest.approx(600_000)
        assert two_hundred.upper_error_limit == pytest.approx(15_000)

    def test_s3_unassessed_items_give_no_assurance(self):
        """Paciolus convention: n = min(sample size, items evaluated). 60
        selected, 40 unassessed -> n = 20 -> 1,000,000 x 3 / 20 = $150,000."""
        rows = [(1_000, 1_000)] * 20 + [(1_000, "")] * 40
        result = self._random(rows, sample_size=60)
        assert result.evaluated_count == 20
        assert result.basic_precision == pytest.approx(150_000)
        assert result.conclusion == "fail"

    def test_s3_mus_zero_error_basic_precision_on_both_sides(self):
        """MUS already reported basic precision for a clean sample (AICPA Audit
        Sampling Guide: CF(0) x interval = 3.00 x 10,000 = $30,000); it now
        appears in both directions' limits."""
        result = evaluate_mus_sample_stringer([], 10_000, 0.95, 50_000, 600_000, 60)
        assert result.upper_error_limit == pytest.approx(30_000)
        assert result.understatement_upper_error_limit == pytest.approx(30_000)

    # ── S6: understatements ─────────────────────────────────────

    def test_s6_random_understatement_is_not_netted_against_overstatement(self):
        """S6. 10 items, $100,000 sample value, population $1,000,000, 95%.
        One $1,000 overstatement and one $1,000 understatement.

        Per direction:
          BP        = 1,000,000 x 3.00 / 10            = $300,000.00
          projected = 1,000 / 100,000 x 1,000,000      =  $10,000.00
          allowance = 10,000 x 3.00 / sqrt(10)         =   $9,486.83
          UEL       = 300,000 + 10,000 + 9,486.83      = $319,486.83  > TM $315,000 -> fail

        Before Sprint 825 the ratio used abs(1,000 - 1,000) = 0: projected $0,
        UEL $0, "pass"."""
        rows = [(10_000, 9_000), (10_000, 11_000)] + [(10_000, 10_000)] * 8
        result = self._random(rows, sample_size=10, tm=315_000)
        assert result.total_misstatement == pytest.approx(0)
        assert result.total_overstatement == pytest.approx(1_000)
        assert result.total_understatement == pytest.approx(1_000)
        assert result.projected_misstatement == pytest.approx(10_000)
        assert result.understatement_projected_misstatement == pytest.approx(10_000)
        assert result.upper_error_limit == pytest.approx(319_486.83, abs=0.01)
        assert result.understatement_upper_error_limit == pytest.approx(319_486.83, abs=0.01)
        assert result.conclusion == "fail"

    def test_s6_mus_understatement_has_its_own_uncapped_bound_and_can_fail(self):
        """S6. Interval $10,000, TM $50,000, 95%. One item recorded $1,000,
        audited $3,000: understated by $2,000, tainting 200% (not capped).

        Understatement UEL = BP 30,000 + projected 2.0 x 10,000 (20,000)
                             + allowance 2.0 x 10,000 x (1.75 - 1) (15,000) = $65,000 -> fail.
        Overstatement UEL  = BP 30,000 (no overstatements).

        Before Sprint 825 the item was scored as a 100% *overstatement*:
        30,000 + 10,000 + 7,500 = $47,500, "pass"."""
        rows = [(1_000, 3_000)] + [(500, 500)] * 19
        config = SamplingConfig(method="mus", confidence_level=0.95, tolerable_misstatement=50_000)
        result = evaluate_sample(self._csv(rows), "s.csv", config, 600_000, 20, sampling_interval=10_000)
        assert result.errors[0].tainting == pytest.approx(2.0)
        assert result.taintings_ranked == []
        assert result.understatement_taintings_ranked == [pytest.approx(2.0)]
        assert result.upper_error_limit == pytest.approx(30_000)
        assert result.understatement_upper_error_limit == pytest.approx(65_000)
        assert result.conclusion == "fail"
        assert "understatement upper limit exceeds" in result.conclusion_detail

    def test_s6_mus_directions_are_ranked_and_bounded_separately(self):
        """One 50% overstatement and one 50% understatement at a $10,000
        interval: each side is 30,000 + 5,000 + 3,750 = $38,750. Before Sprint
        825 both entered one ranking: 30,000 + 10,000 + 3,750 + 2,750 = $46,500."""
        errors = [
            SampleError(1, "O", 5_000, 2_500, 2_500, 0.5),
            SampleError(2, "U", 5_000, 7_500, -2_500, 0.5),
        ]
        result = evaluate_mus_sample_stringer(errors, 10_000, 0.95, 50_000, 600_000, 60)
        assert result.taintings_ranked == [0.5]
        assert result.understatement_taintings_ranked == [0.5]
        assert result.upper_error_limit == pytest.approx(38_750)
        assert result.understatement_upper_error_limit == pytest.approx(38_750)
        assert (result.overstatement_errors_found, result.understatement_errors_found) == (1, 1)
        assert result.conclusion == "pass"

    def test_s6_top_stratum_understatement_stays_on_its_own_side(self):
        """A $250,000 item audited at $300,000 (interval $70,000) adds its
        actual $50,000 to the understatement limit only: 210,000 + 50,000."""
        errors = [SampleError(1, "BIG", 250_000, 300_000, -50_000, 0.2)]
        result = evaluate_mus_sample_stringer(errors, 70_000, 0.95, 250_000, 5_000_000, 72)
        assert result.upper_error_limit == pytest.approx(210_000)
        assert result.understatement_upper_error_limit == pytest.approx(260_000)
        assert result.conclusion == "fail"

    def test_s6_overstatement_tainting_is_still_capped(self):
        rows = [(1_000, -500)] + [(500, 500)] * 4
        config = SamplingConfig(method="mus", confidence_level=0.95, tolerable_misstatement=50_000)
        result = evaluate_sample(self._csv(rows), "s.csv", config, 600_000, 5, sampling_interval=10_000)
        assert result.errors[0].tainting == pytest.approx(1.0)

    def test_route_serialises_both_bounds_through_the_response_model(self):
        """The new fields reach the API response; the legacy fields keep their
        meaning (the overstatement side)."""
        from routes.sampling import _run_evaluation
        from shared.testing_response_schemas import SamplingEvaluationResponse

        rows = [(10_000, 9_000), (10_000, 11_000)] + [(10_000, 10_000)] * 8
        payload = _run_evaluation(self._csv(rows), "s.csv", "random", 0.95, 315_000, 0, 1_000_000, 10, None, None)
        resp = SamplingEvaluationResponse(**payload)
        assert resp.upper_error_limit == pytest.approx(319_486.83, abs=0.01)
        assert resp.understatement_upper_error_limit == pytest.approx(319_486.83, abs=0.01)
        assert resp.understatement_errors_found == 1
        assert resp.conclusion == "fail"
