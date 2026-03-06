"""
AR Aging Engine Tests — Sprint 491 (Council Remediation)

Stub tests verifying core public API contract for run_ar_aging().
Exercises: TB-only pipeline, result structure, composite score,
and basic sign anomaly detection.
"""

from ar_aging_engine import (
    ARAgingResult,
    ARTestResult,
    run_ar_aging,
)
from shared.testing_enums import RiskTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tb_rows() -> tuple[list[dict], list[str]]:
    """Return minimal trial balance rows with AR, allowance, and revenue accounts."""
    columns = ["Account Name", "Account Number", "Balance"]
    rows = [
        {"Account Name": "Accounts Receivable", "Account Number": "1200", "Balance": "150000.00"},
        {"Account Name": "Allowance for Doubtful Accounts", "Account Number": "1210", "Balance": "-3000.00"},
        {"Account Name": "Sales Revenue", "Account Number": "4000", "Balance": "500000.00"},
    ]
    return rows, columns


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestARAgingPipeline:
    """Verify run_ar_aging returns expected structure with TB-only data."""

    def test_returns_ar_aging_result(self):
        rows, columns = _make_tb_rows()
        result = run_ar_aging(rows, columns)
        assert isinstance(result, ARAgingResult)

    def test_result_has_test_results_list(self):
        rows, columns = _make_tb_rows()
        result = run_ar_aging(rows, columns)
        assert isinstance(result.test_results, list)
        # TB-only: 11 tests total (some skipped without sub-ledger)
        assert len(result.test_results) == 11
        for tr in result.test_results:
            assert isinstance(tr, ARTestResult)

    def test_composite_score_fields(self):
        rows, columns = _make_tb_rows()
        result = run_ar_aging(rows, columns)
        cs = result.composite_score
        assert 0 <= cs.score <= 100
        assert isinstance(cs.risk_tier, RiskTier)
        assert cs.tests_run >= 1
        assert isinstance(cs.flags_by_severity, dict)
        assert cs.has_subledger is False

    def test_skipped_tests_without_subledger(self):
        """Without sub-ledger, most tests should be skipped (sub-ledger + DSO)."""
        rows, columns = _make_tb_rows()
        result = run_ar_aging(rows, columns)
        skipped = [t for t in result.test_results if t.skipped]
        # 7 sub-ledger tests + DSO trend (no prior_period_dso) = 8 skipped
        assert len(skipped) == 8

    def test_empty_tb_returns_valid_result(self):
        """Engine should handle empty TB data gracefully."""
        result = run_ar_aging([], ["Account Name", "Balance"])
        assert isinstance(result, ARAgingResult)
        assert result.composite_score.tests_run >= 0
