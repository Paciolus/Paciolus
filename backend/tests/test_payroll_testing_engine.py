"""
Payroll Testing Engine Tests — Sprint 491 (Council Remediation)

Stub tests verifying core public API contract for run_payroll_testing().
Exercises: pipeline with valid/empty data, result structure,
and basic missing-fields detection.
"""

from payroll_testing_engine import (
    PayrollTestingResult,
    PayrollTestResult,
    run_payroll_testing,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_payroll_rows() -> tuple[list[str], list[dict]]:
    """Return minimal payroll rows and headers (note: headers first, rows second)."""
    headers = ["Employee Name", "Employee ID", "Gross Pay", "Pay Date", "Department"]
    rows = [
        {
            "Employee Name": "Alice Smith",
            "Employee ID": "E001",
            "Gross Pay": "5000.00",
            "Pay Date": "2025-01-31",
            "Department": "Engineering",
        },
        {
            "Employee Name": "Bob Jones",
            "Employee ID": "E002",
            "Gross Pay": "4500.00",
            "Pay Date": "2025-01-31",
            "Department": "Sales",
        },
        # Missing name + zero pay — should trigger PR-T2
        {"Employee Name": "", "Employee ID": "E003", "Gross Pay": "0", "Pay Date": "2025-01-31", "Department": ""},
    ]
    return headers, rows


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPayrollTestingPipeline:
    """Verify run_payroll_testing returns expected structure with valid data."""

    def test_returns_payroll_testing_result(self):
        headers, rows = _make_payroll_rows()
        result = run_payroll_testing(headers, rows)
        assert isinstance(result, PayrollTestingResult)

    def test_result_has_test_results_list(self):
        headers, rows = _make_payroll_rows()
        result = run_payroll_testing(headers, rows)
        assert isinstance(result.test_results, list)
        assert len(result.test_results) >= 7  # At least 7 tests when no optional columns
        for tr in result.test_results:
            assert isinstance(tr, PayrollTestResult)

    def test_composite_score_fields(self):
        headers, rows = _make_payroll_rows()
        result = run_payroll_testing(headers, rows)
        cs = result.composite_score
        assert 0 <= cs.score <= 100
        assert cs.risk_tier in ("low", "moderate", "elevated", "high")
        assert cs.total_entries == 3
        assert isinstance(cs.flags_by_severity, dict)

    def test_detects_missing_fields(self):
        """Entry with blank name and zero pay should trigger PR-T2."""
        headers, rows = _make_payroll_rows()
        result = run_payroll_testing(headers, rows)
        missing = next(
            (t for t in result.test_results if t.test_key == "PR-T2"),
            None,
        )
        assert missing is not None
        assert missing.entries_flagged > 0

    def test_empty_rows_returns_valid_result(self):
        """Engine should handle empty payroll data gracefully."""
        headers = ["Employee Name", "Gross Pay", "Pay Date"]
        result = run_payroll_testing(headers, [])
        assert isinstance(result, PayrollTestingResult)
        assert result.composite_score.total_entries == 0
        assert result.composite_score.score == 0.0
