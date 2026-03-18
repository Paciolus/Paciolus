"""Balance direction anomaly detection — accounts with abnormal balance directions."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from audit.classification import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    build_display_name,
    is_balance_abnormal,
    resolve_category,
    resolve_csv_type,
)
from classification_rules import (
    CATEGORY_DISPLAY_NAMES,
    NORMAL_BALANCE_MAP,
    AccountCategory,
    NormalBalance,
)
from security_utils import log_secure_operation
from shared.monetary import BALANCE_TOLERANCE


def detect_abnormal_balances_streaming(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Detect accounts with abnormal balance directions using the heuristic classifier.

    Returns (abnormal_balances_list, classification_stats_dict).
    """
    log_secure_operation(
        "streaming_abnormal",
        f"Analyzing {len(account_balances)} unique accounts (threshold: ${materiality_threshold:,.2f}), "
        f"provided types: {len(provided_account_types)}, provided names: {len(provided_account_names)}",
    )

    abnormal_balances: list[dict[str, Any]] = []
    classification_stats = {"high": 0, "medium": 0, "low": 0, "unknown": 0}

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

        result = classifier.classify(display, net_balance)

        csv_raw = provided_account_types.get(account_key, "")
        csv_cat, csv_conf = resolve_csv_type(csv_raw)
        has_csv_type = csv_cat is not None
        effective_category = category
        confidence = csv_conf if has_csv_type else result.confidence

        if effective_category == AccountCategory.UNKNOWN:
            classification_stats["unknown"] += 1
        elif confidence >= CONFIDENCE_HIGH:
            classification_stats["high"] += 1
        elif confidence >= CONFIDENCE_MEDIUM:
            classification_stats["medium"] += 1
        else:
            classification_stats["low"] += 1

        is_abnormal = is_balance_abnormal(effective_category, net_balance, display)

        if is_abnormal and effective_category != AccountCategory.UNKNOWN:
            abs_amount = abs(net_balance)
            is_material = abs_amount >= materiality_threshold
            materiality_status = "material" if is_material else "immaterial"

            normal = NORMAL_BALANCE_MAP[effective_category]
            expected_balance = "Debit" if normal == NormalBalance.DEBIT else "Credit"
            actual_balance = "Credit" if net_balance < 0 else "Debit"

            if not is_material:
                log_secure_operation(
                    "below_materiality",
                    f"Below materiality: {display} (${abs_amount:,.2f} < ${materiality_threshold:,.2f})",
                )

            abnormal_balances.append(
                {
                    "account": display,
                    "type": CATEGORY_DISPLAY_NAMES.get(effective_category, "Unknown"),
                    "issue": f"Net {actual_balance} balance (should be {expected_balance})",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status,
                    "category": effective_category.value,
                    "confidence": confidence,
                    "matched_keywords": result.matched_keywords if not has_csv_type else ["CSV_ACCOUNT_TYPE"],
                    "requires_review": not has_csv_type and result.requires_review,
                    "anomaly_type": "natural_balance_violation",
                    "expected_balance": expected_balance.lower(),
                    "actual_balance": actual_balance.lower(),
                    "severity": "high" if is_material else "low",
                    "suggestions": [
                        {
                            "category": s.category.value,
                            "confidence": s.confidence,
                            "reason": s.reason,
                            "matched_keywords": s.matched_keywords,
                        }
                        for s in result.suggestions
                    ]
                    if result.suggestions and not has_csv_type
                    else [],
                }
            )

    material_count = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
    immaterial_count = len(abnormal_balances) - material_count
    log_secure_operation(
        "streaming_abnormal_complete",
        f"Found {len(abnormal_balances)} abnormal balances ({material_count} material, {immaterial_count} below materiality). "
        f"Classification: {classification_stats}",
    )

    return abnormal_balances, classification_stats
