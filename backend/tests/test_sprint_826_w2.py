"""
Sprint 826 — W-2 reconciliation findings W3, W4 and W5 from the Sprint 823
discovery (reports/sprint-823-discovery-2026-10-23.md).
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from w2_reconciliation_engine import (
    EmployeePayroll,
    EmployeeW2Draft,
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
        box_12_code_d_401k=employee.retirement_401k,
        box_12_code_w_hsa=employee.hsa_contributions,
        box_12_code_s_simple=employee.retirement_simple_ira,
    )
    values.update(overrides)
    return EmployeeW2Draft(**values)


def _kinds(employees, drafts) -> list[str]:
    result = reconcile_w2(W2ReconciliationConfig(tax_year=2025, employees=employees, w2_drafts=drafts)).to_dict()
    return [d["kind"] for d in result["employee_discrepancies"]]


def test_clean_employee_has_no_discrepancies():
    employee = _employee()
    assert _kinds([employee], [_draft(employee)]) == []


def test_box_4_is_compared_with_what_payroll_actually_withheld():
    """W3: payroll withheld $15,500 while box 4 said $6,200 — nothing was flagged."""
    employee = _employee(ss_tax_withheld=D("15500"))
    assert "ss_tax_withheld_vs_payroll" in _kinds([employee], [_draft(employee)])


def test_box_12_codes_are_compared_with_payroll():
    """W3: draft code D $1,000 against payroll $10,000 raised nothing."""
    employee = _employee(retirement_401k=D("10000"), retirement_plan_type="401k")
    kinds = _kinds([employee], [_draft(employee, box_12_code_d_401k=D("1000"))])
    assert "box_12_vs_payroll" in kinds


def test_deferral_over_the_limit_is_flagged_without_a_plan_type():
    """W5: $30,000 of 401(k) deferrals at age 40 with no plan type raised nothing."""
    employee = _employee(retirement_401k=D("30000"))
    assert "retirement_over_limit" in _kinds([employee], [_draft(employee)])


def test_duplicate_orphan_and_padded_ids_are_reported():
    """W4: the duplicate replaced the first draft, the orphan was summed silently,
    and "B1 " failed to match B1."""
    a1, b1 = _employee("A1"), _employee("B1")
    drafts = [_draft(a1), _draft(a1), _draft(b1, employee_id="B1 "), _draft(_employee("ZZ"))]
    summary = reconcile_w2(W2ReconciliationConfig(tax_year=2025, employees=[a1, b1], w2_drafts=drafts)).summary
    assert summary["duplicate_w2_drafts"] == ["A1"]
    assert summary["orphan_w2_drafts"] == ["ZZ"]
    assert summary["employees_missing_w2_draft"] == []
