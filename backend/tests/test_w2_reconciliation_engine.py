"""Sprint 636 — W-2 / W-3 Reconciliation engine tests."""

from decimal import Decimal

from w2_reconciliation_engine import (
    DEFAULT_SS_WAGE_BASE,
    DiscrepancyKind,
    DiscrepancySeverity,
    EmployeePayroll,
    EmployeeW2Draft,
    Form941Quarter,
    HsaCoverage,
    W2ReconciliationConfig,
    W2ReconciliationInputError,
    reconcile_w2,
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
            tax_year=2026,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        assert result.employee_discrepancies == []
        assert result.w3_totals.employee_count == 1


class TestSSWageBase:
    def test_ss_wages_above_base_flags_exceeded(self):
        emp = _clean_employee(ss_wages="200000")
        cfg = W2ReconciliationConfig(
            tax_year=2026,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
            form_941_quarters=quarters,
        )
        result = reconcile_w2(cfg)
        assert result.form_941_mismatches == []

    def test_941_totals_diverging_flags_high_severity(self):
        emp = _clean_employee()
        quarters = [
            Form941Quarter(
                quarter=1,
                total_federal_wages=Decimal("50000"),  # Wrong — payroll has 60k
                total_federal_withholding=Decimal("5000"),
                total_ss_wages=Decimal("60000"),
                total_medicare_wages=Decimal("60000"),
            ),
        ]
        cfg = W2ReconciliationConfig(
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
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
            tax_year=2026,
            employees=[emp],
            w2_drafts=[_matching_w2(emp)],
        )
        result = reconcile_w2(cfg)
        d = result.to_dict()
        assert d["tax_year"] == 2026
        assert set(d).issuperset({"employee_discrepancies", "form_941_mismatches", "w3_totals", "summary"})
