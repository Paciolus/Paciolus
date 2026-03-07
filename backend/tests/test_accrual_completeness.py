"""
Tests for Accrual Completeness Estimator — Sprint 290 / Sprint 513
"""

import pytest

from accrual_completeness_engine import (
    AccrualAccount,
    AccrualCompletenessReport,
    ExpectedAccrualCheck,
    Finding,
    ReasonablenessResult,
    SuggestedProcedure,
    _analyze_deferred_revenue,
    _build_expected_accrual_checklist,
    _build_reasonableness_results,
    _classify_liability_type,
    _generate_findings,
    _generate_procedures,
    _is_accrual_account,
    _test_reasonableness,
    compute_accrual_completeness,
    run_accrual_completeness,
)

# ═══════════════════════════════════════════════════════════════
# Test Account Classification (Sprint 513)
# ═══════════════════════════════════════════════════════════════


class TestClassifyLiabilityType:
    """Verify _classify_liability_type bucket assignment."""

    def test_accrued_payroll(self):
        bucket, kw = _classify_liability_type("Accrued Payroll")
        assert bucket == "Accrued Liability"
        assert kw is not None

    def test_accrued_interest(self):
        bucket, kw = _classify_liability_type("Accrued Interest")
        assert bucket == "Accrued Liability"
        assert "accrued interest" in kw

    def test_provision_reserve(self):
        bucket, kw = _classify_liability_type("Warranty Reserve")
        assert bucket == "Provision / Reserve"
        assert "reserve" in kw

    def test_provision_allowance(self):
        bucket, kw = _classify_liability_type("Allowance for Returns")
        assert bucket == "Provision / Reserve"
        assert "allowance" in kw

    def test_deferred_revenue(self):
        bucket, kw = _classify_liability_type("Deferred Revenue")
        assert bucket == "Deferred Revenue"
        assert "deferred revenue" in kw

    def test_unearned_revenue(self):
        bucket, kw = _classify_liability_type("Unearned Revenue")
        assert bucket == "Deferred Revenue"
        assert "unearned" in kw.lower()

    def test_deferred_liability_generic(self):
        """Generic 'deferred' should be Deferred Liability, NOT Deferred Revenue."""
        bucket, kw = _classify_liability_type("Deferred Compensation")
        assert bucket == "Deferred Liability"
        assert "deferred" in kw

    def test_deferred_revenue_before_generic_deferred(self):
        """'Deferred Revenue' must match Deferred Revenue, not generic deferred."""
        bucket, _ = _classify_liability_type("Deferred Revenue - Services")
        assert bucket == "Deferred Revenue"

    def test_no_match(self):
        bucket, kw = _classify_liability_type("Accounts Payable")
        assert bucket is None
        assert kw is None

    def test_cash_no_match(self):
        bucket, kw = _classify_liability_type("Cash in Bank")
        assert bucket is None


# ═══════════════════════════════════════════════════════════════
# Test Accrual Account Identification (backward compat)
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
        assert "accrued salaries" in result


# ═══════════════════════════════════════════════════════════════
# Test Per-Account Reasonableness (Sprint 513)
# ═══════════════════════════════════════════════════════════════


