"""
W-2 / W-3 Reconciliation Engine (Sprint 636).

Reconciles per-employee payroll system totals against draft W-2 amounts
and the four quarterly Forms 941 to catch the discrepancies that
produce amended filings and IRS notices: mismatched Social Security
and Medicare wages, mis-applied wage base caps, over-contributions to
HSAs and retirement plans, and 941 totals that do not agree to the W-3
summary.

Zero-storage: form-input only. The engine is a diagnostic tool that
flags discrepancies for practitioner review — it does not determine
the "correct" value when payroll and W-2 disagree.

Reference limits (tax year 2026):
  * Social Security wage base: $176,100
  * SS employee rate: 6.2%
  * Medicare employee rate: 1.45%
  * Additional Medicare (employee): 0.9% above $200,000
  * HSA self-only: $4,300
  * HSA family: $8,550
  * 401(k) elective deferral: $23,500
  * 401(k) catch-up (age 50+): $7,500
  * 401(k) secure 2.0 catch-up (age 60-63): $11,250
  * SIMPLE IRA elective: $16,500
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

CENT = Decimal("0.01")
ZERO = Decimal("0")

# --- 2026 reference values (caller override via Form941ComparisonConfig) ---
DEFAULT_SS_WAGE_BASE = Decimal("176100")
DEFAULT_SS_RATE = Decimal("0.062")
DEFAULT_MEDICARE_RATE = Decimal("0.0145")
DEFAULT_ADDITIONAL_MEDICARE_RATE = Decimal("0.009")
DEFAULT_ADDITIONAL_MEDICARE_THRESHOLD = Decimal("200000")
DEFAULT_HSA_SELF_ONLY = Decimal("4300")
DEFAULT_HSA_FAMILY = Decimal("8550")
DEFAULT_401K_ELECTIVE_LIMIT = Decimal("23500")
DEFAULT_401K_CATCHUP_50 = Decimal("7500")
DEFAULT_401K_CATCHUP_60_63 = Decimal("11250")
DEFAULT_SIMPLE_IRA_LIMIT = Decimal("16500")

# Tolerance for rounding-only differences — $1.00 per line per side.
DEFAULT_TOLERANCE = Decimal("1.00")


class HsaCoverage(str, Enum):
    NONE = "none"
    SELF_ONLY = "self_only"
    FAMILY = "family"


class DiscrepancySeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DiscrepancyKind(str, Enum):
    SS_WAGES = "ss_wages"
    SS_WAGE_BASE_EXCEEDED = "ss_wage_base_exceeded"
    SS_TAX_WITHHOLDING = "ss_tax_withholding"
    MEDICARE_WAGES = "medicare_wages"
    MEDICARE_WITHHOLDING = "medicare_withholding"
    ADDITIONAL_MEDICARE = "additional_medicare"
    FEDERAL_WAGES = "federal_wages"
    FEDERAL_WITHHOLDING = "federal_withholding"
    HSA_OVER_LIMIT = "hsa_over_limit"
    RETIREMENT_OVER_LIMIT = "retirement_over_limit"
    FORM_941_MISMATCH = "form_941_mismatch"


class W2ReconciliationInputError(ValueError):
    """Raised for invalid reconciliation inputs."""


# =============================================================================
# Input dataclasses
# =============================================================================


@dataclass
class EmployeePayroll:
    """Per-employee YTD amounts from the payroll system."""

    employee_id: str
    employee_name: str
    age: int | None = None
    federal_wages: Decimal = ZERO  # Box 1
    federal_withholding: Decimal = ZERO  # Box 2
    ss_wages: Decimal = ZERO  # Box 3
    ss_tax_withheld: Decimal = ZERO  # Box 4
    medicare_wages: Decimal = ZERO  # Box 5
    medicare_tax_withheld: Decimal = ZERO  # Box 6
    hsa_contributions: Decimal = ZERO  # Box 12 code W
    hsa_coverage: HsaCoverage = HsaCoverage.NONE
    retirement_401k: Decimal = ZERO  # Box 12 code D / DD / EE (elective)
    retirement_simple_ira: Decimal = ZERO  # Box 12 code S
    retirement_plan_type: str | None = None  # "401k" / "simple_ira" / None

    def __post_init__(self) -> None:
        for attr in (
            "federal_wages",
            "federal_withholding",
            "ss_wages",
            "ss_tax_withheld",
            "medicare_wages",
            "medicare_tax_withheld",
            "hsa_contributions",
            "retirement_401k",
            "retirement_simple_ira",
        ):
            value = getattr(self, attr)
            if isinstance(value, (int, float)):
                setattr(self, attr, Decimal(str(value)))


@dataclass
class EmployeeW2Draft:
    """The draft W-2 amounts the reconciliation is compared against.

    If a caller can't supply a draft W-2 (e.g. pre-generation review),
    set every field to the payroll value and the reconciliation becomes
    self-consistency only — the limit and wage-base checks still fire.
    """

    employee_id: str
    box_1_federal_wages: Decimal = ZERO
    box_2_federal_withholding: Decimal = ZERO
    box_3_ss_wages: Decimal = ZERO
    box_4_ss_tax_withheld: Decimal = ZERO
    box_5_medicare_wages: Decimal = ZERO
    box_6_medicare_tax_withheld: Decimal = ZERO
    box_12_code_w_hsa: Decimal = ZERO
    box_12_code_d_401k: Decimal = ZERO
    box_12_code_s_simple: Decimal = ZERO

    def __post_init__(self) -> None:
        for attr in (
            "box_1_federal_wages",
            "box_2_federal_withholding",
            "box_3_ss_wages",
            "box_4_ss_tax_withheld",
            "box_5_medicare_wages",
            "box_6_medicare_tax_withheld",
            "box_12_code_w_hsa",
            "box_12_code_d_401k",
            "box_12_code_s_simple",
        ):
            value = getattr(self, attr)
            if isinstance(value, (int, float)):
                setattr(self, attr, Decimal(str(value)))


@dataclass
class Form941Quarter:
    """A single Form 941 quarterly filing (employer side of the check)."""

    quarter: int  # 1-4
    total_federal_wages: Decimal = ZERO  # 941 line 2
    total_federal_withholding: Decimal = ZERO  # 941 line 3
    total_ss_wages: Decimal = ZERO  # 941 line 5a col 1
    total_medicare_wages: Decimal = ZERO  # 941 line 5c col 1

    def __post_init__(self) -> None:
        if self.quarter not in (1, 2, 3, 4):
            raise W2ReconciliationInputError(f"Form 941 quarter must be 1-4 (got {self.quarter})")
        for attr in (
            "total_federal_wages",
            "total_federal_withholding",
            "total_ss_wages",
            "total_medicare_wages",
        ):
            value = getattr(self, attr)
            if isinstance(value, (int, float)):
                setattr(self, attr, Decimal(str(value)))


@dataclass
class W2ReconciliationConfig:
    tax_year: int
    employees: list[EmployeePayroll]
    w2_drafts: list[EmployeeW2Draft] = field(default_factory=list)
    form_941_quarters: list[Form941Quarter] = field(default_factory=list)
    tolerance: Decimal = DEFAULT_TOLERANCE
    ss_wage_base: Decimal = DEFAULT_SS_WAGE_BASE
    ss_rate: Decimal = DEFAULT_SS_RATE
    medicare_rate: Decimal = DEFAULT_MEDICARE_RATE
    additional_medicare_rate: Decimal = DEFAULT_ADDITIONAL_MEDICARE_RATE
    additional_medicare_threshold: Decimal = DEFAULT_ADDITIONAL_MEDICARE_THRESHOLD
    hsa_self_only_limit: Decimal = DEFAULT_HSA_SELF_ONLY
    hsa_family_limit: Decimal = DEFAULT_HSA_FAMILY
    limit_401k_elective: Decimal = DEFAULT_401K_ELECTIVE_LIMIT
    limit_401k_catchup_50: Decimal = DEFAULT_401K_CATCHUP_50
    limit_401k_catchup_60_63: Decimal = DEFAULT_401K_CATCHUP_60_63
    limit_simple_ira: Decimal = DEFAULT_SIMPLE_IRA_LIMIT


# =============================================================================
# Output dataclasses
# =============================================================================


@dataclass
class Discrepancy:
    employee_id: str
    employee_name: str
    kind: DiscrepancyKind
    severity: DiscrepancySeverity
    expected: Decimal
    actual: Decimal
    difference: Decimal
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "kind": self.kind.value,
            "severity": self.severity.value,
            "expected": str(self.expected),
            "actual": str(self.actual),
            "difference": str(self.difference),
            "message": self.message,
        }


@dataclass
class Form941Mismatch:
    quarter: int | None  # None when comparing the 4-quarter sum to W-3
    kind: DiscrepancyKind
    severity: DiscrepancySeverity
    expected: Decimal  # Payroll / W-2 side
    actual: Decimal  # 941 side
    difference: Decimal
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "quarter": self.quarter,
            "kind": self.kind.value,
            "severity": self.severity.value,
            "expected": str(self.expected),
            "actual": str(self.actual),
            "difference": str(self.difference),
            "message": self.message,
        }


@dataclass
class W3Totals:
    """The W-3 summary row — sum of every W-2."""

    total_federal_wages: Decimal
    total_federal_withholding: Decimal
    total_ss_wages: Decimal
    total_ss_tax_withheld: Decimal
    total_medicare_wages: Decimal
    total_medicare_tax_withheld: Decimal
    employee_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_federal_wages": str(self.total_federal_wages),
            "total_federal_withholding": str(self.total_federal_withholding),
            "total_ss_wages": str(self.total_ss_wages),
            "total_ss_tax_withheld": str(self.total_ss_tax_withheld),
            "total_medicare_wages": str(self.total_medicare_wages),
            "total_medicare_tax_withheld": str(self.total_medicare_tax_withheld),
            "employee_count": self.employee_count,
        }


@dataclass
class W2ReconciliationResult:
    tax_year: int
    employee_discrepancies: list[Discrepancy]
    form_941_mismatches: list[Form941Mismatch]
    w3_totals: W3Totals
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_year": self.tax_year,
            "employee_discrepancies": [d.to_dict() for d in self.employee_discrepancies],
            "form_941_mismatches": [m.to_dict() for m in self.form_941_mismatches],
            "w3_totals": self.w3_totals.to_dict(),
            "summary": self.summary,
        }


# =============================================================================
# Helpers
# =============================================================================


def _quantise(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _severity_for_diff(diff: Decimal, tolerance: Decimal) -> DiscrepancySeverity:
    abs_diff = abs(diff)
    if abs_diff <= tolerance:
        return DiscrepancySeverity.LOW
    if abs_diff <= tolerance * Decimal("100"):
        return DiscrepancySeverity.MEDIUM
    return DiscrepancySeverity.HIGH


def _hsa_limit(coverage: HsaCoverage, config: W2ReconciliationConfig) -> Decimal:
    if coverage == HsaCoverage.SELF_ONLY:
        return config.hsa_self_only_limit
    if coverage == HsaCoverage.FAMILY:
        return config.hsa_family_limit
    return ZERO


def _retirement_limit(employee: EmployeePayroll, config: W2ReconciliationConfig) -> Decimal:
    """Compute the employee's max elective deferral including catch-up."""
    if employee.retirement_plan_type == "simple_ira":
        base = config.limit_simple_ira
    else:
        base = config.limit_401k_elective

    if employee.age is None:
        return base
    if 60 <= employee.age <= 63 and employee.retirement_plan_type != "simple_ira":
        return base + config.limit_401k_catchup_60_63
    if employee.age >= 50:
        return base + config.limit_401k_catchup_50
    return base


