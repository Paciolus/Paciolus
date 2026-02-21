"""
Paciolus — Lease Account Diagnostic Engine
Sprint 357: Phase XLIX — IFRS 16 / ASC 842

Identifies lease-related accounts from the trial balance via keyword matching,
pairs ROU assets with lease liabilities, and runs four deterministic tests:
1. Directional consistency (ROU asset ↔ lease liability both present)
2. Classification check (current vs non-current lease liability presence)
3. Amortization trend (ROU asset reduction vs prior period, if available)
4. Expense account presence (lease amortization/expense account exists)

Guardrail: Descriptive metrics only — NEVER evaluative language.
All computation is ephemeral (zero-storage compliance).

IFRS 16 § 22–38, ASC 842 § 20–30.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

NEAR_ZERO = 1e-10

# ═══════════════════════════════════════════════════════════════
# Keyword lists for lease account classification
# ═══════════════════════════════════════════════════════════════

LEASE_ROU_KEYWORDS = [
    "right-of-use asset",
    "right of use asset",
    "right-of-use",
    "right of use",
    "rou asset",
    "rou -",
    "operating lease asset",
    "finance lease asset",
    "lease asset",
]

LEASE_LIABILITY_KEYWORDS = [
    "lease liability current",
    "lease liability non-current",
    "lease liability noncurrent",
    "lease liability long-term",
    "lease liability long term",
    "lease liability - current",
    "lease liability - non-current",
    "lease obligation current",
    "lease obligation non-current",
    "lease obligation",
    "lease liability",
    "lease payable",
    "operating lease liability",
    "finance lease liability",
]

LEASE_EXPENSE_KEYWORDS = [
    "lease amortization",
    "lease depreciation",
    "rou amortization",
    "rou depreciation",
    "right-of-use amortization",
    "right of use amortization",
    "lease expense",
    "operating lease expense",
    "finance lease expense",
    "lease interest",
    "lease interest expense",
]


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════

@dataclass
class LeaseAccount:
    """A single identified lease-related account."""
    account_name: str
    classification: str  # "rou_asset", "lease_liability", "lease_expense"
    balance: float
    matched_keyword: str

    def to_dict(self) -> dict:
        return {
            "account_name": self.account_name,
            "classification": self.classification,
            "balance": round(self.balance, 2),
            "matched_keyword": self.matched_keyword,
        }


@dataclass
class LeaseIssue:
    """A flagged issue from lease diagnostic tests."""
    test_name: str
    severity: str  # "high", "medium", "low"
    description: str
    accounts_involved: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "severity": self.severity,
            "description": self.description,
            "accounts_involved": self.accounts_involved,
        }


@dataclass
class LeaseDiagnosticReport:
    """Complete lease diagnostic result."""
    rou_accounts: list[LeaseAccount] = field(default_factory=list)
    liability_accounts: list[LeaseAccount] = field(default_factory=list)
    expense_accounts: list[LeaseAccount] = field(default_factory=list)
    total_rou_balance: float = 0.0
    total_liability_balance: float = 0.0
    total_expense_balance: float = 0.0
    balance_difference: float = 0.0
    issues: list[LeaseIssue] = field(default_factory=list)
    issue_count: int = 0
    lease_accounts_detected: bool = False
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "rou_accounts": [a.to_dict() for a in self.rou_accounts],
            "liability_accounts": [a.to_dict() for a in self.liability_accounts],
            "expense_accounts": [a.to_dict() for a in self.expense_accounts],
            "total_rou_balance": round(self.total_rou_balance, 2),
            "total_liability_balance": round(self.total_liability_balance, 2),
            "total_expense_balance": round(self.total_expense_balance, 2),
            "balance_difference": round(self.balance_difference, 2),
            "issues": [i.to_dict() for i in self.issues],
            "issue_count": self.issue_count,
            "lease_accounts_detected": self.lease_accounts_detected,
            "narrative": self.narrative,
        }


# ═══════════════════════════════════════════════════════════════
# Keyword matching
# ═══════════════════════════════════════════════════════════════

def _classify_lease_account(account_name: str) -> tuple[Optional[str], Optional[str]]:
    """Classify an account as lease-related.

    Returns (classification, matched_keyword) or (None, None).
    Checks longer (more specific) keywords first.
    """
    name_lower = account_name.lower()

    for kw in sorted(LEASE_ROU_KEYWORDS, key=len, reverse=True):
        if kw in name_lower:
            return "rou_asset", kw

    for kw in sorted(LEASE_LIABILITY_KEYWORDS, key=len, reverse=True):
        if kw in name_lower:
            return "lease_liability", kw

    for kw in sorted(LEASE_EXPENSE_KEYWORDS, key=len, reverse=True):
        if kw in name_lower:
            return "lease_expense", kw

    return None, None


# ═══════════════════════════════════════════════════════════════
# Diagnostic tests
# ═══════════════════════════════════════════════════════════════

def _test_directional_consistency(
    rou_accounts: list[LeaseAccount],
    liability_accounts: list[LeaseAccount],
    total_rou: float,
    total_liability: float,
    materiality_threshold: float,
) -> list[LeaseIssue]:
    """Test 1: ROU asset and lease liability should both exist if either is material."""
    issues: list[LeaseIssue] = []

    has_material_rou = abs(total_rou) >= materiality_threshold
    has_material_liability = abs(total_liability) >= materiality_threshold

    if has_material_rou and not liability_accounts:
        issues.append(LeaseIssue(
            test_name="Directional Consistency",
            severity="high",
            description=(
                f"ROU asset balance of ${total_rou:,.2f} detected "
                f"with no corresponding lease liability accounts."
            ),
            accounts_involved=[a.account_name for a in rou_accounts],
        ))
    elif has_material_liability and not rou_accounts:
        issues.append(LeaseIssue(
            test_name="Directional Consistency",
            severity="high",
            description=(
                f"Lease liability balance of ${total_liability:,.2f} detected "
                f"with no corresponding ROU asset accounts."
            ),
            accounts_involved=[a.account_name for a in liability_accounts],
        ))

    return issues


def _test_classification_check(
    liability_accounts: list[LeaseAccount],
    total_liability: float,
    materiality_threshold: float,
) -> list[LeaseIssue]:
    """Test 2: Lease liabilities should include both current and non-current portions."""
    issues: list[LeaseIssue] = []

    if not liability_accounts or abs(total_liability) < materiality_threshold:
        return issues

    has_current = any(
        "current" in a.matched_keyword and "non-current" not in a.matched_keyword
        and "noncurrent" not in a.matched_keyword and "long" not in a.matched_keyword
        for a in liability_accounts
    )
    has_noncurrent = any(
        "non-current" in a.matched_keyword or "noncurrent" in a.matched_keyword
        or "long" in a.matched_keyword
        for a in liability_accounts
    )

    if len(liability_accounts) >= 1 and not has_current and not has_noncurrent:
        # Generic "lease liability" — no current/non-current split detected
        if abs(total_liability) >= materiality_threshold:
            issues.append(LeaseIssue(
                test_name="Classification Check",
                severity="medium",
                description=(
                    f"Lease liability balance of ${total_liability:,.2f} is not split "
                    f"between current and non-current portions."
                ),
                accounts_involved=[a.account_name for a in liability_accounts],
            ))
    elif has_current and not has_noncurrent:
        issues.append(LeaseIssue(
            test_name="Classification Check",
            severity="low",
            description=(
                "Only current lease liability accounts detected. "
                "Non-current portion may not be separately presented."
            ),
            accounts_involved=[a.account_name for a in liability_accounts if "current" in a.matched_keyword],
        ))
    elif has_noncurrent and not has_current:
        issues.append(LeaseIssue(
            test_name="Classification Check",
            severity="low",
            description=(
                "Only non-current lease liability accounts detected. "
                "Current portion may not be separately presented."
            ),
            accounts_involved=[
                a.account_name for a in liability_accounts
                if "non-current" in a.matched_keyword or "noncurrent" in a.matched_keyword
                or "long" in a.matched_keyword
            ],
        ))

    return issues


def _test_amortization_trend(
    rou_accounts: list[LeaseAccount],
    total_rou: float,
    prior_account_balances: Optional[dict[str, dict[str, float]]],
) -> list[LeaseIssue]:
    """Test 3: ROU asset should decrease period-over-period (amortization)."""
    issues: list[LeaseIssue] = []

    if not prior_account_balances or not rou_accounts:
        return issues

    # Find prior ROU balances
    prior_rou_total = 0.0
    for acct_name, bals in prior_account_balances.items():
        classification, _ = _classify_lease_account(acct_name)
        if classification == "rou_asset":
            # Assets are debit-heavy
            prior_rou_total += bals.get("debit", 0.0) - bals.get("credit", 0.0)

    if abs(prior_rou_total) < NEAR_ZERO:
        return issues

    # ROU should decrease (amortization reduces the asset)
    reduction_pct = ((prior_rou_total - total_rou) / abs(prior_rou_total)) * 100

    if reduction_pct < 0:
        # ROU increased — could be new leases, but worth noting
        issues.append(LeaseIssue(
            test_name="Amortization Trend",
            severity="medium",
            description=(
                f"ROU asset balance increased from ${prior_rou_total:,.2f} to "
                f"${total_rou:,.2f} ({abs(reduction_pct):.1f}% increase). "
                f"New lease additions or reclassifications may have occurred."
            ),
            accounts_involved=[a.account_name for a in rou_accounts],
        ))
    elif reduction_pct < 5.0 and abs(prior_rou_total) > NEAR_ZERO:
        # Less than 5% reduction — unusually low amortization
        issues.append(LeaseIssue(
            test_name="Amortization Trend",
            severity="low",
            description=(
                f"ROU asset decreased by {reduction_pct:.1f}% from "
                f"${prior_rou_total:,.2f} to ${total_rou:,.2f}. "
                f"Amortization rate is below the 5% minimum expected reduction."
            ),
            accounts_involved=[a.account_name for a in rou_accounts],
        ))

    return issues


def _test_expense_presence(
    rou_accounts: list[LeaseAccount],
    expense_accounts: list[LeaseAccount],
    total_rou: float,
    materiality_threshold: float,
) -> list[LeaseIssue]:
    """Test 4: If ROU assets exist, lease amortization/expense accounts should too."""
    issues: list[LeaseIssue] = []

    if not rou_accounts or abs(total_rou) < materiality_threshold:
        return issues

    if not expense_accounts:
        issues.append(LeaseIssue(
            test_name="Expense Account Presence",
            severity="medium",
            description=(
                f"ROU asset balance of ${total_rou:,.2f} detected but no "
                f"lease amortization or lease expense accounts found."
            ),
            accounts_involved=[a.account_name for a in rou_accounts],
        ))

    return issues


# ═══════════════════════════════════════════════════════════════
# Narrative builder
# ═══════════════════════════════════════════════════════════════

def _build_narrative(
    rou_count: int,
    liability_count: int,
    expense_count: int,
    total_rou: float,
    total_liability: float,
    issue_count: int,
) -> str:
    """Build descriptive narrative (no evaluative language)."""
    if rou_count == 0 and liability_count == 0:
        return "No lease-related accounts detected in the trial balance."

    parts = []
    if rou_count > 0:
        parts.append(
            f"{rou_count} ROU asset account(s) with total balance ${total_rou:,.2f}"
        )
    if liability_count > 0:
        parts.append(
            f"{liability_count} lease liability account(s) with total balance ${total_liability:,.2f}"
        )
    if expense_count > 0:
        parts.append(f"{expense_count} lease expense/amortization account(s)")

    summary = "Lease accounts identified: " + "; ".join(parts) + "."

    if issue_count > 0:
        summary += f" {issue_count} diagnostic issue(s) flagged for review."
    else:
        summary += " No diagnostic issues flagged."

    return summary


# ═══════════════════════════════════════════════════════════════
# Main computation
# ═══════════════════════════════════════════════════════════════

def compute_lease_diagnostic(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: dict[str, str],
    materiality_threshold: float = 0.0,
    prior_account_balances: Optional[dict[str, dict[str, float]]] = None,
) -> LeaseDiagnosticReport:
    """Compute lease account diagnostic from pre-aggregated account balances.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: {account_name: category_string} from classifier
        materiality_threshold: Balance threshold for materiality flagging
        prior_account_balances: Optional prior-period balances for trend analysis

    Returns:
        LeaseDiagnosticReport with identified accounts, pair analysis, and issues.
    """
    if not account_balances:
        return LeaseDiagnosticReport(
            narrative="No account data available for lease analysis.",
        )

    rou_accounts: list[LeaseAccount] = []
    liability_accounts: list[LeaseAccount] = []
    expense_accounts: list[LeaseAccount] = []

    for acct_name, bals in account_balances.items():
        classification, matched_kw = _classify_lease_account(acct_name)
        if classification is None:
            continue

        # Compute balance based on normal balance direction
        if classification == "rou_asset":
            balance = bals.get("debit", 0.0) - bals.get("credit", 0.0)
        elif classification == "lease_liability":
            balance = bals.get("credit", 0.0) - bals.get("debit", 0.0)
        else:  # lease_expense
            balance = bals.get("debit", 0.0) - bals.get("credit", 0.0)

        if abs(balance) < NEAR_ZERO:
            continue

        account = LeaseAccount(
            account_name=acct_name,
            classification=classification,
            balance=balance,
            matched_keyword=matched_kw,
        )

        if classification == "rou_asset":
            rou_accounts.append(account)
        elif classification == "lease_liability":
            liability_accounts.append(account)
        else:
            expense_accounts.append(account)

    # Sort by balance descending
    rou_accounts.sort(key=lambda a: abs(a.balance), reverse=True)
    liability_accounts.sort(key=lambda a: abs(a.balance), reverse=True)
    expense_accounts.sort(key=lambda a: abs(a.balance), reverse=True)

    total_rou = math.fsum(a.balance for a in rou_accounts)
    total_liability = math.fsum(a.balance for a in liability_accounts)
    total_expense = math.fsum(a.balance for a in expense_accounts)
    balance_difference = total_rou - total_liability

    # Run diagnostic tests
    issues: list[LeaseIssue] = []
    issues.extend(_test_directional_consistency(
        rou_accounts, liability_accounts, total_rou, total_liability, materiality_threshold
    ))
    issues.extend(_test_classification_check(
        liability_accounts, total_liability, materiality_threshold
    ))
    issues.extend(_test_amortization_trend(
        rou_accounts, total_rou, prior_account_balances
    ))
    issues.extend(_test_expense_presence(
        rou_accounts, expense_accounts, total_rou, materiality_threshold
    ))

    lease_detected = len(rou_accounts) > 0 or len(liability_accounts) > 0

    narrative = _build_narrative(
        len(rou_accounts), len(liability_accounts), len(expense_accounts),
        total_rou, total_liability, len(issues),
    )

    return LeaseDiagnosticReport(
        rou_accounts=rou_accounts,
        liability_accounts=liability_accounts,
        expense_accounts=expense_accounts,
        total_rou_balance=total_rou,
        total_liability_balance=total_liability,
        total_expense_balance=total_expense,
        balance_difference=balance_difference,
        issues=issues,
        issue_count=len(issues),
        lease_accounts_detected=lease_detected,
        narrative=narrative,
    )