class TestReasonableness:
    """Test per-account reasonableness testing."""

    def test_reasonable_variance(self):
        result = _test_reasonableness("Accrued Payroll", 10_000, 120_000, "TB", 1)
        assert result.status == "Reasonable"
        assert result.expected_balance == pytest.approx(10_000, abs=1)

    def test_moderate_variance(self):
        # Expected: 120000/12 = 10000; recorded: 14000 => 40% variance
        result = _test_reasonableness("Accrued Payroll", 14_000, 120_000, "TB", 1)
        assert "Moderate Variance" in result.status

    def test_significant_variance(self):
        # Expected: 120000/12 = 10000; recorded: 20000 => 100% variance
        result = _test_reasonableness("Accrued Payroll", 20_000, 120_000, "TB", 1)
        assert "Significant Variance" in result.status

    def test_no_driver(self):
        result = _test_reasonableness("Accrued Interest", 5_000, None, "N/A", 1)
        assert "Driver Unavailable" in result.status
        assert result.expected_balance is None

    def test_zero_driver(self):
        result = _test_reasonableness("Accrued Interest", 5_000, 0.0, "N/A", 1)
        assert "Driver Unavailable" in result.status

    def test_to_dict(self):
        result = _test_reasonableness("Accrued Payroll", 10_000, 120_000, "TB", 1)
        d = result.to_dict()
        assert "account_name" in d
        assert "recorded_balance" in d
        assert "status" in d
        assert d["recorded_balance"] == 10_000

    def test_build_reasonableness_results_payroll(self):
        accounts = [AccrualAccount("Accrued Payroll", 10_000, "accrued payroll", "Accrued Liability")]
        results = _build_reasonableness_results(accounts, 480_000)
        assert len(results) == 1
        assert results[0].annual_driver is not None  # payroll gets 25% of opex

    def test_build_reasonableness_results_interest_no_driver(self):
        accounts = [AccrualAccount("Accrued Interest", 5_000, "accrued interest", "Accrued Liability")]
        results = _build_reasonableness_results(accounts, 480_000)
        assert len(results) == 1
        assert results[0].annual_driver is None  # interest has no TB driver


# ═══════════════════════════════════════════════════════════════
# Test Deferred Revenue Analysis (Sprint 513)
# ═══════════════════════════════════════════════════════════════


class TestDeferredRevenueAnalysis:
    """Test _analyze_deferred_revenue."""

    def test_with_revenue(self):
        accounts = [AccrualAccount("Deferred Revenue", 60_550, "deferred revenue", "Deferred Revenue")]
        result = _analyze_deferred_revenue(accounts, total_revenue=6_850_000)
        assert result is not None
        assert result.deferred_balance == pytest.approx(60_550)
        assert result.deferred_pct_of_revenue is not None
        assert result.deferred_pct_of_revenue == pytest.approx((60_550 / 6_850_000) * 100, abs=0.01)

    def test_without_revenue(self):
        accounts = [AccrualAccount("Deferred Revenue", 60_550, "deferred revenue", "Deferred Revenue")]
        result = _analyze_deferred_revenue(accounts, total_revenue=None)
        assert result is not None
        assert result.deferred_balance == pytest.approx(60_550)
        assert result.deferred_pct_of_revenue is None

    def test_empty_accounts(self):
        result = _analyze_deferred_revenue([], total_revenue=6_850_000)
        assert result is None

    def test_to_dict(self):
        accounts = [AccrualAccount("Deferred Revenue", 60_550, "deferred revenue", "Deferred Revenue")]
        result = _analyze_deferred_revenue(accounts, total_revenue=6_850_000)
        d = result.to_dict()
        assert "deferred_balance" in d
        assert "total_revenue" in d
        assert "deferred_pct_of_revenue" in d


# ═══════════════════════════════════════════════════════════════
# Test Expected Accrual Checklist / Missing Accruals (Sprint 513)
# ═══════════════════════════════════════════════════════════════


