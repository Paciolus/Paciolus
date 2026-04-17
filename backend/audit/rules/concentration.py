"""Concentration risk detection — category, revenue, and expense concentration."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from audit.classification import build_display_name, resolve_category
from classification_rules import (
    CATEGORY_DISPLAY_NAMES,
    CONCENTRATION_CATEGORIES,
    CONCENTRATION_MIN_CATEGORY_TOTAL,
    CONCENTRATION_THRESHOLD_HIGH,
    CONCENTRATION_THRESHOLD_MEDIUM,
    EXPENSE_CONCENTRATION_THRESHOLD,
    REVENUE_CONCENTRATION_THRESHOLD,
    AccountCategory,
)
from security_utils import log_secure_operation
from shared.monetary import BALANCE_TOLERANCE


def detect_concentration_risk(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect accounts with unusually high concentration within their category."""
    log_secure_operation(
        "concentration_detection", f"Analyzing {len(account_balances)} accounts for concentration risk"
    )

    concentration_risks: list[dict[str, Any]] = []

    category_accounts: dict[AccountCategory, list[tuple[str, float, float, float]]] = {
        cat: [] for cat in CONCENTRATION_CATEGORIES
    }
    category_totals_dec: dict[AccountCategory, Decimal] = {cat: Decimal("0") for cat in CONCENTRATION_CATEGORIES}

    for account_key, balances in account_balances.items():
        debit_amount = balances["debit"]
        credit_amount = balances["credit"]
        net_balance = debit_amount - credit_amount

        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        display = build_display_name(account_key, provided_account_names)

        if category in CONCENTRATION_CATEGORIES:
            abs_balance = abs(net_balance)
            category_accounts[category].append((display, abs_balance, debit_amount, credit_amount))
            category_totals_dec[category] += Decimal(str(abs_balance))

    for category in CONCENTRATION_CATEGORIES:
        total_dec = category_totals_dec[category]

        if float(total_dec) < CONCENTRATION_MIN_CATEGORY_TOTAL:
            continue

        for display, abs_balance, debit_amount, credit_amount in category_accounts[category]:
            concentration_pct = float(Decimal(str(abs_balance)) / total_dec)

            severity = None
            if concentration_pct >= CONCENTRATION_THRESHOLD_HIGH:
                severity = "high"
            elif concentration_pct >= CONCENTRATION_THRESHOLD_MEDIUM:
                severity = "medium"

            if severity:
                is_material = abs_balance >= materiality_threshold
                materiality_status = "material" if is_material else "immaterial"

                _CATEGORY_PLURAL = {
                    "asset": "assets",
                    "liability": "liabilities",
                    "equity": "equity accounts",
                    "revenue": "revenues",
                    "expense": "expenses",
                }
                cat_plural = _CATEGORY_PLURAL.get(category.value, f"{category.value}s")

                concentration_risks.append(
                    {
                        "account": display,
                        "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                        "issue": (
                            f"Represents {concentration_pct:.1%} of total {cat_plural} — "
                            "coverage observation, not an anomaly"
                        ),
                        "amount": round(abs_balance, 2),
                        "debit": round(debit_amount, 2),
                        "credit": round(credit_amount, 2),
                        "materiality": materiality_status,
                        "category": category.value,
                        "confidence": concentration_pct,
                        "matched_keywords": [],
                        "requires_review": False,
                        "anomaly_type": f"{category.value}_concentration",
                        "concentration_percent": round(concentration_pct * 100, 1),
                        "category_total": round(float(total_dec), 2),
                        "severity": severity,
                        "suggestions": [],
                        # Sprint 668 Issue 1: Coverage analysis is informational
                        # context, NOT a structural anomaly. Excluded from risk
                        # scoring and rendered in a dedicated "Materiality
                        # Coverage Analysis" section instead of Exception Details.
                        "coverage_analysis": True,
                        "recommendation": (
                            f"This account represents {concentration_pct:.1%} of total {cat_plural}. "
                            "Documented for materiality coverage. Concentration is not by itself an "
                            "anomaly; consider the impact if this balance is misstated or contested."
                        ),
                    }
                )

    concentration_risks.sort(key=lambda x: x["concentration_percent"], reverse=True)

    log_secure_operation(
        "concentration_detection_complete", f"Found {len(concentration_risks)} concentration risk accounts"
    )

    return concentration_risks


