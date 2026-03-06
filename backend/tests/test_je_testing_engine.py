"""
JE Testing Engine Tests — Sprint 491 (Council Remediation)

Stub tests verifying core public API contract for run_je_testing().
Exercises: pipeline with valid/empty data, result structure,
and basic unbalanced entry detection.
"""

from je_testing_engine import (
    JETestingResult,
    TestResult,
    run_je_testing,
)
from shared.testing_enums import RiskTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_gl_rows() -> tuple[list[dict], list[str]]:
    """Return minimal GL rows with a balanced and an unbalanced entry."""
    columns = ["Entry ID", "Date", "Account", "Debit", "Credit", "Description"]
    rows = [
        # Balanced entry (JE-001)
        {
            "Entry ID": "JE-001",
            "Date": "2025-03-01",
            "Account": "Cash",
            "Debit": "1000.00",
            "Credit": "0",
            "Description": "Receipt",
        },
        {
            "Entry ID": "JE-001",
            "Date": "2025-03-01",
            "Account": "Revenue",
            "Debit": "0",
            "Credit": "1000.00",
            "Description": "Receipt",
        },
        # Unbalanced entry (JE-002): debit 500, credit 300
        {
            "Entry ID": "JE-002",
            "Date": "2025-03-02",
            "Account": "Supplies",
            "Debit": "500.00",
            "Credit": "0",
            "Description": "Purchase",
        },
        {
            "Entry ID": "JE-002",
            "Date": "2025-03-02",
            "Account": "AP",
            "Debit": "0",
            "Credit": "300.00",
            "Description": "Purchase",
        },
    ]
    return rows, columns


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestJETestingPipeline:
    """Verify run_je_testing returns expected structure with valid data."""

    def test_returns_je_testing_result(self):
        rows, columns = _make_gl_rows()
        result = run_je_testing(rows, columns)
        assert isinstance(result, JETestingResult)

    def test_result_has_test_results_list(self):
        rows, columns = _make_gl_rows()
        result = run_je_testing(rows, columns)
        assert isinstance(result.test_results, list)
        assert len(result.test_results) >= 19  # T1 through T19
        for tr in result.test_results:
            assert isinstance(tr, TestResult)

    def test_composite_score_fields(self):
        rows, columns = _make_gl_rows()
        result = run_je_testing(rows, columns)
        cs = result.composite_score
        assert 0 <= cs.score <= 100
        assert isinstance(cs.risk_tier, RiskTier)
        assert cs.tests_run >= 19
        assert cs.total_entries == 4
        assert isinstance(cs.flags_by_severity, dict)

    def test_detects_unbalanced_entry(self):
        """JE-002 has debit 500 vs credit 300 — should be flagged."""
        rows, columns = _make_gl_rows()
        result = run_je_testing(rows, columns)
        unbalanced = next(
            (t for t in result.test_results if t.test_key == "unbalanced_entries"),
            None,
        )
        assert unbalanced is not None
        assert unbalanced.entries_flagged > 0

    def test_empty_rows_returns_valid_result(self):
        """Engine should handle empty GL data gracefully."""
        result = run_je_testing([], ["Date", "Account", "Debit", "Credit"])
        assert isinstance(result, JETestingResult)
        assert result.composite_score.total_entries == 0
        assert result.composite_score.risk_tier == RiskTier.LOW
