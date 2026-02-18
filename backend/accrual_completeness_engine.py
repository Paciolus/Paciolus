"""
Paciolus — Accrual Completeness Estimator Engine
Sprint 290: Phase XXXIX

Identifies accrued liability accounts from the trial balance, computes a
monthly expense run-rate from prior-period DiagnosticSummary operating expenses,
and produces an accrual-to-run-rate ratio with a configurable threshold.

Guardrail: "Balance appears low relative to run-rate" — NEVER
"liabilities may be understated". Descriptive metrics only.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

from column_detector import detect_columns


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
]

NEAR_ZERO = 1e-10
DEFAULT_THRESHOLD_PCT = 50.0
MONTHS_PER_YEAR = 12


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════

@dataclass
class AccrualAccount:
    """One identified accrual account."""
    account_name: str
    balance: float
    matched_keyword: str

    def to_dict(self) -> dict:
        return {
            "account_name": self.account_name,
            "balance": round(self.balance, 2),
            "matched_keyword": self.matched_keyword,
        }


@dataclass
class AccrualCompletenessReport:
    """Complete accrual completeness estimator result."""
    accrual_accounts: list[AccrualAccount] = field(default_factory=list)
    total_accrued_balance: float = 0.0
    accrual_account_count: int = 0
    monthly_run_rate: Optional[float] = None
    accrual_to_run_rate_pct: Optional[float] = None
    threshold_pct: float = DEFAULT_THRESHOLD_PCT
    below_threshold: bool = False
    prior_operating_expenses: Optional[float] = None
    prior_available: bool = False
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "accrual_accounts": [a.to_dict() for a in self.accrual_accounts],
            "total_accrued_balance": round(self.total_accrued_balance, 2),
            "accrual_account_count": self.accrual_account_count,
            "monthly_run_rate": round(self.monthly_run_rate, 2) if self.monthly_run_rate is not None else None,
            "accrual_to_run_rate_pct": round(self.accrual_to_run_rate_pct, 2) if self.accrual_to_run_rate_pct is not None else None,
            "threshold_pct": round(self.threshold_pct, 2),
            "below_threshold": self.below_threshold,
            "prior_operating_expenses": round(self.prior_operating_expenses, 2) if self.prior_operating_expenses is not None else None,
            "prior_available": self.prior_available,
            "narrative": self.narrative,
        }


# ═══════════════════════════════════════════════════════════════
# Accrual account identification
# ═══════════════════════════════════════════════════════════════

def _is_accrual_account(account_name: str) -> Optional[str]:
    """Check if an account name matches accrual keywords.

    Returns the matched keyword or None.
    Phrase keywords (multi-word) are checked first for specificity.
    """
    name_lower = account_name.lower()

    # Check phrase keywords first (longer = more specific)
    for kw in sorted(ACCRUAL_KEYWORDS, key=len, reverse=True):
        if kw in name_lower:
            return kw

    return None


# ═══════════════════════════════════════════════════════════════
# Core computation
# ═══════════════════════════════════════════════════════════════

def compute_accrual_completeness(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: dict[str, str],
    prior_operating_expenses: Optional[float] = None,
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
) -> AccrualCompletenessReport:
    """Compute accrual completeness estimator from pre-aggregated account balances.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: {account_name: category_string} from classifier
        prior_operating_expenses: Annual operating expenses from prior DiagnosticSummary
        threshold_pct: Accrual-to-run-rate % below which to flag (default 50%)

    Returns:
        AccrualCompletenessReport with identified accruals and ratio analysis.
    """
    if not account_balances:
        return AccrualCompletenessReport(
            threshold_pct=threshold_pct,
            narrative="No account data available for analysis.",
        )

    # Identify accrual accounts (must be classified as liability)
    liability_types = {"liability"}
    accrual_accounts: list[AccrualAccount] = []

    for acct_name, bals in account_balances.items():
        classification = classified_accounts.get(acct_name, "").lower()
        if classification not in liability_types:
            continue

        matched_kw = _is_accrual_account(acct_name)
        if matched_kw is None:
            continue

        # Liabilities are credit-heavy; balance = credit - debit
        balance = bals["credit"] - bals["debit"]
        if abs(balance) < NEAR_ZERO:
            continue

        accrual_accounts.append(AccrualAccount(
            account_name=acct_name,
            balance=balance,
            matched_keyword=matched_kw,
        ))

    # Sort by balance descending
    accrual_accounts.sort(key=lambda a: abs(a.balance), reverse=True)

    total_accrued = math.fsum(a.balance for a in accrual_accounts)
    accrual_count = len(accrual_accounts)

    # Compute run-rate if prior data available
    prior_available = prior_operating_expenses is not None and abs(prior_operating_expenses) > NEAR_ZERO
    monthly_run_rate: Optional[float] = None
    accrual_to_run_rate: Optional[float] = None
    below_threshold = False

    if prior_available:
        monthly_run_rate = prior_operating_expenses / MONTHS_PER_YEAR
        if abs(monthly_run_rate) > NEAR_ZERO:
            accrual_to_run_rate = (total_accrued / monthly_run_rate) * 100
            below_threshold = accrual_to_run_rate < threshold_pct

    # Build narrative (guardrail: descriptive only)
    narrative = _build_narrative(
        accrual_count, total_accrued, monthly_run_rate,
        accrual_to_run_rate, threshold_pct, below_threshold, prior_available,
    )

    return AccrualCompletenessReport(
        accrual_accounts=accrual_accounts,
        total_accrued_balance=total_accrued,
        accrual_account_count=accrual_count,
        monthly_run_rate=monthly_run_rate,
        accrual_to_run_rate_pct=accrual_to_run_rate,
        threshold_pct=threshold_pct,
        below_threshold=below_threshold,
        prior_operating_expenses=prior_operating_expenses,
        prior_available=prior_available,
        narrative=narrative,
    )


def _build_narrative(
    count: int,
    total: float,
    run_rate: Optional[float],
    ratio: Optional[float],
    threshold: float,
    below: bool,
    prior_available: bool,
) -> str:
    """Build a descriptive narrative for the accrual completeness analysis.

    Guardrail: uses ONLY descriptive language. Never states that liabilities
    are understated or that the client has a deficiency.
    """
    if count == 0:
        return "No accrued liability accounts were identified in the trial balance."

    parts = [f"Identified {count} accrued liability account{'s' if count != 1 else ''} "
             f"with a combined balance of ${total:,.2f}."]

    if prior_available and run_rate is not None and ratio is not None:
        parts.append(
            f"The monthly expense run-rate based on prior-period operating expenses "
            f"is ${run_rate:,.2f}."
        )
        parts.append(
            f"The accrual-to-run-rate ratio is {ratio:.1f}% "
            f"(threshold: {threshold:.0f}%)."
        )
        if below:
            parts.append(
                "The accrued balance appears low relative to the monthly expense run-rate. "
                "The practitioner should determine whether this warrants further inquiry."
            )
        else:
            parts.append(
                "The accrued balance is at or above the expected threshold "
                "relative to the monthly expense run-rate."
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

        try:
            debit = float(row.get(debit_col) or 0)
        except (ValueError, TypeError):
            debit = 0.0
        try:
            credit = float(row.get(credit_col) or 0)
        except (ValueError, TypeError):
            credit = 0.0

        if acct_str not in account_balances:
            account_balances[acct_str] = {"debit": 0.0, "credit": 0.0}
        account_balances[acct_str]["debit"] += debit
        account_balances[acct_str]["credit"] += credit

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
    )
