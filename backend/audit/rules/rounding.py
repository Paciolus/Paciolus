"""Rounding anomaly detection — suspicious round numbers."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from audit.classification import build_display_name, resolve_category
from classification_rules import (
    CATEGORY_DISPLAY_NAMES,
    ROUNDING_MAX_ANOMALIES,
    ROUNDING_MIN_AMOUNT,
    ROUNDING_PATTERNS,
    classify_round_number_tier,
)
from security_utils import log_secure_operation
from shared.monetary import BALANCE_TOLERANCE


def detect_rounding_anomalies(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
    provided_account_subtypes: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect suspicious round numbers that may indicate estimation or manipulation.

    Sprint 42 - Phase III: Rounding Anomaly Detection.
    Sprint 536: Three-tier framework (Suppress / Minor / Material).
    """
    log_secure_operation("rounding_detection", f"Analyzing {len(account_balances)} accounts for rounding anomalies")
    log_secure_operation("DEPLOY-VERIFY-536", "tiered round-number detection active")
    log_secure_operation("DEPLOY-VERIFY-537", "informational severity tier active")

    tb_total = sum(abs(b["debit"] - b["credit"]) for b in account_balances.values())

    subtype_source = provided_account_subtypes or provided_account_types

    candidates: list[tuple[dict[str, Any], str, float, str, str]] = []

    for account_key, balances in account_balances.items():
        debit_amount = balances["debit"]
        credit_amount = balances["credit"]
        net_balance = debit_amount - credit_amount
        abs_balance = abs(net_balance)

        if abs_balance < ROUNDING_MIN_AMOUNT:
            continue

        display = build_display_name(account_key, provided_account_names)
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        subtype_raw = subtype_source.get(account_key, "")

        abs_balance_dec = Decimal(str(abs_balance))
        matched_pattern = None
        for divisor, pattern_name, pattern_severity in ROUNDING_PATTERNS:
            divisor_dec = Decimal(str(divisor))
            remainder_dec = abs_balance_dec % divisor_dec
            is_round = remainder_dec < BALANCE_TOLERANCE or (divisor_dec - remainder_dec) < BALANCE_TOLERANCE
            if is_round:
                matched_pattern = (divisor, pattern_name, pattern_severity)
                break

        if matched_pattern is None:
            continue

        tier = classify_round_number_tier(
            display,
            category,
            subtype_raw,
            abs_balance,
            tb_total,
            materiality_threshold,
        )
        if tier is None:
            continue

        divisor, pattern_name, pattern_severity = matched_pattern

        if divisor >= 100000:
            round_desc = f"${abs_balance / 1000:,.0f}K"
        else:
            round_desc = f"${abs_balance:,.0f}"

        if tier == "informational":
            effective_severity = "informational"
            materiality_status = "immaterial"
            confidence = 0.2
            issue_text = f"Informational Note: Round balance of {round_desc}"
            recommendation = (
                f"Informational Note: Round balance of {round_desc} on {display}. "
                "For this account type, round balances are common in practice and do not "
                "indicate a recording concern in isolation. No procedure required unless "
                "other risk factors are present."
            )
        elif tier == "minor":
            effective_severity = "low"
            materiality_status = "immaterial"
            confidence = 0.3
            issue_text = f"Round amount noted: {round_desc}"
            recommendation = (
                f"Round amount noted: {round_desc}. For this account type, round balances "
                "are common and may reflect estimates or contractual amounts. No immediate "
                "action required \u2014 verify during substantive procedures if material to "
                "the engagement."
            )
        else:
            effective_severity = pattern_severity if abs_balance >= materiality_threshold else "medium"
            materiality_status = "material" if abs_balance >= materiality_threshold else "immaterial"
            confidence = 0.6 if pattern_severity == "high" else 0.4
            issue_text = f"Exactly round amount: {round_desc}"
            recommendation = (
                f"Exactly round amount: {round_desc}. Inspect supporting documentation "
                "for all transactions comprising this balance. Perform targeted vouching "
                "to confirm amounts reflect actual invoiced or contracted values. Assess "
                "whether the pattern indicates estimation rather than transaction-based recording."
            )

        finding: dict[str, Any] = {
            "account": display,
            "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
            "issue": issue_text,
            "amount": round(abs_balance, 2),
            "debit": round(debit_amount, 2),
            "credit": round(credit_amount, 2),
            "materiality": materiality_status,
            "category": category.value,
            "confidence": confidence,
            "matched_keywords": [],
            "requires_review": True,
            "anomaly_type": "rounding_anomaly",
            "rounding_pattern": pattern_name,
            "rounding_divisor": divisor,
            "severity": effective_severity,
            "suggestions": [],
            "recommendation": recommendation,
            "rounding_tier": tier,
        }
        candidates.append((finding, tier, abs_balance, category.value, subtype_raw.lower().strip()))

    # Second pass: repeated identical amounts (3+) in same type/subtype
    group_amounts: dict[tuple[str, str], list[float]] = {}
    for _, tier, abs_bal, cat_val, sub_val in candidates:
        key = (cat_val, sub_val)
        group_amounts.setdefault(key, []).append(abs_bal)

    repeated_sets: set[tuple[str, str, float]] = set()
    for (cat_val, sub_val), amounts in group_amounts.items():
        counts = Counter(amounts)
        for amt, cnt in counts.items():
            if cnt >= 3:
                repeated_sets.add((cat_val, sub_val, amt))

    rounding_anomalies: list[dict[str, Any]] = []
    for finding, tier, abs_bal, cat_val, sub_val in candidates:
        if (cat_val, sub_val, abs_bal) in repeated_sets:
            n_matching = group_amounts[(cat_val, sub_val)].count(abs_bal)
            matching_accounts = [
                f[0]["account"] for f in candidates if f[3] == cat_val and f[4] == sub_val and f[2] == abs_bal
            ]
            acct_list = ", ".join(matching_accounts)

            if abs_bal >= 100000:
                amt_str = f"${abs_bal / 1000:,.0f}K"
            else:
                amt_str = f"${abs_bal:,.0f}"

            finding["severity"] = "high"
            finding["materiality"] = "material"
            finding["confidence"] = 0.8
            finding["rounding_tier"] = "material"
            finding["issue"] = f"Identical round amount {amt_str} appears across {n_matching} accounts"
            finding["recommendation"] = (
                f"Identical round amount {amt_str} appears across "
                f"{n_matching} accounts ({acct_list}). This pattern may indicate "
                "allocation, estimation, or systematic rounding rather than "
                "transaction-based recording. Obtain documentation for the allocation "
                "methodology and verify each amount independently."
            )

        rounding_anomalies.append(finding)

    rounding_anomalies.sort(key=lambda x: x["amount"], reverse=True)
    if len(rounding_anomalies) > ROUNDING_MAX_ANOMALIES:
        rounding_anomalies = rounding_anomalies[:ROUNDING_MAX_ANOMALIES]

    log_secure_operation("rounding_detection_complete", f"Found {len(rounding_anomalies)} rounding anomalies")

    return rounding_anomalies
