"""
Paciolus — Cutoff Period Risk Indicator Engine
Sprint 358: Phase XLIX — ISA 501

Identifies accounts where TB balance patterns suggest period-end cutoff risk.
Targets accrual, prepaid, and deferred revenue accounts with three
deterministic tests:
1. Round-number test — balance divisible by 1,000 (potential estimate)
2. Zero-balance test — material prior balance now zero (potential omission)
3. Spike test — period-over-period change >3x prior (potential timing issue)

Guardrail: Descriptive metrics only — factual observations, no conclusions.
All computation is ephemeral (zero-storage compliance).

ISA 501 (Audit Evidence — Specific Considerations), ASC 855.
"""

from dataclasses import dataclass, field
from typing import Optional

NEAR_ZERO = 1e-10

# ═══════════════════════════════════════════════════════════════
# Cutoff-sensitive account keywords
# ═══════════════════════════════════════════════════════════════

CUTOFF_SENSITIVE_KEYWORDS = [
    # Accrued liabilities
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
    # Prepaid expenses
    "prepaid",
    "prepaid expense",
    "prepaid insurance",
    "prepaid rent",
    "prepaid interest",
    # Deferred revenue
    "deferred revenue",
    "deferred income",
    "unearned revenue",
    "unearned income",
    "contract liability",
    "advance from customer",
    "customer deposit",
    "customer advance",
    # Accounts payable (cutoff-relevant)
    "accounts payable",
    "trade payable",
]


# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════

@dataclass
class CutoffFlag:
    """A single cutoff risk flag for an account."""
    account_name: str
    test_name: str
    severity: str  # "high", "medium", "low"
    description: str
    balance: float
    prior_balance: Optional[float] = None

    def to_dict(self) -> dict:
        result: dict = {
            "account_name": self.account_name,
            "test_name": self.test_name,
            "severity": self.severity,
            "description": self.description,
            "balance": round(self.balance, 2),
        }
        if self.prior_balance is not None:
            result["prior_balance"] = round(self.prior_balance, 2)
        return result


@dataclass
class CutoffRiskReport:
    """Complete cutoff risk indicator result."""
    cutoff_sensitive_count: int = 0
    flagged_accounts: list[CutoffFlag] = field(default_factory=list)
    flag_count: int = 0
    round_number_flags: int = 0
    zero_balance_flags: int = 0
    spike_flags: int = 0
    prior_period_available: bool = False
    narrative: str = ""

    def to_dict(self) -> dict:
        return {
            "cutoff_sensitive_count": self.cutoff_sensitive_count,
            "flagged_accounts": [f.to_dict() for f in self.flagged_accounts],
            "flag_count": self.flag_count,
            "round_number_flags": self.round_number_flags,
            "zero_balance_flags": self.zero_balance_flags,
            "spike_flags": self.spike_flags,
            "prior_period_available": self.prior_period_available,
            "narrative": self.narrative,
        }


# ═══════════════════════════════════════════════════════════════
# Keyword matching
# ═══════════════════════════════════════════════════════════════

def _is_cutoff_sensitive(account_name: str) -> Optional[str]:
    """Check if account is cutoff-sensitive. Returns matched keyword or None."""
    name_lower = account_name.lower()
    for kw in sorted(CUTOFF_SENSITIVE_KEYWORDS, key=len, reverse=True):
        if kw in name_lower:
            return kw
    return None


# ═══════════════════════════════════════════════════════════════
# Cutoff tests
# ═══════════════════════════════════════════════════════════════

def _test_round_number(
    account_name: str,
    balance: float,
    materiality_threshold: float,
) -> Optional[CutoffFlag]:
    """Test 1: Flag cutoff-sensitive accounts with round balances (divisible by 1000).

    Round balances in accrual/prepaid accounts may indicate estimates rather than
    calculated accruals, which increases cutoff risk.
    """
    if abs(balance) < materiality_threshold:
        return None

    # Check divisible by 1000 with zero remainder
    if abs(balance) >= 1000 and abs(balance % 1000) < NEAR_ZERO:
        severity = "high" if abs(balance) >= materiality_threshold * 2 else "medium"
        return CutoffFlag(
            account_name=account_name,
            test_name="Round Number",
            severity=severity,
            description=(
                f"Balance of ${balance:,.2f} is a round number (divisible by $1,000). "
                f"Cutoff-sensitive accounts with round balances may indicate estimated accruals."
            ),
            balance=balance,
        )
    return None


def _test_zero_balance(
    account_name: str,
    balance: float,
    prior_balance: float,
    materiality_threshold: float,
) -> Optional[CutoffFlag]:
    """Test 2: Flag cutoff-sensitive accounts with zero current balance but material prior balance.

    A material accrual/prepaid that drops to zero may indicate a cutoff omission
    (reversal without re-accrual).
    """
    if abs(balance) > NEAR_ZERO:
        return None  # Not zero — skip

    if abs(prior_balance) < materiality_threshold:
        return None  # Prior was immaterial — skip

    severity = "high" if abs(prior_balance) >= materiality_threshold * 2 else "medium"
    return CutoffFlag(
        account_name=account_name,
        test_name="Zero Balance",
        severity=severity,
        description=(
            f"Balance is $0.00 but prior period balance was ${prior_balance:,.2f}. "
            f"A material cutoff-sensitive account dropping to zero may indicate "
            f"reversal without re-accrual."
        ),
        balance=balance,
        prior_balance=prior_balance,
    )


