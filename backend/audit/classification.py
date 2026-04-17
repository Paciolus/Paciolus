"""Account classification, legacy keyword mappings, and chart-of-accounts logic.

This module owns the mapping from raw account names to accounting categories.
It wraps the weighted-heuristic ``AccountClassifier`` and the CSV-provided
type resolution logic, providing a single ``_resolve_category`` entry point
that respects the priority: CSV-provided type > heuristic classifier.  It
also contains the balance-sheet equation validator and the legacy keyword
lists retained for backward compatibility.
"""

from __future__ import annotations

import threading
from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from classification_rules import (
    NORMAL_BALANCE_MAP,
    AccountCategory,
    NormalBalance,
    is_contra_account,
)
from ratio_engine import CategoryTotals
from security_utils import log_secure_operation
from shared.monetary import BALANCE_TOLERANCE

# ── Legacy keyword mappings ──────────────────────────────────────────
# Kept for backward compatibility with detect_abnormal_balances().
# The production path uses weighted heuristics in AccountClassifier.
ASSET_KEYWORDS = [
    "cash",
    "bank",
    "receivable",
    "inventory",
    "prepaid",
    "equipment",
    "land",
    "building",
    "vehicle",
]
LIABILITY_KEYWORDS = [
    "payable",
    "loan",
    "tax",
    "accrued",
    "unearned",
    "deferred",
    "debt",
    "mortgage",
    "note payable",
]

# Balance sheet imbalance severity thresholds
BS_IMBALANCE_THRESHOLD_LOW = 1_000
BS_IMBALANCE_THRESHOLD_HIGH = 10_000

# Classification confidence thresholds
CONFIDENCE_HIGH = 0.7
CONFIDENCE_MEDIUM = 0.4


# ── CSV Type Resolution ──────────────────────────────────────────────

_CSV_TYPE_MAP: dict[str, AccountCategory] = {
    # Asset variants
    "asset": AccountCategory.ASSET,
    "assets": AccountCategory.ASSET,
    "current asset": AccountCategory.ASSET,
    "current assets": AccountCategory.ASSET,
    "non-current asset": AccountCategory.ASSET,
    "non-current assets": AccountCategory.ASSET,
    "noncurrent asset": AccountCategory.ASSET,
    "noncurrent assets": AccountCategory.ASSET,
    "long-term asset": AccountCategory.ASSET,
    "long-term assets": AccountCategory.ASSET,
    "fixed asset": AccountCategory.ASSET,
    "fixed assets": AccountCategory.ASSET,
    "other asset": AccountCategory.ASSET,
    "other assets": AccountCategory.ASSET,
    # Liability variants
    "liability": AccountCategory.LIABILITY,
    "liabilities": AccountCategory.LIABILITY,
    "current liability": AccountCategory.LIABILITY,
    "current liabilities": AccountCategory.LIABILITY,
    "non-current liability": AccountCategory.LIABILITY,
    "non-current liabilities": AccountCategory.LIABILITY,
    "noncurrent liability": AccountCategory.LIABILITY,
    "noncurrent liabilities": AccountCategory.LIABILITY,
    "long-term liability": AccountCategory.LIABILITY,
    "long-term liabilities": AccountCategory.LIABILITY,
    "other liability": AccountCategory.LIABILITY,
    "other liabilities": AccountCategory.LIABILITY,
    # Equity variants
    "equity": AccountCategory.EQUITY,
    "stockholders equity": AccountCategory.EQUITY,
    "shareholders equity": AccountCategory.EQUITY,
    "owners equity": AccountCategory.EQUITY,
    "net assets": AccountCategory.EQUITY,
    # Revenue variants
    "revenue": AccountCategory.REVENUE,
    "revenues": AccountCategory.REVENUE,
    "income": AccountCategory.REVENUE,
    "sales": AccountCategory.REVENUE,
    "non-operating revenue": AccountCategory.REVENUE,
    "non-operating income": AccountCategory.REVENUE,
    "nonoperating revenue": AccountCategory.REVENUE,
    "other income": AccountCategory.REVENUE,
    "other revenue": AccountCategory.REVENUE,
    # Expense variants
    "expense": AccountCategory.EXPENSE,
    "expenses": AccountCategory.EXPENSE,
    "cost of revenue": AccountCategory.EXPENSE,
    "cost of goods sold": AccountCategory.EXPENSE,
    "cogs": AccountCategory.EXPENSE,
    "operating expense": AccountCategory.EXPENSE,
    "operating expenses": AccountCategory.EXPENSE,
    "non-operating expense": AccountCategory.EXPENSE,
    "nonoperating expense": AccountCategory.EXPENSE,
    "other expense": AccountCategory.EXPENSE,
    "other expenses": AccountCategory.EXPENSE,
    "selling general and administrative": AccountCategory.EXPENSE,
    "sg&a": AccountCategory.EXPENSE,
}

# Suffix fallback for compound values not in the explicit map
_CSV_TYPE_SUFFIXES: list[tuple[str, AccountCategory]] = [
    ("asset", AccountCategory.ASSET),
    ("assets", AccountCategory.ASSET),
    ("liability", AccountCategory.LIABILITY),
    ("liabilities", AccountCategory.LIABILITY),
    ("equity", AccountCategory.EQUITY),
    ("revenue", AccountCategory.REVENUE),
    ("revenues", AccountCategory.REVENUE),
    ("income", AccountCategory.REVENUE),
    ("expense", AccountCategory.EXPENSE),
    ("expenses", AccountCategory.EXPENSE),
]

