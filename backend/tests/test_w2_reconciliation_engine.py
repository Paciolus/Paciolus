"""
Sprint 636 — W-2 / W-3 Reconciliation engine tests.

Sprint 811 (finding A-7) changed every `tax_year=2025` below to `tax_year=2025`.
That is not a cosmetic edit. These tests asserted against the statutory figures
that shipped under a `# --- 2026 reference values ---` heading, and every one of
those figures is the **2025** set (SS wage base 176,100; 401(k) 23,500; catch-up
7,500; HSA 4,300/8,550; SIMPLE 16,500). The tests were green because the engine
applied one fixed set of limits to every tax year — so passing 2026 and asserting
2025 law agreed with itself.

`tax_year` is now the key the limits are resolved by, and a year with no table is
refused rather than answered with another year's law. The 2026 table needs a
practitioner and stays with Sprint 793b; `TestSprint811StatutoryYearKeying` below
covers the refusal and the override path that unblocks a 2026 engagement today.
"""

from decimal import Decimal

import pytest

from w2_reconciliation_engine import (
    DEFAULT_SS_WAGE_BASE,
    STATUTORY_LIMITS_BY_YEAR,
    DiscrepancyKind,
    DiscrepancySeverity,
    EmployeePayroll,
    EmployeeW2Draft,
    Form941Quarter,
    HsaCoverage,
    StatutoryLimitsUnavailableError,
    W2ReconciliationConfig,
    W2ReconciliationInputError,
    reconcile_w2,
    statutory_limits_for_year,
)


def _clean_employee(
    employee_id: str = "E1",
    name: str = "Alice",
    federal_wages: str = "60000",
    ss_wages: str = "60000",
    medicare_wages: str = "60000",
    **extra,
) -> EmployeePayroll:
    return EmployeePayroll(
        employee_id=employee_id,
        employee_name=name,
        federal_wages=Decimal(federal_wages),
        federal_withholding=Decimal("6000"),
        ss_wages=Decimal(ss_wages),
        ss_tax_withheld=Decimal(ss_wages) * Decimal("0.062"),
        medicare_wages=Decimal(medicare_wages),
        medicare_tax_withheld=Decimal(medicare_wages) * Decimal("0.0145"),
        **extra,
    )


def _matching_w2(employee: EmployeePayroll, ss_wage_base: Decimal = DEFAULT_SS_WAGE_BASE) -> EmployeeW2Draft:
    ss_wages = min(employee.ss_wages, ss_wage_base)
    return EmployeeW2Draft(
        employee_id=employee.employee_id,
        box_1_federal_wages=employee.federal_wages,
        box_2_federal_withholding=employee.federal_withholding,
        box_3_ss_wages=ss_wages,
        box_4_ss_tax_withheld=(ss_wages * Decimal("0.062")).quantize(Decimal("0.01")),
        box_5_medicare_wages=employee.medicare_wages,
        box_6_medicare_tax_withheld=(employee.medicare_wages * Decimal("0.0145")).quantize(Decimal("0.01")),
        box_12_code_w_hsa=employee.hsa_contributions,
        box_12_code_d_401k=employee.retirement_401k,
        box_12_code_s_simple=employee.retirement_simple_ira,
    )


class TestHappyPath:
    def test_clean_payroll_and_matching_w2_produce_no_discrepancies(self):
        emp = _clean_employee()
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        assert result.employee_discrepancies == []
        assert result.w3_totals.employee_count == 1


