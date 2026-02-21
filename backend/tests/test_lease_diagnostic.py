"""
Tests for Lease Account Diagnostic Engine — Sprint 357

IFRS 16 / ASC 842 lease account detection and consistency checking.

Covers:
- Keyword classification (ROU assets, lease liabilities, lease expenses)
- Directional consistency test
- Classification check (current/non-current split)
- Amortization trend test (with prior period)
- Expense account presence test
- Full computation with various account mixes
- Edge cases: no leases, zero balances, no prior period
"""

from lease_diagnostic_engine import (
    LeaseAccount,
    LeaseDiagnosticReport,
    LeaseIssue,
    _classify_lease_account,
    _test_amortization_trend,
    _test_classification_check,
    _test_directional_consistency,
    _test_expense_presence,
    compute_lease_diagnostic,
)


# =============================================================================
# KEYWORD CLASSIFICATION
# =============================================================================


class TestLeaseClassification:
    """Tests for _classify_lease_account()."""

    def test_rou_asset_detected(self):
        cls, kw = _classify_lease_account("Right-of-Use Asset - Building")
        assert cls == "rou_asset"
        assert "right-of-use" in kw

    def test_rou_asset_abbreviation(self):
        cls, kw = _classify_lease_account("ROU Asset - Equipment")
        assert cls == "rou_asset"

    def test_operating_lease_asset(self):
        cls, kw = _classify_lease_account("Operating Lease Asset")
        assert cls == "rou_asset"

    def test_finance_lease_asset(self):
        cls, kw = _classify_lease_account("Finance Lease Asset")
        assert cls == "rou_asset"

    def test_lease_liability_generic(self):
        cls, kw = _classify_lease_account("Lease Liability")
        assert cls == "lease_liability"
        assert "lease liability" in kw

    def test_lease_liability_current(self):
        cls, kw = _classify_lease_account("Lease Liability Current")
        assert cls == "lease_liability"
        assert "current" in kw

    def test_lease_liability_noncurrent(self):
        cls, kw = _classify_lease_account("Lease Liability Non-Current")
        assert cls == "lease_liability"
        assert "non-current" in kw

    def test_lease_obligation(self):
        cls, kw = _classify_lease_account("Lease Obligation - Office")
        assert cls == "lease_liability"

    def test_lease_expense(self):
        cls, kw = _classify_lease_account("Lease Expense")
        assert cls == "lease_expense"

    def test_lease_amortization(self):
        cls, kw = _classify_lease_account("Lease Amortization Expense")
        assert cls == "lease_expense"

    def test_rou_amortization(self):
        cls, kw = _classify_lease_account("ROU Amortization")
        assert cls == "lease_expense"

    def test_lease_interest_expense(self):
        cls, kw = _classify_lease_account("Lease Interest Expense")
        assert cls == "lease_expense"

    def test_non_lease_account_returns_none(self):
        cls, kw = _classify_lease_account("Cash and Cash Equivalents")
        assert cls is None
        assert kw is None

    def test_accounts_receivable_not_lease(self):
        cls, kw = _classify_lease_account("Accounts Receivable")
        assert cls is None

    def test_case_insensitive(self):
        cls, kw = _classify_lease_account("RIGHT-OF-USE ASSET")
        assert cls == "rou_asset"


# =============================================================================
# TEST 1: DIRECTIONAL CONSISTENCY
# =============================================================================


class TestDirectionalConsistency:
    """Tests for _test_directional_consistency()."""

    def test_both_present_no_issues(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 100000, "right-of-use")]
        liab = [LeaseAccount("Lease Liability", "lease_liability", 95000, "lease liability")]
        issues = _test_directional_consistency(rou, liab, 100000, 95000, 50000)
        assert len(issues) == 0

    def test_rou_without_liability_flagged(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 100000, "right-of-use")]
        issues = _test_directional_consistency(rou, [], 100000, 0, 50000)
        assert len(issues) == 1
        assert issues[0].severity == "high"
        assert "no corresponding lease liability" in issues[0].description

    def test_liability_without_rou_flagged(self):
        liab = [LeaseAccount("Lease Liability", "lease_liability", 80000, "lease liability")]
        issues = _test_directional_consistency([], liab, 0, 80000, 50000)
        assert len(issues) == 1
        assert "no corresponding ROU asset" in issues[0].description

    def test_immaterial_rou_not_flagged(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 1000, "right-of-use")]
        issues = _test_directional_consistency(rou, [], 1000, 0, 50000)
        assert len(issues) == 0

    def test_both_empty_no_issues(self):
        issues = _test_directional_consistency([], [], 0, 0, 50000)
        assert len(issues) == 0


