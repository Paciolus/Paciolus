"""Suspense and clearing account detection."""

from __future__ import annotations

import re
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

# Sprint 670 Issue 10: Structural patterns that indicate an unusual or
# placeholder account regardless of vocabulary. These augment the literal
# SUSPENSE_KEYWORDS table for accounts whose names don't contain a
# recognised suspense word but whose shape is suspect.

# Symbolic name: contains AT LEAST one non-alphabetic character AND has
# fewer alphabetic characters than non-alphabetic ones. Catches "????-001"
# and "###-pending" without flagging legitimate names like "401(k)".
_SYMBOLIC_NON_ALPHA_RE = re.compile(r"[^a-zA-Z\s]")

# Annotation pattern: parentheses containing a question mark. Catches
# "(personal?)", "(non-ded?)", "(see note)" — auditor-visible margin
# notes the bookkeeper left in the account name itself.
_ANNOTATION_QMARK_RE = re.compile(r"\([^)]*\?[^)]*\)")

# Foreign currency prefix: ISO-4217 code followed by a separator. Catches
# "EUR-AR", "GBP_Receivables", "JPY Payables" — accounts denominated in
# a non-functional currency that may need translation review.
_FX_PREFIX_RE = re.compile(
    r"^(eur|gbp|jpy|cad|aud|chf|cny|hkd|sgd|inr|brl|mxn|nzd|sek|nok|dkk|zar|try|krw)[\s\-_]",
    re.IGNORECASE,
)

# Annotation-only marker: a question mark on its own at the end of the
# name (e.g. "Vendor Refund?"). Less specific than the parens variant
# but still worth surfacing.
_TRAILING_QMARK_RE = re.compile(r"\?\s*$")


def _detect_unusual_patterns(display: str) -> tuple[float, list[str]]:
    """Return (confidence, matched patterns) for structural unusual-name signals.

    Confidence is summed across all matching patterns and capped at 1.0
    by the caller. The matched-patterns list is plain-language and
    appears in `matched_keywords` on the resulting suspense entry so the
    user can see why the account was flagged.
    """
    matched: list[str] = []
    confidence = 0.0

    alpha_count = sum(1 for c in display if c.isalpha())
    non_space_count = sum(1 for c in display if not c.isspace())

    # Symbolic-only name: zero alphabetic characters, or fewer than 25%
    # alphabetic when stripped of whitespace. Strong signal.
    if non_space_count > 0:
        if alpha_count == 0:
            matched.append("symbolic-only name")
            confidence += 0.95
        elif alpha_count / non_space_count < 0.25 and _SYMBOLIC_NON_ALPHA_RE.search(display):
            matched.append("predominantly symbolic name")
            confidence += 0.80

    if _ANNOTATION_QMARK_RE.search(display):
        matched.append("annotation with question mark")
        confidence += 0.75
    elif _TRAILING_QMARK_RE.search(display):
        matched.append("trailing question mark")
        confidence += 0.65

    if _FX_PREFIX_RE.match(display):
        matched.append("foreign currency prefix")
        confidence += 0.70

    return confidence, matched


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

        # Sprint 670 Issue 10: structural patterns (symbolic, annotation,
        # FX prefix) augment the literal vocabulary check.
        structural_weight, structural_matches = _detect_unusual_patterns(display)
        if structural_matches:
            matched_keywords.extend(structural_matches)
            total_weight += structural_weight

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