class TestSSWageBase:
    def test_correctly_capped_draft_is_not_flagged_for_uncapped_payroll(self):
        """Sprint 826 (W6): payroll routinely reports uncapped SS wages. A draft
        whose box 3 is correctly capped drew a HIGH "must be capped" finding —
        this test used to assert exactly that."""
        emp = _clean_employee(ss_wages="200000")
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        kinds = {d.kind for d in result.employee_discrepancies}
        assert DiscrepancyKind.SS_WAGE_BASE_EXCEEDED not in kinds

    def test_without_a_draft_uncapped_payroll_still_gets_the_reminder(self):
        emp = _clean_employee(ss_wages="200000")
        result = reconcile_w2(W2ReconciliationConfig(tax_year=2025, employees=[emp], w2_drafts=[]))
        kinds = {d.kind for d in result.employee_discrepancies}
        assert DiscrepancyKind.SS_WAGE_BASE_EXCEEDED in kinds

    def test_w2_box_3_exceeding_base_flags_mismatch(self):
        emp = _clean_employee(ss_wages="200000")
        bad_w2 = EmployeeW2Draft(
            employee_id="E1",
            box_1_federal_wages=Decimal("60000"),
            box_2_federal_withholding=Decimal("6000"),
            box_3_ss_wages=Decimal("200000"),  # Wrong — not capped
            box_4_ss_tax_withheld=Decimal("200000") * Decimal("0.062"),
            box_5_medicare_wages=Decimal("60000"),
            box_6_medicare_tax_withheld=Decimal("60000") * Decimal("0.0145"),
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[bad_w2],
        )
        result = reconcile_w2(cfg)
        kinds = {d.kind for d in result.employee_discrepancies}
        assert DiscrepancyKind.SS_WAGE_BASE_EXCEEDED in kinds
        assert DiscrepancyKind.SS_WAGES in kinds


class TestMedicareWithholding:
    def test_standard_medicare_matches_expected(self):
        emp = _clean_employee(medicare_wages="100000")
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        med_discrepancies = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.MEDICARE_WITHHOLDING]
        assert med_discrepancies == []

    def test_high_earner_triggers_additional_medicare(self):
        emp = _clean_employee(medicare_wages="250000")
        # Draft W-2 with only standard 1.45% — additional 0.9% on 50k missed.
        bad_w2 = _matching_w2(emp)
        bad_w2.box_6_medicare_tax_withheld = (Decimal("250000") * Decimal("0.0145")).quantize(Decimal("0.01"))
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[bad_w2],
        )
        result = reconcile_w2(cfg)
        kinds = [d.kind for d in result.employee_discrepancies]
        assert DiscrepancyKind.MEDICARE_WITHHOLDING in kinds
        assert DiscrepancyKind.ADDITIONAL_MEDICARE in kinds


class TestHSA:
    def test_self_only_over_limit_flags(self):
        emp = _clean_employee(
            hsa_contributions=Decimal("5000"),
            hsa_coverage=HsaCoverage.SELF_ONLY,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        hsa = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.HSA_OVER_LIMIT]
        assert len(hsa) == 1
        assert hsa[0].severity == DiscrepancySeverity.HIGH
        assert hsa[0].difference == Decimal("700")  # 5000 - 4300

    def test_family_limit_higher(self):
        emp = _clean_employee(
            hsa_contributions=Decimal("5000"),
            hsa_coverage=HsaCoverage.FAMILY,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        hsa = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.HSA_OVER_LIMIT]
        assert hsa == []

    def test_no_coverage_suppresses_limit_check(self):
        emp = _clean_employee(
            hsa_contributions=Decimal("5000"),
            hsa_coverage=HsaCoverage.NONE,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        hsa = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.HSA_OVER_LIMIT]
        assert hsa == []


class TestRetirementLimits:
    def test_401k_over_limit_flags(self):
        emp = _clean_employee(
            retirement_401k=Decimal("30000"),
            retirement_plan_type="401k",
            age=35,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        ret = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.RETIREMENT_OVER_LIMIT]
        assert len(ret) == 1
        assert ret[0].difference == Decimal("6500")  # 30000 - 23500

    def test_catchup_raises_limit_for_age_50_plus(self):
        # 23,500 + 7,500 catch-up = 31,000 allowable.
        emp = _clean_employee(
            retirement_401k=Decimal("30000"),
            retirement_plan_type="401k",
            age=55,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        ret = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.RETIREMENT_OVER_LIMIT]
        assert ret == []

    def test_super_catchup_at_age_60_through_63(self):
        # 23,500 + 11,250 = 34,750 allowable.
        emp = _clean_employee(
            retirement_401k=Decimal("34000"),
            retirement_plan_type="401k",
            age=62,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        ret = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.RETIREMENT_OVER_LIMIT]
        assert ret == []

    def test_simple_ira_limit(self):
        emp = _clean_employee(
            retirement_simple_ira=Decimal("20000"),
            retirement_plan_type="simple_ira",
            age=35,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        ret = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.RETIREMENT_OVER_LIMIT]
        assert len(ret) == 1
        assert ret[0].difference == Decimal("3500")  # 20000 - 16500