def detect_revenue_concentration(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Revenue concentration analysis."""
    findings: list[dict[str, Any]] = []
    revenue_accounts: list[tuple[str, str, float, dict]] = []
    total_revenue = Decimal("0")

    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        if category == AccountCategory.REVENUE:
            abs_bal = abs(net_balance)
            display = build_display_name(account_key, provided_account_names)
            revenue_accounts.append((account_key, display, abs_bal, balances))
            total_revenue += Decimal(str(abs_bal))

    if float(total_revenue) < CONCENTRATION_MIN_CATEGORY_TOTAL:
        return findings

    for key, display, abs_bal, bals in revenue_accounts:
        pct = float(Decimal(str(abs_bal)) / total_revenue)
        if pct >= REVENUE_CONCENTRATION_THRESHOLD:
            is_material = abs_bal >= materiality_threshold
            findings.append(
                {
                    "account": display,
                    "type": "Revenue",
                    "issue": (
                        f"Revenue concentration: {pct:.1%} of total revenue "
                        f"(${float(total_revenue):,.0f}) — coverage observation, not an anomaly"
                    ),
                    "amount": round(abs_bal, 2),
                    "debit": round(bals["debit"], 2),
                    "credit": round(bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": "revenue",
                    "confidence": pct,
                    "matched_keywords": [],
                    "requires_review": False,
                    "anomaly_type": "concentration_risk",
                    "concentration_percent": round(pct * 100, 1),
                    "category_total": round(float(total_revenue), 2),
                    "severity": "high" if is_material and pct >= REVENUE_CONCENTRATION_THRESHOLD else "medium",
                    "suggestions": [],
                    # Sprint 668 Issue 1: see detect_concentration_risk for rationale.
                    "coverage_analysis": True,
                }
            )

    return findings


def detect_expense_concentration(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Expense concentration analysis."""
    findings: list[dict[str, Any]] = []
    expense_accounts: list[tuple[str, str, float, dict]] = []
    total_expense = Decimal("0")

    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        if category == AccountCategory.EXPENSE:
            abs_bal = abs(net_balance)
            display = build_display_name(account_key, provided_account_names)
            expense_accounts.append((account_key, display, abs_bal, balances))
            total_expense += Decimal(str(abs_bal))

    if float(total_expense) < CONCENTRATION_MIN_CATEGORY_TOTAL:
        return findings

    for key, display, abs_bal, bals in expense_accounts:
        pct = float(Decimal(str(abs_bal)) / total_expense)
        if pct >= EXPENSE_CONCENTRATION_THRESHOLD:
            is_material = abs_bal >= materiality_threshold
            findings.append(
                {
                    "account": display,
                    "type": "Expense",
                    "issue": (
                        f"Expense concentration: {pct:.1%} of total expenses "
                        f"(${float(total_expense):,.0f}) — coverage observation, not an anomaly"
                    ),
                    "amount": round(abs_bal, 2),
                    "debit": round(bals["debit"], 2),
                    "credit": round(bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": "expense",
                    "confidence": pct,
                    "matched_keywords": [],
                    "requires_review": False,
                    "anomaly_type": "concentration_risk",
                    "concentration_percent": round(pct * 100, 1),
                    "category_total": round(float(total_expense), 2),
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                    # Sprint 668 Issue 1: see detect_concentration_risk for rationale.
                    "coverage_analysis": True,
                }
            )

    return findings
