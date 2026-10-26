"""
W-2 / W-3 Reconciliation Engine (Sprint 636).

Reconciles per-employee payroll system totals against draft W-2 amounts
and the four quarterly Forms 941 to catch the discrepancies that
produce amended filings and IRS notices: mismatched Social Security
and Medicare wages, mis-applied wage base caps, over-contributions to
HSAs and retirement plans, and 941 totals that do not agree to the payroll
year-to-date totals or to the W-3.

The four-quarter 941 sum is compared with payroll YTD and, when draft W-2s are
supplied, with the W-3 totals of those drafts (Sprint 846, W4). Both annual
comparisons run only when exactly one 941 is supplied for each of Q1-Q4, and
only for the 941 fields every quarter supplies; otherwise the result's
``checks_not_run`` says what was missing (W9). With no draft W-2s there is no
W-3, and ``w3_totals`` is ``None`` rather than a row of zeros (W8).

Zero-storage: form-input only. The engine is a diagnostic tool that
flags discrepancies for practitioner review — it does not determine
the "correct" value when payroll and W-2 disagree.

Statutory limits are keyed by tax year in ``STATUTORY_LIMITS_BY_YEAR`` and
resolved per run by ``statutory_limits_for_year()``, which **refuses** a year it
has no table for rather than substituting another year's figures. See the
comment on that table for why (Sprint 811, finding A-7).

Currently tabulated: **tax year 2025 only**. A 2026 engagement must supply the
figures via the per-request ``statutory_limits`` override (Sprint 793a) until the
2026 table lands with practitioner-confirmed values (Sprint 793b).

Catch-up limits (Sprint 826, W1/W2 — CEO decision "option C") are optional:
the HSA age-55 catch-up and the SIMPLE IRA age 50+ / 60-63 catch-ups run only
when their figure is supplied (by the year's table or the override). When it is
absent, or the employee's age is not in the data, the result's
``checks_not_run`` says which check could not run and why, and an amount over
the base limit is reported without asserting an excess contribution.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any, ClassVar

CENT = Decimal("0.01")
ZERO = Decimal("0")


class W2ReconciliationInputError(ValueError):
    """Raised for invalid reconciliation inputs."""


class StatutoryLimitsUnavailableError(W2ReconciliationInputError):
    """
    Raised when no statutory limit table exists for the requested tax year and
    the caller did not supply the figures.

    An input error by design: the fix is in the caller's hands — supply the
    year's limits, or use a year that has a table.
    """


# =============================================================================
# Statutory limits, keyed by tax year
# =============================================================================
#
# Sprint 811 (finding A-7, structural half). This block used to be headed
# `# --- 2026 reference values ---` and every figure in it was the **2025**
# statutory set. A mislabelled block is worse than a stale one, because the
# comment defeats the next reader's check.
#
# The structural defect was larger than the label: `tax_year` is a *required*
# input accepted for any year from 2000 to 2099 (`routes/w2_reconciliation.py`),
# and **no statutory constant was keyed by it**. Every tax year got one fixed
# set of limits, so the tool answered a 2026 question with 2025 law and said
# nothing about it. The route's own docstring admitted as much.
#
# What this sprint changes: the figures are year-keyed, the 2025 set is labelled
# 2025, and `statutory_limits_for_year()` **refuses** a year it has no table for
# rather than falling back. Sprint 793a's per-request overrides are the
# documented escape hatch and are unchanged.
#
# What this sprint deliberately does not change: the 2026 figures. Those need a
# practitioner, and they stay with Sprint 793b. Adding an unconfirmed 2026 row
# here would recreate exactly the defect being fixed — a figure that reads as
# authoritative because it is sitting in an authoritative-looking table.
#
# ---------------------------------------------------------------------------
# Sprint 793b practitioner confirmation list — every statutory figure below.
# Paciolus is not an authority; these restate the authorities' figures, and each
# needs a practitioner's sign-off against the cited source before 793b closes.
#
#   Tax year 2025
#   - SS wage base $176,100 ............ SSA 2025 COLA fact sheet
#   - SS rate 6.2%; Medicare 1.45% ..... IRC §3101(a), §3101(b)(1)
#   - Additional Medicare 0.9% over
#     $200,000 wages .................... IRC §3101(b)(2), §3102(f) (not indexed)
#   - HSA $4,300 self-only / $8,550
#     family ............................ IRC §223(b)(2); Rev. Proc. 2024-25
#   - HSA age-55 catch-up $1,000 ....... IRC §223(b)(3)(B) (statutory, not indexed)
#                                        [Sprint 826, W2]
#   - 401(k) elective $23,500 .......... IRC §402(g); IRS Notice 2024-80
#   - 401(k) catch-up 50+ $7,500 ....... IRC §414(v)(2)(B)(i); IRS Notice 2024-80
#   - 401(k) catch-up 60-63 $11,250 .... IRC §414(v)(2)(E)(i) (SECURE 2.0 §109);
#                                        IRS Notice 2024-80
#   - SIMPLE elective $16,500 .......... IRC §408(p)(2)(E); IRS Notice 2024-80
#   - SIMPLE catch-up 50+ $3,500 ....... IRC §414(v)(2)(B)(ii); IRS Notice 2024-80
#                                        [Sprint 826, W1]
#   - SIMPLE catch-up 60-63 $5,250 ..... IRC §414(v)(2)(E)(ii) (SECURE 2.0 §109);
#                                        IRS Notice 2024-80 [Sprint 826, W1]
#   - HSA excess-contribution excise
#     tax 6% (message text) ............ IRC §4973(a), §4973(g)
#   - Age-60-63 tier from tax year 2025 . SECURE 2.0 Act §109 (taxable years
#                                        beginning after 2024)
#   - Catch-up age tested at year end .. IRC §223(b)(3)(A) ("attained age 55
#                                        before the close of the taxable year");
#                                        IRC §414(v)(5) (age 50 by end of the
#                                        plan year). The engine treats the
#                                        supplied `age` as age at year end.
#
#   Not modelled (practitioner to confirm scope): the SECURE 2.0 §117 increased
#   SIMPLE limits (110% of the base and catch-up) for employers with 25 or fewer
#   employees, or that elect them with a higher employer contribution. A SIMPLE
#   plan using them is checked against the standard figures above.
#
#   Tax year 2026: no row. See `test_no_table_claims_to_be_2026_until_sprint_793b`.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StatutoryLimits:
    """One tax year's federal payroll limits, with its own provenance."""

    tax_year: int
    ss_wage_base: Decimal
    ss_rate: Decimal
    medicare_rate: Decimal
    additional_medicare_rate: Decimal
    additional_medicare_threshold: Decimal
    hsa_self_only: Decimal
    hsa_family: Decimal
    limit_401k_elective: Decimal
    limit_401k_catchup_50: Decimal
    limit_401k_catchup_60_63: Decimal
    limit_simple_ira: Decimal
    source: str
    verified_by: str
    # Sprint 826 (W1/W2, CEO decision "option C"): catch-up limits are
    # **optional**. A year whose figure is not tabulated (or a request override
    # that does not supply it) leaves the field ``None``; the engine then does
    # not run that catch-up check and says so in ``checks_not_run`` rather than
    # skipping it silently or substituting a guess. Optional so that a 2026
    # request which fully overrides the eleven required fields keeps working.
    hsa_catchup_55: Decimal | None = None
    limit_simple_catchup_50: Decimal | None = None
    limit_simple_catchup_60_63: Decimal | None = None
    catchup_source: str | None = None