class TestForm941:
    def test_matching_quarters_produce_no_mismatches(self):
        emp = _clean_employee()
        q = Decimal("60000") / Decimal("4")
        quarters = [
            Form941Quarter(
                quarter=i,
                total_federal_wages=q,
                total_federal_withholding=Decimal("6000") / Decimal("4"),
                total_ss_wages=q,
                total_medicare_wages=q,
            )
            for i in range(1, 5)
        ]
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
            form_941_quarters=quarters,
        )
        result = reconcile_w2(cfg)
        assert result.form_941_mismatches == []

    def test_941_totals_diverging_flags_high_severity(self):
        # Sprint 846 (W9): this used to supply Q1 alone, which only "diverged"
        # because three returns were missing. Now four quarters, Q1 understated.
        emp = _clean_employee()
        q = Decimal("15000")
        quarters = [
            Form941Quarter(
                quarter=i,
                total_federal_wages=Decimal("5000") if i == 1 else q,  # Wrong — payroll has 60k
                total_federal_withholding=Decimal("1500"),
                total_ss_wages=q,
                total_medicare_wages=q,
            )
            for i in range(1, 5)
        ]
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
            form_941_quarters=quarters,
        )
        result = reconcile_w2(cfg)
        assert len(result.form_941_mismatches) >= 1
        fed_wage_issue = [m for m in result.form_941_mismatches if m.kind == DiscrepancyKind.FEDERAL_WAGES]
        assert fed_wage_issue
        assert fed_wage_issue[0].severity == DiscrepancySeverity.HIGH


class TestW3Totals:
    def test_w3_sums_all_w2_drafts(self):
        e1 = _clean_employee(employee_id="E1", name="A", federal_wages="50000")
        e2 = _clean_employee(employee_id="E2", name="B", federal_wages="70000")
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[e1, e2],
            w2_drafts=[_matching_w2(e1), _matching_w2(e2)],
        )
        result = reconcile_w2(cfg)
        assert result.w3_totals.employee_count == 2
        assert result.w3_totals.total_federal_wages == Decimal("120000.00")


class TestInputValidation:
    def test_invalid_tax_year_rejected(self):
        try:
            reconcile_w2(W2ReconciliationConfig(tax_year=1999, employees=[]))
        except W2ReconciliationInputError:
            return
        raise AssertionError("expected W2ReconciliationInputError")

    def test_invalid_quarter_rejected(self):
        try:
            Form941Quarter(quarter=5)
        except W2ReconciliationInputError:
            return
        raise AssertionError("expected W2ReconciliationInputError")


class TestMissingW2Draft:
    def test_self_consistent_w2_still_runs_limit_checks(self):
        """Even without a draft W-2 the HSA / retirement checks must fire."""
        emp = _clean_employee(
            hsa_contributions=Decimal("5000"),
            hsa_coverage=HsaCoverage.SELF_ONLY,
        )
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[],
        )
        result = reconcile_w2(cfg)
        hsa = [d for d in result.employee_discrepancies if d.kind == DiscrepancyKind.HSA_OVER_LIMIT]
        assert len(hsa) == 1
        assert emp.employee_id in result.summary["employees_missing_w2_draft"]


