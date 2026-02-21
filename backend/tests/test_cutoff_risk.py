"""
Tests for Cutoff Period Risk Indicator Engine — Sprint 358

ISA 501 cutoff risk detection for accrual, prepaid, and deferred revenue accounts.

Covers:
- Keyword classification of cutoff-sensitive accounts
- Round number test (divisible by 1000)
- Zero balance test (material prior → zero current)
- Spike test (>3x change from prior)
- Full computation with and without prior period
- Edge cases: no accounts, immaterial, no prior
"""

from cutoff_risk_engine import (
    CutoffFlag,
    CutoffRiskReport,
    _is_cutoff_sensitive,
    _test_round_number,
    _test_spike,
    _test_zero_balance,
    compute_cutoff_risk,
)


# =============================================================================
# KEYWORD CLASSIFICATION
# =============================================================================


class TestCutoffKeywords:
    """Tests for _is_cutoff_sensitive()."""

    def test_accrued_expense(self):
        assert _is_cutoff_sensitive("Accrued Expenses") is not None

    def test_accrued_wages(self):
        kw = _is_cutoff_sensitive("Accrued Wages Payable")
        assert kw is not None
        assert "accrued wages" in kw

    def test_prepaid_insurance(self):
        assert _is_cutoff_sensitive("Prepaid Insurance") is not None

    def test_deferred_revenue(self):
        assert _is_cutoff_sensitive("Deferred Revenue") is not None

    def test_unearned_income(self):
        assert _is_cutoff_sensitive("Unearned Income") is not None

    def test_accounts_payable(self):
        assert _is_cutoff_sensitive("Accounts Payable - Trade") is not None

    def test_customer_deposit(self):
        assert _is_cutoff_sensitive("Customer Deposits") is not None

    def test_contract_liability(self):
        assert _is_cutoff_sensitive("Contract Liability") is not None

    def test_cash_not_sensitive(self):
        assert _is_cutoff_sensitive("Cash and Cash Equivalents") is None

    def test_revenue_not_sensitive(self):
        assert _is_cutoff_sensitive("Revenue - Product Sales") is None

    def test_case_insensitive(self):
        assert _is_cutoff_sensitive("ACCRUED INTEREST") is not None


# =============================================================================
# TEST 1: ROUND NUMBER
# =============================================================================


class TestRoundNumber:
    """Tests for _test_round_number()."""

    def test_round_balance_flagged(self):
        flag = _test_round_number("Accrued Expenses", 50000.0, 10000.0)
        assert flag is not None
        assert flag.test_name == "Round Number"
        assert "round number" in flag.description.lower()

    def test_non_round_balance_not_flagged(self):
        flag = _test_round_number("Accrued Expenses", 52347.89, 10000.0)
        assert flag is None

    def test_immaterial_balance_not_flagged(self):
        flag = _test_round_number("Accrued Expenses", 5000.0, 10000.0)
        assert flag is None

    def test_high_severity_for_double_materiality(self):
        flag = _test_round_number("Accrued Expenses", 100000.0, 25000.0)
        assert flag is not None
        assert flag.severity == "high"

    def test_medium_severity_for_single_materiality(self):
        flag = _test_round_number("Accrued Expenses", 50000.0, 40000.0)
        assert flag is not None
        assert flag.severity == "medium"

    def test_small_round_under_threshold(self):
        flag = _test_round_number("Prepaid Rent", 1000.0, 5000.0)
        assert flag is None

    def test_zero_balance_not_flagged(self):
        flag = _test_round_number("Accrued Expenses", 0.0, 10000.0)
        assert flag is None


# =============================================================================
# TEST 2: ZERO BALANCE
# =============================================================================


class TestZeroBalance:
    """Tests for _test_zero_balance()."""

    def test_zero_with_material_prior_flagged(self):
        flag = _test_zero_balance("Accrued Rent", 0.0, 50000.0, 10000.0)
        assert flag is not None
        assert flag.test_name == "Zero Balance"
        assert flag.prior_balance == 50000.0

    def test_non_zero_balance_not_flagged(self):
        flag = _test_zero_balance("Accrued Rent", 25000.0, 50000.0, 10000.0)
        assert flag is None

    def test_immaterial_prior_not_flagged(self):
        flag = _test_zero_balance("Accrued Rent", 0.0, 500.0, 10000.0)
        assert flag is None

    def test_high_severity_for_double_materiality(self):
        flag = _test_zero_balance("Accrued Rent", 0.0, 100000.0, 25000.0)
        assert flag is not None
        assert flag.severity == "high"


# =============================================================================
# TEST 3: SPIKE
# =============================================================================


