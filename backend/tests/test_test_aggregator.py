"""
Tests for shared/test_aggregator.py — Sprint 152

Tests the parameterized composite score calculation shared across
all testing engines (except Three-Way Match).
"""

import pytest
from dataclasses import dataclass, field
from shared.testing_enums import RiskTier, Severity, score_to_risk_tier
from shared.test_aggregator import (
    CompositeScoreResult,
    calculate_composite_score,
)


# =============================================================================
# MOCK DATACLASSES
# =============================================================================

@dataclass
class MockEntry:
    row_number: int = 0


@dataclass
class MockFlaggedEntry:
    entry: MockEntry = field(default_factory=MockEntry)
    severity: Severity = Severity.LOW


@dataclass
class MockTestResult:
    test_name: str = "Test"
    flag_rate: float = 0.0
    entries_flagged: int = 0
    total_entries: int = 100
    severity: Severity = Severity.LOW
    flagged_entries: list = field(default_factory=list)


def _make_flagged(row: int, severity: Severity = Severity.LOW) -> MockFlaggedEntry:
    return MockFlaggedEntry(entry=MockEntry(row_number=row), severity=severity)


def _make_test_result(
    name: str,
    severity: Severity,
    flagged_rows: list[int],
    total: int = 100,
) -> MockTestResult:
    flagged = [_make_flagged(r, severity) for r in flagged_rows]
    return MockTestResult(
        test_name=name,
        flag_rate=len(flagged_rows) / total if total > 0 else 0.0,
        entries_flagged=len(flagged_rows),
        total_entries=total,
        severity=severity,
        flagged_entries=flagged,
    )


# =============================================================================
# SCORE_TO_RISK_TIER TESTS
# =============================================================================

class TestScoreToRiskTier:
    """Tests for score_to_risk_tier in shared testing_enums."""

    def test_low_tier(self):
        assert score_to_risk_tier(0) == RiskTier.LOW
        assert score_to_risk_tier(5) == RiskTier.LOW
        assert score_to_risk_tier(9.9) == RiskTier.LOW

    def test_elevated_tier(self):
        assert score_to_risk_tier(10) == RiskTier.ELEVATED
        assert score_to_risk_tier(15) == RiskTier.ELEVATED
        assert score_to_risk_tier(24.9) == RiskTier.ELEVATED

    def test_moderate_tier(self):
        assert score_to_risk_tier(25) == RiskTier.MODERATE
        assert score_to_risk_tier(35) == RiskTier.MODERATE
        assert score_to_risk_tier(49.9) == RiskTier.MODERATE

    def test_high_tier(self):
        assert score_to_risk_tier(50) == RiskTier.HIGH
        assert score_to_risk_tier(60) == RiskTier.HIGH
        assert score_to_risk_tier(74.9) == RiskTier.HIGH

    def test_critical_tier(self):
        assert score_to_risk_tier(75) == RiskTier.CRITICAL
        assert score_to_risk_tier(80) == RiskTier.CRITICAL
        assert score_to_risk_tier(100) == RiskTier.CRITICAL


# =============================================================================
# CALCULATE_COMPOSITE_SCORE TESTS
# =============================================================================