class TestExpectedAccrualChecklist:
    """Test _build_expected_accrual_checklist with enhanced fields."""

    def test_detects_payroll(self):
        accounts = [AccrualAccount("Accrued Payroll", 10_000, "accrued payroll", "Accrued Liability")]
        checklist = _build_expected_accrual_checklist(accounts)
        payroll_item = next(c for c in checklist if c.expected_name == "Payroll Accrual")
        assert payroll_item.detected is True
        assert payroll_item.balance == 10_000

    def test_missing_tax_has_recommended_action(self):
        accounts = [AccrualAccount("Accrued Payroll", 10_000, "accrued payroll", "Accrued Liability")]
        checklist = _build_expected_accrual_checklist(accounts)
        tax_item = next(c for c in checklist if c.expected_name == "Tax Accrual")
        assert tax_item.detected is False
        assert tax_item.recommended_action != ""
        assert "tax" in tax_item.recommended_action.lower()

    def test_basis_populated(self):
        accounts = [AccrualAccount("Accrued Payroll", 10_000, "accrued payroll", "Accrued Liability")]
        checklist = _build_expected_accrual_checklist(accounts)
        for item in checklist:
            assert item.basis != ""  # All items should have a basis

    def test_to_dict_has_new_fields(self):
        accounts = [AccrualAccount("Accrued Payroll", 10_000, "accrued payroll", "Accrued Liability")]
        checklist = _build_expected_accrual_checklist(accounts)
        d = checklist[0].to_dict()
        assert "basis" in d
        assert "recommended_action" in d

    def test_vacation_pto_in_checklist(self):
        """Sprint 513: Vacation/PTO should be in the expected accrual checklist."""
        accounts = []
        checklist = _build_expected_accrual_checklist(accounts)
        pto_item = next((c for c in checklist if "PTO" in c.expected_name or "Vacation" in c.expected_name), None)
        assert pto_item is not None
        assert pto_item.detected is False


# ═══════════════════════════════════════════════════════════════
# Test Findings Generation (Sprint 513)
# ═══════════════════════════════════════════════════════════════


class TestFindingsGeneration:
    """Test _generate_findings."""

    def test_ratio_below_threshold_generates_high_finding(self):
        findings = _generate_findings(
            meets_threshold=False,
            ratio=47.0,
            threshold=50.0,
            reasonableness_results=[],
            missing_accruals=[],
            deferred_revenue_accounts=[],
        )
        high_findings = [f for f in findings if f.risk == "High"]
        assert len(high_findings) >= 1
        assert any("below" in f.finding.lower() for f in high_findings)

    def test_ratio_above_threshold_no_completeness_finding(self):
        findings = _generate_findings(
            meets_threshold=True,
            ratio=55.0,
            threshold=50.0,
            reasonableness_results=[],
            missing_accruals=[],
            deferred_revenue_accounts=[],
        )
        completeness_findings = [f for f in findings if f.area == "Accrual Completeness"]
        assert len(completeness_findings) == 0

    def test_moderate_variance_generates_finding(self):
        r = ReasonablenessResult(
            account_name="Accrued Payroll",
            recorded_balance=14_000,
            annual_driver=120_000,
            driver_source="TB",
            months_to_accrue=1,
            expected_balance=10_000,
            variance=4_000,
            variance_pct=0.40,
            status="Moderate Variance — Inquire",
        )
        findings = _generate_findings(True, 55.0, 50.0, [r], [], [])
        assert any(f.area == "Accrued Payroll" for f in findings)

    def test_missing_accruals_generate_finding(self):
        checklist = [
            ExpectedAccrualCheck("Tax Accrual", False, None, "Understated tax", "Tax provision", "Verify"),
            ExpectedAccrualCheck("Payroll Accrual", True, 10_000, "Understated labor", "Payroll", ""),
        ]
        findings = _generate_findings(True, 55.0, 50.0, [], checklist, [])
        missing_findings = [f for f in findings if f.area == "Missing Accruals"]
        assert len(missing_findings) == 1

    def test_deferred_revenue_generates_finding(self):
        dr_accounts = [AccrualAccount("Deferred Revenue", 60_550, "deferred revenue", "Deferred Revenue")]
        findings = _generate_findings(True, 55.0, 50.0, [], [], dr_accounts)
        dr_findings = [f for f in findings if f.area == "Deferred Revenue"]
        assert len(dr_findings) == 1
        assert "ASC 606" in dr_findings[0].finding

    def test_finding_to_dict(self):
        f = Finding("Area", "Finding text", "High", "Action")
        d = f.to_dict()
        assert d["area"] == "Area"
        assert d["risk"] == "High"