# =============================================================================
# TEST 2: CLASSIFICATION CHECK
# =============================================================================


class TestClassificationCheck:
    """Tests for _test_classification_check()."""

    def test_both_current_and_noncurrent_no_issues(self):
        liabs = [
            LeaseAccount("Lease Liability Current", "lease_liability", 20000, "lease liability current"),
            LeaseAccount("Lease Liability Non-Current", "lease_liability", 80000, "lease liability non-current"),
        ]
        issues = _test_classification_check(liabs, 100000, 50000)
        assert len(issues) == 0

    def test_generic_liability_not_split(self):
        liabs = [
            LeaseAccount("Lease Liability", "lease_liability", 100000, "lease liability"),
        ]
        issues = _test_classification_check(liabs, 100000, 50000)
        assert len(issues) == 1
        assert "not split" in issues[0].description

    def test_only_current_flagged(self):
        liabs = [
            LeaseAccount("Lease Liability Current", "lease_liability", 20000, "lease liability current"),
        ]
        issues = _test_classification_check(liabs, 20000, 10000)
        assert len(issues) == 1
        assert "Only current" in issues[0].description

    def test_only_noncurrent_flagged(self):
        liabs = [
            LeaseAccount("Lease Liability Non-Current", "lease_liability", 80000, "lease liability non-current"),
        ]
        issues = _test_classification_check(liabs, 80000, 50000)
        assert len(issues) == 1
        assert "Only non-current" in issues[0].description

    def test_immaterial_not_flagged(self):
        liabs = [
            LeaseAccount("Lease Liability", "lease_liability", 100, "lease liability"),
        ]
        issues = _test_classification_check(liabs, 100, 50000)
        assert len(issues) == 0


# =============================================================================
# TEST 3: AMORTIZATION TREND
# =============================================================================


class TestAmortizationTrend:
    """Tests for _test_amortization_trend()."""

    def test_normal_decrease_no_issues(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 80000, "right-of-use")]
        prior = {"ROU Asset": {"debit": 100000, "credit": 0}}
        issues = _test_amortization_trend(rou, 80000, prior)
        assert len(issues) == 0  # 20% decrease is normal

    def test_increase_flagged(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 120000, "right-of-use")]
        prior = {"ROU Asset": {"debit": 100000, "credit": 0}}
        issues = _test_amortization_trend(rou, 120000, prior)
        assert len(issues) == 1
        assert "increased" in issues[0].description
        assert issues[0].severity == "medium"

    def test_minimal_decrease_flagged(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 97000, "right-of-use")]
        prior = {"ROU Asset": {"debit": 100000, "credit": 0}}
        issues = _test_amortization_trend(rou, 97000, prior)
        assert len(issues) == 1
        assert "below the 5%" in issues[0].description

    def test_no_prior_data_skipped(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 100000, "right-of-use")]
        issues = _test_amortization_trend(rou, 100000, None)
        assert len(issues) == 0

    def test_no_prior_rou_skipped(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 100000, "right-of-use")]
        prior = {"Cash": {"debit": 50000, "credit": 0}}
        issues = _test_amortization_trend(rou, 100000, prior)
        assert len(issues) == 0

    def test_no_rou_accounts_skipped(self):
        issues = _test_amortization_trend([], 0, {"ROU Asset": {"debit": 100000, "credit": 0}})
        assert len(issues) == 0


# =============================================================================
# TEST 4: EXPENSE ACCOUNT PRESENCE
# =============================================================================


class TestExpensePresence:
    """Tests for _test_expense_presence()."""

    def test_expense_exists_no_issues(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 100000, "right-of-use")]
        expense = [LeaseAccount("Lease Expense", "lease_expense", 12000, "lease expense")]
        issues = _test_expense_presence(rou, expense, 100000, 50000)
        assert len(issues) == 0

    def test_no_expense_flagged(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 100000, "right-of-use")]
        issues = _test_expense_presence(rou, [], 100000, 50000)
        assert len(issues) == 1
        assert "no lease amortization" in issues[0].description.lower()

    def test_immaterial_rou_not_flagged(self):
        rou = [LeaseAccount("ROU Asset", "rou_asset", 1000, "right-of-use")]
        issues = _test_expense_presence(rou, [], 1000, 50000)
        assert len(issues) == 0

    def test_no_rou_skipped(self):
        issues = _test_expense_presence([], [], 0, 50000)
        assert len(issues) == 0


