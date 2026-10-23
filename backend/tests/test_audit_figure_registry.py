"""
Sprint 805 — findings A-1, A-2 and A-9: the figures registry.

A-9's thesis is that published figures living as bare literals next to a prose
citation are indistinguishable from verified ones, and that both read as cited.
The response is twofold: provenance travels with the value, and anything that is
arithmetically determined by another series is *derived* rather than typed in.

These tests enforce both. The Stringer increments are the first differences of
the Poisson reliability factors, so they are pinned back to the series they come
from — which is the check that would have caught finding A-1 the day the table
was written.
"""

import math

import pytest

from sampling_engine import evaluate_mus_sample_stringer
from shared.audit_figure_registry import (
    EXPANSION_FACTORS,
    POISSON_RELIABILITY_FACTORS,
    FigureSet,
    expansion_factor,
    provenance,
    reliability_factor,
    stringer_increments,
    supported_confidence_levels,
    supported_risks,
)


class TestProvenance:
    """Every figure carries its source, edition and verification stamp."""

    def test_every_figure_set_is_stamped(self):
        for risk, figures in POISSON_RELIABILITY_FACTORS.items():
            assert figures.source, risk
            assert figures.edition, risk
            assert figures.verified_by, risk
            assert figures.verified_on, risk
        assert EXPANSION_FACTORS.verified_by
        assert EXPANSION_FACTORS.verified_on

    def test_an_unstamped_figure_set_cannot_be_constructed(self):
        """The guard, not just the convention."""
        with pytest.raises(ValueError, match="verification stamp"):
            FigureSet(values=(1.0,), source="somewhere", edition="2026", verified_by="", verified_on="")

    def test_an_empty_figure_set_cannot_be_constructed(self):
        with pytest.raises(ValueError, match="at least one value"):
            FigureSet(values=(), source="s", edition="e", verified_by="v", verified_on="2026-01-01")

    def test_provenance_covers_every_figure_set(self):
        entries = provenance()
        assert len(entries) == len(POISSON_RELIABILITY_FACTORS) + 1
        for key, entry in entries.items():
            assert entry["source"], key
            assert entry["verified_on"], key


class TestReliabilityFactorSeries:
    """The published series themselves."""

    def test_the_zero_misstatement_factors_are_the_published_confidence_factors(self):
        assert reliability_factor(0.95) == 3.00
        assert reliability_factor(0.90) == 2.31
        assert reliability_factor(0.99) == 4.61
        assert reliability_factor(0.97) == 3.51
        assert reliability_factor(0.85) == 1.90
        assert reliability_factor(0.80) == 1.61

    def test_every_series_is_strictly_increasing(self):
        for risk, figures in POISSON_RELIABILITY_FACTORS.items():
            values = figures.values
            assert all(values[i] < values[i + 1] for i in range(len(values) - 1)), risk

    def test_a_lower_risk_of_incorrect_acceptance_demands_a_higher_factor(self):
        risks = supported_risks()
        factors = [POISSON_RELIABILITY_FACTORS[r].values[0] for r in risks]
        assert factors == sorted(factors, reverse=True)

    def test_an_untabulated_confidence_level_is_refused(self):
        with pytest.raises(ValueError, match="No published reliability-factor series"):
            reliability_factor(0.93)

    def test_a_count_beyond_the_published_series_is_refused(self):
        series_length = len(POISSON_RELIABILITY_FACTORS[0.05].values)
        with pytest.raises(ValueError, match="published series stops"):
            reliability_factor(0.95, overstatements=series_length)

    def test_supported_levels_round_trip(self):
        for level in supported_confidence_levels():
            assert reliability_factor(level) > 0


class TestStringerIncrementsAreDerived:
    """
    The A-9 check: the increments cannot disagree with the series, because they
    are computed from it. Finding A-1 existed because they had been typed in
    separately and matched neither published series.
    """

    @pytest.mark.parametrize("confidence_level", [0.80, 0.85, 0.90, 0.95, 0.97, 0.99])
    def test_each_increment_is_the_first_difference_of_the_series(self, confidence_level):
        series = POISSON_RELIABILITY_FACTORS[round(1.0 - confidence_level, 10)].values
        increments = stringer_increments(confidence_level)

        assert len(increments) == len(series) - 1
        for i, increment in enumerate(increments):
            assert increment == pytest.approx(series[i + 1] - series[i])

    def test_the_published_95_percent_increments(self):
        """
        Restated independently by the 2026-10-22 review. The shipped table held
        1.58 / 1.30 / 1.15 / 1.06 / 1.00 / 0.95 / 0.92 — neither this series nor
        the 90% one.
        """
        assert [round(x, 2) for x in stringer_increments(0.95)[:7]] == [
            1.75,
            1.55,
            1.46,
            1.40,
            1.36,
            1.33,
            1.30,
        ]

    def test_the_published_90_percent_increments(self):
        """The shipped 90% table held 1.10 / 0.92 / 0.82 / 0.76 / 0.71 / 0.68 / 0.65."""
        assert [round(x, 2) for x in stringer_increments(0.90)[:7]] == [
            1.58,
            1.44,
            1.36,
            1.31,
            1.28,
            1.26,
            1.24,
        ]

    def test_the_99_percent_rank_one_increment_is_not_the_95_percent_one(self):
        """
        A-1's third compounding defect: any confidence level >= 0.95 received the
        95% table, so a 99% engagement used 1.75 where the published figure is 2.03.
        """
        assert round(stringer_increments(0.99)[0], 2) == 2.03
        assert round(stringer_increments(0.95)[0], 2) == 1.75

    @pytest.mark.parametrize("confidence_level", [0.80, 0.85, 0.90, 0.95, 0.97, 0.99])
    def test_every_increment_exceeds_one_and_never_rises(self, confidence_level):
        """
        Why the `max(factor - 1.0, 0.0)` clamp in the engine can never bind once
        the values are right. Every shipped literal from rank 5 onward was
        <= 1.00, which is how the 5th and later misstatements came to contribute
        exactly zero incremental allowance.

        Non-increasing rather than strictly decreasing: the published tables
        carry two decimals, and at 80% / 85% confidence the tail increments tie
        (1.14, 1.14, 1.14 and 1.17, 1.17). That is rounding in the source, not a
        defect — which is also why the engine holds the last published increment
        for ranks beyond the series rather than extrapolating a trend.
        """
        increments = stringer_increments(confidence_level)

        assert all(inc > 1.0 for inc in increments), increments
        assert all(increments[i] >= increments[i + 1] for i in range(len(increments) - 1)), increments