# ═══════════════════════════════════════════════════════════════
# Test Procedures Generation (Sprint 513)
# ═══════════════════════════════════════════════════════════════


class TestProceduresGeneration:
    """Test _generate_procedures."""

    def test_ratio_below_threshold_high_procedure(self):
        procedures = _generate_procedures([], False, 47.0, 50.0, [], [])
        high_procs = [p for p in procedures if p.priority == "High"]
        assert len(high_procs) >= 1
        assert any("accrual schedule" in p.procedure.lower() for p in high_procs)

    def test_deferred_revenue_moderate_procedure(self):
        dr = [AccrualAccount("Deferred Revenue", 60_550, "deferred revenue", "Deferred Revenue")]
        procedures = _generate_procedures([], True, 55.0, 50.0, [], dr)
        dr_procs = [p for p in procedures if p.area == "Deferred Revenue"]
        assert len(dr_procs) == 1
        assert "ASC 606" in dr_procs[0].procedure

    def test_general_completeness_always_present(self):
        procedures = _generate_procedures([], True, 55.0, 50.0, [], [])
        general = [p for p in procedures if p.area == "General Completeness"]
        assert len(general) == 1
        assert "post-period-end" in general[0].procedure.lower()

    def test_procedure_to_dict(self):
        p = SuggestedProcedure("High", "Completeness", "Do things")
        d = p.to_dict()
        assert d["priority"] == "High"
        assert d["procedure"] == "Do things"


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

    def test_deferred_revenue_excluded_from_ratio(self):
        """Deferred Revenue must NOT be included in accrual-to-run-rate calculation."""
        balances = {
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Deferred Revenue": {"debit": 0.0, "credit": 3000.0},
        }
        classified = {
            "Accrued Wages": "liability",
            "Deferred Revenue": "liability",
        }
        result = compute_accrual_completeness(balances, classified, prior_operating_expenses=120000.0)
        # Only Accrued Wages (5000) should be in the ratio, not Deferred Revenue
        assert result.accrual_account_count == 1
        assert abs(result.total_accrued_balance - 5000.0) < 0.01
        assert result.total_deferred_revenue == pytest.approx(3000.0)
        assert len(result.deferred_revenue_accounts) == 1
        assert result.deferred_revenue_accounts[0].classification == "Deferred Revenue"

    def test_deferred_revenue_ratio_corrected(self):
        """Verify the bug fix: ratio computed without deferred revenue."""
        balances = {
            "Accrued Payroll": {"debit": 0.0, "credit": 142_000.0},
            "Accrued Interest Payable": {"debit": 0.0, "credit": 24_500.0},
            "Accrued Utilities": {"debit": 0.0, "credit": 8_200.0},
            "Accrued Legal Fees": {"debit": 0.0, "credit": 35_000.0},
            "Warranty Reserve": {"debit": 0.0, "credit": 18_750.0},
            "Deferred Revenue": {"debit": 0.0, "credit": 60_550.0},
        }
        classified = {k: "liability" for k in balances}
        result = compute_accrual_completeness(balances, classified, prior_operating_expenses=5_827_750.0)
        # Accrual total = 228,450 (without deferred revenue)
        assert abs(result.total_accrued_balance - 228_450.0) < 1.0
        # Ratio should be ~47.0%, NOT 59.5%
        assert result.accrual_to_run_rate_pct is not None
        assert result.accrual_to_run_rate_pct < 50.0
        # Should NOT meet threshold
        assert result.meets_threshold is False
        assert result.below_threshold is True

    def test_provision_reserve_included(self):
        """Provision/Reserve accounts should be included in accrual population."""
        balances = {
            "Warranty Reserve": {"debit": 0.0, "credit": 18_750.0},
        }
        classified = {"Warranty Reserve": "liability"}
        result = compute_accrual_completeness(balances, classified)
        assert result.accrual_account_count == 1
        assert result.accrual_accounts[0].classification == "Provision / Reserve"

    def test_run_rate_calculation(self):
        """Monthly run-rate should be prior_operating_expenses / 12."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 5000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances,
            classified,
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
            balances,
            classified,
            prior_operating_expenses=120000.0,  # run-rate = 10,000
        )
        assert result.accrual_to_run_rate_pct is not None
        # 3000 / 10000 * 100 = 30%
        assert abs(result.accrual_to_run_rate_pct - 30.0) < 0.01

    def test_meets_threshold_flag(self):
        """When ratio >= threshold, meets_threshold should be True."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 8000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances,
            classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        # ratio = 80% > 50% threshold
        assert result.meets_threshold is True
        assert result.below_threshold is False

    def test_below_threshold_flag(self):
        """When ratio < threshold, meets_threshold should be False."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 3000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances,
            classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        # ratio = 30% < 50% threshold
        assert result.meets_threshold is False
        assert result.below_threshold is True

    def test_no_prior_data(self):
        """Without prior data, run-rate metrics should be None."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 5000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(balances, classified)
        assert result.prior_available is False
        assert result.monthly_run_rate is None
        assert result.accrual_to_run_rate_pct is None
        assert result.meets_threshold is False

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
            balances,
            classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        narrative_lower = result.narrative.lower()
        assert "understated" not in narrative_lower
        assert "deficiency" not in narrative_lower
        assert "material weakness" not in narrative_lower

    def test_narrative_mentions_deferred_revenue_exclusion(self):
        """Narrative should mention deferred revenue exclusion when present."""
        balances = {
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Deferred Revenue": {"debit": 0.0, "credit": 3000.0},
        }
        classified = {k: "liability" for k in balances}
        result = compute_accrual_completeness(balances, classified)
        assert "deferred revenue" in result.narrative.lower()
        assert "excluded" in result.narrative.lower()

    def test_to_dict_structure(self):
        """to_dict() should return expected shape with new fields."""
        balances = {
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Deferred Revenue": {"debit": 0.0, "credit": 3000.0},
        }
        classified = {k: "liability" for k in balances}
        result = compute_accrual_completeness(
            balances,
            classified,
            prior_operating_expenses=120000.0,
            total_revenue=500000.0,
        )
        d = result.to_dict()
        # Original fields
        assert "accrual_accounts" in d
        assert "total_accrued_balance" in d
        assert "accrual_account_count" in d
        assert "monthly_run_rate" in d
        assert "accrual_to_run_rate_pct" in d
        assert "threshold_pct" in d
        assert "narrative" in d
        # New Sprint 513 fields
        assert "deferred_revenue_accounts" in d
        assert "total_deferred_revenue" in d
        assert "meets_threshold" in d
        assert "below_threshold" in d
        assert "reasonableness_results" in d
        assert "expected_accrual_checklist" in d
        assert "deferred_revenue_analysis" in d
        assert "findings" in d
        assert "suggested_procedures" in d
        # Type checks
        assert isinstance(d["accrual_accounts"], list)
        assert isinstance(d["deferred_revenue_accounts"], list)
        assert isinstance(d["findings"], list)
        assert isinstance(d["suggested_procedures"], list)

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

    def test_findings_generated_when_below_threshold(self):
        """When ratio is below threshold, findings should include a High-priority item."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 3000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances,
            classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        assert result.below_threshold is True
        assert len(result.findings) > 0
        high_findings = [f for f in result.findings if f.risk == "High"]
        assert len(high_findings) >= 1

    def test_procedures_always_generated(self):
        """Suggested procedures should always include at least general completeness."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 8000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances,
            classified,
            prior_operating_expenses=120000.0,
        )
        assert len(result.suggested_procedures) >= 1
        general = [p for p in result.suggested_procedures if p.area == "General Completeness"]
        assert len(general) == 1

    def test_deferred_revenue_analysis_present(self):
        """Deferred revenue analysis should be computed when DR accounts exist."""
        balances = {
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Deferred Revenue": {"debit": 0.0, "credit": 3000.0},
        }
        classified = {k: "liability" for k in balances}
        result = compute_accrual_completeness(
            balances,
            classified,
            total_revenue=500000.0,
        )
        assert result.deferred_revenue_analysis is not None
        assert result.deferred_revenue_analysis.deferred_balance == pytest.approx(3000.0)
        assert result.deferred_revenue_analysis.deferred_pct_of_revenue is not None

    def test_reasonableness_results_populated(self):
        """Reasonableness results should be populated for each accrual account."""
        balances = {
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Accrued Interest": {"debit": 0.0, "credit": 1000.0},
        }
        classified = {k: "liability" for k in balances}
        result = compute_accrual_completeness(
            balances,
            classified,
            prior_operating_expenses=120000.0,
        )
        assert len(result.reasonableness_results) == 2

    def test_classification_on_accrual_accounts(self):
        """Each accrual account should have a classification field."""
        balances = {
            "Accrued Wages": {"debit": 0.0, "credit": 5000.0},
            "Warranty Reserve": {"debit": 0.0, "credit": 1000.0},
        }
        classified = {k: "liability" for k in balances}
        result = compute_accrual_completeness(balances, classified)
        classifications = {a.classification for a in result.accrual_accounts}
        assert "Accrued Liability" in classifications
        assert "Provision / Reserve" in classifications


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

        self.routes = [r.path for r in app.routes if hasattr(r, "path")]

    def test_accrual_completeness_route(self):
        assert "/audit/accrual-completeness" in self.routes

    def test_accrual_completeness_memo_route(self):
        assert "/export/accrual-completeness-memo" in self.routes

    def test_accrual_completeness_csv_route(self):
        assert "/export/csv/accrual-completeness" in self.routes


