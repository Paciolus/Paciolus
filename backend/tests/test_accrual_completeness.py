"""
Tests for Accrual Completeness Estimator — Sprint 290
"""

import pytest

from accrual_completeness_engine import (
    AccrualCompletenessReport,
    _is_accrual_account,
    compute_accrual_completeness,
    run_accrual_completeness,
)

# ═══════════════════════════════════════════════════════════════
# Test Accrual Account Identification
# ═══════════════════════════════════════════════════════════════

class TestAccrualIdentification:
    """Verify keyword matching for accrual accounts."""

    def test_accrued_expense_match(self):
        assert _is_accrual_account("Accrued Expenses") is not None

    def test_accrued_wages_match(self):
        assert _is_accrual_account("Accrued Wages Payable") is not None

    def test_accrued_interest_match(self):
        result = _is_accrual_account("Accrued Interest")
        assert result is not None
        assert "accrued interest" in result

    def test_accrued_tax_match(self):
        assert _is_accrual_account("Accrued Tax Liabilities") is not None

    def test_non_accrual_returns_none(self):
        assert _is_accrual_account("Cash in Bank") is None
        assert _is_accrual_account("Accounts Receivable") is None
        assert _is_accrual_account("Revenue") is None

    def test_non_accrual_payable_returns_none(self):
        """Accounts Payable is NOT an accrual account."""
        assert _is_accrual_account("Accounts Payable") is None

    def test_phrase_specificity(self):
        """More specific phrase matches should be returned over generic 'accrued'."""
        result = _is_accrual_account("Accrued Salaries Expense")
        assert result is not None
        # Should match the more specific "accrued salaries" over generic "accrued"
        assert "accrued salaries" in result


# ═══════════════════════════════════════════════════════════════
# Test compute_accrual_completeness
# ═══════════════════════════════════════════════════════════════

class TestComputeAccrualCompleteness:
    """Test core accrual completeness computation."""

    def test_empty_input(self):
        result = compute_accrual_completeness({}, {})
        assert isinstance(result, AccrualCompletenessReport)
        assert result.accrual_account_count == 0
        assert result.total_accrued_balance == 0.0

    def test_identifies_accrual_liabilities(self):
        """Only liability-classified accounts with accrual keywords are identified."""
        balances = {
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Accrued Interest": {"debit": 0.0, "credit": 1000.0},
            "Cash": {"debit": 10000.0, "credit": 0.0},
        }
        classified = {
            "Accrued Wages": "liability",
            "Accrued Interest": "liability",
            "Cash": "asset",
        }
        result = compute_accrual_completeness(balances, classified)
        assert result.accrual_account_count == 2
        assert abs(result.total_accrued_balance - 6000.0) < 0.01

    def test_excludes_non_liability(self):
        """Accrual keywords on non-liability accounts are excluded."""
        balances = {
            "Accrued Revenue": {"debit": 3000.0, "credit": 0.0},
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
        }
        classified = {
            "Accrued Revenue": "asset",
            "Accrued Wages": "liability",
        }
        result = compute_accrual_completeness(balances, classified)
        assert result.accrual_account_count == 1
        assert abs(result.total_accrued_balance - 5000.0) < 0.01

    def test_run_rate_calculation(self):
        """Monthly run-rate should be prior_operating_expenses / 12."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 5000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,
        )
        assert result.prior_available is True
        assert result.monthly_run_rate is not None
        assert abs(result.monthly_run_rate - 10000.0) < 0.01

    def test_ratio_calculation(self):
        """Accrual-to-run-rate ratio = (total_accrued / monthly_run_rate) * 100."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 3000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,  # run-rate = 10,000
        )
        assert result.accrual_to_run_rate_pct is not None
        # 3000 / 10000 * 100 = 30%
        assert abs(result.accrual_to_run_rate_pct - 30.0) < 0.01

    def test_below_threshold_flag(self):
        """When ratio < threshold, below_threshold should be True."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 3000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        # ratio = 30% < 50% threshold
        assert result.below_threshold is True

    def test_above_threshold_flag(self):
        """When ratio >= threshold, below_threshold should be False."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 8000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        # ratio = 80% > 50% threshold
        assert result.below_threshold is False

    def test_no_prior_data(self):
        """Without prior data, run-rate metrics should be None."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 5000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(balances, classified)
        assert result.prior_available is False
        assert result.monthly_run_rate is None
        assert result.accrual_to_run_rate_pct is None
        assert result.below_threshold is False

    def test_narrative_present(self):
        """Narrative should always be populated."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 5000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(balances, classified)
        assert len(result.narrative) > 0

    def test_narrative_guardrail(self):
        """Narrative must NOT contain 'understated' or 'deficiency'."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 1000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        narrative_lower = result.narrative.lower()
        assert "understated" not in narrative_lower
        assert "deficiency" not in narrative_lower
        assert "material weakness" not in narrative_lower

    def test_to_dict_structure(self):
        """to_dict() should return expected shape."""
        balances = {"Accrued Wages": {"debit": 0.0, "credit": 5000.0}}
        classified = {"Accrued Wages": "liability"}
        result = compute_accrual_completeness(balances, classified)
        d = result.to_dict()
        assert "accrual_accounts" in d
        assert "total_accrued_balance" in d
        assert "accrual_account_count" in d
        assert "monthly_run_rate" in d
        assert "accrual_to_run_rate_pct" in d
        assert "threshold_pct" in d
        assert "below_threshold" in d
        assert "narrative" in d
        assert isinstance(d["accrual_accounts"], list)

    def test_sorted_by_balance_descending(self):
        """Accrual accounts should be sorted by absolute balance descending."""
        balances = {
            "Accrued Interest": {"debit": 0.0, "credit": 1000.0},
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Accrued Tax": {"debit": 0.0, "credit": 3000.0},
        }
        classified = {k: "liability" for k in balances}
        result = compute_accrual_completeness(balances, classified)
        amounts = [a.balance for a in result.accrual_accounts]
        assert amounts == sorted(amounts, key=abs, reverse=True)


# ═══════════════════════════════════════════════════════════════
# Test run_accrual_completeness (standalone entry point)
# ═══════════════════════════════════════════════════════════════

class TestRunAccrualCompleteness:
    """Test the standalone entry point that parses raw data."""

    def test_missing_columns(self):
        result = run_accrual_completeness(
            column_names=["foo", "bar"],
            rows=[{"foo": "x", "bar": 1}],
            filename="test.csv",
        )
        assert isinstance(result, AccrualCompletenessReport)
        assert result.accrual_account_count == 0

    def test_basic_parsed_data(self):
        columns = ["Account", "Debit", "Credit"]
        rows = [
            {"Account": "Accrued Wages", "Debit": 0, "Credit": 5000},
            {"Account": "Cash", "Debit": 10000, "Credit": 0},
            {"Account": "Revenue", "Debit": 0, "Credit": 20000},
        ]
        result = run_accrual_completeness(columns, rows, "test.csv")
        # Accrued Wages should be identified as accrual liability
        assert result.accrual_account_count >= 1


# ═══════════════════════════════════════════════════════════════
# Test Route Registration
# ═══════════════════════════════════════════════════════════════

class TestRouteRegistration:
    """Verify that new routes are registered on the app."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        from main import app
        self.routes = [r.path for r in app.routes if hasattr(r, 'path')]

    def test_accrual_completeness_route(self):
        assert "/audit/accrual-completeness" in self.routes

    def test_accrual_completeness_memo_route(self):
        assert "/export/accrual-completeness-memo" in self.routes

    def test_accrual_completeness_csv_route(self):
        assert "/export/csv/accrual-completeness" in self.routes