STATUTORY_LIMITS_BY_YEAR: dict[int, StatutoryLimits] = {
    2025: StatutoryLimits(
        tax_year=2025,
        ss_wage_base=Decimal("176100"),
        ss_rate=Decimal("0.062"),
        medicare_rate=Decimal("0.0145"),
        additional_medicare_rate=Decimal("0.009"),
        additional_medicare_threshold=Decimal("200000"),
        hsa_self_only=Decimal("4300"),
        hsa_family=Decimal("8550"),
        limit_401k_elective=Decimal("23500"),
        limit_401k_catchup_50=Decimal("7500"),
        limit_401k_catchup_60_63=Decimal("11250"),
        limit_simple_ira=Decimal("16500"),
        # Sprint 826 (W2). IRC §223(b)(3)(B): an HSA holder who has attained
        # age 55 before the close of the taxable year may contribute an
        # additional $1,000. A fixed statutory amount — not inflation-indexed
        # (it is not among the §223(g) adjusted amounts), unchanged since 2009.
        hsa_catchup_55=Decimal("1000"),
        # Sprint 826 (W1). IRC §414(v)(2)(B)(ii) SIMPLE catch-up, as adjusted
        # for 2025 by IRS Notice 2024-80 (News Release IR-2024-285): $3,500.
        limit_simple_catchup_50=Decimal("3500"),
        # Sprint 826 (W1). IRC §414(v)(2)(E)(ii), added by SECURE 2.0 Act §109
        # (taxable years beginning after 2024): the greater of $5,000 or 150% of
        # the regular SIMPLE catch-up — $5,250 for 2025 per IRS Notice 2024-80.
        limit_simple_catchup_60_63=Decimal("5250"),
        catchup_source=(
            "IRC §223(b)(3)(B) (HSA age-55 catch-up, $1,000, statutory); "
            "IRC §414(v) and IRS Notice 2024-80 (SIMPLE catch-up $3,500; age 60-63 $5,250)"
        ),
        source="IRS Notice 2024-80 (retirement limits); SSA 2025 wage base; Rev. Proc. 2024-25 (HSA)",
        verified_by=(
            "These are the figures that shipped under a '2026' heading. The 2026-10-22 "
            "full-spectrum review identified them as the 2025 set, which is how they are "
            "now labelled. Not independently re-verified against the notices — Sprint 793b "
            "owns practitioner confirmation of both 2025 and 2026. The three catch-up "
            "figures (Sprint 826) restate IRC §223(b)(3)(B) and IRS Notice 2024-80 and are "
            "on the same 793b confirmation list."
        ),
    ),
}

# The year whose limits the engine uses when a caller does not say. Kept
# explicit rather than "the newest row", so adding a row cannot silently move
# every existing caller onto a different statutory set.
DEFAULT_STATUTORY_YEAR = 2025


def statutory_limits_for_year(tax_year: int) -> StatutoryLimits:
    """
    Return the statutory limits for `tax_year`, or raise.

    Sprint 811: refuses rather than falling back. Answering a 2026 engagement
    with 2025 law and no disclosure is worse than declining to answer, because
    the W-2 and 941 findings it produces — wage-base exceeded, over-limit
    deferral — are wrong in a direction the practitioner cannot see.

    Callers that need a year with no table can supply the figures per request
    via `statutory_limits` (Sprint 793a), which is the documented escape hatch.
    """
    limits = STATUTORY_LIMITS_BY_YEAR.get(tax_year)
    if limits is None:
        available = ", ".join(str(year) for year in sorted(STATUTORY_LIMITS_BY_YEAR))
        # A `W2ReconciliationInputError`, not a bare ValueError: both routes
        # already map that to a verbatim 400, so the practitioner is told what
        # to do. A bare ValueError reaches the analyze route's `sanitize_error`
        # path, which would strip the actionable half, and the CSV export route
        # does not catch it at all — it would 500.
        raise StatutoryLimitsUnavailableError(
            f"No statutory limit table for tax year {tax_year}. "
            f"Tables available: {available}. "
            f"Supply the figures for your filing year via the `statutory_limits` "
            f"override, or wait for the {tax_year} table to be added with "
            f"practitioner-confirmed figures. Substituting another year's limits "
            f"would misstate the wage-base and over-limit findings without saying so."
        )
    return limits


