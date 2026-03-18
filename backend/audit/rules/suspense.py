"""Suspense and clearing account detection."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from audit.classification import build_display_name, resolve_category
from classification_rules import (
    CATEGORY_DISPLAY_NAMES,
    SUSPENSE_CONFIDENCE_THRESHOLD,
    SUSPENSE_KEYWORDS,
)
from security_utils import log_secure_operation
from shared.monetary import BALANCE_TOLERANCE


def detect_suspense_accounts(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect suspense and clearing accounts with outstanding balances."""
    log_secure_operation("suspense_detection", f"Scanning {len(account_balances)} accounts for suspense indicators")

    suspense_accounts: list[dict[str, Any]] = []

    for account_key, balances in account_balances.items():
        debit_amount = balances["debit"]
        credit_amount = balances["credit"]
        net_balance = debit_amount - credit_amount

        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        display = build_display_name(account_key, provided_account_names)
        account_lower = display.lower()
        matched_keywords: list[str] = []
        total_weight = 0.0

        for keyword, weight, is_phrase in SUSPENSE_KEYWORDS:
            if keyword in account_lower:
                matched_keywords.append(keyword)
                total_weight += weight

        confidence = min(total_weight, 1.0)

        if confidence >= SUSPENSE_CONFIDENCE_THRESHOLD:
            abs_amount = abs(net_balance)
            is_material = abs_amount >= materiality_threshold
            materiality_status = "material" if is_material else "immaterial"

            category = resolve_category(
                account_key,
                net_balance,
                provided_account_types,
                provided_account_names,
                classifier,
            )

            suspense_accounts.append(
                {
                    "account": display,
                    "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                    "issue": "Suspense/clearing account with outstanding balance",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status,
                    "category": category.value,
                    "confidence": confidence,
                    "matched_keywords": matched_keywords,
                    "requires_review": True,
                    "anomaly_type": "suspense_account",
                    "expected_balance": "zero",
                    "actual_balance": "debit" if net_balance > 0 else "credit",
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                    "recommendation": (
                        "Investigate and clear this suspense account. "
                        "Determine proper classification for the outstanding balance."
                    ),
                }
            )

    log_secure_operation(
        "suspense_detection_complete", f"Found {len(suspense_accounts)} suspense accounts with balances"
    )

    return suspense_accounts