# =============================================================================
# Core checks
# =============================================================================


def _check_employee(
    employee: EmployeePayroll,
    w2: EmployeeW2Draft,
    config: W2ReconciliationConfig,
) -> list[Discrepancy]:
    """Run every per-employee check, return the discrepancies found."""
    issues: list[Discrepancy] = []
    tolerance = config.tolerance

    # --- SS wages ---
    expected_ss = min(employee.ss_wages, config.ss_wage_base)
    if employee.ss_wages > config.ss_wage_base:
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.SS_WAGE_BASE_EXCEEDED,
                severity=DiscrepancySeverity.HIGH,
                expected=config.ss_wage_base,
                actual=employee.ss_wages,
                difference=employee.ss_wages - config.ss_wage_base,
                message=(
                    f"Payroll SS wages ${employee.ss_wages:,.2f} exceed the "
                    f"${config.ss_wage_base:,.2f} wage base — W-2 box 3 must be capped."
                ),
            )
        )

    ss_wage_diff = w2.box_3_ss_wages - expected_ss
    if abs(ss_wage_diff) > tolerance:
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.SS_WAGES,
                severity=_severity_for_diff(ss_wage_diff, tolerance),
                expected=expected_ss,
                actual=w2.box_3_ss_wages,
                difference=ss_wage_diff,
                message=(
                    f"W-2 box 3 (${w2.box_3_ss_wages:,.2f}) does not match expected "
                    f"capped SS wages (${expected_ss:,.2f})."
                ),
            )
        )

    # --- SS tax withholding should equal ss_wages × SS rate ---
    expected_ss_tax = expected_ss * config.ss_rate
    ss_tax_diff = w2.box_4_ss_tax_withheld - expected_ss_tax
    if abs(ss_tax_diff) > tolerance:
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.SS_TAX_WITHHOLDING,
                severity=_severity_for_diff(ss_tax_diff, tolerance),
                expected=_quantise(expected_ss_tax),
                actual=w2.box_4_ss_tax_withheld,
                difference=ss_tax_diff,
                message=(
                    f"W-2 box 4 SS tax withheld (${w2.box_4_ss_tax_withheld:,.2f}) "
                    f"deviates from expected "
                    f"(${_quantise(expected_ss_tax):,.2f} at "
                    f"{config.ss_rate * 100:.2f}%)."
                ),
            )
        )

    # --- Medicare wages (no cap) ---
    medicare_diff = w2.box_5_medicare_wages - employee.medicare_wages
    if abs(medicare_diff) > tolerance:
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.MEDICARE_WAGES,
                severity=_severity_for_diff(medicare_diff, tolerance),
                expected=employee.medicare_wages,
                actual=w2.box_5_medicare_wages,
                difference=medicare_diff,
                message=(
                    f"W-2 box 5 Medicare wages (${w2.box_5_medicare_wages:,.2f}) "
                    f"differ from payroll (${employee.medicare_wages:,.2f})."
                ),
            )
        )

    # --- Medicare tax: standard 1.45% + 0.9% additional above threshold ---
    standard_medicare = employee.medicare_wages * config.medicare_rate
    excess = max(ZERO, employee.medicare_wages - config.additional_medicare_threshold)
    additional_medicare = excess * config.additional_medicare_rate
    expected_medicare_total = standard_medicare + additional_medicare
    med_withhold_diff = w2.box_6_medicare_tax_withheld - expected_medicare_total
    if abs(med_withhold_diff) > tolerance:
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.MEDICARE_WITHHOLDING,
                severity=_severity_for_diff(med_withhold_diff, tolerance),
                expected=_quantise(expected_medicare_total),
                actual=w2.box_6_medicare_tax_withheld,
                difference=med_withhold_diff,
                message=(
                    f"W-2 box 6 Medicare tax (${w2.box_6_medicare_tax_withheld:,.2f}) "
                    f"deviates from expected "
                    f"(${_quantise(expected_medicare_total):,.2f})."
                ),
            )
        )

    # Additional Medicare: require at least `excess * rate` when the
    # employee earned above threshold; fire as its own discrepancy so
    # payroll can see the wage-threshold trip.
    if excess > ZERO and additional_medicare > tolerance:
        # Informational — already included in MEDICARE_WITHHOLDING expected;
        # surfaced separately so the caller can see the threshold crossed.
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.ADDITIONAL_MEDICARE,
                severity=DiscrepancySeverity.LOW,
                expected=_quantise(additional_medicare),
                actual=_quantise(additional_medicare),
                difference=ZERO,
                message=(
                    f"Additional Medicare threshold crossed — "
                    f"${excess:,.2f} above ${config.additional_medicare_threshold:,.2f} "
                    f"triggers ${_quantise(additional_medicare):,.2f} "
                    f"at {config.additional_medicare_rate * 100:.1f}%."
                ),
            )
        )

    # --- Federal wages (Box 1) ---
    fed_wage_diff = w2.box_1_federal_wages - employee.federal_wages
    if abs(fed_wage_diff) > tolerance:
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.FEDERAL_WAGES,
                severity=_severity_for_diff(fed_wage_diff, tolerance),
                expected=employee.federal_wages,
                actual=w2.box_1_federal_wages,
                difference=fed_wage_diff,
                message=(
                    f"W-2 box 1 federal wages (${w2.box_1_federal_wages:,.2f}) "
                    f"differ from payroll (${employee.federal_wages:,.2f})."
                ),
            )
        )

    fed_withhold_diff = w2.box_2_federal_withholding - employee.federal_withholding
    if abs(fed_withhold_diff) > tolerance:
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.FEDERAL_WITHHOLDING,
                severity=_severity_for_diff(fed_withhold_diff, tolerance),
                expected=employee.federal_withholding,
                actual=w2.box_2_federal_withholding,
                difference=fed_withhold_diff,
                message=(
                    f"W-2 box 2 federal tax withheld "
                    f"(${w2.box_2_federal_withholding:,.2f}) differs from payroll "
                    f"(${employee.federal_withholding:,.2f})."
                ),
            )
        )

    # --- HSA over-limit ---
    hsa_limit = _hsa_limit(employee.hsa_coverage, config)
    if employee.hsa_coverage != HsaCoverage.NONE and employee.hsa_contributions > hsa_limit:
        over = employee.hsa_contributions - hsa_limit
        issues.append(
            Discrepancy(
                employee_id=employee.employee_id,
                employee_name=employee.employee_name,
                kind=DiscrepancyKind.HSA_OVER_LIMIT,
                severity=DiscrepancySeverity.HIGH,
                expected=hsa_limit,
                actual=employee.hsa_contributions,
                difference=over,
                message=(
                    f"HSA contribution ${employee.hsa_contributions:,.2f} exceeds "
                    f"the {employee.hsa_coverage.value.replace('_', '-')} limit "
                    f"of ${hsa_limit:,.2f} by ${over:,.2f}. "
                    "Excess is subject to 6% excise tax unless withdrawn."
                ),
            )
        )

    # --- Retirement over-limit ---
    if employee.retirement_plan_type:
        retirement_total = (
            employee.retirement_401k if employee.retirement_plan_type == "401k" else employee.retirement_simple_ira
        )
        limit = _retirement_limit(employee, config)
        if retirement_total > limit:
            over = retirement_total - limit
            issues.append(
                Discrepancy(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    kind=DiscrepancyKind.RETIREMENT_OVER_LIMIT,
                    severity=DiscrepancySeverity.HIGH,
                    expected=limit,
                    actual=retirement_total,
                    difference=over,
                    message=(
                        f"Elective deferral ${retirement_total:,.2f} exceeds the "
                        f"{employee.retirement_plan_type} limit of ${limit:,.2f} by "
                        f"${over:,.2f}. Excess must be distributed by April 15."
                    ),
                )
            )

    return issues


