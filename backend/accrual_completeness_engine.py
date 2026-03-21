"""
Paciolus — Accrual Completeness Estimator Engine
Sprint 290 / Sprint 513

Identifies accrued liability accounts from the trial balance, classifies
them into analytical buckets (Accrued Liability, Provision/Reserve,
Deferred Revenue, Deferred Liability), computes a monthly expense run-rate
from prior-period operating expenses, produces an accrual-to-run-rate ratio
with a configurable threshold, per-account reasonableness testing,
missing accrual estimation, findings register, and suggested procedures.

Deferred Revenue is excluded from the accrual-to-run-rate calculation
and analysed separately (ASC 606 framing).

Guardrail: Descriptive metrics only — NEVER "appears low", NEVER
"liabilities may be understated". Pure numeric comparisons only.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from column_detector import detect_columns
from shared.parsing_helpers import safe_decimal

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

ACCRUAL_KEYWORDS = [
    "accrued",
    "accrued expense",
    "accrued liability",
    "accrued liabilities",
    "accrued wages",
    "accrued salaries",
    "accrued interest",
    "accrued tax",
    "accrued rent",
    "accrued payroll",
    "accrued bonus",
    "accrued vacation",
    "accrued benefits",
    "accrual",
]

PROVISION_KEYWORDS = ["reserve", "provision", "allowance"]
DEFERRED_REVENUE_KEYWORDS = ["deferred revenue", "unearned revenue", "unearned"]
DEFERRED_LIABILITY_KEYWORDS = ["deferred"]
PREPAID_KEYWORDS = ["prepaid"]

NEAR_ZERO = 1e-10
DEFAULT_THRESHOLD_PCT = 50.0
MONTHS_PER_YEAR = 12

# Reasonableness variance thresholds
REASONABLE_VARIANCE_PCT = 0.20
MODERATE_VARIANCE_PCT = 0.50

# ═══════════════════════════════════════════════════════════════
# Expected Accruals Checklist (CONTENT-09)
# ═══════════════════════════════════════════════════════════════

EXPECTED_ACCRUALS: list[dict[str, str | list[str]]] = [
    {
        "name": "Payroll Accrual",
        "keywords": ["payroll", "salary", "salaries", "wages", "compensation"],
        "risk_if_absent": "Understated labor costs",
        "basis": "Payroll expense × stub period",
    },
    {
        "name": "Interest Accrual",
        "keywords": ["interest payable", "accrued interest"],
        "risk_if_absent": "Understated financing costs",
        "basis": "Debt × rate × stub period",
    },
    {
        "name": "Tax Accrual",
        "keywords": ["tax payable", "income tax", "tax provision"],
        "risk_if_absent": "Understated tax liabilities",
        "basis": "Current period tax provision",
    },
    {
        "name": "Rent Accrual",
        "keywords": ["rent payable", "accrued rent", "lease"],
        "risk_if_absent": "Understated occupancy costs",
        "basis": "Lease obligations under ASC 842",
    },
    {
        "name": "Utilities Accrual",
        "keywords": ["utilities", "electric", "gas", "water"],
        "risk_if_absent": "Understated operating costs",
        "basis": "Utility expense stub period",
    },
    {
        "name": "Insurance Accrual",
        "keywords": ["insurance", "premium"],
        "risk_if_absent": "Understated insurance obligations",
        "basis": "Insurance premium obligations",
    },
    {
        "name": "Warranty Accrual",
        "keywords": ["warranty", "guarantee"],
        "risk_if_absent": "Understated contingent liabilities",
        "basis": "Historical warranty claim rate × sales",
    },
    {
        "name": "Bonus Accrual",
        "keywords": ["bonus", "incentive"],
        "risk_if_absent": "Understated compensation",
        "basis": "Performance-based compensation",
    },
    {
        "name": "Legal Accrual",
        "keywords": ["legal", "litigation", "settlement"],
        "risk_if_absent": "Understated legal obligations",
        "basis": "ASC 450-20 loss contingencies",
    },
    {
        "name": "Professional Fees",
        "keywords": ["audit", "consulting", "professional"],
        "risk_if_absent": "Understated service obligations",
        "basis": "Professional services",
    },
    {
        "name": "Vacation / PTO",
        "keywords": ["vacation", "pto", "paid time off", "leave"],
        "risk_if_absent": "Understated PTO liability",
        "basis": "Estimated unused PTO liability",
    },
]


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════


@dataclass
class AccrualAccount:
    """One identified accrual-related account."""

    account_name: str
    balance: Decimal
    matched_keyword: str
    classification: str = "Accrued Liability"

    def __post_init__(self) -> None:
        if isinstance(self.balance, (int, float)):
            self.balance = Decimal(str(self.balance))

    def to_dict(self) -> dict:
        return {
            "account_name": self.account_name,
            "balance": round(self.balance, 2),
            "matched_keyword": self.matched_keyword,
            "classification": self.classification,
        }


@dataclass
class ReasonablenessResult:
    """Per-account reasonableness test result."""

    account_name: str
    recorded_balance: float
    annual_driver: Optional[float]
    driver_source: str
    months_to_accrue: int
    expected_balance: Optional[float]
    variance: Optional[float]
    variance_pct: Optional[float]
    status: str

    def to_dict(self) -> dict:
        return {
            "account_name": self.account_name,
            "recorded_balance": round(self.recorded_balance, 2),
            "annual_driver": round(self.annual_driver, 2) if self.annual_driver is not None else None,
            "driver_source": self.driver_source,
            "months_to_accrue": self.months_to_accrue,
            "expected_balance": round(self.expected_balance, 2) if self.expected_balance is not None else None,
            "variance": round(self.variance, 2) if self.variance is not None else None,
            "variance_pct": round(self.variance_pct, 4) if self.variance_pct is not None else None,
            "status": self.status,
        }


@dataclass
class DeferredRevenueAnalysis:
    """Deferred Revenue analysis metrics (ASC 606)."""

    deferred_balance: float
    total_revenue: Optional[float]
    deferred_pct_of_revenue: Optional[float]

    def to_dict(self) -> dict:
        return {
            "deferred_balance": round(self.deferred_balance, 2),
            "total_revenue": round(self.total_revenue, 2) if self.total_revenue is not None else None,
            "deferred_pct_of_revenue": round(self.deferred_pct_of_revenue, 4)
            if self.deferred_pct_of_revenue is not None
            else None,
        }


@dataclass
class Finding:
    """One finding from the analysis."""

    area: str
    finding: str
    risk: str
    action_required: str

    def to_dict(self) -> dict:
        return {
            "area": self.area,
            "finding": self.finding,
            "risk": self.risk,
            "action_required": self.action_required,
        }


@dataclass
class SuggestedProcedure:
    """One suggested audit procedure."""

    priority: str
    area: str
    procedure: str

    def to_dict(self) -> dict:
        return {
            "priority": self.priority,
            "area": self.area,
            "procedure": self.procedure,
        }


@dataclass
class ExpectedAccrualCheck:
    """One row in the expected accrual checklist."""

    expected_name: str
    detected: bool
    balance: Optional[float]
    risk_if_absent: str
    basis: str = ""
    recommended_action: str = ""

    def to_dict(self) -> dict:
        return {
            "expected_name": self.expected_name,
            "detected": self.detected,
            "balance": round(self.balance, 2) if self.balance is not None else None,
            "risk_if_absent": self.risk_if_absent,
            "basis": self.basis,
            "recommended_action": self.recommended_action,
        }


@dataclass
class AccrualCompletenessReport:
    """Complete accrual completeness estimator result."""

    # Core accrual accounts (Accrued Liability + Provision/Reserve only)
    accrual_accounts: list[AccrualAccount] = field(default_factory=list)
    total_accrued_balance: float = 0.0
    accrual_account_count: int = 0

    # Deferred Revenue accounts (excluded from ratio)
    deferred_revenue_accounts: list[AccrualAccount] = field(default_factory=list)
    total_deferred_revenue: float = 0.0

    # Run-rate analysis
    monthly_run_rate: Optional[float] = None
    accrual_to_run_rate_pct: Optional[float] = None
    threshold_pct: float = DEFAULT_THRESHOLD_PCT
    meets_threshold: bool = False
    prior_operating_expenses: Optional[float] = None
    prior_available: bool = False
    narrative: str = ""

    # Per-account reasonableness (Section II enhancement)
    reasonableness_results: list[ReasonablenessResult] = field(default_factory=list)

    # Expected accrual checklist / missing accruals
    expected_accrual_checklist: list[ExpectedAccrualCheck] = field(default_factory=list)

    # Deferred Revenue analysis (Section IV-B)
    deferred_revenue_analysis: Optional[DeferredRevenueAnalysis] = None

    # Findings register (Section V)
    findings: list[Finding] = field(default_factory=list)

    # Suggested procedures (Section VI)
    suggested_procedures: list[SuggestedProcedure] = field(default_factory=list)

    # Backward compatibility alias
    @property
    def below_threshold(self) -> bool:
        return not self.meets_threshold

    def to_dict(self) -> dict:
        return {
            "accrual_accounts": [a.to_dict() for a in self.accrual_accounts],
            "total_accrued_balance": round(self.total_accrued_balance, 2),
            "accrual_account_count": self.accrual_account_count,
            "deferred_revenue_accounts": [a.to_dict() for a in self.deferred_revenue_accounts],
            "total_deferred_revenue": round(self.total_deferred_revenue, 2),
            "monthly_run_rate": round(self.monthly_run_rate, 2) if self.monthly_run_rate is not None else None,
            "accrual_to_run_rate_pct": round(self.accrual_to_run_rate_pct, 2)
            if self.accrual_to_run_rate_pct is not None
            else None,
            "threshold_pct": round(self.threshold_pct, 2),
            "meets_threshold": self.meets_threshold,
            "below_threshold": self.below_threshold,
            "prior_operating_expenses": round(self.prior_operating_expenses, 2)
            if self.prior_operating_expenses is not None
            else None,
            "prior_available": self.prior_available,
            "narrative": self.narrative,
            "reasonableness_results": [r.to_dict() for r in self.reasonableness_results],
            "expected_accrual_checklist": [c.to_dict() for c in self.expected_accrual_checklist],
            "deferred_revenue_analysis": self.deferred_revenue_analysis.to_dict()
            if self.deferred_revenue_analysis
            else None,
            "findings": [f.to_dict() for f in self.findings],
            "suggested_procedures": [p.to_dict() for p in self.suggested_procedures],
        }


# ═══════════════════════════════════════════════════════════════
# Account classification
# ═══════════════════════════════════════════════════════════════


def _classify_liability_type(account_name: str) -> tuple[Optional[str], Optional[str]]:
    """Classify a liability account into an analytical bucket.

    Returns (classification, matched_keyword) or (None, None) if no match.
    Order: deferred revenue (most specific) → accrued → provision → deferred → None.
    """
    name_lower = account_name.lower()

    # 1. Deferred Revenue / Unearned Revenue — must be checked BEFORE generic deferred
    for kw in DEFERRED_REVENUE_KEYWORDS:
        if kw in name_lower:
            return "Deferred Revenue", kw

    # 2. Accrued Liability — check phrase keywords first (longer = more specific)
    for kw in sorted(ACCRUAL_KEYWORDS, key=len, reverse=True):
        if kw in name_lower:
            return "Accrued Liability", kw

    # 3. Provision / Reserve
    for kw in PROVISION_KEYWORDS:
        if kw in name_lower:
            return "Provision / Reserve", kw

    # 4. Generic deferred liability (not revenue)
    for kw in DEFERRED_LIABILITY_KEYWORDS:
        if kw in name_lower:
            return "Deferred Liability", kw

    return None, None


def _is_accrual_account(account_name: str) -> Optional[str]:
    """Check if an account name matches accrual keywords.

    Returns the matched keyword or None.
    Phrase keywords (multi-word) are checked first for specificity.

    Note: This function only checks ACCRUAL_KEYWORDS for backward
    compatibility. Use _classify_liability_type for full classification.
    """
    name_lower = account_name.lower()

    # Check phrase keywords first (longer = more specific)
    for kw in sorted(ACCRUAL_KEYWORDS, key=len, reverse=True):
        if kw in name_lower:
            return kw

    return None


# ═══════════════════════════════════════════════════════════════
# Per-account reasonableness testing
# ═══════════════════════════════════════════════════════════════


def _test_reasonableness(
    account_name: str,
    balance: float,
    annual_driver: Optional[float],
    driver_source: str,
    months_to_accrue: int = 1,
) -> ReasonablenessResult:
    """Test reasonableness of an accrual account balance against its driver.

    Args:
        account_name: Name of the accrual account
        balance: Recorded balance
        annual_driver: Annual expense driver amount (None if unavailable)
        driver_source: Description of where driver comes from
        months_to_accrue: Expected accrual period in months (default 1)

    Returns:
        ReasonablenessResult with status assessment.
    """
    if annual_driver is None or abs(annual_driver) < NEAR_ZERO:
        return ReasonablenessResult(
            account_name=account_name,
            recorded_balance=balance,
            annual_driver=annual_driver,
            driver_source=driver_source,
            months_to_accrue=months_to_accrue,
            expected_balance=None,
            variance=None,
            variance_pct=None,
            status="Driver Unavailable — Auditor Judgment Required",
        )

    expected = float(Decimal(str(annual_driver)) / MONTHS_PER_YEAR * months_to_accrue)
    variance = balance - expected

    if abs(expected) < NEAR_ZERO:
        variance_pct = None
        status = "Cannot estimate — zero expected balance"
    else:
        variance_pct = variance / expected
        abs_pct = abs(variance_pct)
        if abs_pct <= REASONABLE_VARIANCE_PCT:
            status = "Reasonable"
        elif abs_pct <= MODERATE_VARIANCE_PCT:
            status = "Moderate Variance — Inquire"
        else:
            status = "Significant Variance — Investigate"

    return ReasonablenessResult(
        account_name=account_name,
        recorded_balance=balance,
        annual_driver=annual_driver,
        driver_source=driver_source,
        months_to_accrue=months_to_accrue,
        expected_balance=expected,
        variance=variance,
        variance_pct=variance_pct,
        status=status,
    )


def _build_reasonableness_results(
    accrual_accounts: list[AccrualAccount],
    prior_operating_expenses: Optional[float],
) -> list[ReasonablenessResult]:
    """Build per-account reasonableness test results.

    Uses prior operating expenses as the annual driver proxy.
    Specific driver mappings are applied where possible.
    """
    results: list[ReasonablenessResult] = []

    for acct in accrual_accounts:
        name_lower = acct.account_name.lower()
        driver: Optional[float] = None
        source = "Not available"

        # Map accounts to their most logical driver
        if any(kw in name_lower for kw in ["payroll", "salary", "wages", "compensation"]):
            # Payroll typically ~25% of operating expenses (rough heuristic)
            if prior_operating_expenses is not None:
                driver = prior_operating_expenses * 0.25
                source = "Estimated from operating expenses (25% allocation)"
        elif "interest" in name_lower:
            # Interest is hard to estimate without debt schedule
            source = "Requires debt schedule — not derivable from TB"
        elif any(kw in name_lower for kw in ["utilities", "electric", "gas", "water"]):
            # Utilities typically ~2% of operating expenses
            if prior_operating_expenses is not None:
                driver = prior_operating_expenses * 0.02
                source = "Estimated from operating expenses (2% allocation)"
        elif any(kw in name_lower for kw in ["legal", "litigation"]):
            # Legal fees are judgment-dependent
            source = "Requires legal counsel confirmation"
        elif any(kw in name_lower for kw in ["warranty", "guarantee"]):
            # Warranty reserve requires historical claims data
            source = "Requires warranty claims history"
        elif any(kw in name_lower for kw in ["rent", "lease"]):
            if prior_operating_expenses is not None:
                driver = prior_operating_expenses * 0.05
                source = "Estimated from operating expenses (5% allocation)"
        elif any(kw in name_lower for kw in ["bonus", "incentive"]):
            source = "Requires compensation plan details"
        elif any(kw in name_lower for kw in ["vacation", "pto", "leave"]):
            source = "Requires PTO policy and headcount data"
        elif any(kw in name_lower for kw in ["tax", "income tax"]):
            source = "Requires tax provision computation"
        elif any(kw in name_lower for kw in ["insurance", "premium"]):
            source = "Requires insurance policy schedule"
        elif prior_operating_expenses is not None:
            # Generic fallback: use total opex as a rough proxy
            driver = prior_operating_expenses
            source = "Total operating expenses (rough proxy)"

        results.append(
            _test_reasonableness(
                account_name=acct.account_name,
                balance=float(acct.balance),
                annual_driver=driver,
                driver_source=source,
            )
        )

    return results


# ═══════════════════════════════════════════════════════════════
# Expected accrual checklist / missing accrual estimation
# ═══════════════════════════════════════════════════════════════


def _build_expected_accrual_checklist(
    accrual_accounts: list[AccrualAccount],
) -> list[ExpectedAccrualCheck]:
    """Match detected accrual accounts against the EXPECTED_ACCRUALS lookup.

    For each expected accrual type, checks whether any detected account's
    matched_keyword maps to the expected type's keywords. Produces one
    checklist row per expected accrual type with recommended actions
    for missing items.
    """
    checklist: list[ExpectedAccrualCheck] = []

    for expected in EXPECTED_ACCRUALS:
        expected_name: str = expected["name"]  # type: ignore[assignment]
        expected_keywords: list[str] = expected["keywords"]  # type: ignore[assignment]
        risk: str = expected["risk_if_absent"]  # type: ignore[assignment]
        basis: str = expected.get("basis", "")  # type: ignore[assignment]

        # Search detected accounts for a keyword match
        detected = False
        total_balance: Decimal = Decimal("0")

        for acct in accrual_accounts:
            acct_name_lower = acct.account_name.lower()
            kw_lower = acct.matched_keyword.lower()
            for ek in expected_keywords:
                if ek in kw_lower or ek in acct_name_lower:
                    detected = True
                    total_balance += acct.balance
                    break

        # Build recommended action for missing items
        if detected:
            recommended_action = ""
        else:
            action_map = {
                "Payroll Accrual": "Verify whether entity accrues payroll at period-end",
                "Interest Accrual": "Confirm no outstanding debt obligations exist",
                "Tax Accrual": "Verify entity tax status (LLC pass-through may explain absence)",
                "Rent Accrual": "Confirm no lease obligations exist under ASC 842",
                "Utilities Accrual": "Inquire whether utilities are prepaid or accrued",
                "Insurance Accrual": "Confirm insurance premium payment timing",
                "Warranty Accrual": "Confirm no warranty arrangements exist",
                "Bonus Accrual": "Confirm no bonus or incentive arrangements exist",
                "Legal Accrual": "Inquire regarding pending or threatened litigation",
                "Professional Fees": "Confirm no unpaid professional service obligations",
                "Vacation / PTO": "Inquire whether entity accrues PTO liability",
            }
            recommended_action = action_map.get(expected_name, "Inquire with management")

        checklist.append(
            ExpectedAccrualCheck(
                expected_name=expected_name,
                detected=detected,
                balance=float(round(total_balance, 2)) if detected else None,
                risk_if_absent=risk,
                basis=basis,
                recommended_action=recommended_action,
            )
        )

    return checklist


# ═══════════════════════════════════════════════════════════════
# Deferred Revenue analysis
# ═══════════════════════════════════════════════════════════════


def _analyze_deferred_revenue(
    deferred_accounts: list[AccrualAccount],
    total_revenue: Optional[float] = None,
) -> Optional[DeferredRevenueAnalysis]:
    """Analyze deferred revenue accounts under ASC 606 framing."""
    if not deferred_accounts:
        return None

    total_deferred = sum((a.balance for a in deferred_accounts), Decimal("0"))

    pct_of_revenue: Optional[float] = None
    if total_revenue is not None and abs(total_revenue) > NEAR_ZERO:
        pct_of_revenue = float(total_deferred / Decimal(str(total_revenue)) * 100)

    return DeferredRevenueAnalysis(
        deferred_balance=float(total_deferred),
        total_revenue=total_revenue,
        deferred_pct_of_revenue=pct_of_revenue,
    )


# ═══════════════════════════════════════════════════════════════
# Findings generation
# ═══════════════════════════════════════════════════════════════


def _generate_findings(
    meets_threshold: bool,
    ratio: Optional[float],
    threshold: float,
    reasonableness_results: list[ReasonablenessResult],
    missing_accruals: list[ExpectedAccrualCheck],
    deferred_revenue_accounts: list[AccrualAccount],
) -> list[Finding]:
    """Generate findings dynamically from analysis results."""
    findings: list[Finding] = []

    # 1. Ratio below threshold
    if ratio is not None and not meets_threshold:
        findings.append(
            Finding(
                area="Accrual Completeness",
                finding=(
                    f"Accrual-to-run-rate ratio of {ratio:.1f}% is below the "
                    f"{threshold:.0f}% minimum threshold after excluding Deferred Revenue"
                ),
                risk="High",
                action_required="Perform additional completeness procedures",
            )
        )

    # 2. Per-account reasonableness variances
    for r in reasonableness_results:
        if "Moderate Variance" in r.status:
            findings.append(
                Finding(
                    area=r.account_name,
                    finding=(
                        f"Balance of ${r.recorded_balance:,.0f} "
                        f"{'exceeds' if r.variance and r.variance > 0 else 'is below'} "
                        f"expected estimate by {abs(r.variance_pct or 0):.0%}"
                    ),
                    risk="Moderate",
                    action_required=f"Obtain {r.account_name.lower()} accrual schedule",
                )
            )
        elif "Significant Variance" in r.status:
            findings.append(
                Finding(
                    area=r.account_name,
                    finding=(
                        f"Balance of ${r.recorded_balance:,.0f} shows significant variance "
                        f"({abs(r.variance_pct or 0):.0%}) from expected estimate"
                    ),
                    risk="High",
                    action_required=f"Investigate {r.account_name.lower()} — obtain supporting schedules",
                )
            )

    # 3. Missing expected accruals
    missing_names = [m.expected_name for m in missing_accruals if not m.detected]
    if missing_names:
        findings.append(
            Finding(
                area="Missing Accruals",
                finding=(
                    f"{len(missing_names)} expected accrual type(s) not identified in TB: "
                    f"{', '.join(missing_names[:5])}"
                    + (f" and {len(missing_names) - 5} more" if len(missing_names) > 5 else "")
                ),
                risk="Moderate" if len(missing_names) <= 3 else "High",
                action_required="Inquire with management regarding completeness of accrued liabilities",
            )
        )

    # 4. Deferred Revenue requires ASC 606 verification
    if deferred_revenue_accounts:
        total_deferred = sum((a.balance for a in deferred_revenue_accounts), Decimal("0"))
        findings.append(
            Finding(
                area="Deferred Revenue",
                finding=f"Deferred Revenue balance of ${total_deferred:,.0f} requires ASC 606 completeness verification",
                risk="Moderate",
                action_required="Obtain deferred revenue rollforward schedule",
            )
        )

    # 5. Driver-unavailable accounts (low priority)
    driver_unavailable = [r for r in reasonableness_results if "Driver Unavailable" in r.status]
    if driver_unavailable:
        findings.append(
            Finding(
                area="Reasonableness Testing",
                finding=(f"{len(driver_unavailable)} account(s) could not be tested against a run-rate driver"),
                risk="Low",
                action_required="Obtain supporting documentation for accounts without determinable drivers",
            )
        )

    return findings


# ═══════════════════════════════════════════════════════════════
# Suggested procedures generation
# ═══════════════════════════════════════════════════════════════


def _generate_procedures(
    findings: list[Finding],
    meets_threshold: bool,
    ratio: Optional[float],
    threshold: float,
    missing_accruals: list[ExpectedAccrualCheck],
    deferred_revenue_accounts: list[AccrualAccount],
) -> list[SuggestedProcedure]:
    """Generate suggested audit procedures from findings."""
    procedures: list[SuggestedProcedure] = []

    # 1. Ratio below threshold
    if ratio is not None and not meets_threshold:
        procedures.append(
            SuggestedProcedure(
                priority="High",
                area="Accrual Completeness",
                procedure=(
                    f"Accrual-to-run-rate ratio of {ratio:.1f}% is below the {threshold:.0f}% "
                    "minimum threshold. Request management's accrual schedule and supporting "
                    "calculations for all identified accrual accounts. Perform cutoff testing "
                    "around the period end date."
                ),
            )
        )

    # 2. Missing accruals
    missing_names = [m.expected_name for m in missing_accruals if not m.detected]
    if missing_names:
        procedures.append(
            SuggestedProcedure(
                priority="High",
                area="Missing Accruals",
                procedure=(
                    f"{len(missing_names)} expected accrual type(s) not identified in the trial "
                    "balance. Inquire with management regarding "
                    + ", ".join(missing_names[:4])
                    + (f", and {len(missing_names) - 4} other categories" if len(missing_names) > 4 else "")
                    + ". Obtain written representation regarding completeness of accrued liabilities."
                ),
            )
        )

    # 3. Deferred Revenue
    if deferred_revenue_accounts:
        total_deferred = sum((a.balance for a in deferred_revenue_accounts), Decimal("0"))
        procedures.append(
            SuggestedProcedure(
                priority="Moderate",
                area="Deferred Revenue",
                procedure=(
                    f"Deferred Revenue balance of ${total_deferred:,.0f} requires ASC 606 "
                    "completeness verification. Obtain the deferred revenue rollforward. "
                    "Confirm all balances relate to unfulfilled performance obligations "
                    "as of the balance sheet date."
                ),
            )
        )

    # 4. Moderate/Significant variance accounts
    high_variance_findings = [
        f
        for f in findings
        if f.risk in ("High", "Moderate")
        and f.area not in ("Accrual Completeness", "Missing Accruals", "Deferred Revenue", "Reasonableness Testing")
    ]
    for f in high_variance_findings:
        procedures.append(
            SuggestedProcedure(
                priority=f.risk,
                area=f.area,
                procedure=f.action_required + ". Compare to management's accrual methodology documentation.",
            )
        )

    # 5. General completeness procedure (always)
    procedures.append(
        SuggestedProcedure(
            priority="Moderate",
            area="General Completeness",
            procedure=(
                "Review post-period-end disbursements for items that should have been "
                "accrued at period end. Scan unrecorded liability search results "
                "for omitted accruals."
            ),
        )
    )

    return procedures


# ═══════════════════════════════════════════════════════════════
# Core computation
# ═══════════════════════════════════════════════════════════════


def compute_accrual_completeness(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: dict[str, str],
    prior_operating_expenses: Optional[float] = None,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
    total_revenue: Optional[float] = None,
) -> AccrualCompletenessReport:
    """Compute accrual completeness estimator from pre-aggregated account balances.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: {account_name: category_string} from classifier
        prior_operating_expenses: Annual operating expenses from prior DiagnosticSummary
        threshold_pct: Accrual-to-run-rate % below which to flag (default 50%)
        total_revenue: Total revenue for deferred revenue analysis

    Returns:
        AccrualCompletenessReport with identified accruals and ratio analysis.
    """
    if not account_balances:
        return AccrualCompletenessReport(
            threshold_pct=threshold_pct,
            narrative="No account data available for analysis.",
        )

    # Identify and classify liability accounts
    liability_types = {"liability"}
    accrual_accounts: list[AccrualAccount] = []
    deferred_revenue_accounts: list[AccrualAccount] = []

    for acct_name, bals in account_balances.items():
        classification = classified_accounts.get(acct_name, "").lower()
        if classification not in liability_types:
            continue

        bucket, matched_kw = _classify_liability_type(acct_name)
        if bucket is None:
            continue

        # Liabilities are credit-heavy; balance = credit - debit
        balance = bals["credit"] - bals["debit"]
        if abs(balance) < NEAR_ZERO:
            continue

        acct = AccrualAccount(
            account_name=acct_name,
            balance=Decimal(str(balance)),
            matched_keyword=matched_kw or "",
            classification=bucket,
        )

        if bucket == "Deferred Revenue":
            deferred_revenue_accounts.append(acct)
        elif bucket in ("Accrued Liability", "Provision / Reserve"):
            accrual_accounts.append(acct)
        # Deferred Liability and other buckets are noted but not included in ratio

    # Sort by balance descending
    accrual_accounts.sort(key=lambda a: abs(a.balance), reverse=True)
    deferred_revenue_accounts.sort(key=lambda a: abs(a.balance), reverse=True)

    # Sum only accrual + provision accounts for ratio (NOT deferred revenue)
    total_accrued = sum((a.balance for a in accrual_accounts), Decimal("0"))
    accrual_count = len(accrual_accounts)
    total_deferred = sum((a.balance for a in deferred_revenue_accounts), Decimal("0"))

    # Compute run-rate if prior data available
    prior_available = prior_operating_expenses is not None and abs(prior_operating_expenses) > NEAR_ZERO
    monthly_run_rate: Optional[float] = None
    accrual_to_run_rate: Optional[float] = None
    meets_threshold = False

    if prior_available:
        assert prior_operating_expenses is not None
        monthly_run_rate = prior_operating_expenses / MONTHS_PER_YEAR
        if abs(monthly_run_rate) > NEAR_ZERO:
            accrual_to_run_rate = float(total_accrued / Decimal(str(monthly_run_rate)) * 100)
            meets_threshold = accrual_to_run_rate >= threshold_pct

    # Per-account reasonableness testing
    reasonableness_results = _build_reasonableness_results(accrual_accounts, prior_operating_expenses)

    # Build expected accrual checklist / missing accruals
    expected_checklist = _build_expected_accrual_checklist(accrual_accounts)

    # Deferred Revenue analysis
    deferred_analysis = _analyze_deferred_revenue(deferred_revenue_accounts, total_revenue)

    # Build narrative (guardrail: descriptive only)
    narrative = _build_narrative(
        accrual_count,
        float(total_accrued),
        monthly_run_rate,
        accrual_to_run_rate,
        threshold_pct,
        meets_threshold,
        prior_available,
        float(total_deferred),
    )

    # Generate findings
    findings = _generate_findings(
        meets_threshold=meets_threshold,
        ratio=accrual_to_run_rate,
        threshold=threshold_pct,
        reasonableness_results=reasonableness_results,
        missing_accruals=expected_checklist,
        deferred_revenue_accounts=deferred_revenue_accounts,
    )

    # Generate suggested procedures
    procedures = _generate_procedures(
        findings=findings,
        meets_threshold=meets_threshold,
        ratio=accrual_to_run_rate,
        threshold=threshold_pct,
        missing_accruals=expected_checklist,
        deferred_revenue_accounts=deferred_revenue_accounts,
    )

    return AccrualCompletenessReport(
        accrual_accounts=accrual_accounts,
        total_accrued_balance=float(total_accrued),
        accrual_account_count=accrual_count,
        deferred_revenue_accounts=deferred_revenue_accounts,
        total_deferred_revenue=float(total_deferred),
        monthly_run_rate=monthly_run_rate,
        accrual_to_run_rate_pct=accrual_to_run_rate,
        threshold_pct=threshold_pct,
        meets_threshold=meets_threshold,
        prior_operating_expenses=prior_operating_expenses,
        prior_available=prior_available,
        narrative=narrative,
        reasonableness_results=reasonableness_results,
        expected_accrual_checklist=expected_checklist,
        deferred_revenue_analysis=deferred_analysis,
        findings=findings,
        suggested_procedures=procedures,
    )


def _build_narrative(
    count: int,
    total: float,
    run_rate: Optional[float],
    ratio: Optional[float],
    threshold: float,
    meets_threshold: bool,
    prior_available: bool,
    total_deferred: float = 0.0,
) -> str:
    """Build a descriptive narrative for the accrual completeness analysis.

    Guardrail: uses ONLY descriptive language. Never states that liabilities
    are understated or that the client has a deficiency.
    """
    if count == 0:
        return "No accrued liability accounts were identified in the trial balance."

    parts = [
        f"Identified {count} accrued liability account{'s' if count != 1 else ''} "
        f"with a combined balance of ${total:,.2f}."
    ]

    if total_deferred > 0:
        parts.append(
            f"Deferred Revenue of ${total_deferred:,.2f} has been excluded from the "
            f"accrual-to-run-rate calculation and is analyzed separately."
        )

    if prior_available and run_rate is not None and ratio is not None:
        parts.append(f"The monthly expense run-rate based on prior-period operating expenses is ${run_rate:,.2f}.")
        parts.append(f"The accrual-to-run-rate ratio is {ratio:.1f}% (threshold: {threshold:.0f}%).")
        if meets_threshold:
            parts.append(
                f"The accrued balance meets the {threshold:.0f}% minimum threshold "
                f"relative to the monthly expense run-rate ({ratio:.1f}% vs {threshold:.0f}% threshold)."
            )
        else:
            parts.append(
                f"The accrued balance is below the {threshold:.0f}% minimum threshold "
                f"of the monthly expense run-rate ({ratio:.1f}% vs {threshold:.0f}% threshold)."
            )
    else:
        parts.append(
            "Prior-period operating expense data was not provided. "
            "The run-rate comparison requires prior-period data from a saved diagnostic summary."
        )

    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════
# Standalone entry point
# ═══════════════════════════════════════════════════════════════


def run_accrual_completeness(
    column_names: list[str],
    rows: list[dict],
    filename: str,
    prior_operating_expenses: Optional[float] = None,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
    total_revenue: Optional[float] = None,
) -> AccrualCompletenessReport:
    """Run accrual completeness analysis from raw parsed file data.

    Uses column_detector.detect_columns() to find columns, accumulates
    per-account balances, classifies, then computes.
    """
    from account_classifier import create_classifier

    detection = detect_columns(column_names)
    account_col = detection.account_column
    debit_col = detection.debit_column
    credit_col = detection.credit_column

    if not account_col or not debit_col or not credit_col:
        return AccrualCompletenessReport(
            threshold_pct=threshold_pct,
            narrative="Required columns (account, debit, credit) could not be detected.",
        )

    # Accumulate per-account balances
    account_balances: dict[str, dict[str, float]] = {}
    for row in rows:
        acct = row.get(account_col)
        if acct is None:
            continue
        acct_str = str(acct).strip()
        if not acct_str:
            continue

        debit = safe_decimal(row.get(debit_col))
        credit = safe_decimal(row.get(credit_col))

        if acct_str not in account_balances:
            account_balances[acct_str] = {"debit": 0.0, "credit": 0.0}
        account_balances[acct_str]["debit"] += float(debit)
        account_balances[acct_str]["credit"] += float(credit)

    # Classify accounts
    classifier = create_classifier()
    classified_accounts: dict[str, str] = {}
    for acct_name, bals in account_balances.items():
        net = bals["debit"] - bals["credit"]
        cls_result = classifier.classify(acct_name, net)
        classified_accounts[acct_name] = cls_result.category.value

    return compute_accrual_completeness(
        account_balances,
        classified_accounts,
        prior_operating_expenses=prior_operating_expenses,
        threshold_pct=threshold_pct,
        total_revenue=total_revenue,
    )
