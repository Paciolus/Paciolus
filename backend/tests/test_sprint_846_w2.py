"""
Sprint 846 — W-2 reconciliation findings W4 (W-3 vs the 941s), W8 (a W-3 with
no drafts) and W9 (duplicate or missing 941 quarters) from the Sprint 823
discovery (reports/sprint-823-discovery-2026-10-23.md).
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from w2_reconciliation_engine import (
    DiscrepancyKind,
    EmployeePayroll,
    EmployeeW2Draft,
    Form941Quarter,
    W2ReconciliationConfig,
    reconcile_w2,
)

D = Decimal


def _employee(employee_id="A1", **overrides) -> EmployeePayroll:
    values = dict(
        employee_id=employee_id,
        employee_name="Alex",
        age=40,
        federal_wages=D("100000"),
        federal_withholding=D("15000"),
        ss_wages=D("100000"),
        ss_tax_withheld=D("6200"),
        medicare_wages=D("100000"),
        medicare_tax_withheld=D("1450"),
    )
    values.update(overrides)
    return EmployeePayroll(**values)


def _draft(employee: EmployeePayroll, **overrides) -> EmployeeW2Draft:
    values = dict(
        employee_id=employee.employee_id,
        box_1_federal_wages=employee.federal_wages,
        box_2_federal_withholding=employee.federal_withholding,
        box_3_ss_wages=employee.ss_wages,
        box_4_ss_tax_withheld=D("6200.00"),
        box_5_medicare_wages=employee.medicare_wages,
        box_6_medicare_tax_withheld=D("1450.00"),
    )
    values.update(overrides)
    return EmployeeW2Draft(**values)


def _quarters(numbers=(1, 2, 3, 4), **fields) -> list[Form941Quarter]:
    """Four even quarters of the payroll above; ``fields`` overrides every quarter."""
    values = dict(
        total_federal_wages=D("25000"),
        total_federal_withholding=D("3750"),
        total_ss_wages=D("25000"),
        total_medicare_wages=D("25000"),
    )
    values.update(fields)
    return [Form941Quarter(quarter=n, **values) for n in numbers]


def _run(employees, drafts, quarters):
    return reconcile_w2(
        W2ReconciliationConfig(tax_year=2025, employees=employees, w2_drafts=drafts, form_941_quarters=quarters)
    )


class TestW4W3AgainstThe941s:
    def test_w3_that_disagrees_with_941s_is_flagged_even_when_payroll_agrees(self):
        # Payroll and the 941s agree at $100,000; the draft W-2 (and so the W-3)
        # says $90,000. The 941 comparison used to look only at payroll, so the
        # filing pair that the SSA/IRS actually matches went unchecked.
        emp = _employee()
        result = _run([emp], [_draft(emp, box_1_federal_wages=D("90000"))], _quarters())

        w3 = [m for m in result.form_941_mismatches if m.compared_with == "w3"]
        assert [m.kind for m in w3] == [DiscrepancyKind.FEDERAL_WAGES]
        assert w3[0].expected == D("90000.00")
        assert w3[0].actual == D("100000.00")
        assert "W-3" in w3[0].message
        assert not [m for m in result.form_941_mismatches if m.compared_with == "payroll_ytd"]

    def test_941s_that_agree_with_w3_but_not_payroll_flag_only_payroll(self):
        emp = _employee()
        drafts = [_draft(emp, box_1_federal_wages=D("90000"))]
        result = _run([emp], drafts, _quarters(total_federal_wages=D("22500")))

        by_basis = {(m.compared_with, m.kind) for m in result.form_941_mismatches}
        assert by_basis == {("payroll_ytd", DiscrepancyKind.FEDERAL_WAGES)}

    def test_all_four_fields_compared_with_w3(self):
        emp = _employee()
        drafts = [
            _draft(
                emp,
                box_1_federal_wages=D("1"),
                box_2_federal_withholding=D("1"),
                box_3_ss_wages=D("1"),
                box_5_medicare_wages=D("1"),
            )
        ]
        result = _run([emp], drafts, _quarters())
        kinds = {m.kind for m in result.form_941_mismatches if m.compared_with == "w3"}
        assert kinds == {
            DiscrepancyKind.FEDERAL_WAGES,
            DiscrepancyKind.FEDERAL_WITHHOLDING,
            DiscrepancyKind.SS_WAGES,
            DiscrepancyKind.MEDICARE_WAGES,
        }

    def test_no_drafts_means_no_w3_comparison(self):
        emp = _employee()
        result = _run([emp], [], _quarters(total_federal_wages=D("1")))
        assert {m.compared_with for m in result.form_941_mismatches} == {"payroll_ytd"}

    def test_a_941_field_not_supplied_is_not_compared_and_is_disclosed(self):
        # A 941 CSV with no Medicare column used to send "0" for every quarter
        # and produce a HIGH Medicare-wages mismatch against payroll.
        emp = _employee()
        result = _run([emp], [_draft(emp)], _quarters(total_medicare_wages=None))

        assert result.form_941_mismatches == []
        notices = [n for n in result.checks_not_run if n["reason"] == "form_941_field_not_supplied"]
        assert len(notices) == 1
        assert "Medicare wages" in notices[0]["message"]

    def test_a_field_supplied_for_only_some_quarters_is_not_compared(self):
        emp = _employee()
        quarters = _quarters()
        quarters[2].total_federal_withholding = None
        result = _run([emp], [_draft(emp)], quarters)

        assert result.form_941_mismatches == []
        assert any(n["reason"] == "form_941_field_not_supplied" for n in result.checks_not_run)

    def test_serialised_mismatch_carries_its_basis(self):
        emp = _employee()
        out = _run([emp], [_draft(emp, box_1_federal_wages=D("90000"))], _quarters()).to_dict()
        assert out["form_941_mismatches"][0]["compared_with"] == "w3"


class TestW8NoDraftsNoW3:
    def test_no_drafts_yields_no_w3_totals(self):
        # With no drafts the W-3 was reported as six zero totals and an employee
        # count of 0 — indistinguishable from a real, empty W-3.
        result = _run([_employee()], [], [])
        assert result.w3_totals is None
        out = result.to_dict()
        assert out["w3_totals"] is None
        assert "No draft W-2s" in out["summary"]["w3_status"]

    def test_drafts_supplied_still_total(self):
        emp = _employee()
        result = _run([emp], [_draft(emp)], [])
        assert result.w3_totals is not None
        assert result.w3_totals.total_federal_wages == D("100000.00")
        assert result.to_dict()["summary"]["w3_status"] is None


class TestW9QuarterCoverage:
    def test_missing_quarter_flagged_and_annual_tieout_not_run(self):
        # Three quarters compared with a full year of payroll produced a HIGH
        # "941 disagrees" mismatch whose real cause was the absent quarter.
        emp = _employee()
        result = _run([emp], [_draft(emp)], _quarters(numbers=(1, 2, 3)))

        assert result.summary["form_941_quarters_missing"] == [4]
        assert result.summary["form_941_quarters_duplicated"] == []
        assert result.form_941_mismatches == []
        notices = [n for n in result.checks_not_run if n["reason"] == "form_941_quarters_incomplete"]
        assert len(notices) == 1
        assert "Q4" in notices[0]["message"]

    def test_duplicate_quarter_flagged_and_annual_tieout_not_run(self):
        emp = _employee()
        result = _run([emp], [_draft(emp)], _quarters(numbers=(1, 2, 2, 3)))

        assert result.summary["form_941_quarters_duplicated"] == [2]
        assert result.summary["form_941_quarters_missing"] == [4]
        assert result.form_941_mismatches == []
        notice = next(n for n in result.checks_not_run if n["reason"] == "form_941_quarters_incomplete")
        assert "Q2" in notice["message"]

    def test_no_941s_supplied_is_not_a_finding(self):
        emp = _employee()
        result = _run([emp], [_draft(emp)], [])
        assert result.summary["form_941_quarters_missing"] == []
        assert not [n for n in result.checks_not_run if n["reason"].startswith("form_941")]

    def test_complete_quarters_have_no_coverage_issue(self):
        emp = _employee()
        result = _run([emp], [_draft(emp)], _quarters())
        assert result.summary["form_941_quarters_missing"] == []
        assert result.summary["form_941_quarters_duplicated"] == []
        assert result.form_941_mismatches == []
        assert result.checks_not_run == []