class TestStringerBoundIdentity:
    """
    The arithmetic identity that fixes the *form* of the allowance term, and the
    reason the `- 1.0` is not cosmetic: for a fully-tainted sample the Stringer
    bound must equal `interval x RF(k)` exactly.

        BP        = interval x RF(0)
        projected = k x interval
        allowance = interval x sum(dRF_i - 1) = interval x (RF(k) - RF(0) - k)
        total     = interval x RF(k)
    """

    @pytest.mark.parametrize("count", [1, 2, 3, 5, 8, 10])
    @pytest.mark.parametrize("confidence_level", [0.90, 0.95, 0.99])
    def test_a_fully_tainted_sample_reproduces_the_reliability_factor(self, count, confidence_level):
        from sampling_engine import SampleError

        interval = 10_000.0
        errors = [
            SampleError(
                row_index=i,
                item_id=str(i),
                recorded_amount=interval,
                audited_amount=0.0,
                misstatement=interval,
                tainting=1.0,
            )
            for i in range(count)
        ]
        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=interval,
            confidence_level=confidence_level,
            tolerable_misstatement=10_000_000.0,
            population_value=10_000_000.0,
            sample_size=1000,
        )
        expected = interval * reliability_factor(confidence_level, overstatements=count)
        assert result.upper_error_limit == pytest.approx(expected, rel=1e-9)


class TestMeasuredUpperErrorLimits:
    """
    Reproduces the five rows the review measured, which is where the defect
    changed an audit conclusion: at 22, 24 and 26 misstatements the tool
    reported `pass` where the method it cites reports `fail`.

    Engagement: BV $10,000,000, TM $500,000, EM $100,000, 95% confidence, each
    misstatement tainted 0.10, at the review's measured interval of $86,021.51.
    """

    INTERVAL = 86_021.51
    TOLERABLE = 500_000.0

    # (misstatements, correct Stringer UEL, correct conclusion)
    MEASURED = [
        (20, 486_624, "pass"),
        (22, 508_301, "fail"),
        (24, 529_979, "fail"),
        (26, 551_656, "fail"),
        (28, 573_333, "fail"),
    ]

    @pytest.mark.parametrize(("count", "expected_uel", "expected_conclusion"), MEASURED)
    def test_measured_row(self, count, expected_uel, expected_conclusion):
        from sampling_engine import SampleError

        errors = [
            SampleError(
                row_index=i,
                item_id=str(i),
                recorded_amount=1_000.0,
                audited_amount=900.0,
                misstatement=100.0,
                tainting=0.10,
            )
            for i in range(count)
        ]
        result = evaluate_mus_sample_stringer(
            errors=errors,
            sampling_interval=self.INTERVAL,
            confidence_level=0.95,
            tolerable_misstatement=self.TOLERABLE,
            population_value=10_000_000.0,
            sample_size=117,
        )
        assert result.upper_error_limit == pytest.approx(expected_uel, abs=1.0)
        assert result.conclusion == expected_conclusion

    def test_the_error_was_in_the_unconservative_direction(self):
        """
        The shipped tables understated the upper error limit, which increases the
        risk of incorrect acceptance. Pinned as a property: the correct allowance
        must exceed what the shipped literals produced.
        """
        shipped_literals = [1.58, 1.30, 1.15, 1.06, 1.00, 0.95, 0.92, 0.89, 0.87, 0.85, 0.83]
        correct = stringer_increments(0.95)

        shipped_allowance = math.fsum(max(f - 1.0, 0.0) for f in shipped_literals)
        correct_allowance = math.fsum(inc - 1.0 for inc in correct)
        assert correct_allowance > shipped_allowance


class TestExpansionFactor:
    """A-2: one-dimensional, in risk of incorrect acceptance."""

    def test_published_values(self):
        assert expansion_factor(0.99) == pytest.approx(1.9)
        assert expansion_factor(0.95) == pytest.approx(1.6)
        assert expansion_factor(0.90) == pytest.approx(1.5)
        assert expansion_factor(0.85) == pytest.approx(1.4)
        assert expansion_factor(0.80) == pytest.approx(1.3)

    def test_interpolates_between_tabulated_risks(self):
        """Risk 7.5% sits halfway between 5% (1.6) and 10% (1.5)."""
        assert expansion_factor(0.925) == pytest.approx(1.55)

    def test_clamps_outside_the_tabulated_range(self):
        assert expansion_factor(0.999) == pytest.approx(1.9)
        assert expansion_factor(0.50) == pytest.approx(1.0)

    def test_decreases_as_risk_of_incorrect_acceptance_rises(self):
        factors = [expansion_factor(1.0 - r) for r in (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.37, 0.50)]
        assert factors == sorted(factors, reverse=True)
        assert factors == [1.9, 1.6, 1.5, 1.4, 1.3, 1.25, 1.2, 1.15, 1.0]