def _check_form_941(
    employees: list[EmployeePayroll],
    quarters: list[Form941Quarter],
    tolerance: Decimal,
) -> list[Form941Mismatch]:
    """Compare the sum of all 4 quarterly 941s to the payroll YTD totals."""
    if not quarters:
        return []

    total_941_fed_wages = sum((q.total_federal_wages for q in quarters), ZERO)
    total_941_fed_withhold = sum((q.total_federal_withholding for q in quarters), ZERO)
    total_941_ss_wages = sum((q.total_ss_wages for q in quarters), ZERO)
    total_941_medicare_wages = sum((q.total_medicare_wages for q in quarters), ZERO)

    total_payroll_fed_wages = sum((e.federal_wages for e in employees), ZERO)
    total_payroll_fed_withhold = sum((e.federal_withholding for e in employees), ZERO)
    total_payroll_ss_wages = sum((e.ss_wages for e in employees), ZERO)
    total_payroll_medicare = sum((e.medicare_wages for e in employees), ZERO)

    mismatches: list[Form941Mismatch] = []

    for kind, expected, actual, label in (
        (DiscrepancyKind.FEDERAL_WAGES, total_payroll_fed_wages, total_941_fed_wages, "federal wages"),
        (
            DiscrepancyKind.FEDERAL_WITHHOLDING,
            total_payroll_fed_withhold,
            total_941_fed_withhold,
            "federal withholding",
        ),
        (DiscrepancyKind.SS_WAGES, total_payroll_ss_wages, total_941_ss_wages, "Social Security wages"),
        (
            DiscrepancyKind.MEDICARE_WAGES,
            total_payroll_medicare,
            total_941_medicare_wages,
            "Medicare wages",
        ),
    ):
        diff = actual - expected
        if abs(diff) > tolerance:
            mismatches.append(
                Form941Mismatch(
                    quarter=None,
                    kind=kind,
                    severity=DiscrepancySeverity.HIGH if abs(diff) > tolerance * 100 else DiscrepancySeverity.MEDIUM,
                    expected=_quantise(expected),
                    actual=_quantise(actual),
                    difference=_quantise(diff),
                    message=(
                        f"Sum of 4 quarters of Form 941 {label} (${actual:,.2f}) "
                        f"disagrees with payroll YTD (${expected:,.2f})."
                    ),
                )
            )

    return mismatches