def _test_spike(
    account_name: str,
    balance: float,
    prior_balance: float,
    materiality_threshold: float,
) -> Optional[CutoffFlag]:
    """Test 3: Flag cutoff-sensitive accounts where balance changed >3x from prior.

    A 3x+ spike in an accrual/deferred account may indicate a cutoff timing issue
    (transactions recorded in the wrong period).
    """
    if abs(balance) < materiality_threshold:
        return None
    if abs(prior_balance) < NEAR_ZERO:
        return None  # Can't compute ratio without prior

    change_ratio = abs(balance) / abs(prior_balance)
    if change_ratio <= 3.0:
        return None

    severity = "high" if change_ratio > 5.0 else "medium"
    return CutoffFlag(
        account_name=account_name,
        test_name="Balance Spike",
        severity=severity,
        description=(
            f"Balance changed from ${prior_balance:,.2f} to ${balance:,.2f} "
            f"({change_ratio:.1f}x). A {change_ratio:.1f}x change in a "
            f"cutoff-sensitive account may indicate a period-end timing issue."
        ),
        balance=balance,
        prior_balance=prior_balance,
    )


# ═══════════════════════════════════════════════════════════════
# Main computation
# ═══════════════════════════════════════════════════════════════

def compute_cutoff_risk(
    account_balances: dict[str, dict[str, float]],
    classified_accounts: dict[str, str],
    materiality_threshold: float = 0.0,
    prior_account_balances: Optional[dict[str, dict[str, float]]] = None,
) -> CutoffRiskReport:
    """Compute cutoff risk indicators from pre-aggregated account balances.

    Args:
        account_balances: {account_name: {"debit": float, "credit": float}}
        classified_accounts: {account_name: category_string} from classifier
        materiality_threshold: Balance threshold for flagging
        prior_account_balances: Optional prior-period balances for tests 2 & 3

    Returns:
        CutoffRiskReport with cutoff-sensitive accounts and flagged issues.
    """
    if not account_balances:
        return CutoffRiskReport(narrative="No account data available for cutoff analysis.")

    prior_available = prior_account_balances is not None and len(prior_account_balances) > 0

    # Identify cutoff-sensitive accounts
    cutoff_accounts: list[tuple[str, float, Optional[str]]] = []  # (name, balance, keyword)

    for acct_name, bals in account_balances.items():
        keyword = _is_cutoff_sensitive(acct_name)
        if keyword is None:
            continue

        classification = classified_accounts.get(acct_name, "").lower()
        # Compute net balance based on account type
        if classification in ("asset",):
            balance = bals.get("debit", 0.0) - bals.get("credit", 0.0)
        elif classification in ("liability", "revenue"):
            balance = bals.get("credit", 0.0) - bals.get("debit", 0.0)
        else:
            # Default: use absolute net
            debit = bals.get("debit", 0.0)
            credit = bals.get("credit", 0.0)
            balance = debit - credit if debit >= credit else credit - debit

        cutoff_accounts.append((acct_name, balance, keyword))

    cutoff_count = len(cutoff_accounts)

    # Run tests
    flags: list[CutoffFlag] = []
    round_count = 0
    zero_count = 0
    spike_count = 0

    for acct_name, balance, _kw in cutoff_accounts:
        # Test 1: Round number
        flag = _test_round_number(acct_name, balance, materiality_threshold)
        if flag:
            flags.append(flag)
            round_count += 1

        # Tests 2 & 3 require prior period
        if prior_available:
            prior_bals = prior_account_balances.get(acct_name)  # type: ignore[union-attr]
            if prior_bals:
                prior_classification = classified_accounts.get(acct_name, "").lower()
                if prior_classification in ("asset",):
                    prior_balance = prior_bals.get("debit", 0.0) - prior_bals.get("credit", 0.0)
                elif prior_classification in ("liability", "revenue"):
                    prior_balance = prior_bals.get("credit", 0.0) - prior_bals.get("debit", 0.0)
                else:
                    d = prior_bals.get("debit", 0.0)
                    c = prior_bals.get("credit", 0.0)
                    prior_balance = d - c if d >= c else c - d

                # Test 2: Zero balance
                flag = _test_zero_balance(acct_name, balance, prior_balance, materiality_threshold)
                if flag:
                    flags.append(flag)
                    zero_count += 1

                # Test 3: Spike
                flag = _test_spike(acct_name, balance, prior_balance, materiality_threshold)
                if flag:
                    flags.append(flag)
                    spike_count += 1

    # Build narrative
    if cutoff_count == 0:
        narrative = "No cutoff-sensitive accounts detected in the trial balance."
    else:
        narrative = f"{cutoff_count} cutoff-sensitive account(s) identified."
        if len(flags) > 0:
            narrative += f" {len(flags)} flag(s) raised across {round_count} round-number, {zero_count} zero-balance, and {spike_count} spike test(s)."
        else:
            narrative += " No cutoff risk flags raised."
        if not prior_available:
            narrative += " Prior period data not available — zero-balance and spike tests were skipped."

    return CutoffRiskReport(
        cutoff_sensitive_count=cutoff_count,
        flagged_accounts=flags,
        flag_count=len(flags),
        round_number_flags=round_count,
        zero_balance_flags=zero_count,
        spike_flags=spike_count,
        prior_period_available=prior_available,
        narrative=narrative,
    )