# ═══════════════════════════════════════════════════════════════
# Test PDF Memo Generation (Sprint 513)
# ═══════════════════════════════════════════════════════════════


class TestMemoGeneration:
    """Test that the memo generates valid PDF bytes."""

    @pytest.fixture
    def sample_report(self):
        prior_opex = 5_827_750.00
        monthly_rr = prior_opex / 12
        accrual_total = 228_450.00
        ratio = (accrual_total / monthly_rr) * 100

        return {
            "accrual_accounts": [
                {
                    "account_name": "Accrued Payroll",
                    "balance": 142_000.00,
                    "matched_keyword": "accrued payroll",
                    "classification": "Accrued Liability",
                },
                {
                    "account_name": "Accrued Legal Fees",
                    "balance": 35_000.00,
                    "matched_keyword": "accrued",
                    "classification": "Accrued Liability",
                },
                {
                    "account_name": "Accrued Interest Payable",
                    "balance": 24_500.00,
                    "matched_keyword": "accrued interest",
                    "classification": "Accrued Liability",
                },
                {
                    "account_name": "Warranty Reserve",
                    "balance": 18_750.00,
                    "matched_keyword": "reserve",
                    "classification": "Provision / Reserve",
                },
                {
                    "account_name": "Accrued Utilities",
                    "balance": 8_200.00,
                    "matched_keyword": "accrued",
                    "classification": "Accrued Liability",
                },
            ],
            "total_accrued_balance": accrual_total,
            "accrual_account_count": 5,
            "deferred_revenue_accounts": [
                {
                    "account_name": "Deferred Revenue",
                    "balance": 60_550.00,
                    "matched_keyword": "deferred revenue",
                    "classification": "Deferred Revenue",
                },
            ],
            "total_deferred_revenue": 60_550.00,
            "monthly_run_rate": round(monthly_rr, 2),
            "accrual_to_run_rate_pct": round(ratio, 2),
            "threshold_pct": 50.0,
            "meets_threshold": False,
            "below_threshold": True,
            "prior_available": True,
            "prior_operating_expenses": prior_opex,
            "narrative": f"Test narrative. Ratio {ratio:.1f}%.",
            "reasonableness_results": [
                {
                    "account_name": "Accrued Payroll",
                    "recorded_balance": 142_000.00,
                    "annual_driver": prior_opex * 0.25,
                    "driver_source": "Estimated",
                    "months_to_accrue": 1,
                    "expected_balance": round(prior_opex * 0.25 / 12, 2),
                    "variance": round(142_000 - prior_opex * 0.25 / 12, 2),
                    "variance_pct": 0.17,
                    "status": "Reasonable",
                },
            ],
            "expected_accrual_checklist": [
                {
                    "expected_name": "Payroll Accrual",
                    "detected": True,
                    "balance": 142_000.00,
                    "risk_if_absent": "Understated",
                    "basis": "Payroll",
                    "recommended_action": "",
                },
                {
                    "expected_name": "Tax Accrual",
                    "detected": False,
                    "balance": None,
                    "risk_if_absent": "Understated",
                    "basis": "Tax",
                    "recommended_action": "Verify tax status",
                },
            ],
            "deferred_revenue_analysis": {
                "deferred_balance": 60_550.00,
                "total_revenue": 6_850_000.00,
                "deferred_pct_of_revenue": 0.88,
            },
            "findings": [
                {
                    "area": "Accrual Completeness",
                    "finding": "Ratio below threshold",
                    "risk": "High",
                    "action_required": "Investigate",
                },
                {
                    "area": "Deferred Revenue",
                    "finding": "ASC 606 verification needed",
                    "risk": "Moderate",
                    "action_required": "Obtain rollforward",
                },
            ],
            "suggested_procedures": [
                {"priority": "High", "area": "Completeness", "procedure": "Request accrual schedules"},
                {"priority": "Moderate", "area": "General", "procedure": "Post-period review"},
            ],
        }

    def test_pdf_generation(self, sample_report):
        from accrual_completeness_memo import generate_accrual_completeness_memo

        pdf = generate_accrual_completeness_memo(
            sample_report,
            "test.csv",
            client_name="Test Client",
            period_tested="FY2025",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000
        assert pdf[:4] == b"%PDF"

    def test_pdf_with_all_options(self, sample_report):
        from accrual_completeness_memo import generate_accrual_completeness_memo

        pdf = generate_accrual_completeness_memo(
            sample_report,
            "test.csv",
            client_name="Meridian Capital Group LLC",
            period_tested="FY2025",
            prepared_by="Test",
            reviewed_by="Reviewer",
            workpaper_date="March 7, 2026",
            source_document_title="Trial Balance",
            source_context_note="ERP",
            include_signoff=True,
        )
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_pdf_minimal(self):
        """PDF should generate even with minimal data."""
        from accrual_completeness_memo import generate_accrual_completeness_memo

        pdf = generate_accrual_completeness_memo(
            {"accrual_accounts": [], "total_accrued_balance": 0, "accrual_account_count": 0},
            "test.csv",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_pdf_no_deferred_revenue(self):
        """PDF should generate without deferred revenue data."""
        from accrual_completeness_memo import generate_accrual_completeness_memo

        report = {
            "accrual_accounts": [
                {
                    "account_name": "Accrued Wages",
                    "balance": 5000,
                    "matched_keyword": "accrued",
                    "classification": "Accrued Liability",
                },
            ],
            "total_accrued_balance": 5000,
            "accrual_account_count": 1,
            "prior_available": True,
            "monthly_run_rate": 10_000,
            "accrual_to_run_rate_pct": 50.0,
            "threshold_pct": 50.0,
            "meets_threshold": True,
            "below_threshold": False,
            "prior_operating_expenses": 120_000,
            "narrative": "Test.",
        }
        pdf = generate_accrual_completeness_memo(report, "test.csv")
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"
