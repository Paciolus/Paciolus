"""
Sprint 826 — W1 (SIMPLE IRA catch-up) and W2 (HSA age-55 catch-up) from the
Sprint 823 discovery (reports/sprint-823-discovery-2026-10-23.md).

CEO decision "option C": the catch-up limits are *optional* statutory fields.
Supplied (year table or request override) -> the check runs. Absent -> the check
does not run and ``checks_not_run`` says so; an amount over the base limit is
still reported, but without asserting an excess contribution. The same applies
when the employee's age is not in the data.

2025 figures under test: HSA catch-up $1,000 (IRC §223(b)(3)(B)); SIMPLE
catch-up $3,500 and age 60-63 $5,250 (IRC §414(v); IRS Notice 2024-80).
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from w2_reconciliation_engine import (
    DiscrepancyKind,
    DiscrepancySeverity,
    EmployeePayroll,
    HsaCoverage,
    W2ReconciliationConfig,
    reconcile_w2,
    statutory_limits_for_year,
)

D = Decimal

# The eleven fields a 2026 caller fully overrides today (Sprint 793a / 811).
# Illustrative values only — this file tests the override contract, not 2026 law.
OLD_STYLE_FULL_OVERRIDE = dict(
    ss_wage_base=D("184500"),
    ss_rate=D("0.062"),
    medicare_rate=D("0.0145"),
    additional_medicare_rate=D("0.009"),
    additional_medicare_threshold=D("200000"),
    hsa_self_only_limit=D("4400"),
    hsa_family_limit=D("8750"),
    limit_401k_elective=D("24500"),
    limit_401k_catchup_50=D("8000"),
    limit_401k_catchup_60_63=D("11250"),
    limit_simple_ira=D("17000"),
)


def _employee(employee_id="E1", **overrides) -> EmployeePayroll:
    values = dict(
        employee_id=employee_id,
        employee_name="Pat",
        age=40,
        federal_wages=D("60000"),
        ss_wages=D("60000"),
        medicare_wages=D("60000"),
    )
    values.update(overrides)
    return EmployeePayroll(**values)


def _run(employees, tax_year=2025, **limits):
    # No drafts: the engine builds self-consistent ones, so only the limit
    # checks can produce HSA / retirement findings.
    return reconcile_w2(W2ReconciliationConfig(tax_year=tax_year, employees=employees, **limits))


def _of(result, kind: DiscrepancyKind):
    return [d for d in result.employee_discrepancies if d.kind == kind]


def _notice(result, check: str):
    matches = [n for n in result.checks_not_run if n["check"] == check]
    return matches[0] if matches else None


# ---------------------------------------------------------------------------
# The 2025 table carries the catch-ups, each with a source
# ---------------------------------------------------------------------------


def test_2025_table_carries_the_catchup_figures_with_their_source():
    limits = statutory_limits_for_year(2025)
    assert limits.hsa_catchup_55 == D("1000")
    assert limits.limit_simple_catchup_50 == D("3500")
    assert limits.limit_simple_catchup_60_63 == D("5250")
    assert "§223(b)(3)" in limits.catchup_source
    assert "§414(v)" in limits.catchup_source
    assert "Notice 2024-80" in limits.catchup_source


# ---------------------------------------------------------------------------
# W2 — HSA age-55 catch-up
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "coverage, contribution",
    [(HsaCoverage.SELF_ONLY, "5300"), (HsaCoverage.FAMILY, "9550")],
)
def test_hsa_catchup_within_limit_for_55_plus_is_not_flagged(coverage, contribution):
    """The W2 defect: $4,300 + $1,000 at age 56 drew HIGH with an excise message."""
    result = _run([_employee(age=56, hsa_coverage=coverage, hsa_contributions=D(contribution))])
    assert _of(result, DiscrepancyKind.HSA_OVER_LIMIT) == []
    assert result.checks_not_run == []


def test_hsa_over_limit_including_catchup_is_flagged_and_cites_the_source():
    result = _run([_employee(age=56, hsa_coverage=HsaCoverage.SELF_ONLY, hsa_contributions=D("5400"))])
    [finding] = _of(result, DiscrepancyKind.HSA_OVER_LIMIT)
    assert finding.severity == DiscrepancySeverity.HIGH
    assert finding.expected == D("5300")
    assert finding.difference == D("100")
    assert "IRC §223(b)(3)" in finding.message
    assert "excise" in finding.message


def test_hsa_catchup_does_not_apply_below_55():
    result = _run([_employee(age=54, hsa_coverage=HsaCoverage.SELF_ONLY, hsa_contributions=D("5000"))])
    [finding] = _of(result, DiscrepancyKind.HSA_OVER_LIMIT)
    assert finding.expected == D("4300")
    assert finding.difference == D("700")


def test_hsa_over_base_with_no_age_is_reported_without_asserting_an_excess():
    """No age -> catch-up eligibility unknown. Still HIGH (conservative), but the
    message must not assert an excise-tax violation, and the run says why."""
    result = _run([_employee(age=None, hsa_coverage=HsaCoverage.SELF_ONLY, hsa_contributions=D("4800"))])
    [finding] = _of(result, DiscrepancyKind.HSA_OVER_LIMIT)
    assert finding.severity == DiscrepancySeverity.HIGH
    assert finding.expected == D("4300")
    assert "excise" not in finding.message
    assert "not verifiable" in finding.message
    assert "Not asserted as an excess" in finding.message

    notice = _notice(result, "hsa_catchup_age_unknown")
    assert notice is not None
    assert notice["reason"] == "age_not_supplied"
    assert notice["employee_ids"] == ["E1"]


def test_hsa_over_even_the_catchup_with_no_age_is_a_definite_excess():
    """Above base + catch-up the excess exists at any age; report the certain part."""
    result = _run([_employee(age=None, hsa_coverage=HsaCoverage.SELF_ONLY, hsa_contributions=D("5500"))])
    [finding] = _of(result, DiscrepancyKind.HSA_OVER_LIMIT)
    assert finding.expected == D("5300")
    assert finding.difference == D("200")
    assert "excise" in finding.message
    assert _notice(result, "hsa_catchup_age_unknown") is None


# ---------------------------------------------------------------------------
# W1 — SIMPLE IRA catch-up has its own figures
# ---------------------------------------------------------------------------


def test_simple_catchup_50_uses_the_simple_figure_not_the_401k_one():
    """Old code allowed $16,500 + $7,500 (the 401(k) catch-up). SIMPLE is $3,500."""
    result = _run([_employee(age=55, retirement_plan_type="simple_ira", retirement_simple_ira=D("21000"))])
    [finding] = _of(result, DiscrepancyKind.RETIREMENT_OVER_LIMIT)
    assert finding.expected == D("20000")
    assert finding.difference == D("1000")
    assert "IRC §414(v)(2)(B)(ii)" in finding.message


def test_simple_catchup_50_within_limit_is_not_flagged():
    result = _run([_employee(age=55, retirement_plan_type="simple_ira", retirement_simple_ira=D("20000"))])
    assert _of(result, DiscrepancyKind.RETIREMENT_OVER_LIMIT) == []


def test_simple_catchup_60_63_is_checked():
    """SECURE 2.0 age 60-63: $16,500 + $5,250 = $21,750 for 2025."""
    within = _run([_employee(age=61, retirement_plan_type="simple_ira", retirement_simple_ira=D("21750"))])
    assert _of(within, DiscrepancyKind.RETIREMENT_OVER_LIMIT) == []

    over = _run([_employee(age=61, retirement_plan_type="simple_ira", retirement_simple_ira=D("22000"))])
    [finding] = _of(over, DiscrepancyKind.RETIREMENT_OVER_LIMIT)
    assert finding.expected == D("21750")
    assert finding.difference == D("250")
    assert "IRC §414(v)(2)(E)(ii)" in finding.message


def test_age_64_returns_to_the_ordinary_catchup():
    result = _run([_employee(age=64, retirement_plan_type="simple_ira", retirement_simple_ira=D("21000"))])
    [finding] = _of(result, DiscrepancyKind.RETIREMENT_OVER_LIMIT)
    assert finding.expected == D("20000")


def test_401k_over_base_with_no_age_is_reported_without_asserting_an_excess():
    result = _run([_employee(age=None, retirement_plan_type="401k", retirement_401k=D("25000"))])
    [finding] = _of(result, DiscrepancyKind.RETIREMENT_OVER_LIMIT)
    assert finding.severity == DiscrepancySeverity.HIGH
    assert "April 15" not in finding.message
    assert _notice(result, "401k_catchup_age_unknown")["employee_ids"] == ["E1"]


# ---------------------------------------------------------------------------
# Option C — absent figures: the check does not run, and the result says so
# ---------------------------------------------------------------------------


def test_old_style_full_eleven_field_override_is_still_accepted():
    """Non-breaking: a 2026 request that overrides today's eleven fields must not
    be refused because the new catch-up fields are absent."""
    config = W2ReconciliationConfig(tax_year=2026, employees=[], **OLD_STYLE_FULL_OVERRIDE)
    assert config.statutory_year is None
    assert config.hsa_catchup_55 is None
    assert config.limit_simple_catchup_50 is None
    assert reconcile_w2(config).checks_not_run == []


def test_absent_catchup_limits_produce_check_not_run_notices():
    employees = [
        _employee("H1", age=57, hsa_coverage=HsaCoverage.SELF_ONLY, hsa_contributions=D("5000")),
        _employee("S1", age=55, retirement_plan_type="simple_ira", retirement_simple_ira=D("19000")),
    ]
    result = _run(employees, tax_year=2026, **OLD_STYLE_FULL_OVERRIDE)

    hsa_notice = _notice(result, "hsa_catchup_55")
    assert hsa_notice["reason"] == "limit_not_supplied"
    assert hsa_notice["employee_ids"] == ["H1"]
    assert "not run" in hsa_notice["message"]
    assert "2026" in hsa_notice["message"]
    assert "IRC §223(b)(3)" in hsa_notice["message"]

    simple_notice = _notice(result, "simple_catchup_50")
    assert simple_notice["employee_ids"] == ["S1"]
    assert "IRC §414(v)(2)(B)(ii)" in simple_notice["message"]

    # Over the base limit is still reported, but not as an excess.
    [hsa] = _of(result, DiscrepancyKind.HSA_OVER_LIMIT)
    assert hsa.expected == D("4400")
    assert "excise" not in hsa.message
    assert "not supplied" in hsa.message
    [simple] = _of(result, DiscrepancyKind.RETIREMENT_OVER_LIMIT)
    assert simple.expected == D("17000")
    assert "April 15" not in simple.message

    assert result.to_dict()["checks_not_run"] == result.checks_not_run


def test_supplied_catchup_overrides_run_the_check():
    employees = [
        _employee("H1", age=57, hsa_coverage=HsaCoverage.SELF_ONLY, hsa_contributions=D("5400")),
        _employee("S1", age=61, retirement_plan_type="simple_ira", retirement_simple_ira=D("22250")),
    ]
    result = _run(
        employees,
        tax_year=2026,
        hsa_catchup_55=D("1000"),
        limit_simple_catchup_50=D("3500"),
        limit_simple_catchup_60_63=D("5250"),
        **OLD_STYLE_FULL_OVERRIDE,
    )
    assert _of(result, DiscrepancyKind.HSA_OVER_LIMIT) == []
    assert _of(result, DiscrepancyKind.RETIREMENT_OVER_LIMIT) == []
    assert result.checks_not_run == []


def test_no_notice_when_nobody_could_qualify():
    """A missing figure no employee could use is not reported."""
    employees = [_employee(age=40, retirement_plan_type="simple_ira", retirement_simple_ira=D("10000"))]
    result = _run(employees, tax_year=2026, **OLD_STYLE_FULL_OVERRIDE)
    assert result.checks_not_run == []


def test_age_60_63_tier_does_not_exist_before_2025():
    """SECURE 2.0 §109 applies from 2025; a 2024 run uses the age-50 catch-up and
    does not report a missing 60-63 figure."""
    employees = [_employee(age=61, retirement_plan_type="simple_ira", retirement_simple_ira=D("19500"))]
    result = _run(
        employees,
        tax_year=2024,
        limit_simple_catchup_50=D("3500"),
        **{**OLD_STYLE_FULL_OVERRIDE, "limit_simple_ira": D("16000")},
    )
    assert _of(result, DiscrepancyKind.RETIREMENT_OVER_LIMIT) == []
    assert result.checks_not_run == []
