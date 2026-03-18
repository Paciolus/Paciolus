"""Equity signal detection — abnormal equity patterns."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from audit.classification import build_display_name, resolve_category
from classification_rules import (
    EQUITY_DIVIDEND_KEYWORDS,
    EQUITY_RETAINED_EARNINGS_KEYWORDS,
    EQUITY_TREASURY_KEYWORDS,
    AccountCategory,
)


def detect_equity_signals(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect abnormal equity patterns (deficit + dividends)."""
    findings: list[dict[str, Any]] = []
    equity_accounts: dict[str, tuple[str, float, dict]] = {}

    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        if category == AccountCategory.EQUITY:
            display = build_display_name(account_key, provided_account_names)
            equity_accounts[account_key] = (display, net_balance, balances)

    if not equity_accounts:
        return findings

    retained_earnings_deficit = None
    dividends_declared = None
    treasury_stock = None
    total_equity = Decimal("0")

    for key, (display, net, bals) in equity_accounts.items():
        lower = display.lower()
        total_equity += Decimal(str(net))
        if any(kw in lower for kw, _w, _p in EQUITY_RETAINED_EARNINGS_KEYWORDS):
            retained_earnings_deficit = (key, display, net, bals)
        if any(kw in lower for kw, _w, _p in EQUITY_DIVIDEND_KEYWORDS):
            dividends_declared = (key, display, net, bals)
        if any(kw in lower for kw, _w, _p in EQUITY_TREASURY_KEYWORDS):
            treasury_stock = (key, display, net, bals)

    if retained_earnings_deficit and dividends_declared:
        re_key, re_display, re_net, re_bals = retained_earnings_deficit
        div_key, div_display, div_net, div_bals = dividends_declared
        if re_net > 0:  # Debit balance (deficit)
            combined_return = abs(div_net) + (abs(treasury_stock[2]) if treasury_stock else 0)
            is_material = abs(re_net) >= materiality_threshold

            findings.append(
                {
                    "account": re_display,
                    "type": "Equity",
                    "issue": (
                        f"Accumulated deficit of ${abs(re_net):,.2f} while dividends of "
                        f"${abs(div_net):,.2f} have been declared \u2014 governance and solvency concern"
                    ),
                    "amount": round(abs(re_net), 2),
                    "debit": round(re_bals["debit"], 2),
                    "credit": round(re_bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": "equity",
                    "confidence": 0.90,
                    "matched_keywords": ["retained earnings", "deficit", "dividend"],
                    "requires_review": True,
                    "anomaly_type": "equity_signal",
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                    "cross_reference_note": (
                        f"Combined capital return: ${combined_return:,.2f} "
                        f"(dividends: ${abs(div_net):,.2f}"
                        + (f", treasury: ${abs(treasury_stock[2]):,.2f}" if treasury_stock else "")
                        + ") declared against a deficit"
                    ),
                }
            )

    return findings