# =============================================================================
# FULL COMPUTATION
# =============================================================================


class TestComputeLeaseDiagnostic:
    """Tests for compute_lease_diagnostic()."""

    def test_no_lease_accounts(self):
        balances = {
            "Cash": {"debit": 50000, "credit": 0},
            "Accounts Receivable": {"debit": 30000, "credit": 0},
        }
        classifications = {"Cash": "asset", "Accounts Receivable": "asset"}
        report = compute_lease_diagnostic(balances, classifications)
        assert report.lease_accounts_detected is False
        assert "No lease-related accounts" in report.narrative

    def test_complete_lease_structure(self):
        balances = {
            "Right-of-Use Asset - Building": {"debit": 100000, "credit": 0},
            "Lease Liability Current": {"debit": 0, "credit": 20000},
            "Lease Liability Non-Current": {"debit": 0, "credit": 75000},
            "Lease Amortization Expense": {"debit": 12000, "credit": 0},
            "Cash": {"debit": 50000, "credit": 0},
        }
        classifications = {
            "Right-of-Use Asset - Building": "asset",
            "Lease Liability Current": "liability",
            "Lease Liability Non-Current": "liability",
            "Lease Amortization Expense": "expense",
            "Cash": "asset",
        }
        report = compute_lease_diagnostic(balances, classifications, materiality_threshold=10000)
        assert report.lease_accounts_detected is True
        assert len(report.rou_accounts) == 1
        assert len(report.liability_accounts) == 2
        assert len(report.expense_accounts) == 1
        assert report.total_rou_balance == 100000
        assert report.total_liability_balance == 95000
        assert report.balance_difference == 5000
        assert report.issue_count == 0  # All present, no issues

    def test_rou_without_liability_flags(self):
        balances = {
            "Right-of-Use Asset": {"debit": 200000, "credit": 0},
        }
        classifications = {"Right-of-Use Asset": "asset"}
        report = compute_lease_diagnostic(balances, classifications, materiality_threshold=50000)
        assert report.issue_count >= 1
        issue_tests = [i.test_name for i in report.issues]
        assert "Directional Consistency" in issue_tests

    def test_empty_balances(self):
        report = compute_lease_diagnostic({}, {})
        assert "No account data" in report.narrative

    def test_zero_balance_accounts_excluded(self):
        balances = {
            "Right-of-Use Asset": {"debit": 0, "credit": 0},
            "Lease Liability": {"debit": 0, "credit": 0},
        }
        report = compute_lease_diagnostic(balances, {})
        assert report.lease_accounts_detected is False

    def test_to_dict_serialization(self):
        balances = {
            "Right-of-Use Asset": {"debit": 100000, "credit": 0},
            "Lease Liability": {"debit": 0, "credit": 95000},
        }
        report = compute_lease_diagnostic(balances, {}, materiality_threshold=10000)
        d = report.to_dict()
        assert "rou_accounts" in d
        assert "liability_accounts" in d
        assert "issues" in d
        assert "narrative" in d
        assert isinstance(d["total_rou_balance"], float)

    def test_with_prior_period_amortization(self):
        balances = {
            "Right-of-Use Asset": {"debit": 120000, "credit": 0},
            "Lease Liability": {"debit": 0, "credit": 110000},
        }
        prior = {
            "Right-of-Use Asset": {"debit": 100000, "credit": 0},
        }
        report = compute_lease_diagnostic(
            balances, {}, materiality_threshold=10000, prior_account_balances=prior
        )
        # ROU increased — should flag amortization trend
        issue_tests = [i.test_name for i in report.issues]
        assert "Amortization Trend" in issue_tests

    def test_narrative_with_issues(self):
        balances = {
            "Right-of-Use Asset": {"debit": 200000, "credit": 0},
        }
        report = compute_lease_diagnostic(balances, {}, materiality_threshold=50000)
        assert "issue(s) flagged" in report.narrative

    def test_narrative_without_issues(self):
        balances = {
            "Right-of-Use Asset": {"debit": 100000, "credit": 0},
            "Lease Liability Current": {"debit": 0, "credit": 20000},
            "Lease Liability Non-Current": {"debit": 0, "credit": 75000},
            "Lease Expense": {"debit": 12000, "credit": 0},
        }
        report = compute_lease_diagnostic(balances, {}, materiality_threshold=50000)
        assert "No diagnostic issues" in report.narrative