class TestSpike:
    """Tests for _test_spike()."""

    def test_4x_increase_flagged(self):
        flag = _test_spike("Deferred Revenue", 40000.0, 10000.0, 5000.0)
        assert flag is not None
        assert flag.test_name == "Balance Spike"
        assert "4.0x" in flag.description

    def test_2x_increase_not_flagged(self):
        flag = _test_spike("Deferred Revenue", 20000.0, 10000.0, 5000.0)
        assert flag is None

    def test_6x_increase_high_severity(self):
        flag = _test_spike("Prepaid Expenses", 60000.0, 10000.0, 5000.0)
        assert flag is not None
        assert flag.severity == "high"

    def test_3_5x_increase_medium_severity(self):
        flag = _test_spike("Prepaid Expenses", 35000.0, 10000.0, 5000.0)
        assert flag is not None
        assert flag.severity == "medium"

    def test_immaterial_balance_not_flagged(self):
        flag = _test_spike("Deferred Revenue", 3000.0, 500.0, 5000.0)
        assert flag is None

    def test_zero_prior_not_flagged(self):
        flag = _test_spike("Deferred Revenue", 40000.0, 0.0, 5000.0)
        assert flag is None

    def test_decrease_not_flagged(self):
        """A decrease (even >3x) should not flag — balance < prior/3."""
        flag = _test_spike("Deferred Revenue", 3000.0, 10000.0, 2000.0)
        assert flag is None  # 3000/10000 = 0.3x, not >3x


# =============================================================================
# FULL COMPUTATION
# =============================================================================


class TestComputeCutoffRisk:
    """Tests for compute_cutoff_risk()."""

    def test_no_cutoff_sensitive_accounts(self):
        balances = {
            "Cash": {"debit": 50000, "credit": 0},
            "Revenue": {"debit": 0, "credit": 100000},
        }
        report = compute_cutoff_risk(balances, {"Cash": "asset", "Revenue": "revenue"})
        assert report.cutoff_sensitive_count == 0
        assert "No cutoff-sensitive" in report.narrative

    def test_round_number_detection(self):
        balances = {
            "Accrued Expenses": {"debit": 0, "credit": 50000},
        }
        report = compute_cutoff_risk(
            balances, {"Accrued Expenses": "liability"}, materiality_threshold=10000
        )
        assert report.cutoff_sensitive_count == 1
        assert report.round_number_flags == 1

    def test_with_prior_period_zero_balance(self):
        balances = {
            "Prepaid Insurance": {"debit": 0, "credit": 0},
        }
        prior = {
            "Prepaid Insurance": {"debit": 50000, "credit": 0},
        }
        report = compute_cutoff_risk(
            balances, {"Prepaid Insurance": "asset"},
            materiality_threshold=10000, prior_account_balances=prior
        )
        assert report.zero_balance_flags == 1
        assert report.prior_period_available is True

    def test_with_prior_period_spike(self):
        balances = {
            "Deferred Revenue": {"debit": 0, "credit": 200000},
        }
        prior = {
            "Deferred Revenue": {"debit": 0, "credit": 40000},
        }
        report = compute_cutoff_risk(
            balances, {"Deferred Revenue": "liability"},
            materiality_threshold=10000, prior_account_balances=prior
        )
        assert report.spike_flags == 1

    def test_no_prior_skips_tests_2_and_3(self):
        balances = {
            "Accrued Wages": {"debit": 0, "credit": 50000},
        }
        report = compute_cutoff_risk(
            balances, {"Accrued Wages": "liability"}, materiality_threshold=10000
        )
        assert report.prior_period_available is False
        assert report.zero_balance_flags == 0
        assert report.spike_flags == 0
        assert "Prior period data not available" in report.narrative

    def test_empty_balances(self):
        report = compute_cutoff_risk({}, {})
        assert "No account data" in report.narrative

    def test_multiple_flags(self):
        balances = {
            "Accrued Expenses": {"debit": 0, "credit": 100000},
            "Prepaid Rent": {"debit": 0, "credit": 0},
            "Deferred Revenue": {"debit": 0, "credit": 300000},
        }
        prior = {
            "Prepaid Rent": {"debit": 80000, "credit": 0},
            "Deferred Revenue": {"debit": 0, "credit": 50000},
        }
        classifications = {
            "Accrued Expenses": "liability",
            "Prepaid Rent": "asset",
            "Deferred Revenue": "liability",
        }
        report = compute_cutoff_risk(
            balances, classifications,
            materiality_threshold=10000, prior_account_balances=prior
        )
        assert report.cutoff_sensitive_count == 3
        assert report.flag_count >= 2  # At least round-number + spike or zero

    def test_to_dict_serialization(self):
        balances = {
            "Accrued Interest": {"debit": 0, "credit": 25000},
        }
        report = compute_cutoff_risk(balances, {"Accrued Interest": "liability"}, 10000)
        d = report.to_dict()
        assert "cutoff_sensitive_count" in d
        assert "flagged_accounts" in d
        assert "narrative" in d
        assert isinstance(d["flag_count"], int)

    def test_narrative_with_flags(self):
        balances = {
            "Accrued Expenses": {"debit": 0, "credit": 50000},
        }
        report = compute_cutoff_risk(
            balances, {"Accrued Expenses": "liability"}, materiality_threshold=10000
        )
        assert "flag(s) raised" in report.narrative

    def test_narrative_no_flags(self):
        balances = {
            "Accrued Expenses": {"debit": 0, "credit": 7532.49},
        }
        report = compute_cutoff_risk(
            balances, {"Accrued Expenses": "liability"}, materiality_threshold=10000
        )
        assert "No cutoff risk flags" in report.narrative