_DEFAULTS = STATUTORY_LIMITS_BY_YEAR[DEFAULT_STATUTORY_YEAR]

# The default year's wage base, which tests use to build matching W-2 drafts.
# Sprint 817: the other ten aliases were unreferenced — the config's field
# defaults now resolve through the year-keyed table, not these names.
DEFAULT_SS_WAGE_BASE = _DEFAULTS.ss_wage_base

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
    # Sprint 826 (W3): the draft against what payroll actually withheld and
    # deferred. Boxes 4 and 6 were only compared with a rate-based expectation,
    # and Box 12 was never compared at all.
    SS_TAX_WITHHELD_VS_PAYROLL = "ss_tax_withheld_vs_payroll"
    MEDICARE_TAX_WITHHELD_VS_PAYROLL = "medicare_tax_withheld_vs_payroll"
    BOX_12_VS_PAYROLL = "box_12_vs_payroll"


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
    # Sprint 846 (W4): ``None`` means "not supplied" and the field is left out
    # of the comparison. A missing CSV column used to arrive as zero and draw a
    # HIGH mismatch for a figure the 941 never stated.
    total_federal_wages: Decimal | None = None  # 941 line 2
    total_federal_withholding: Decimal | None = None  # 941 line 3
    total_ss_wages: Decimal | None = None  # 941 line 5a col 1
    total_medicare_wages: Decimal | None = None  # 941 line 5c col 1

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
    """
    One reconciliation run.

    Sprint 811 (A-7): every statutory field defaults to ``None`` and is resolved
    from ``tax_year`` in ``__post_init__``. A field the caller supplies wins —
    that is Sprint 793a's per-request override, and it is the escape hatch for a
    year with no table. A field left ``None`` for a year with no table raises,
    rather than quietly receiving some other year's law.

    ``statutory_year`` records which table was actually applied, so the memo can
    print the statutory set's effective year and the workpaper carries its own
    provenance.
    """

    tax_year: int
    employees: list[EmployeePayroll]
    w2_drafts: list[EmployeeW2Draft] = field(default_factory=list)
    form_941_quarters: list[Form941Quarter] = field(default_factory=list)
    tolerance: Decimal = DEFAULT_TOLERANCE

    # Annotated `Decimal`, defaulted to None, resolved in __post_init__.
    #
    # The `type: ignore[assignment]` on each is deliberate and is the narrow
    # version of the lie. `None` is only ever the *pre-init* value: by the time
    # any caller can observe these attributes, __post_init__ has either filled
    # them from the tax year's table or raised. Annotating them `Decimal | None`
    # instead would be honest about the default and dishonest about the type
    # every one of the ~30 downstream arithmetic sites actually sees — it added
    # 33 mypy errors of the form `Unsupported operand types for * ("Decimal"
    # and "None")` for a None that cannot reach them. Eleven local, explained
    # suppressions beat thirty-three false positives.
    ss_wage_base: Decimal = None  # type: ignore[assignment]
    ss_rate: Decimal = None  # type: ignore[assignment]
    medicare_rate: Decimal = None  # type: ignore[assignment]
    additional_medicare_rate: Decimal = None  # type: ignore[assignment]
    additional_medicare_threshold: Decimal = None  # type: ignore[assignment]
    hsa_self_only_limit: Decimal = None  # type: ignore[assignment]
    hsa_family_limit: Decimal = None  # type: ignore[assignment]
    limit_401k_elective: Decimal = None  # type: ignore[assignment]
    limit_401k_catchup_50: Decimal = None  # type: ignore[assignment]
    limit_401k_catchup_60_63: Decimal = None  # type: ignore[assignment]
    limit_simple_ira: Decimal = None  # type: ignore[assignment]

    # Sprint 826 (W1/W2): optional catch-up limits. Honestly typed
    # `Decimal | None` — unlike the eleven above, `None` survives __post_init__
    # when neither the caller nor the year's table supplies the figure, and the
    # check that needs it then reports itself in `checks_not_run`. They never
    # count towards "missing": a request that overrides the eleven required
    # fields is still a full override and consults no table (non-breaking).
    hsa_catchup_55: Decimal | None = None
    limit_simple_catchup_50: Decimal | None = None
    limit_simple_catchup_60_63: Decimal | None = None

    # Populated by __post_init__: the tax year whose table supplied any figure
    # the caller did not override, or None when the caller supplied them all.
    statutory_year: int | None = field(default=None, init=False)
    statutory_source: str | None = field(default=None, init=False)

    # (config attribute, StatutoryLimits attribute)
    _STATUTORY_FIELDS: ClassVar[tuple[tuple[str, str], ...]] = (
        ("ss_wage_base", "ss_wage_base"),
        ("ss_rate", "ss_rate"),
        ("medicare_rate", "medicare_rate"),
        ("additional_medicare_rate", "additional_medicare_rate"),
        ("additional_medicare_threshold", "additional_medicare_threshold"),
        ("hsa_self_only_limit", "hsa_self_only"),
        ("hsa_family_limit", "hsa_family"),
        ("limit_401k_elective", "limit_401k_elective"),
        ("limit_401k_catchup_50", "limit_401k_catchup_50"),
        ("limit_401k_catchup_60_63", "limit_401k_catchup_60_63"),
        ("limit_simple_ira", "limit_simple_ira"),
    )
    _OPTIONAL_STATUTORY_FIELDS: ClassVar[tuple[str, ...]] = (
        "hsa_catchup_55",
        "limit_simple_catchup_50",
        "limit_simple_catchup_60_63",
    )

    def __post_init__(self) -> None:
        missing = [attr for attr, _ in self._STATUTORY_FIELDS if getattr(self, attr) is None]
        if not missing:
            # Fully overridden: no table is consulted, so no year is claimed.
            return

        # Raises for a year with no table. Deliberately not caught: a run that
        # cannot name its statutory basis must not produce findings.
        limits = statutory_limits_for_year(self.tax_year)
        for attr, source_attr in self._STATUTORY_FIELDS:
            if getattr(self, attr) is None:
                object.__setattr__(self, attr, getattr(limits, source_attr))
        # Optional catch-ups: fill from the table only where the table has a
        # figure. A table without one leaves `None`, and the check reports
        # itself as not run.
        for attr in self._OPTIONAL_STATUTORY_FIELDS:
            if getattr(self, attr) is None:
                object.__setattr__(self, attr, getattr(limits, attr))
        object.__setattr__(self, "statutory_year", limits.tax_year)
        object.__setattr__(self, "statutory_source", limits.source)


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
    quarter: int | None  # None when comparing the 4-quarter sum
    kind: DiscrepancyKind
    severity: DiscrepancySeverity
    expected: Decimal  # Payroll / W-3 side
    actual: Decimal  # 941 side
    difference: Decimal
    message: str
    # Sprint 846 (W4): what the 941 sum was compared with — "payroll_ytd" or "w3".
    compared_with: str = "payroll_ytd"

    def to_dict(self) -> dict[str, Any]:
        return {
            "quarter": self.quarter,
            "compared_with": self.compared_with,
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
    # Sprint 846 (W8): None when no draft W-2s were supplied — there is no W-3.
    w3_totals: W3Totals | None
    summary: dict[str, Any]
    # Sprint 811 (A-7): which statutory set actually produced these findings.
    # `statutory_basis` is the year whose table was used, or None when the
    # caller supplied every figure. It travels into the response and onto the
    # memo so the workpaper carries its own provenance — a reader can tell
    # whether a wage-base finding was computed under the right year's law
    # without having to go and read the engine.
    statutory_basis: int | None = None
    statutory_basis_source: str | None = None
    # Sprint 826 (W1/W2, option C): checks that could not run, and why — a
    # catch-up limit not supplied for the year, or no age in the data. Never a
    # silent skip: each entry names the check, the employees affected, and the
    # authority whose figure was missing.
    checks_not_run: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tax_year": self.tax_year,
            "employee_discrepancies": [d.to_dict() for d in self.employee_discrepancies],
            "form_941_mismatches": [m.to_dict() for m in self.form_941_mismatches],
            "w3_totals": self.w3_totals.to_dict() if self.w3_totals is not None else None,
            "summary": self.summary,
            "statutory_basis": self.statutory_basis,
            "statutory_basis_source": self.statutory_basis_source,
            "checks_not_run": self.checks_not_run,
            "statutory_basis_note": (
                f"Statutory limits applied: tax year {self.statutory_basis}."
                if self.statutory_basis is not None
                else "Statutory limits applied: supplied by the caller for this run."
            ),
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


# The age 60-63 catch-up tier exists only for taxable years beginning after
# 2024 (SECURE 2.0 Act §109, adding IRC §414(v)(2)(E)). Before that, an employee
# aged 60-63 had the ordinary age-50 catch-up.
FIRST_YEAR_AGE_60_63_CATCHUP = 2025


@dataclass(frozen=True)
class _CatchUpTier:
    """One age-based addition to a contribution limit (Sprint 826, W1/W2)."""

    check: str  # stable id used in `checks_not_run`
    label: str  # human-readable, shown in messages
    citation: str  # the authority the figure comes from
    config_field: str  # the override that supplies it
    min_age: int
    max_age: int | None
    amount: Decimal | None  # None = not supplied for this run

    def applies_to(self, age: int) -> bool:
        return age >= self.min_age and (self.max_age is None or age <= self.max_age)


@dataclass(frozen=True)
class _LimitRule:
    plan_label: str  # "self-only HSA", "401k", "simple_ira"
    base: Decimal
    tiers: tuple[_CatchUpTier, ...]  # most specific first
    age_check: str  # `checks_not_run` id for "no age in the data"


# (check id, label, citation, config field, min age, max age or None)
_TierSpec = tuple[str, str, str, str, int, int | None]

_HSA_CATCHUP_55: _TierSpec = ("hsa_catchup_55", "HSA age-55 catch-up", "IRC §223(b)(3)", "hsa_catchup_55", 55, None)
_401K_CATCHUP_60_63: _TierSpec = (
    "401k_catchup_60_63",
    "401(k) age 60-63 catch-up",
    "IRC §414(v)(2)(E)(i)",
    "limit_401k_catchup_60_63",
    60,
    63,
)
_401K_CATCHUP_50: _TierSpec = (
    "401k_catchup_50",
    "401(k) age 50+ catch-up",
    "IRC §414(v)(2)(B)(i)",
    "limit_401k_catchup_50",
    50,
    None,
)
_SIMPLE_CATCHUP_60_63: _TierSpec = (
    "simple_catchup_60_63",
    "SIMPLE IRA age 60-63 catch-up",
    "IRC §414(v)(2)(E)(ii)",
    "limit_simple_catchup_60_63",
    60,
    63,
)
_SIMPLE_CATCHUP_50: _TierSpec = (
    "simple_catchup_50",
    "SIMPLE IRA age 50+ catch-up",
    "IRC §414(v)(2)(B)(ii)",
    "limit_simple_catchup_50",
    50,
    None,
)

_AGE_UNKNOWN_LABELS: dict[str, str] = {
    "hsa_catchup_age_unknown": "HSA age-55 catch-up",
    "401k_catchup_age_unknown": "401(k) catch-up",
    "simple_catchup_age_unknown": "SIMPLE IRA catch-up",
}


def _tier(spec: _TierSpec, config: W2ReconciliationConfig) -> _CatchUpTier:
    check, label, citation, config_field, min_age, max_age = spec
    return _CatchUpTier(
        check=check,
        label=label,
        citation=citation,
        config_field=config_field,
        min_age=min_age,
        max_age=max_age,
        amount=getattr(config, config_field),
    )


def _hsa_rule(coverage: HsaCoverage, config: W2ReconciliationConfig) -> _LimitRule:
    base = config.hsa_self_only_limit if coverage == HsaCoverage.SELF_ONLY else config.hsa_family_limit
    return _LimitRule(
        plan_label=f"{coverage.value.replace('_', '-')} HSA",
        base=base,
        tiers=(_tier(_HSA_CATCHUP_55, config),),
        age_check="hsa_catchup_age_unknown",
    )


def _retirement_rule(plan_type: str, config: W2ReconciliationConfig) -> _LimitRule:
    has_60_63 = config.tax_year >= FIRST_YEAR_AGE_60_63_CATCHUP
    if plan_type == "simple_ira":
        specs: list[_TierSpec] = [_SIMPLE_CATCHUP_60_63] if has_60_63 else []
        specs.append(_SIMPLE_CATCHUP_50)
        return _LimitRule(
            plan_label="simple_ira",
            base=config.limit_simple_ira,
            tiers=tuple(_tier(spec, config) for spec in specs),
            age_check="simple_catchup_age_unknown",
        )
    specs_401k: list[_TierSpec] = [_401K_CATCHUP_60_63] if has_60_63 else []
    specs_401k.append(_401K_CATCHUP_50)
    return _LimitRule(
        plan_label="401k",
        base=config.limit_401k_elective,
        tiers=tuple(_tier(spec, config) for spec in specs_401k),
        age_check="401k_catchup_age_unknown",
    )


def _inferred_plan_type(employee: EmployeePayroll) -> str | None:
    # Sprint 826 (W5): with no plan type the deferral went unchecked entirely —
    # $30,000 of 401(k) deferrals at age 40 raised nothing. Infer the plan from
    # which deferral field is populated.
    return employee.retirement_plan_type or (
        "401k" if employee.retirement_401k > 0 else "simple_ira" if employee.retirement_simple_ira > 0 else None
    )


def _check_contribution_limit(
    employee: EmployeePayroll,
    amount: Decimal,
    rule: _LimitRule,
    *,
    kind: DiscrepancyKind,
    subject: str,
    consequence: str,
    tax_year: int,
    age_unknown_ids: dict[str, set[str]],
) -> Discrepancy | None:
    """
    Compare a contribution with its limit, catch-ups included where they can be
    established (Sprint 826, W1/W2).

    Documented choice (CEO option C). An amount over the *base* limit is always
    reported, at HIGH as before — it is a potential excess contribution, and
    missing one costs the employee an excise tax or a corrective distribution.
    What changes is the claim: an excess (and its consequence) is asserted only
    when the limit used accounts for every catch-up the employee could have.
    When it cannot — no age in the data, or the year's catch-up figure was not
    supplied — the finding says "exceeds the base limit", names what could not
    be assessed, and does not assert an excess.
    """
    base = rule.base
    if amount <= base:
        return None

    age = employee.age
    limit = base
    tier_used: _CatchUpTier | None = None
    hedge: str | None = None

    if age is not None:
        tier = next((t for t in rule.tiers if t.applies_to(age)), None)
        if tier is not None and tier.amount is not None:
            limit, tier_used = base + tier.amount, tier
        elif tier is not None:
            hedge = (
                f"The employee (age {age}) may be entitled to the {tier.label} ({tier.citation}), "
                f"but its figure for tax year {tax_year} was not supplied, so the catch-up could not be applied."
            )
    else:
        known = [t for t in rule.tiers if t.amount is not None]
        largest = max(known, key=lambda t: t.amount or ZERO) if known and len(known) == len(rule.tiers) else None
        if largest is not None and largest.amount is not None and amount > base + largest.amount:
            # Over even the most generous catch-up: an excess exists whatever
            # the employee's age. Report only the part that is certain.
            limit, tier_used = base + largest.amount, largest
        else:
            age_unknown_ids[rule.age_check].add(employee.employee_id)
            hedge = "Catch-up eligibility is not verifiable from the data — no age was supplied."
            if largest is not None and largest.amount is not None:
                hedge += f" With the largest applicable catch-up the limit would be ${base + largest.amount:,.2f}."
            else:
                hedge += f" A catch-up figure for tax year {tax_year} was not supplied either."

    if amount <= limit:
        return None  # within the limit once the catch-up is applied

    over = amount - limit
    if hedge is not None:
        message = (
            f"{subject} ${amount:,.2f} exceeds the {rule.plan_label} base limit of ${base:,.2f} "
            f"by ${over:,.2f}. {hedge} Not asserted as an excess contribution — confirm the "
            f"employee's age and catch-up eligibility before treating it as one."
        )
    else:
        breakdown = ""
        if tier_used is not None and tier_used.amount is not None:
            qualifier = "" if age is not None else "; the most allowed at any age"
            breakdown = (
                f" (${base:,.2f} base + ${tier_used.amount:,.2f} {tier_used.label}, {tier_used.citation}{qualifier})"
            )
        message = (
            f"{subject} ${amount:,.2f} exceeds the {rule.plan_label} limit of ${limit:,.2f}"
            f"{breakdown} by ${over:,.2f}. {consequence}"
        )

    return Discrepancy(
        employee_id=employee.employee_id,
        employee_name=employee.employee_name,
        kind=kind,
        severity=DiscrepancySeverity.HIGH,
        expected=limit,
        actual=amount,
        difference=over,
        message=message,
    )


def _checks_not_run(
    employees: list[EmployeePayroll],
    config: W2ReconciliationConfig,
    age_unknown_ids: dict[str, set[str]],
) -> list[dict[str, Any]]:
    """
    Sprint 826 (W1/W2, option C): every catch-up check that could not run.

    ``limit_not_supplied`` — the year's figure is absent (no table value and no
    override). Reported when at least one employee could qualify: covered by
    the plan and within the tier's ages, or of unknown age. A missing figure
    nobody could use is not reported; the check had nothing to do.

    ``age_not_supplied`` — an amount over the base limit could not be resolved
    because the employee has no age.
    """
    missing: dict[str, tuple[_CatchUpTier, set[str]]] = {}
    for employee in employees:
        rules: list[_LimitRule] = []
        if employee.hsa_coverage != HsaCoverage.NONE:
            rules.append(_hsa_rule(employee.hsa_coverage, config))
        plan_type = _inferred_plan_type(employee)
        if plan_type:
            rules.append(_retirement_rule(plan_type, config))
        for rule in rules:
            for tier in rule.tiers:
                if tier.amount is None and (employee.age is None or tier.applies_to(employee.age)):
                    missing.setdefault(tier.check, (tier, set()))[1].add(employee.employee_id)

    notices: list[dict[str, Any]] = []
    for check in sorted(missing):
        tier, ids = missing[check]
        notices.append(
            {
                "check": check,
                "reason": "limit_not_supplied",
                "employee_ids": sorted(ids),
                "message": (
                    f"{tier.label} check not run — the {tier.citation} limit for tax year "
                    f"{config.tax_year} was not supplied. {len(ids)} employee(s) who may qualify were "
                    f"checked against the base limit only; any amount above it is reported without "
                    f"asserting an excess contribution. Supply `{tier.config_field}` in the statutory "
                    f"limits to run this check."
                ),
            }
        )
    for check in sorted(age_unknown_ids):
        ids = age_unknown_ids[check]
        if not ids:
            continue
        notices.append(
            {
                "check": check,
                "reason": "age_not_supplied",
                "employee_ids": sorted(ids),
                "message": (
                    f"{_AGE_UNKNOWN_LABELS[check]} eligibility not verified for {len(ids)} employee(s) — "
                    f"the data has no age for them. Their amounts above the base limit are reported as "
                    f"over the base limit, not as excess contributions. Add an age column (age at the "
                    f"end of the tax year) to assess catch-up eligibility."
                ),
            }
        )
    return notices


# =============================================================================
# Core checks
# =============================================================================


def _check_employee(
    employee: EmployeePayroll,
    w2: EmployeeW2Draft,
    config: W2ReconciliationConfig,
    *,
    draft_supplied: bool = True,
    age_unknown_ids: dict[str, set[str]] | None = None,
) -> list[Discrepancy]:
    """Run every per-employee check, return the discrepancies found."""
    if age_unknown_ids is None:
        age_unknown_ids = defaultdict(set)
    issues: list[Discrepancy] = []
    tolerance = config.tolerance

    # --- SS wages ---
    expected_ss = min(employee.ss_wages, config.ss_wage_base)
    # Sprint 826 (W6): with a supplied draft, what matters is whether *Box 3*
    # exceeds the base. Payroll routinely reports uncapped SS wages, so a draft
    # correctly capped at the base drew a HIGH "must be capped" finding. With no
    # draft, the engine builds a capped one itself and this finding is the only
    # reminder to cap the real W-2 — so it stays.
    box_3_over_base = w2.box_3_ss_wages > config.ss_wage_base + tolerance
    if employee.ss_wages > config.ss_wage_base and (box_3_over_base or not draft_supplied):
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

    # --- Draft vs payroll: tax actually withheld, and Box 12 (Sprint 826, W3) ---
    for kind, box_label, drafted, payroll_value in (
        (
            DiscrepancyKind.SS_TAX_WITHHELD_VS_PAYROLL,
            "box 4 SS tax",
            w2.box_4_ss_tax_withheld,
            employee.ss_tax_withheld,
        ),
        (
            DiscrepancyKind.MEDICARE_TAX_WITHHELD_VS_PAYROLL,
            "box 6 Medicare tax",
            w2.box_6_medicare_tax_withheld,
            employee.medicare_tax_withheld,
        ),
    ):
        # Zero in payroll means "not supplied" — the rate-based checks above
        # still cover the box.
        if payroll_value != 0 and abs(drafted - payroll_value) > tolerance:
            diff = drafted - payroll_value
            issues.append(
                Discrepancy(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    kind=kind,
                    severity=_severity_for_diff(diff, tolerance),
                    expected=payroll_value,
                    actual=drafted,
                    difference=diff,
                    message=(
                        f"W-2 {box_label} withheld (${drafted:,.2f}) differs from the "
                        f"${payroll_value:,.2f} payroll actually withheld."
                    ),
                )
            )
    for code, drafted, payroll_value in (
        ("D", w2.box_12_code_d_401k, employee.retirement_401k),
        ("W", w2.box_12_code_w_hsa, employee.hsa_contributions),
        ("S", w2.box_12_code_s_simple, employee.retirement_simple_ira),
    ):
        if abs(drafted - payroll_value) > tolerance:
            diff = drafted - payroll_value
            issues.append(
                Discrepancy(
                    employee_id=employee.employee_id,
                    employee_name=employee.employee_name,
                    kind=DiscrepancyKind.BOX_12_VS_PAYROLL,
                    severity=_severity_for_diff(diff, tolerance),
                    expected=payroll_value,
                    actual=drafted,
                    difference=diff,
                    message=(f"W-2 box 12 code {code} (${drafted:,.2f}) differs from payroll (${payroll_value:,.2f})."),
                )
            )

    # --- HSA over-limit (Sprint 826 W2: age-55 catch-up, IRC §223(b)(3)) ---
    if employee.hsa_coverage != HsaCoverage.NONE:
        finding = _check_contribution_limit(
            employee,
            employee.hsa_contributions,
            _hsa_rule(employee.hsa_coverage, config),
            kind=DiscrepancyKind.HSA_OVER_LIMIT,
            subject="HSA contribution",
            consequence="Excess is subject to the 6% excise tax (IRC §4973) unless withdrawn.",
            tax_year=config.tax_year,
            age_unknown_ids=age_unknown_ids,
        )
        if finding is not None:
            issues.append(finding)

    # --- Retirement over-limit (Sprint 826 W1: SIMPLE catch-up has its own figures) ---
    plan_type = _inferred_plan_type(employee)
    if plan_type:
        retirement_total = employee.retirement_401k if plan_type == "401k" else employee.retirement_simple_ira
        finding = _check_contribution_limit(
            employee,
            retirement_total,
            _retirement_rule(plan_type, config),
            kind=DiscrepancyKind.RETIREMENT_OVER_LIMIT,
            subject="Elective deferral",
            consequence="Excess must be distributed by April 15.",
            tax_year=config.tax_year,
            age_unknown_ids=age_unknown_ids,
        )
        if finding is not None:
            issues.append(finding)

    return issues


# (941 / W-3 field, payroll field, kind, label). The 941 and W-3 dataclasses
# share field names for the four figures a 941 states.
_FORM_941_FIELDS: tuple[tuple[str, str, DiscrepancyKind, str], ...] = (
    ("total_federal_wages", "federal_wages", DiscrepancyKind.FEDERAL_WAGES, "federal wages"),
    ("total_federal_withholding", "federal_withholding", DiscrepancyKind.FEDERAL_WITHHOLDING, "federal withholding"),
    ("total_ss_wages", "ss_wages", DiscrepancyKind.SS_WAGES, "Social Security wages"),
    ("total_medicare_wages", "medicare_wages", DiscrepancyKind.MEDICARE_WAGES, "Medicare wages"),
)


def _form_941_quarter_coverage(quarters: list[Form941Quarter]) -> tuple[list[int], list[int]]:
    """Sprint 846 (W9): (missing quarters, duplicated quarters). No 941s at all is not a finding."""
    if not quarters:
        return [], []
    counts: dict[int, int] = defaultdict(int)
    for q in quarters:
        counts[q.quarter] += 1
    missing = [n for n in (1, 2, 3, 4) if counts[n] == 0]
    duplicated = sorted(n for n, c in counts.items() if c > 1)
    return missing, duplicated


def _check_form_941(
    employees: list[EmployeePayroll],
    w3: W3Totals | None,
    quarters: list[Form941Quarter],
    tolerance: Decimal,
) -> tuple[list[Form941Mismatch], list[dict[str, Any]]]:
    """
    Compare the four-quarter 941 sum with payroll YTD and, when there is a W-3,
    with the W-3 (Sprint 846, W4). Returns the mismatches and any
    ``checks_not_run`` notices.

    Both comparisons are annual, so they run only with exactly one 941 per
    quarter (W9): three quarters against a year of payroll is a guaranteed
    "mismatch" whose real cause is the absent return. A figure is compared only
    when every quarter states it.
    """
    if not quarters:
        return [], []

    missing, duplicated = _form_941_quarter_coverage(quarters)
    if missing or duplicated:
        problems = []
        if missing:
            problems.append("no Form 941 for " + ", ".join(f"Q{n}" for n in missing))
        if duplicated:
            problems.append("more than one Form 941 for " + ", ".join(f"Q{n}" for n in duplicated))
        return [], [
            {
                "check": "form_941_annual_tieout",
                "reason": "form_941_quarters_incomplete",
                "employee_ids": [],
                "message": (
                    "Form 941 annual tie-out not run — "
                    + "; ".join(problems)
                    + ". The four-quarter totals are compared with payroll year-to-date and the W-3 only "
                    "when exactly one return is supplied for each quarter."
                ),
            }
        ]

    mismatches: list[Form941Mismatch] = []
    not_supplied: list[str] = []
    for field_name, payroll_field, kind, label in _FORM_941_FIELDS:
        values = [getattr(q, field_name) for q in quarters]
        if any(v is None for v in values):
            not_supplied.append(label)
            continue
        actual = sum(values, ZERO)

        comparisons = [("payroll_ytd", sum((getattr(e, payroll_field) for e in employees), ZERO), "payroll YTD")]
        if w3 is not None:
            comparisons.append(("w3", getattr(w3, field_name), "the W-3 total of the draft W-2s"))

        for compared_with, expected, description in comparisons:
            diff = actual - expected
            if abs(diff) > tolerance:
                mismatches.append(
                    Form941Mismatch(
                        quarter=None,
                        kind=kind,
                        severity=(
                            DiscrepancySeverity.HIGH if abs(diff) > tolerance * 100 else DiscrepancySeverity.MEDIUM
                        ),
                        expected=_quantise(expected),
                        actual=_quantise(actual),
                        difference=_quantise(diff),
                        message=(
                            f"Sum of 4 quarters of Form 941 {label} (${actual:,.2f}) "
                            f"disagrees with {description} (${expected:,.2f})."
                        ),
                        compared_with=compared_with,
                    )
                )

    notices: list[dict[str, Any]] = []
    if not_supplied:
        notices.append(
            {
                "check": "form_941_annual_tieout",
                "reason": "form_941_field_not_supplied",
                "employee_ids": [],
                "message": (
                    f"Form 941 {', '.join(not_supplied)} not compared — the figure was not supplied for every quarter."
                ),
            }
        )
    return mismatches, notices


# =============================================================================
# Public entry point
# =============================================================================


def reconcile_w2(config: W2ReconciliationConfig) -> W2ReconciliationResult:
    """Run the full W-2 / W-3 / 941 reconciliation."""
    if config.tax_year < 2000 or config.tax_year > 2099:
        raise W2ReconciliationInputError(f"Tax year must be a 4-digit year between 2000 and 2099 ({config.tax_year})")
    # Sprint 826 (W10): a negative tolerance flagged every line HIGH with a
    # difference of zero.
    if config.tolerance < ZERO:
        raise W2ReconciliationInputError(f"Tolerance cannot be negative ({config.tolerance})")

    # Sprint 826 (W4): IDs compared stripped ("B1 " is B1), and duplicate or
    # orphan drafts are reported. Keyed naively, a duplicate silently replaced
    # the first draft while the W-3 below still summed both, and a draft for no
    # payroll employee was summed into the W-3 with no finding at all.
    def _key(employee_id: str) -> str:
        return employee_id.strip()

    draft_counts: dict[str, int] = defaultdict(int)
    for w in config.w2_drafts:
        draft_counts[_key(w.employee_id)] += 1
    payroll_ids = {_key(e.employee_id) for e in config.employees}
    duplicate_w2_drafts = sorted(k for k, n in draft_counts.items() if n > 1)
    orphan_w2_drafts = sorted(k for k in draft_counts if k not in payroll_ids)

    w2_by_id: dict[str, EmployeeW2Draft] = {}
    for w in config.w2_drafts:
        w2_by_id.setdefault(_key(w.employee_id), w)

    employee_discrepancies: list[Discrepancy] = []
    employees_missing_w2: list[str] = []
    age_unknown_ids: dict[str, set[str]] = defaultdict(set)

    for employee in config.employees:
        w2 = w2_by_id.get(_key(employee.employee_id))
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
        employee_discrepancies.extend(
            _check_employee(
                employee,
                w2,
                config,
                draft_supplied=employee.employee_id not in employees_missing_w2,
                age_unknown_ids=age_unknown_ids,
            )
        )

    # --- W-3 totals (sum of every W-2) ---
    # Sprint 846 (W8): with no drafts there is no W-3. Six zero totals and an
    # employee count of 0 read as a real, empty W-3.
    w3: W3Totals | None = None
    if config.w2_drafts:
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
    form_941_mismatches, form_941_notices = _check_form_941(
        config.employees, w3, config.form_941_quarters, config.tolerance
    )
    quarters_missing, quarters_duplicated = _form_941_quarter_coverage(config.form_941_quarters)

    # --- Summary ---
    by_kind: dict[str, int] = defaultdict(int)
    for d in employee_discrepancies:
        by_kind[d.kind.value] += 1
    for m in form_941_mismatches:
        by_kind[m.kind.value] += 1

    summary = {
        "employee_count": len(config.employees),
        "employees_missing_w2_draft": employees_missing_w2,
        "duplicate_w2_drafts": duplicate_w2_drafts,
        "orphan_w2_drafts": orphan_w2_drafts,
        # Sprint 826 (W7): the Additional Medicare threshold notice is
        # informational — its amount is already inside the box 6 expectation —
        # so it is counted on its own rather than as a discrepancy. A clean
        # dataset with one high earner reported "1 discrepancy".
        "total_employee_discrepancies": sum(
            1 for d in employee_discrepancies if d.kind != DiscrepancyKind.ADDITIONAL_MEDICARE
        ),
        "informational_notices": sum(
            1 for d in employee_discrepancies if d.kind == DiscrepancyKind.ADDITIONAL_MEDICARE
        ),
        "total_form_941_mismatches": len(form_941_mismatches),
        "form_941_quarters_missing": quarters_missing,
        "form_941_quarters_duplicated": quarters_duplicated,
        "w3_status": None if w3 is not None else "No draft W-2s supplied — there is no W-3 to total.",
        "discrepancies_by_kind": dict(by_kind),
    }

    return W2ReconciliationResult(
        tax_year=config.tax_year,
        employee_discrepancies=employee_discrepancies,
        form_941_mismatches=form_941_mismatches,
        w3_totals=w3,
        summary=summary,
        statutory_basis=config.statutory_year,
        statutory_basis_source=config.statutory_source,
        checks_not_run=_checks_not_run(config.employees, config, age_unknown_ids) + form_941_notices,
    )
