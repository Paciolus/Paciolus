"""
Revenue Testing Engine Tests — Sprint 491 (Council Remediation)

Stub tests verifying core public API contract for run_revenue_testing().
Exercises: pipeline with valid/empty data, result structure,
and composite score integrity.
"""

from revenue_testing_engine import (
    RevenueTestingResult,
    RevenueTestResult,
    run_revenue_testing,
)
from shared.testing_enums import RiskTier

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_revenue_rows() -> tuple[list[dict], list[str]]:
    """Return minimal revenue GL rows and column names."""
    columns = ["Date", "Amount", "Account Name", "Description"]
    rows = [
        {
            "Date": "2025-06-15",
            "Amount": "10000.00",
            "Account Name": "Product Revenue",
            "Description": "Monthly subscription",
        },
        {
            "Date": "2025-06-20",
            "Amount": "25000.00",
            "Account Name": "Service Revenue",
            "Description": "Consulting fee",
        },
        {"Date": "2025-06-30", "Amount": "5000.00", "Account Name": "Product Revenue", "Description": "License sale"},
    ]
    return rows, columns


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRevenueTestingPipeline:
    """Verify run_revenue_testing returns expected structure."""

    def test_returns_revenue_testing_result(self):
        rows, columns = _make_revenue_rows()
        result = run_revenue_testing(rows, columns)
        assert isinstance(result, RevenueTestingResult)

    def test_result_has_test_results_list(self):
        rows, columns = _make_revenue_rows()
        result = run_revenue_testing(rows, columns)
        assert isinstance(result.test_results, list)
        # 12 core tests + up to 4 contract tests (all skipped when no contract cols)
        assert len(result.test_results) >= 12
        for tr in result.test_results:
            assert isinstance(tr, RevenueTestResult)

    def test_composite_score_fields(self):
        rows, columns = _make_revenue_rows()
        result = run_revenue_testing(rows, columns)
        cs = result.composite_score
        assert 0 <= cs.score <= 100
        assert isinstance(cs.risk_tier, RiskTier)
        assert cs.total_entries == 3
        assert isinstance(cs.flags_by_severity, dict)

    def test_contract_evidence_present(self):
        """Contract evidence assessment should always be populated."""
        rows, columns = _make_revenue_rows()
        result = run_revenue_testing(rows, columns)
        assert result.contract_evidence is not None
        assert result.contract_evidence.level in ("full", "partial", "minimal", "none")

    def test_empty_rows_returns_valid_result(self):
        """Engine should handle empty revenue data gracefully."""
        result = run_revenue_testing([], ["Date", "Amount", "Account Name"])
        assert isinstance(result, RevenueTestingResult)
        assert result.composite_score.total_entries == 0
        assert result.composite_score.risk_tier == RiskTier.LOW
