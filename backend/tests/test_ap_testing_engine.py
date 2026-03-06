"""
AP Testing Engine Tests — Sprint 491 (Council Remediation)

Stub tests verifying core public API contract for run_ap_testing().
Exercises: instantiation with valid/empty data, result structure,
and basic duplicate payment detection.
"""

from ap_testing_engine import (
    APTestingResult,
    APTestResult,
    run_ap_testing,
)
from shared.testing_enums import RiskTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ap_rows() -> tuple[list[dict], list[str]]:
    """Return minimal AP payment rows and column names."""
    columns = ["Vendor Name", "Amount", "Payment Date", "Invoice Number"]
    rows = [
        {"Vendor Name": "Acme Corp", "Amount": "1500.00", "Payment Date": "2025-01-15", "Invoice Number": "INV-001"},
        {"Vendor Name": "Beta LLC", "Amount": "2500.00", "Payment Date": "2025-02-10", "Invoice Number": "INV-002"},
        {"Vendor Name": "Acme Corp", "Amount": "1500.00", "Payment Date": "2025-01-15", "Invoice Number": "INV-001"},
    ]
    return rows, columns


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAPTestingPipeline:
    """Verify run_ap_testing returns expected structure with valid data."""

    def test_returns_ap_testing_result(self):
        rows, columns = _make_ap_rows()
        result = run_ap_testing(rows, columns)
        assert isinstance(result, APTestingResult)

    def test_result_has_test_results_list(self):
        rows, columns = _make_ap_rows()
        result = run_ap_testing(rows, columns)
        assert isinstance(result.test_results, list)
        assert len(result.test_results) == 13  # AP-T1 through AP-T13
        for tr in result.test_results:
            assert isinstance(tr, APTestResult)

    def test_composite_score_fields(self):
        rows, columns = _make_ap_rows()
        result = run_ap_testing(rows, columns)
        cs = result.composite_score
        assert 0 <= cs.score <= 100
        assert isinstance(cs.risk_tier, RiskTier)
        assert cs.tests_run == 13
        assert cs.total_entries > 0
        assert isinstance(cs.flags_by_severity, dict)

    def test_detects_duplicate_payment(self):
        """Two payments to same vendor, same amount, same invoice => flagged."""
        rows, columns = _make_ap_rows()
        result = run_ap_testing(rows, columns)
        dup_test = next(
            (t for t in result.test_results if t.test_key == "exact_duplicate_payments"),
            None,
        )
        assert dup_test is not None
        assert dup_test.entries_flagged > 0

    def test_empty_rows_returns_valid_result(self):
        """Engine should handle empty payment list gracefully."""
        result = run_ap_testing([], ["Vendor Name", "Amount", "Payment Date"])
        assert isinstance(result, APTestingResult)
        assert result.composite_score.total_entries == 0
        assert result.composite_score.risk_tier == RiskTier.LOW