class TestCalculateCompositeScore:
    """Tests for the calculate_composite_score function."""

    def test_zero_entries(self):
        """Zero total entries returns empty score."""
        result = calculate_composite_score([], 0)
        assert result.score == 0.0
        assert result.risk_tier == RiskTier.LOW
        assert result.tests_run == 0
        assert result.total_entries == 0
        assert result.total_flagged == 0
        assert result.flag_rate == 0.0

    def test_no_flags(self):
        """Tests with zero flagged entries produce score 0."""
        results = [
            _make_test_result("Test A", Severity.HIGH, [], total=100),
            _make_test_result("Test B", Severity.LOW, [], total=100),
        ]
        result = calculate_composite_score(results, 100)
        assert result.score == 0.0
        assert result.risk_tier == RiskTier.LOW
        assert result.tests_run == 2
        assert result.total_flagged == 0
        assert result.top_findings == []

    def test_standard_scoring_max_possible(self):
        """Standard max_possible normalization produces correct score."""
        results = [
            _make_test_result("High Test", Severity.HIGH, [1, 2, 3], total=100),
            _make_test_result("Low Test", Severity.LOW, [4, 5], total=100),
        ]
        result = calculate_composite_score(results, 100)

        # weighted_sum = (3/100)*3.0 + (2/100)*1.0 = 0.09 + 0.02 = 0.11
        # max_possible = 3.0 + 1.0 = 4.0
        # base_score = 0.11 / 4.0 * 100 = 2.75
        # No multi-flag entries (each flagged by only 1 test)
        # multiplier = 1.0
        # score = 2.75
        assert result.score == pytest.approx(2.75, abs=0.1)
        assert result.risk_tier == RiskTier.LOW
        assert result.total_flagged == 5
        assert result.flag_rate == 0.05

    def test_multi_flag_multiplier(self):
        """Entries flagged by 3+ tests increase the multiplier."""
        # Row 1 flagged by all 3 tests
        results = [
            _make_test_result("Test A", Severity.HIGH, [1], total=10),
            _make_test_result("Test B", Severity.MEDIUM, [1], total=10),
            _make_test_result("Test C", Severity.LOW, [1], total=10),
        ]
        result = calculate_composite_score(results, 10)

        # weighted_sum = (1/10)*3.0 + (1/10)*2.0 + (1/10)*1.0 = 0.3+0.2+0.1 = 0.6
        # max_possible = 3.0 + 2.0 + 1.0 = 6.0
        # base_score = 0.6/6.0 * 100 = 10.0
        # row 1 flagged by 3 tests >= threshold=3
        # multi_flag_count = 1, ratio = 1/10 = 0.1
        # multiplier = 1.0 + 0.1 * 0.25 = 1.025
        # score = 10.0 * 1.025 = 10.25
        assert result.score == pytest.approx(10.25, abs=0.01)

    def test_custom_multi_flag_threshold(self):
        """Custom threshold (e.g., 2) changes which entries trigger multiplier."""
        # Row 1 flagged by 2 tests
        results = [
            _make_test_result("Test A", Severity.HIGH, [1], total=10),
            _make_test_result("Test B", Severity.LOW, [1], total=10),
        ]
        # Default threshold=3: row 1 at 2 tests, no multiplier
        result_default = calculate_composite_score(results, 10, multi_flag_threshold=3)
        # Custom threshold=2: row 1 at 2 tests, triggers multiplier
        result_custom = calculate_composite_score(results, 10, multi_flag_threshold=2)

        assert result_custom.score > result_default.score

    def test_total_entries_normalization(self):
        """Payroll-style normalization: total flags / total entries."""
        results = [
            _make_test_result("Test A", Severity.HIGH, [1, 2], total=100),
            _make_test_result("Test B", Severity.LOW, [3], total=100),
        ]
        result = calculate_composite_score(results, 100, normalization="total_entries")

        # weighted_sum = 2*3.0 + 1*1.0 = 7.0
        # base_score = 7.0 / 100 * 100 = 7.0
        # No multi-flag multiplier
        # score = 7.0
        assert result.score == pytest.approx(7.0, abs=0.01)

    def test_score_capped_at_100(self):
        """Score never exceeds 100.0."""
        # All entries flagged with high severity
        results = [
            _make_test_result("Test A", Severity.HIGH, list(range(1, 11)), total=10),
            _make_test_result("Test B", Severity.HIGH, list(range(1, 11)), total=10),
            _make_test_result("Test C", Severity.HIGH, list(range(1, 11)), total=10),
        ]
        result = calculate_composite_score(results, 10)
        assert result.score <= 100.0

    def test_top_findings_limit(self):
        """Top findings respects top_n parameter."""
        results = [
            _make_test_result(f"Test {i}", Severity.LOW, [i], total=100)
            for i in range(1, 11)
        ]
        result = calculate_composite_score(results, 100, top_n=3)
        assert len(result.top_findings) <= 3

    def test_top_findings_sorted_by_flag_rate(self):
        """Findings are sorted by flag_rate descending."""
        results = [
            _make_test_result("Low Rate", Severity.LOW, [1], total=100),
            _make_test_result("High Rate", Severity.LOW, list(range(1, 51)), total=100),
        ]
        result = calculate_composite_score(results, 100)
        assert result.top_findings[0].startswith("High Rate")

    def test_flags_by_severity(self):
        """Flags are correctly counted by severity."""
        results = [
            _make_test_result("Test A", Severity.HIGH, [1, 2], total=100),
            _make_test_result("Test B", Severity.LOW, [3, 4, 5], total=100),
        ]
        result = calculate_composite_score(results, 100)
        assert result.flags_by_severity["high"] == 2
        assert result.flags_by_severity["low"] == 3
        assert result.flags_by_severity["medium"] == 0

    def test_entity_label(self):
        """Entity label appears in top_findings strings."""
        results = [
            _make_test_result("Test A", Severity.HIGH, [1], total=10),
        ]
        result = calculate_composite_score(results, 10, entity_label="payments")
        assert "payments flagged" in result.top_findings[0]

    def test_custom_row_accessor(self):
        """Custom row accessor for engines using different row identifiers."""
        @dataclass
        class PayrollEntry:
            _row_index: int = 0

        @dataclass
        class PayrollFlagged:
            entry: PayrollEntry = field(default_factory=PayrollEntry)
            severity: str = "low"

        @dataclass
        class PayrollTestResult:
            test_name: str = "Test"
            flag_rate: float = 0.0
            entries_flagged: int = 0
            total_entries: int = 10
            severity: str = "high"
            flagged_entries: list = field(default_factory=list)

        flagged = [
            PayrollFlagged(entry=PayrollEntry(_row_index=1), severity="high"),
            PayrollFlagged(entry=PayrollEntry(_row_index=2), severity="high"),
        ]
        results = [PayrollTestResult(
            test_name="PR-T1",
            flag_rate=0.2,
            entries_flagged=2,
            flagged_entries=flagged,
            severity="high",
        )]

        result = calculate_composite_score(
            results, 10,
            row_accessor=lambda fe: fe.entry._row_index,
            severity_accessor=lambda fe: fe.severity,
            test_severity_accessor=lambda tr: tr.severity,
        )
        assert result.total_flagged == 2
        assert result.score > 0

    def test_to_dict_shape(self):
        """to_dict returns correct structure."""
        results = [_make_test_result("Test", Severity.LOW, [1], total=10)]
        result = calculate_composite_score(results, 10)
        d = result.to_dict()

        assert "score" in d
        assert "risk_tier" in d
        assert "tests_run" in d
        assert "total_entries" in d
        assert "total_flagged" in d
        assert "flag_rate" in d
        assert "flags_by_severity" in d
        assert "top_findings" in d
        assert isinstance(d["risk_tier"], str)

    def test_invalid_normalization_raises(self):
        """Invalid normalization mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown normalization"):
            calculate_composite_score([], 10, normalization="invalid")

    def test_tests_with_zero_flagged_excluded_from_findings(self):
        """Tests with no flagged entries don't appear in findings."""
        results = [
            _make_test_result("Flagged", Severity.HIGH, [1], total=10),
            _make_test_result("Clean", Severity.HIGH, [], total=10),
        ]
        result = calculate_composite_score(results, 10)
        assert len(result.top_findings) == 1
        assert result.top_findings[0].startswith("Flagged")

    def test_flag_rate_calculation(self):
        """Overall flag rate = unique flagged rows / total entries."""
        # 3 unique rows flagged across 2 tests (row 1 appears in both)
        results = [
            _make_test_result("Test A", Severity.HIGH, [1, 2], total=100),
            _make_test_result("Test B", Severity.LOW, [1, 3], total=100),
        ]
        result = calculate_composite_score(results, 100)
        # Unique rows: {1, 2, 3} = 3
        assert result.total_flagged == 3
        assert result.flag_rate == pytest.approx(0.03, abs=0.001)