class TestSerialisation:
    def test_to_dict_roundtrip(self):
        emp = _clean_employee()
        cfg = W2ReconciliationConfig(
            tax_year=2025,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        d = result.to_dict()
        assert d["tax_year"] == 2025
        assert set(d).issuperset({"employee_discrepancies", "form_941_mismatches", "w3_totals", "summary"})


class TestSprint811StatutoryYearKeying:
    """
    Finding A-7, structural half. `tax_year` is a required input accepted for any
    year 2000-2099, and no statutory constant was keyed by it: every tax year got
    one fixed set of limits. A 2026 engagement was answered with 2025 law, and the
    block holding those figures was headed "2026 reference values", so the comment
    defeated the next reader's check.
    """

    def test_a_tabulated_year_resolves_its_own_limits_and_records_which(self):
        config = W2ReconciliationConfig(tax_year=2025, employees=[])

        assert config.ss_wage_base == Decimal("176100")
        assert config.limit_401k_elective == Decimal("23500")
        assert config.statutory_year == 2025
        assert config.statutory_source  # provenance travels with the figures

    def test_a_year_with_no_table_is_refused_not_answered_with_another_years_law(self):
        """
        The behaviour change. Refusing is the honest answer: the wage-base and
        over-limit findings this tool produces are wrong in a direction the
        practitioner cannot see if they are computed from the wrong year.
        """
        with pytest.raises(StatutoryLimitsUnavailableError) as excinfo:
            W2ReconciliationConfig(tax_year=2026, employees=[])

        message = str(excinfo.value)
        assert "2026" in message
        assert "2025" in message  # names what *is* available
        assert "statutory_limits" in message  # names the way forward

    def test_the_refusal_is_an_input_error_so_the_routes_return_400(self):
        """
        Both routes map `W2ReconciliationInputError` to a verbatim 400. A bare
        ValueError would be sanitised by the analyze route and uncaught by the
        CSV export route, which would 500.
        """
        assert issubclass(StatutoryLimitsUnavailableError, W2ReconciliationInputError)

    def test_a_fully_overridden_run_needs_no_table(self):
        """
        Sprint 793a's per-request overrides are the escape hatch, and they must
        keep working for a year the engine has no table for — that is what
        unblocks a 2026 engagement before Sprint 793b lands.
        """
        config = W2ReconciliationConfig(
            tax_year=2026,
            employees=[],
            ss_wage_base=Decimal("184500"),
            ss_rate=Decimal("0.062"),
            medicare_rate=Decimal("0.0145"),
            additional_medicare_rate=Decimal("0.009"),
            additional_medicare_threshold=Decimal("200000"),
            hsa_self_only_limit=Decimal("4400"),
            hsa_family_limit=Decimal("8750"),
            limit_401k_elective=Decimal("24500"),
            limit_401k_catchup_50=Decimal("8000"),
            limit_401k_catchup_60_63=Decimal("11250"),
            limit_simple_ira=Decimal("17000"),
        )

        assert config.ss_wage_base == Decimal("184500")
        # No table was consulted, so no statutory year is claimed. The memo must
        # not be able to print "2025" over a run that used the caller's figures.
        assert config.statutory_year is None
        assert config.statutory_source is None

    def test_a_partial_override_still_needs_a_table_for_the_rest(self):
        """
        Supplying one figure must not be read as supplying them all — the
        unsupplied ones would silently come from somewhere.
        """
        with pytest.raises(StatutoryLimitsUnavailableError):
            W2ReconciliationConfig(
                tax_year=2026,
                employees=[],
                ss_wage_base=Decimal("184500"),
            )

    def test_an_override_wins_over_a_tabulated_year(self):
        config = W2ReconciliationConfig(
            tax_year=2025,
            employees=[],
            ss_wage_base=Decimal("999999"),
        )

        assert config.ss_wage_base == Decimal("999999")
        # The rest came from the 2025 table, and that is recorded.
        assert config.limit_401k_elective == Decimal("23500")
        assert config.statutory_year == 2025

    def test_the_tabulated_figures_are_the_2025_set_and_are_labelled_so(self):
        """
        The mislabelling, asserted. Every figure that shipped under a "2026"
        heading is here under 2025.
        """
        limits = statutory_limits_for_year(2025)

        assert limits.tax_year == 2025
        assert limits.ss_wage_base == Decimal("176100")
        assert limits.limit_401k_elective == Decimal("23500")
        assert limits.limit_401k_catchup_50 == Decimal("7500")
        assert limits.hsa_self_only == Decimal("4300")
        assert limits.hsa_family == Decimal("8550")
        assert limits.limit_simple_ira == Decimal("16500")

    def test_no_table_claims_to_be_2026_until_sprint_793b(self):
        """
        Guards against someone adding a 2026 row with unconfirmed figures, which
        would recreate the defect: a number that reads as authoritative because
        it sits in an authoritative-looking table. When 793b lands with
        practitioner-confirmed figures, delete this test in the same commit.
        """
        assert 2026 not in STATUTORY_LIMITS_BY_YEAR

    def test_every_tabulated_year_carries_provenance(self):
        for year, limits in STATUTORY_LIMITS_BY_YEAR.items():
            assert limits.tax_year == year
            assert limits.source, year
            assert limits.verified_by, year
