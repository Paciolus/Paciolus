"""Related party and intercompany account detection."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from audit.classification import build_display_name, resolve_category
from classification_rules import (
    CATEGORY_DISPLAY_NAMES,
    INTERCOMPANY_KEYWORDS,
    RELATED_PARTY_EXCLUSION_KEYWORDS,
    RELATED_PARTY_KEYWORDS,
)
from shared.monetary import BALANCE_TOLERANCE


def detect_related_party_accounts(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect accounts indicating related party activity."""
    findings: list[dict[str, Any]] = []
    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        display = build_display_name(account_key, provided_account_names)
        search_text = display.lower()

        if any(excl in search_text for excl in RELATED_PARTY_EXCLUSION_KEYWORDS):
            continue

        matched = []
        weight = 0.0
        for keyword, kw_weight, is_phrase in RELATED_PARTY_KEYWORDS:
            if keyword in search_text:
                matched.append(keyword)
                weight = max(weight, kw_weight)

        if not matched:
            continue

        abs_amount = abs(net_balance)
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        is_material = abs_amount >= materiality_threshold

        findings.append(
            {
                "account": display,
                "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                "issue": "Related party balance \u2014 requires ASC 850 disclosure assessment",
                "amount": round(abs_amount, 2),
                "debit": round(balances["debit"], 2),
                "credit": round(balances["credit"], 2),
                "materiality": "material" if is_material else "immaterial",
                "category": category.value,
                "confidence": weight,
                "matched_keywords": matched,
                "requires_review": True,
                "anomaly_type": "related_party",
                "severity": "high" if is_material else "medium",
                "suggestions": [],
            }
        )

    return findings


def detect_intercompany_imbalances(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect intercompany accounts with elimination gaps."""
    ic_accounts: list[tuple[str, str, float, dict]] = []
    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        display = build_display_name(account_key, provided_account_names)
        search_text = display.lower()
        if any(kw in search_text for kw, _w, _p in INTERCOMPANY_KEYWORDS):
            ic_accounts.append((account_key, display, net_balance, balances))

    if not ic_accounts:
        return []

    def _extract_counterparty(name: str) -> str:
        lower = name.lower()
        for sep in [" \u2014 ", " \u2013 ", " - ", "\u2014", "\u2013", "-"]:
            if sep in lower:
                parts = lower.split(sep)
                cp = parts[-1].strip()
                if cp and cp not in ("receivable", "payable", "loan"):
                    return cp
        return ""

    counterparty_groups: dict[str, list[tuple[str, str, float, dict]]] = {}
    for key, display, net, bals in ic_accounts:
        cp = _extract_counterparty(display)
        if cp:
            counterparty_groups.setdefault(cp, []).append((key, display, net, bals))

    findings: list[dict[str, Any]] = []
    for cp_name, accounts in counterparty_groups.items():
        net_total = sum(net for _, _, net, _ in accounts)
        if abs(Decimal(str(net_total))) < BALANCE_TOLERANCE:
            continue

        has_debit = any(net > 0 for _, _, net, _ in accounts)
        has_credit = any(net < 0 for _, _, net, _ in accounts)

        if has_debit and has_credit:
            issue = f"Intercompany elimination gap of ${abs(net_total):,.2f} with {cp_name.title()}"
        elif has_debit:
            issue = f"Intercompany receivable from {cp_name.title()} \u2014 no offsetting payable found"
        else:
            issue = f"Intercompany payable to {cp_name.title()} \u2014 no offsetting receivable found"

        for key, display, net, bals in accounts:
            if abs(net) < 0.01:
                continue
            abs_amount = abs(net)
            category = resolve_category(
                key,
                net,
                provided_account_types,
                provided_account_names,
                classifier,
            )
            is_material = abs_amount >= materiality_threshold

            findings.append(
                {
                    "account": display,
                    "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                    "issue": issue,
                    "amount": round(abs_amount, 2),
                    "debit": round(bals["debit"], 2),
                    "credit": round(bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": category.value,
                    "confidence": 0.85,
                    "matched_keywords": ["intercompany"],
                    "requires_review": True,
                    "anomaly_type": "intercompany_imbalance",
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                    "cross_reference_note": f"Counterparty: {cp_name.title()} \u2014 net exposure: ${abs(net_total):,.2f}",
                }
            )

    return findings