# =============================================================================
# Public entry point
# =============================================================================


def reconcile_w2(config: W2ReconciliationConfig) -> W2ReconciliationResult:
    """Run the full W-2 / W-3 / 941 reconciliation."""
    if config.tax_year < 2000 or config.tax_year > 2099:
        raise W2ReconciliationInputError(f"Tax year must be a 4-digit year between 2000 and 2099 ({config.tax_year})")

    w2_by_id: dict[str, EmployeeW2Draft] = {w.employee_id: w for w in config.w2_drafts}

    employee_discrepancies: list[Discrepancy] = []
    employees_missing_w2: list[str] = []

    for employee in config.employees:
        w2 = w2_by_id.get(employee.employee_id)
        if w2 is None:
            # Build a self-consistent default from payroll so the limit
            # checks still run even when no draft W-2 is supplied.
            w2 = EmployeeW2Draft(
                employee_id=employee.employee_id,
                box_1_federal_wages=employee.federal_wages,
                box_2_federal_withholding=employee.federal_withholding,
                box_3_ss_wages=min(employee.ss_wages, config.ss_wage_base),
                box_4_ss_tax_withheld=_quantise(min(employee.ss_wages, config.ss_wage_base) * config.ss_rate),
                box_5_medicare_wages=employee.medicare_wages,
                box_6_medicare_tax_withheld=_quantise(
                    employee.medicare_wages * config.medicare_rate
                    + max(ZERO, employee.medicare_wages - config.additional_medicare_threshold)
                    * config.additional_medicare_rate
                ),
                box_12_code_w_hsa=employee.hsa_contributions,
                box_12_code_d_401k=employee.retirement_401k,
                box_12_code_s_simple=employee.retirement_simple_ira,
            )
            employees_missing_w2.append(employee.employee_id)
        employee_discrepancies.extend(_check_employee(employee, w2, config))

    # --- W-3 totals (sum of every W-2) ---
    w3 = W3Totals(
        total_federal_wages=_quantise(sum((w.box_1_federal_wages for w in config.w2_drafts), ZERO)),
        total_federal_withholding=_quantise(sum((w.box_2_federal_withholding for w in config.w2_drafts), ZERO)),
        total_ss_wages=_quantise(sum((w.box_3_ss_wages for w in config.w2_drafts), ZERO)),
        total_ss_tax_withheld=_quantise(sum((w.box_4_ss_tax_withheld for w in config.w2_drafts), ZERO)),
        total_medicare_wages=_quantise(sum((w.box_5_medicare_wages for w in config.w2_drafts), ZERO)),
        total_medicare_tax_withheld=_quantise(sum((w.box_6_medicare_tax_withheld for w in config.w2_drafts), ZERO)),
        employee_count=len(config.w2_drafts),
    )

    # --- Form 941 check ---
    form_941_mismatches = _check_form_941(config.employees, config.form_941_quarters, config.tolerance)

    # --- Summary ---
    by_kind: dict[str, int] = defaultdict(int)
    for d in employee_discrepancies:
        by_kind[d.kind.value] += 1
    for m in form_941_mismatches:
        by_kind[m.kind.value] += 1

    summary = {
        "employee_count": len(config.employees),
        "employees_missing_w2_draft": employees_missing_w2,
        "total_employee_discrepancies": len(employee_discrepancies),
        "total_form_941_mismatches": len(form_941_mismatches),
        "discrepancies_by_kind": dict(by_kind),
    }

    return W2ReconciliationResult(
        tax_year=config.tax_year,
        employee_discrepancies=employee_discrepancies,
        form_941_mismatches=form_941_mismatches,
        w3_totals=w3,
        summary=summary,
    )
