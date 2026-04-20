"""Raw upload parsing, schema validation, and DataFrame normalization.

This module handles the first stage of the audit pipeline: accepting raw
file bytes, detecting column layouts, normalizing headers, and producing a
clean DataFrame that downstream stages can rely on without re-parsing.
It also contains the standalone ``check_balance`` function that validates
whether total debits equal total credits.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from security_utils import log_secure_operation
from shared.monetary import BALANCE_TOLERANCE, quantize_monetary


def check_balance(df: pd.DataFrame) -> dict[str, Any]:
    """Check if debits equal credits. Returns JSON report with totals and balance status."""
    log_secure_operation("check_balance", "Validating trial balance")

    # Normalize column names (case-insensitive matching)
    df.columns = df.columns.str.strip()
    column_map = {col.lower(): col for col in df.columns}

    # Find debit and credit columns
    debit_col = None
    credit_col = None

    for col_lower, col_original in column_map.items():
        if "debit" in col_lower:
            debit_col = col_original
        if "credit" in col_lower:
            credit_col = col_original

    if debit_col is None or credit_col is None:
        return {
            "status": "error",
            "message": "Could not find 'Debit' and 'Credit' columns in the file",
            "timestamp": datetime.now(UTC).isoformat(),
            "balanced": False,
        }

    # Convert columns to numeric, coercing errors to NaN
    debits = pd.to_numeric(df[debit_col], errors="coerce").fillna(0)
    credits = pd.to_numeric(df[credit_col], errors="coerce").fillna(0)

    total_debits = math.fsum(debits.values)
    total_credits = math.fsum(credits.values)
    difference = total_debits - total_credits

    # Decimal-aware balance check (Sprint 340)
    is_balanced = abs(Decimal(str(difference))) < BALANCE_TOLERANCE

    return {
        "status": "success",
        "balanced": is_balanced,
        "total_debits": str(quantize_monetary(total_debits)),
        "total_credits": str(quantize_monetary(total_credits)),
        "difference": str(quantize_monetary(difference)),
        "row_count": len(df),
        "timestamp": datetime.now(UTC).isoformat(),
        "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE",
    }


def detect_abnormal_balances(df: pd.DataFrame, materiality_threshold: float = 0.0) -> list[dict[str, Any]]:
    """Detect accounts with abnormal balance directions (e.g., assets with credit balances).

    This is the legacy standalone function that uses simple keyword matching
    rather than the weighted heuristic classifier. It is preserved for backward
    compatibility; the StreamingAuditor's ``get_abnormal_balances`` method is
    the preferred entry point for production analysis.
    """
    import re

    # Sprint 687: source the keyword lists from ``audit/classification`` so
    # the legacy vectorized path stays in lock-step with the canonical list
    # (previously these were hardcoded duplicates and drifted from the
    # canonical list when goodwill/intangible/ROU/DTA were added).
    from audit.classification import ASSET_KEYWORDS, LIABILITY_KEYWORDS

    log_secure_operation(
        "detect_abnormal", f"Scanning for abnormal balances (threshold: ${materiality_threshold:,.2f})"
    )

    abnormal_balances: list[dict[str, Any]] = []

    # Work on a copy to avoid modifying the original
    df = df.copy()

    # Normalize column names (strip whitespace, case-insensitive matching)
    df.columns = df.columns.str.strip()
    column_map = {col.lower().strip(): col for col in df.columns}

    log_secure_operation("detect_abnormal_cols", f"Columns found: {list(df.columns)}")

    # Find account name column with expanded search terms
    account_col = None
    account_search_terms = ["account", "name", "description", "ledger", "gl", "item"]
    for col_lower, col_original in column_map.items():
        if any(term in col_lower for term in account_search_terms):
            account_col = col_original
            break

    # Fallback: use first column if no account column found
    if account_col is None and len(df.columns) > 0:
        account_col = df.columns[0]
        log_secure_operation("detect_abnormal_fallback", f"Using first column as account: {account_col}")

    # Find debit and credit columns
    debit_col = None
    credit_col = None
    for col_lower, col_original in column_map.items():
        if "debit" in col_lower:
            debit_col = col_original
        if "credit" in col_lower:
            credit_col = col_original

    log_secure_operation("detect_abnormal_mapping", f"Account: {account_col}, Debit: {debit_col}, Credit: {credit_col}")

    if account_col is None or debit_col is None or credit_col is None:
        log_secure_operation("detect_abnormal_error", "Missing required columns")
        return []

    # Convert to numeric (on the copy)
    df[debit_col] = pd.to_numeric(df[debit_col], errors="coerce").fillna(0)
    df[credit_col] = pd.to_numeric(df[credit_col], errors="coerce").fillna(0)

    # Performance optimization: Vectorized processing instead of iterrows()
    account_names = df[account_col].astype(str).str.strip()
    account_lower = account_names.str.lower()
    debit_amounts = df[debit_col].values
    credit_amounts = df[credit_col].values
    net_balances = debit_amounts - credit_amounts

    # Vectorized keyword matching for assets and liabilities
    asset_pattern = "|".join(re.escape(kw) for kw in ASSET_KEYWORDS)
    liability_pattern = "|".join(re.escape(kw) for kw in LIABILITY_KEYWORDS)
    is_asset_mask = account_lower.str.contains(asset_pattern, regex=True, na=False)
    is_liability_mask = account_lower.str.contains(liability_pattern, regex=True, na=False)

    # Pre-compute vectorized conditions for abnormal balances
    net_balance_series = pd.Series(net_balances)
    abs_balances = net_balance_series.abs()
    significant = abs_balances >= BALANCE_TOLERANCE

    # Asset accounts with net credit balance (abnormal)
    asset_abnormal = is_asset_mask & (net_balance_series < 0) & significant
    # Liability accounts with net debit balance (abnormal)
    liability_abnormal = is_liability_mask & (net_balance_series > 0) & significant

    for i in asset_abnormal[asset_abnormal].index:
        net_balance = net_balances[i]
        abs_amount = abs(net_balance)
        account_name = account_names.iloc[i]
        debit_amount = debit_amounts[i]
        credit_amount = credit_amounts[i]
        is_material = abs_amount >= materiality_threshold
        materiality_status = "material" if is_material else "immaterial"

        if not is_material:
            log_secure_operation(
                "below_materiality",
                f"Below materiality: {account_name} (${abs_amount:,.2f} < ${materiality_threshold:,.2f})",
            )

        abnormal_balances.append(
            {
                "account": account_name,
                "type": "Asset",
                "issue": "Net Credit balance (should be Debit)",
                "amount": round(abs_amount, 2),
                "debit": round(debit_amount, 2),
                "credit": round(credit_amount, 2),
                "materiality": materiality_status,
                "suggestions": [],  # Sprint 31: Legacy function, no suggestions
            }
        )

    for i in liability_abnormal[liability_abnormal].index:
        net_balance = net_balances[i]
        abs_amount = abs(net_balance)
        account_name = account_names.iloc[i]
        debit_amount = debit_amounts[i]
        credit_amount = credit_amounts[i]
        is_material = abs_amount >= materiality_threshold
        materiality_status = "material" if is_material else "immaterial"

        if not is_material:
            log_secure_operation(
                "below_materiality",
                f"Below materiality: {account_name} (${abs_amount:,.2f} < ${materiality_threshold:,.2f})",
            )

        abnormal_balances.append(
            {
                "account": account_name,
                "type": "Liability",
                "issue": "Net Debit balance (should be Credit)",
                "amount": round(abs_amount, 2),
                "debit": round(debit_amount, 2),
                "credit": round(credit_amount, 2),
                "materiality": materiality_status,
                "suggestions": [],  # Sprint 31: Legacy function, no suggestions
            }
        )

    material_count = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
    immaterial_count = len(abnormal_balances) - material_count
    log_secure_operation(
        "detect_abnormal_complete",
        f"Found {len(abnormal_balances)} abnormal balances ({material_count} material, {immaterial_count} below materiality)",
    )

    return abnormal_balances