_csv_type_log_lock = threading.Lock()
_csv_type_log_count: int = 0


def resolve_csv_type(raw_value: str) -> tuple[AccountCategory | None, float]:
    """Resolve a raw CSV account type value to a category and confidence.

    Returns (category, confidence) or (None, 0.0) if no match.
    Direct map hit = 1.0 confidence; suffix match = 0.90.
    """
    global _csv_type_log_count
    normalized = raw_value.lower().strip()

    if _csv_type_log_count < 5 and raw_value:
        with _csv_type_log_lock:
            if _csv_type_log_count < 5:
                _csv_type_log_count += 1
                log_secure_operation(
                    "csv_type_trace",
                    f"[{_csv_type_log_count}/5] raw={raw_value!r} normalized={normalized!r}",
                )

    if not normalized:
        return None, 0.0
    # Direct lookup
    if normalized in _CSV_TYPE_MAP:
        return _CSV_TYPE_MAP[normalized], 1.0
    # Suffix fallback
    for suffix, category in _CSV_TYPE_SUFFIXES:
        if normalized.endswith(suffix):
            return category, 0.90
    return None, 0.0


def resolve_category(
    account_key: str,
    net_balance: float,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
    classifier: AccountClassifier,
) -> AccountCategory:
    """Resolve the account category -- CSV-provided type takes priority over heuristic."""
    csv_raw = provided_account_types.get(account_key, "")
    csv_category, _ = resolve_csv_type(csv_raw)
    if csv_category is not None:
        return csv_category
    # Fallback: use the heuristic classifier with account name context
    classify_name = build_display_name(account_key, provided_account_names)
    result = classifier.classify(classify_name, net_balance)
    return result.category


def build_display_name(account_key: str, provided_account_names: dict[str, str]) -> str:
    """Build display name: '[code] -- [name]' when account_name column is available."""
    name = provided_account_names.get(account_key)
    if name and name != account_key:
        return f"{account_key} \u2014 {name}"
    return account_key


def is_balance_abnormal(category: AccountCategory, net_balance: float, account_name: str = "") -> bool:
    """Check if balance direction is abnormal for the given category.

    Sprint 530: Contra accounts carry the opposite of their parent
    category's normal balance. When detected, the expected direction
    is inverted so the normal contra balance is not flagged.
    """
    if abs(net_balance) < 0.01 or category == AccountCategory.UNKNOWN:
        return False
    normal = NORMAL_BALANCE_MAP[category]

    # Sprint 530 Fix 1: Invert expected balance for contra accounts
    if account_name and is_contra_account(account_name, category):
        if normal == NormalBalance.DEBIT:
            return net_balance > 0
        return net_balance < 0

    if normal == NormalBalance.DEBIT:
        return net_balance < 0
    return net_balance > 0


def validate_balance_sheet_equation(category_totals: CategoryTotals) -> dict[str, Any]:
    """Validate the fundamental accounting equation: Assets = Liabilities + Equity.

    Sprint 43 - Phase III: Balance Sheet Validator (Standalone Function)

    This validation checks if the categorized trial balance satisfies the
    basic accounting equation. An imbalance may indicate:
    - Misclassified accounts
    - Missing accounts
    - Data entry errors
    - Incomplete trial balance
    """
    total_assets = category_totals.total_assets
    total_liabilities = category_totals.total_liabilities
    total_equity = category_totals.total_equity

    liabilities_plus_equity = total_liabilities + total_equity
    difference = total_assets - liabilities_plus_equity

    # Decimal-aware balance check (Sprint 340)
    is_balanced = abs(Decimal(str(difference))) < BALANCE_TOLERANCE

    abs_diff = abs(difference)
    if is_balanced:
        severity = None
        status = "balanced"
    elif abs_diff < BS_IMBALANCE_THRESHOLD_LOW:
        severity = "low"
        status = "minor_imbalance"
    elif abs_diff < BS_IMBALANCE_THRESHOLD_HIGH:
        severity = "medium"
        status = "moderate_imbalance"
    else:
        severity = "high"
        status = "significant_imbalance"

    if is_balanced:
        recommendation = "Balance sheet equation is satisfied."
    elif difference > 0:
        recommendation = (
            f"Assets exceed Liabilities + Equity by ${abs_diff:,.2f}. "
            "Review for: (1) Liabilities classified as assets, "
            "(2) Missing liability/equity accounts, "
            "(3) Overstated asset balances."
        )
    else:
        recommendation = (
            f"Liabilities + Equity exceed Assets by ${abs_diff:,.2f}. "
            "Review for: (1) Assets classified as liabilities/equity, "
            "(2) Missing asset accounts, "
            "(3) Understated asset balances."
        )

    log_secure_operation(
        "balance_sheet_validation",
        f"A={total_assets:,.2f}, L+E={liabilities_plus_equity:,.2f}, Diff={difference:,.2f}, Status={status}",
    )

    return {
        "is_balanced": is_balanced,
        "status": status,
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(total_liabilities, 2),
        "total_equity": round(total_equity, 2),
        "liabilities_plus_equity": round(liabilities_plus_equity, 2),
        "difference": round(difference, 2),
        "abs_difference": round(abs_diff, 2),
        "severity": severity,
        "recommendation": recommendation,
        "equation": "Assets = Liabilities + Equity",
    }
