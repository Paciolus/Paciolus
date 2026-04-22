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
        # Sprint 682: AP-T14 Invoice Without PO added. 14 total slots; the
        # new test emits a skipped result when no PO column is detected
        # so the count is stable across PO/non-PO fixtures.
        assert len(result.test_results) == 14  # AP-T1 through AP-T14
        for tr in result.test_results:
            assert isinstance(tr, APTestResult)

    def test_composite_score_fields(self):
        rows, columns = _make_ap_rows()
        result = run_ap_testing(rows, columns)
        cs = result.composite_score
        assert 0 <= cs.score <= 100
        assert isinstance(cs.risk_tier, RiskTier)
        assert cs.tests_run == 14  # Sprint 682: AP-T14 added
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


# ---------------------------------------------------------------------------
# Sprint 643: Duplicate Payment Recovery Summary
# ---------------------------------------------------------------------------


class TestDuplicatePaymentSummary:
    """Sprint 643: recovery value, vendor-level duplicate rate, monthly trend."""

    def _rows_with_fuzzy_and_exact(self) -> tuple[list[dict], list[str]]:
        columns = ["Vendor Name", "Amount", "Payment Date", "Invoice Number"]
        rows = [
            # Exact dup pair — Acme, INV-001, $1,500, same date
            {
                "Vendor Name": "Acme Corp",
                "Amount": "1500.00",
                "Payment Date": "2025-01-15",
                "Invoice Number": "INV-001",
            },
            {
                "Vendor Name": "Acme Corp",
                "Amount": "1500.00",
                "Payment Date": "2025-01-15",
                "Invoice Number": "INV-001",
            },
            # Fuzzy pair — Acme, $900, different dates within window
            {"Vendor Name": "Acme Corp", "Amount": "900.00", "Payment Date": "2025-02-10", "Invoice Number": "INV-005"},
            {"Vendor Name": "Acme Corp", "Amount": "900.00", "Payment Date": "2025-02-14", "Invoice Number": "INV-006"},
            # Clean row
            {"Vendor Name": "Beta LLC", "Amount": "2500.00", "Payment Date": "2025-03-01", "Invoice Number": "INV-010"},
        ]
        return rows, columns

    def test_summary_present_on_result(self):
        rows, columns = self._rows_with_fuzzy_and_exact()
        result = run_ap_testing(rows, columns)
        assert result.duplicate_payment_summary is not None
        assert "recovery_value_total" in result.duplicate_payment_summary
        assert "vendor_rates" in result.duplicate_payment_summary
        assert "monthly_trend" in result.duplicate_payment_summary

    def test_recovery_value_reflects_exact_and_fuzzy(self):
        rows, columns = self._rows_with_fuzzy_and_exact()
        result = run_ap_testing(rows, columns)
        summary = result.duplicate_payment_summary
        # Exact dup recovery = 1 excess * $1,500. Fuzzy pair adds $900.
        assert summary["recovery_value_total"] == 2400.00
        assert summary["distinct_flagged_payments"] == 4

    def test_vendor_rates_sorted_and_top_vendor_acme(self):
        rows, columns = self._rows_with_fuzzy_and_exact()
        result = run_ap_testing(rows, columns)
        rates = result.duplicate_payment_summary["vendor_rates"]
        assert rates[0]["vendor"].lower().startswith("acme")
        # 4 acme payments flagged out of 4 acme payments
        assert rates[0]["duplicate_payments"] == 4
        assert rates[0]["total_payments"] == 4
        assert rates[0]["duplicate_rate"] == 1.0

    def test_monthly_trend_includes_flagged_months(self):
        rows, columns = self._rows_with_fuzzy_and_exact()
        result = run_ap_testing(rows, columns)
        months = {entry["month"] for entry in result.duplicate_payment_summary["monthly_trend"]}
        assert "2025-01" in months
        assert "2025-02" in months

    def test_no_duplicates_zero_recovery(self):
        columns = ["Vendor Name", "Amount", "Payment Date", "Invoice Number"]
        rows = [
            {"Vendor Name": "Acme", "Amount": "100", "Payment Date": "2025-01-01", "Invoice Number": "A"},
            {"Vendor Name": "Beta", "Amount": "200", "Payment Date": "2025-01-02", "Invoice Number": "B"},
        ]
        result = run_ap_testing(rows, columns)
        summary = result.duplicate_payment_summary
        assert summary["recovery_value_total"] == 0.0
        assert summary["distinct_flagged_payments"] == 0
        assert summary["vendor_rates"] == []
        assert summary["monthly_trend"] == []
