"""Trial balance analysis and validation with chunked streaming for large files."""

import gc
import math
import re
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Optional

import pandas as pd

from account_classifier import AccountClassifier, create_classifier
from classification_rules import (
    CATEGORY_DISPLAY_NAMES,
    CONCENTRATION_CATEGORIES,
    CONCENTRATION_MIN_CATEGORY_TOTAL,
    # Sprint 42: Concentration Risk
    CONCENTRATION_THRESHOLD_HIGH,
    CONCENTRATION_THRESHOLD_MEDIUM,
    # Sprint 527: Consolidated detection keywords
    EQUITY_DIVIDEND_KEYWORDS,
    EQUITY_RETAINED_EARNINGS_KEYWORDS,
    EQUITY_TREASURY_KEYWORDS,
    EXPENSE_CONCENTRATION_THRESHOLD,
    INTERCOMPANY_KEYWORDS,
    NORMAL_BALANCE_MAP,
    RELATED_PARTY_EXCLUSION_KEYWORDS,
    RELATED_PARTY_KEYWORDS,
    REVENUE_CONCENTRATION_THRESHOLD,
    ROUNDING_EXCLUDE_KEYWORDS,
    ROUNDING_MAX_ANOMALIES,
    # Sprint 42: Rounding Anomaly
    ROUNDING_MIN_AMOUNT,
    ROUNDING_PATTERNS,
    # Sprint 536: Round-number tiering
    ROUND_NUMBER_COGS_SUBTYPES,
    ROUND_NUMBER_TIER1_SUPPRESS,
    classify_round_number_tier,
    SUSPENSE_CONFIDENCE_THRESHOLD,
    SUSPENSE_KEYWORDS,
    AccountCategory,
    NormalBalance,
    # Sprint 530: Contra account recognition
    is_contra_account,
)
from classification_validator import run_classification_validation
from column_detector import ColumnDetectionResult, ColumnMapping, detect_columns
from ratio_engine import CategoryTotals, calculate_analytics, extract_category_totals
from security_utils import (
    DEFAULT_CHUNK_SIZE,
    clear_memory,
    log_secure_operation,
    process_tb_chunked,
    read_excel_multi_sheet_chunked,
)
from shared.monetary import BALANCE_TOLERANCE, quantize_monetary

# Legacy keyword mappings (kept for backward compatibility, will be removed)
# New system uses weighted heuristics in account_classifier.py
ASSET_KEYWORDS = ["cash", "bank", "receivable", "inventory", "prepaid", "equipment", "land", "building", "vehicle"]
LIABILITY_KEYWORDS = ["payable", "loan", "tax", "accrued", "unearned", "deferred", "debt", "mortgage", "note payable"]

# Balance sheet imbalance severity thresholds
BS_IMBALANCE_THRESHOLD_LOW = 1_000
BS_IMBALANCE_THRESHOLD_HIGH = 10_000

# Classification confidence thresholds
CONFIDENCE_HIGH = 0.7
CONFIDENCE_MEDIUM = 0.4


def validate_balance_sheet_equation(category_totals: CategoryTotals) -> dict[str, Any]:
    """
    Validate the fundamental accounting equation: Assets = Liabilities + Equity.

    Sprint 43 - Phase III: Balance Sheet Validator (Standalone Function)

    This validation checks if the categorized trial balance satisfies the
    basic accounting equation. An imbalance may indicate:
    - Misclassified accounts
    - Missing accounts
    - Data entry errors
    - Incomplete trial balance

    GAAP/IFRS Notes:
    - Both frameworks require this equation to hold
    - The equation is fundamental to double-entry bookkeeping
    - Retained earnings bridges equity to income statement

    Args:
        category_totals: The CategoryTotals object with computed totals

    Returns:
        Dict with validation result, difference, and recommendation
    """
    total_assets = category_totals.total_assets
    total_liabilities = category_totals.total_liabilities
    total_equity = category_totals.total_equity

    # Calculate expected equity side (Liabilities + Equity)
    liabilities_plus_equity = total_liabilities + total_equity

    # Calculate difference
    difference = total_assets - liabilities_plus_equity

    # Decimal-aware balance check (Sprint 340)
    is_balanced = abs(Decimal(str(difference))) < BALANCE_TOLERANCE

    # Determine severity based on difference magnitude
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

    # Build recommendation
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
        "total_debits": float(quantize_monetary(total_debits)),
        "total_credits": float(quantize_monetary(total_credits)),
        "difference": float(quantize_monetary(difference)),
        "row_count": len(df),
        "timestamp": datetime.now(UTC).isoformat(),
        "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE",
    }


def detect_abnormal_balances(df: pd.DataFrame, materiality_threshold: float = 0.0) -> list[dict[str, Any]]:
    """Detect accounts with abnormal balance directions (e.g., assets with credit balances)."""
    log_secure_operation(
        "detect_abnormal", f"Scanning for abnormal balances (threshold: ${materiality_threshold:,.2f})"
    )

    abnormal_balances = []

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
    # Pre-compute all values using pandas vectorized operations
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
    significant = abs_balances >= float(BALANCE_TOLERANCE)

    # Asset accounts with net credit balance (abnormal)
    asset_abnormal = is_asset_mask & (net_balance_series < 0) & significant
    # Liability accounts with net debit balance (abnormal)
    liability_abnormal = is_liability_mask & (net_balance_series > 0) & significant

    for i in asset_abnormal[asset_abnormal].index:
        net_balance = net_balances[i]
        abs_amount = abs(net_balance)
        account_name = account_names.iloc[i]
        debit_amount = float(debit_amounts[i])
        credit_amount = float(credit_amounts[i])
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
        debit_amount = float(debit_amounts[i])
        credit_amount = float(credit_amounts[i])
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


class StreamingAuditor:
    """Memory-efficient streaming auditor that processes trial balances in chunks."""

    def __init__(
        self,
        materiality_threshold: float = 0.0,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        classifier: Optional[AccountClassifier] = None,
        column_mapping: Optional[ColumnMapping] = None,
    ):
        self.materiality_threshold = materiality_threshold
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback

        # Weighted heuristic classifier (Day 9)
        self.classifier = classifier or create_classifier()

        # User-provided column mapping (Day 9.2 - Zero-Storage: session-only)
        self.user_column_mapping = column_mapping

        # Per-chunk sums for compensated summation at result time
        self._debit_chunks: list[float] = []
        self._credit_chunks: list[float] = []
        self.total_rows = 0

        # Per-account aggregation for abnormal balance detection
        # Key: account_name, Value: {"debit": float, "credit": float}
        self.account_balances: dict[str, dict[str, float]] = {}

        # Column mapping (discovered from first chunk or user-provided)
        self.debit_col: Optional[str] = None
        self.credit_col: Optional[str] = None
        self.account_col: Optional[str] = None
        self.columns_discovered = False

        # Sprint 526: Supplementary column detection
        self.account_type_col: Optional[str] = None
        self.account_name_col: Optional[str] = None

        # Sprint 526: Provided account types and names from CSV columns
        # Key: account identifier (from account_col), Value: type string / name string
        self.provided_account_types: dict[str, str] = {}
        self.provided_account_names: dict[str, str] = {}
        # Sprint 535: Provided account subtypes from CSV "subtype" column
        # Key: account identifier, Value: subtype string (e.g., "Current Asset", "Cost of Goods Sold")
        self.provided_account_subtypes: dict[str, str] = {}

        # Column detection result (Day 9.2)
        self.column_detection: Optional[ColumnDetectionResult] = None

    def _report_progress(self, rows: int, message: str) -> None:
        """Report progress via callback if available."""
        if self.progress_callback:
            self.progress_callback(rows, message)

    def _discover_columns(self, df: pd.DataFrame) -> bool:
        """Discover and cache column mappings from the first chunk. Returns True if found."""
        if self.columns_discovered:
            return True

        df.columns = df.columns.str.strip()
        all_columns = list(df.columns)

        # Priority 1: Use user-provided column mapping (Day 9.2)
        if self.user_column_mapping:
            # Find actual column names (case-insensitive matching)
            col_map_lower = {col.lower().strip(): col for col in all_columns}

            user_acc = self.user_column_mapping.account_column.lower().strip()
            user_deb = self.user_column_mapping.debit_column.lower().strip()
            user_cred = self.user_column_mapping.credit_column.lower().strip()

            self.account_col = col_map_lower.get(user_acc)
            self.debit_col = col_map_lower.get(user_deb)
            self.credit_col = col_map_lower.get(user_cred)

            self.columns_discovered = True

            # Sprint 528 Fix: Even with user mapping, auto-detect supplementary
            # columns (account_type, account_name) so CSV-provided types flow
            # through to _resolve_category(). Without this, process_chunk()
            # skips type extraction because account_type_col stays None.
            supplementary = detect_columns(all_columns)
            self.account_type_col = supplementary.account_type_column
            self.account_name_col = supplementary.account_name_column

            # Create detection result with 100% confidence for user mapping
            self.column_detection = ColumnDetectionResult(
                account_column=self.account_col,
                debit_column=self.debit_col,
                credit_column=self.credit_col,
                account_confidence=1.0,
                debit_confidence=1.0,
                credit_confidence=1.0,
                overall_confidence=1.0,
                all_columns=all_columns,
                detection_notes=["Using user-provided column mapping"],
                account_type_column=supplementary.account_type_column,
                account_type_confidence=supplementary.account_type_confidence,
                account_name_column=supplementary.account_name_column,
                account_name_confidence=supplementary.account_name_confidence,
            )

            log_secure_operation(
                "streaming_columns_user",
                f"User mapping - Account: {self.account_col}, Debit: {self.debit_col}, Credit: {self.credit_col}",
            )

            return self.debit_col is not None and self.credit_col is not None

        # Priority 2: Use intelligent column detection (Day 9.2)
        self.column_detection = detect_columns(all_columns)

        self.account_col = self.column_detection.account_column
        self.debit_col = self.column_detection.debit_column
        self.credit_col = self.column_detection.credit_column

        # Sprint 526: Extract supplementary columns
        self.account_type_col = self.column_detection.account_type_column
        self.account_name_col = self.column_detection.account_name_column

        self.columns_discovered = True

        log_secure_operation(
            "streaming_columns_auto",
            f"Auto-detected - Account: {self.account_col} ({self.column_detection.account_confidence:.0%}), "
            f"Debit: {self.debit_col} ({self.column_detection.debit_confidence:.0%}), "
            f"Credit: {self.credit_col} ({self.column_detection.credit_confidence:.0%}), "
            f"Overall: {self.column_detection.overall_confidence:.0%}",
        )

        if self.column_detection.detection_notes:
            for note in self.column_detection.detection_notes:
                log_secure_operation("column_detection_note", note)

        return self.debit_col is not None and self.credit_col is not None

    def get_column_detection(self) -> Optional[ColumnDetectionResult]:
        """Get the column detection result after processing."""
        return self.column_detection

    def process_chunk(self, chunk: pd.DataFrame, rows_so_far: int) -> None:
        """Process a single chunk, updating running totals and account aggregations."""
        # Normalize columns
        chunk.columns = chunk.columns.str.strip()

        # Discover columns on first chunk
        if not self._discover_columns(chunk):
            log_secure_operation("streaming_error", "Required columns not found")
            return

        # Convert to numeric
        debits = pd.to_numeric(chunk[self.debit_col], errors="coerce").fillna(0)
        credits = pd.to_numeric(chunk[self.credit_col], errors="coerce").fillna(0)

        # Collect per-chunk sums for compensated summation in get_balance_result()
        self._debit_chunks.append(math.fsum(debits.values))
        self._credit_chunks.append(math.fsum(credits.values))
        self.total_rows = rows_so_far

        # Aggregate per-account balances for abnormal detection
        # Performance optimization: Use vectorized groupby instead of iterrows()
        # This reduces O(n) row-by-row iteration to O(unique_accounts) after groupby
        if self.account_col:
            # Create temporary DataFrame for vectorized aggregation
            temp_df = pd.DataFrame(
                {
                    "account": chunk[self.account_col].astype(str).str.strip(),
                    "debit": debits.values,
                    "credit": credits.values,
                }
            )

            # Vectorized groupby aggregation - O(n) but highly optimized in pandas
            grouped = temp_df.groupby("account", as_index=False).agg({"debit": "sum", "credit": "sum"})

            # Merge into running totals - only iterates unique accounts (typically <500)
            for account_name, debit_sum, credit_sum in zip(grouped["account"], grouped["debit"], grouped["credit"]):
                if account_name not in self.account_balances:
                    self.account_balances[account_name] = {"debit": 0.0, "credit": 0.0}
                self.account_balances[account_name]["debit"] += float(debit_sum)
                self.account_balances[account_name]["credit"] += float(credit_sum)

            # Sprint 526: Extract account_type values from dedicated column
            if self.account_type_col and self.account_type_col in chunk.columns:
                for acct_key, acct_type in zip(
                    chunk[self.account_col].astype(str).str.strip(),
                    chunk[self.account_type_col].astype(str).str.strip(),
                ):
                    if acct_key and acct_type and acct_type.lower() not in ("", "nan", "none"):
                        self.provided_account_types[acct_key] = acct_type

            # Sprint 526: Extract account_name values from dedicated column
            if self.account_name_col and self.account_name_col in chunk.columns:
                for acct_key, acct_name in zip(
                    chunk[self.account_col].astype(str).str.strip(),
                    chunk[self.account_name_col].astype(str).str.strip(),
                ):
                    if acct_key and acct_name and acct_name.lower() not in ("", "nan", "none"):
                        self.provided_account_names[acct_key] = acct_name

            # Sprint 535: Extract subtype values from dedicated column
            # Checks common column names: "subtype", "sub_type", "account_subtype"
            if not hasattr(self, '_subtype_col_resolved'):
                self._subtype_col_resolved = True
                self._subtype_col: str | None = None
                chunk_lower = {c.lower().strip(): c for c in chunk.columns}
                for candidate in ("subtype", "sub_type", "account_subtype", "account sub type"):
                    if candidate in chunk_lower:
                        self._subtype_col = chunk_lower[candidate]
                        break
            if self._subtype_col and self._subtype_col in chunk.columns:
                for acct_key, acct_sub in zip(
                    chunk[self.account_col].astype(str).str.strip(),
                    chunk[self._subtype_col].astype(str).str.strip(),
                ):
                    if acct_key and acct_sub and acct_sub.lower() not in ("", "nan", "none"):
                        self.provided_account_subtypes[acct_key] = acct_sub

            # Cleanup temporary DataFrame
            del temp_df, grouped

        self._report_progress(rows_so_far, f"Scanning rows: {rows_so_far:,}")

        # Explicit cleanup
        del debits
        del credits
        gc.collect()

    def get_balance_result(self) -> dict[str, Any]:
        """Get the balance check result after all chunks processed."""
        total_debits = math.fsum(self._debit_chunks)
        total_credits = math.fsum(self._credit_chunks)
        difference = total_debits - total_credits
        # Decimal-aware balance check (Sprint 340)
        is_balanced = abs(Decimal(str(difference))) < BALANCE_TOLERANCE

        return {
            "status": "success",
            "balanced": is_balanced,
            "total_debits": float(quantize_monetary(total_debits)),
            "total_credits": float(quantize_monetary(total_credits)),
            "difference": float(quantize_monetary(difference)),
            "row_count": self.total_rows,
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE",
        }

    def get_abnormal_balances(self) -> list[dict[str, Any]]:
        """Detect abnormal balances using CSV-provided types or weighted heuristic classification.

        Sprint 526: When an account_type column is detected, uses those values
        instead of heuristic classification. Also produces display names in
        "[code] — [name]" format when account_name column is available.
        """
        log_secure_operation(
            "streaming_abnormal",
            f"Analyzing {len(self.account_balances)} unique accounts (threshold: ${self.materiality_threshold:,.2f}), "
            f"provided types: {len(self.provided_account_types)}, provided names: {len(self.provided_account_names)}",
        )

        abnormal_balances = []
        classification_stats = {"high": 0, "medium": 0, "low": 0, "unknown": 0}

        for account_key, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount

            # Skip zero balances (Decimal-aware, Sprint 340)
            if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
                continue

            # Sprint 526: Resolve category from CSV or heuristic
            category = self._resolve_category(account_key, net_balance)
            display = self._display_name(account_key)

            # Also run heuristic for confidence stats and suggestions
            result = self.classifier.classify(display, net_balance)

            # Use CSV-provided category if available, overriding heuristic
            csv_raw = self.provided_account_types.get(account_key, "")
            csv_cat, csv_conf = self._resolve_csv_type(csv_raw)
            has_csv_type = csv_cat is not None
            effective_category = category
            confidence = csv_conf if has_csv_type else result.confidence

            # Track classification confidence stats
            if effective_category == AccountCategory.UNKNOWN:
                classification_stats["unknown"] += 1
            elif confidence >= CONFIDENCE_HIGH:
                classification_stats["high"] += 1
            elif confidence >= CONFIDENCE_MEDIUM:
                classification_stats["medium"] += 1
            else:
                classification_stats["low"] += 1

            # Check if balance is abnormal for the effective category
            # Sprint 530 Fix 1: Pass display name for contra account detection
            is_abnormal = self._is_balance_abnormal(effective_category, net_balance, display)

            # Only flag if abnormal AND classified (not UNKNOWN)
            if is_abnormal and effective_category != AccountCategory.UNKNOWN:
                abs_amount = abs(net_balance)
                is_material = abs_amount >= self.materiality_threshold
                materiality_status = "material" if is_material else "immaterial"

                # Determine human-readable issue description
                normal = NORMAL_BALANCE_MAP[effective_category]
                expected_balance = "Debit" if normal == NormalBalance.DEBIT else "Credit"
                actual_balance = "Credit" if net_balance < 0 else "Debit"

                if not is_material:
                    log_secure_operation(
                        "below_materiality",
                        f"Below materiality: {display} (${abs_amount:,.2f} < ${self.materiality_threshold:,.2f})",
                    )

                abnormal_balances.append(
                    {
                        # EXISTING FIELDS (backward compatible)
                        "account": display,
                        "type": CATEGORY_DISPLAY_NAMES.get(effective_category, "Unknown"),
                        "issue": f"Net {actual_balance} balance (should be {expected_balance})",
                        "amount": round(abs_amount, 2),
                        "debit": round(debit_amount, 2),
                        "credit": round(credit_amount, 2),
                        "materiality": materiality_status,
                        # Classification fields
                        "category": effective_category.value,
                        "confidence": confidence,
                        "matched_keywords": result.matched_keywords if not has_csv_type else ["CSV_ACCOUNT_TYPE"],
                        "requires_review": not has_csv_type and result.requires_review,
                        # Anomaly categorization for Risk Dashboard
                        "anomaly_type": "natural_balance_violation",
                        "expected_balance": expected_balance.lower(),
                        "actual_balance": actual_balance.lower(),
                        "severity": "high" if is_material else "low",
                        # Classification suggestions for low-confidence accounts
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

        # Store stats for response
        self._classification_stats = classification_stats

        return abnormal_balances

    def get_classification_summary(self) -> dict[str, int]:
        """Get classification confidence summary after get_abnormal_balances() is called."""
        return getattr(self, "_classification_stats", {})

    def detect_suspense_accounts(self) -> list[dict[str, Any]]:
        """
        Detect suspense and clearing accounts that may indicate control weaknesses.

        Sprint 41 - Phase III: Suspense Account Detector

        Suspense accounts are temporary holding accounts that should be cleared
        regularly. Their presence (especially with balances) may indicate:
        - Items awaiting proper classification
        - Reconciliation issues
        - Internal control weaknesses

        Returns:
            List of suspense account anomalies with confidence scores
        """
        log_secure_operation(
            "suspense_detection", f"Scanning {len(self.account_balances)} accounts for suspense indicators"
        )

        suspense_accounts: list[dict[str, Any]] = []

        for account_key, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount

            # Skip zero balances (Decimal-aware, Sprint 340)
            if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
                continue

            # Sprint 526: Use display name for keyword matching
            display = self._display_name(account_key)
            account_lower = display.lower()
            matched_keywords: list[str] = []
            total_weight = 0.0

            for keyword, weight, is_phrase in SUSPENSE_KEYWORDS:
                if is_phrase:
                    if keyword in account_lower:
                        matched_keywords.append(keyword)
                        total_weight += weight
                else:
                    if keyword in account_lower:
                        matched_keywords.append(keyword)
                        total_weight += weight

            # Calculate confidence (capped at 1.0)
            confidence = min(total_weight, 1.0)

            # Only flag if confidence meets threshold
            if confidence >= SUSPENSE_CONFIDENCE_THRESHOLD:
                abs_amount = abs(net_balance)
                is_material = abs_amount >= self.materiality_threshold
                materiality_status = "material" if is_material else "immaterial"

                category = self._resolve_category(account_key, net_balance)

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

    def detect_concentration_risk(self) -> list[dict[str, Any]]:
        """
        Detect accounts with unusually high concentration within their category.

        Sprint 42 - Phase III: Concentration Risk Detection

        Concentration risk occurs when a single account represents a large
        percentage of its category total, indicating potential:
        - Over-reliance on a single customer (receivables)
        - Over-reliance on a single vendor (payables)
        - Audit sampling risk
        - Collection/payment risk

        Returns:
            List of concentration risk anomalies with percentage and severity
        """
        log_secure_operation(
            "concentration_detection", f"Analyzing {len(self.account_balances)} accounts for concentration risk"
        )

        concentration_risks: list[dict[str, Any]] = []

        # Group accounts by category and calculate totals
        # Use Decimal accumulation for precise category totals
        category_accounts: dict[AccountCategory, list[tuple[str, float, float, float]]] = {
            cat: [] for cat in CONCENTRATION_CATEGORIES
        }
        category_totals_dec: dict[AccountCategory, Decimal] = {cat: Decimal("0") for cat in CONCENTRATION_CATEGORIES}

        for account_key, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount

            # Skip zero balances (Decimal-aware, Sprint 340)
            if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
                continue

            # Sprint 526: Use resolved category
            category = self._resolve_category(account_key, net_balance)
            display = self._display_name(account_key)

            if category in CONCENTRATION_CATEGORIES:
                abs_balance = abs(net_balance)
                category_accounts[category].append((display, abs_balance, debit_amount, credit_amount))
                category_totals_dec[category] += Decimal(str(abs_balance))

        # Analyze concentration for each category
        for category in CONCENTRATION_CATEGORIES:
            total_dec = category_totals_dec[category]

            # Skip categories below minimum threshold
            if float(total_dec) < CONCENTRATION_MIN_CATEGORY_TOTAL:
                continue

            for display, abs_balance, debit_amount, credit_amount in category_accounts[category]:
                # Perform percentage division in Decimal for precision
                concentration_pct = float(Decimal(str(abs_balance)) / total_dec)

                # Determine severity based on concentration level
                severity = None
                if concentration_pct >= CONCENTRATION_THRESHOLD_HIGH:
                    severity = "high"
                elif concentration_pct >= CONCENTRATION_THRESHOLD_MEDIUM:
                    severity = "medium"

                if severity:
                    is_material = abs_balance >= self.materiality_threshold
                    materiality_status = "material" if is_material else "immaterial"

                    # Sprint 530 Fix 8: Correct pluralization
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
                            "issue": f"Represents {concentration_pct:.1%} of total {cat_plural}",
                            "amount": round(abs_balance, 2),
                            "debit": round(debit_amount, 2),
                            "credit": round(credit_amount, 2),
                            "materiality": materiality_status,
                            "category": category.value,
                            "confidence": concentration_pct,
                            "matched_keywords": [],
                            "requires_review": True,
                            "anomaly_type": f"{category.value}_concentration",
                            "concentration_percent": round(concentration_pct * 100, 1),
                            "category_total": round(float(total_dec), 2),
                            "severity": severity,
                            "suggestions": [],
                            "recommendation": (
                                f"This account represents {concentration_pct:.1%} of total {cat_plural}. "
                                "Review for over-reliance on a single counterparty and consider "
                                "the impact if this balance becomes uncollectible or disputed."
                            ),
                        }
                    )

        # Sort by concentration percentage (highest first)
        concentration_risks.sort(key=lambda x: x["concentration_percent"], reverse=True)

        log_secure_operation(
            "concentration_detection_complete", f"Found {len(concentration_risks)} concentration risk accounts"
        )

        return concentration_risks

    def detect_rounding_anomalies(self) -> list[dict[str, Any]]:
        """
        Detect suspicious round numbers that may indicate estimation or manipulation.

        Sprint 42 - Phase III: Rounding Anomaly Detection
        Sprint 536: Three-tier framework (Suppress / Minor / Material)

        Returns:
            List of rounding anomalies with tier-appropriate severity and text
        """
        log_secure_operation(
            "rounding_detection", f"Analyzing {len(self.account_balances)} accounts for rounding anomalies"
        )
        log_secure_operation("DEPLOY-VERIFY-536", "tiered round-number detection active")
        log_secure_operation("DEPLOY-VERIFY-537", "informational severity tier active")

        # Compute TB total for 10% concentration threshold
        tb_total = sum(
            abs(b["debit"] - b["credit"]) for b in self.account_balances.values()
        )

        # Prefer dedicated subtype column; fall back to type column
        subtype_source = self.provided_account_subtypes or self.provided_account_types

        # ── First pass: identify round accounts and classify tier ──────
        # Collect candidates as (finding_dict, tier, abs_balance, category, subtype)
        candidates: list[tuple[dict[str, Any], str, float, str, str]] = []

        for account_key, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount
            abs_balance = abs(net_balance)

            # Skip amounts below minimum threshold
            if abs_balance < ROUNDING_MIN_AMOUNT:
                continue

            display = self._display_name(account_key)
            category = self._resolve_category(account_key, net_balance)
            subtype_raw = subtype_source.get(account_key, "")

            # Check against rounding patterns (most significant first)
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
                continue  # Not a round number

            # Sprint 536: Classify into tier
            tier = classify_round_number_tier(
                display, category, subtype_raw, abs_balance, tb_total, self.materiality_threshold,
            )
            if tier is None:
                continue  # Tier 1 — suppressed

            divisor, pattern_name, pattern_severity = matched_pattern

            if divisor >= 100000:
                round_desc = f"${abs_balance / 1000:,.0f}K"
            else:
                round_desc = f"${abs_balance:,.0f}"

            # Tier-appropriate severity and text
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
                    "action required — verify during substantive procedures if material to "
                    "the engagement."
                )
            else:
                # tier == "material"
                effective_severity = pattern_severity if abs_balance >= self.materiality_threshold else "medium"
                materiality_status = "material" if abs_balance >= self.materiality_threshold else "immaterial"
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

        # ── Second pass: repeated identical amounts (3+) in same type/subtype ──
        from collections import Counter

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

        # Upgrade repeated-pattern accounts to Material
        rounding_anomalies: list[dict[str, Any]] = []
        for finding, tier, abs_bal, cat_val, sub_val in candidates:
            if (cat_val, sub_val, abs_bal) in repeated_sets:
                # Count how many accounts share this amount
                n_matching = group_amounts[(cat_val, sub_val)].count(abs_bal)
                matching_accounts = [
                    f[0]["account"] for f in candidates
                    if f[3] == cat_val and f[4] == sub_val and f[2] == abs_bal
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
                finding["issue"] = (
                    f"Identical round amount {amt_str} appears across "
                    f"{n_matching} accounts"
                )
                finding["recommendation"] = (
                    f"Identical round amount {amt_str} appears across "
                    f"{n_matching} accounts ({acct_list}). This pattern may indicate "
                    "allocation, estimation, or systematic rounding rather than "
                    "transaction-based recording. Obtain documentation for the allocation "
                    "methodology and verify each amount independently."
                )

            rounding_anomalies.append(finding)

        # Sort by amount (highest first) and limit results
        rounding_anomalies.sort(key=lambda x: x["amount"], reverse=True)
        if len(rounding_anomalies) > ROUNDING_MAX_ANOMALIES:
            rounding_anomalies = rounding_anomalies[:ROUNDING_MAX_ANOMALIES]

        log_secure_operation("rounding_detection_complete", f"Found {len(rounding_anomalies)} rounding anomalies")

        return rounding_anomalies

    # ─── Sprint 526: Helpers for classification pipeline ────────────────

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

    _csv_type_log_count: int = 0

    def _resolve_csv_type(self, raw_value: str) -> tuple[AccountCategory | None, float]:
        """Resolve a raw CSV account type value to a category and confidence.

        Returns (category, confidence) or (None, 0.0) if no match.
        Direct map hit = 1.0 confidence; suffix match = 0.90.
        """
        normalized = raw_value.lower().strip()

        # Sprint 528 Step 4: Log first 5 CSV type values for deploy verification
        if self._csv_type_log_count < 5 and raw_value:
            self._csv_type_log_count += 1
            log_secure_operation(
                "csv_type_trace",
                f"[{self._csv_type_log_count}/5] raw={raw_value!r} normalized={normalized!r}",
            )

        if not normalized:
            return None, 0.0
        # Direct lookup
        if normalized in self._CSV_TYPE_MAP:
            return self._CSV_TYPE_MAP[normalized], 1.0
        # Suffix fallback — catches qualified variants not explicitly listed
        for suffix, category in self._CSV_TYPE_SUFFIXES:
            if normalized.endswith(suffix):
                return category, 0.90
        return None, 0.0

    def _resolve_category(self, account_key: str, net_balance: float = 0.0) -> AccountCategory:
        """Resolve the account category — CSV-provided type takes priority over heuristic."""
        csv_raw = self.provided_account_types.get(account_key, "")
        csv_category, _ = self._resolve_csv_type(csv_raw)
        if csv_category is not None:
            return csv_category
        # Fallback: use the heuristic classifier with account name context
        classify_name = self._display_name(account_key)
        result = self.classifier.classify(classify_name, net_balance)
        return result.category

    def _display_name(self, account_key: str) -> str:
        """Build display name: '[code] — [name]' when account_name column is available."""
        name = self.provided_account_names.get(account_key)
        if name and name != account_key:
            return f"{account_key} — {name}"
        return account_key

    def _is_balance_abnormal(
        self, category: AccountCategory, net_balance: float, account_name: str = ""
    ) -> bool:
        """Check if balance direction is abnormal for the given category.

        Sprint 530: Contra accounts (e.g. Accumulated Depreciation) carry the
        opposite of their parent category's normal balance.  When a contra
        account is detected, the expected direction is inverted so that the
        *normal* contra balance is not flagged.
        """
        if abs(net_balance) < 0.01 or category == AccountCategory.UNKNOWN:
            return False
        normal = NORMAL_BALANCE_MAP[category]

        # Sprint 530 Fix 1: Invert expected balance for contra accounts
        if account_name and is_contra_account(account_name, category):
            if normal == NormalBalance.DEBIT:
                # Contra-asset: expected credit — debit balance is abnormal
                return net_balance > 0
            # Contra-revenue/equity: expected debit — credit balance is abnormal
            return net_balance < 0

        if normal == NormalBalance.DEBIT:
            return net_balance < 0
        return net_balance > 0

    # ─── Sprint 527: Keywords imported from classification_rules.py ──

    # ─── Sprint 526 Fix 3 / Sprint 536: Rounding Tier Configuration ──
    # Superseded by classify_round_number_tier() in classification_rules.py.
    # Kept as class attributes for backward compatibility with any tests
    # that reference them directly.
    _ROUNDING_TIER1_KEYWORDS: list[str] = ROUND_NUMBER_TIER1_SUPPRESS
    _ROUNDING_TIER1_CATEGORIES: set[str] = set()
    _ROUNDING_TIER3_KEYWORDS: list[str] = [
        "suspense",
        "clearing",
        "miscellaneous",
        "sundry",
        "unallocated",
        "unclassified",
    ]

    def detect_related_party_accounts(self) -> list[dict[str, Any]]:
        """Sprint 526 Fix 4d: Detect accounts indicating related party activity.

        Sprint 530 Fix 2: Tightened keyword matching. Accounts matching
        RELATED_PARTY_EXCLUSION_KEYWORDS (e.g. insurance, board fees) are
        excluded even if they match a related party keyword.
        """
        findings: list[dict[str, Any]] = []
        for account_key, balances in self.account_balances.items():
            net_balance = balances["debit"] - balances["credit"]
            if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
                continue

            display = self._display_name(account_key)
            search_text = display.lower()

            # Sprint 530 Fix 2: Exclude insurance/fee accounts that mention
            # directors or officers in a non-counterparty context.
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
            category = self._resolve_category(account_key, net_balance)
            is_material = abs_amount >= self.materiality_threshold

            findings.append(
                {
                    "account": display,
                    "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                    "issue": "Related party balance — requires ASC 850 disclosure assessment",
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

    def detect_intercompany_imbalances(self) -> list[dict[str, Any]]:
        """Sprint 526 Fix 4e: Detect intercompany accounts with elimination gaps."""
        # Collect intercompany accounts and try to match counterparties
        ic_accounts: list[tuple[str, str, float, dict]] = []  # (key, display, net, balances)
        for account_key, balances in self.account_balances.items():
            net_balance = balances["debit"] - balances["credit"]
            if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
                continue

            display = self._display_name(account_key)
            search_text = display.lower()
            if any(kw in search_text for kw, _w, _p in INTERCOMPANY_KEYWORDS):
                ic_accounts.append((account_key, display, net_balance, balances))

        if not ic_accounts:
            return []

        # Extract counterparty names from account descriptions
        # Pattern: "Intercompany Receivable — Meridian UK" → counterparty = "meridian uk"
        # Sprint 530 Fix 4: Handle all separator variants including bare em-dash
        def _extract_counterparty(name: str) -> str:
            lower = name.lower()
            # Try separators from most specific to least (spaces around dashes first)
            for sep in [" — ", " – ", " - ", "—", "–", "-"]:
                if sep in lower:
                    parts = lower.split(sep)
                    # Take the last segment as the counterparty name
                    cp = parts[-1].strip()
                    # Skip if the last segment is a common account term, not a name
                    if cp and cp not in ("receivable", "payable", "loan"):
                        return cp
            return ""

        # Group by counterparty
        counterparty_groups: dict[str, list[tuple[str, str, float, dict]]] = {}
        for key, display, net, bals in ic_accounts:
            cp = _extract_counterparty(display)
            if cp:
                counterparty_groups.setdefault(cp, []).append((key, display, net, bals))

        findings: list[dict[str, Any]] = []
        for cp_name, accounts in counterparty_groups.items():
            net_total = sum(net for _, _, net, _ in accounts)
            # If counterparty nets to zero, no elimination gap
            if abs(Decimal(str(net_total))) < BALANCE_TOLERANCE:
                continue

            # Check if there's only a receivable without payable (or vice versa)
            has_debit = any(net > 0 for _, _, net, _ in accounts)
            has_credit = any(net < 0 for _, _, net, _ in accounts)

            if has_debit and has_credit:
                # Both sides exist but don't net — partial gap
                issue = f"Intercompany elimination gap of ${abs(net_total):,.2f} with {cp_name.title()}"
            elif has_debit:
                issue = f"Intercompany receivable from {cp_name.title()} — no offsetting payable found"
            else:
                issue = f"Intercompany payable to {cp_name.title()} — no offsetting receivable found"

            # Flag the account(s) with the unmatched balance
            for key, display, net, bals in accounts:
                if abs(net) < 0.01:
                    continue
                abs_amount = abs(net)
                category = self._resolve_category(key, net)
                is_material = abs_amount >= self.materiality_threshold

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
                        "cross_reference_note": f"Counterparty: {cp_name.title()} — net exposure: ${abs(net_total):,.2f}",
                    }
                )

        return findings

    def detect_equity_signals(self) -> list[dict[str, Any]]:
        """Sprint 526 Fix 4f: Detect abnormal equity patterns."""
        findings: list[dict[str, Any]] = []
        equity_accounts: dict[str, tuple[str, float, dict]] = {}  # key → (display, net, bals)

        for account_key, balances in self.account_balances.items():
            net_balance = balances["debit"] - balances["credit"]
            category = self._resolve_category(account_key, net_balance)
            if category == AccountCategory.EQUITY:
                display = self._display_name(account_key)
                equity_accounts[account_key] = (display, net_balance, balances)

        if not equity_accounts:
            return findings

        # Find specific equity components
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

        # Signal: Deficit + Dividends Declared
        if retained_earnings_deficit and dividends_declared:
            re_key, re_display, re_net, re_bals = retained_earnings_deficit
            div_key, div_display, div_net, div_bals = dividends_declared
            # Retained earnings with debit balance = deficit
            if re_net > 0:  # Debit balance (deficit)
                combined_return = abs(div_net) + (abs(treasury_stock[2]) if treasury_stock else 0)
                is_material = abs(re_net) >= self.materiality_threshold

                findings.append(
                    {
                        "account": re_display,
                        "type": "Equity",
                        "issue": (
                            f"Accumulated deficit of ${abs(re_net):,.2f} while dividends of "
                            f"${abs(div_net):,.2f} have been declared — governance and solvency concern"
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

    def detect_revenue_concentration(self) -> list[dict[str, Any]]:
        """Sprint 526 Fix 4g: Revenue concentration analysis (threshold from classification_rules)."""
        findings: list[dict[str, Any]] = []
        revenue_accounts: list[tuple[str, str, float, dict]] = []
        total_revenue = Decimal("0")

        for account_key, balances in self.account_balances.items():
            net_balance = balances["debit"] - balances["credit"]
            category = self._resolve_category(account_key, net_balance)
            if category == AccountCategory.REVENUE:
                abs_bal = abs(net_balance)
                display = self._display_name(account_key)
                revenue_accounts.append((account_key, display, abs_bal, balances))
                total_revenue += Decimal(str(abs_bal))

        if float(total_revenue) < CONCENTRATION_MIN_CATEGORY_TOTAL:
            return findings

        for key, display, abs_bal, bals in revenue_accounts:
            pct = float(Decimal(str(abs_bal)) / total_revenue)
            if pct >= REVENUE_CONCENTRATION_THRESHOLD:
                is_material = abs_bal >= self.materiality_threshold
                findings.append(
                    {
                        "account": display,
                        "type": "Revenue",
                        "issue": f"Revenue concentration: {pct:.1%} of total revenue (${float(total_revenue):,.0f})",
                        "amount": round(abs_bal, 2),
                        "debit": round(bals["debit"], 2),
                        "credit": round(bals["credit"], 2),
                        "materiality": "material" if is_material else "immaterial",
                        "category": "revenue",
                        "confidence": pct,
                        "matched_keywords": [],
                        "requires_review": True,
                        "anomaly_type": "concentration_risk",
                        "concentration_percent": round(pct * 100, 1),
                        "category_total": round(float(total_revenue), 2),
                        "severity": "high" if is_material and pct >= REVENUE_CONCENTRATION_THRESHOLD else "medium",
                        "suggestions": [],
                    }
                )

        return findings

    def detect_expense_concentration(self) -> list[dict[str, Any]]:
        """Sprint 526 Fix 4h: Expense concentration analysis (threshold from classification_rules)."""
        findings: list[dict[str, Any]] = []
        expense_accounts: list[tuple[str, str, float, dict]] = []
        total_expense = Decimal("0")

        for account_key, balances in self.account_balances.items():
            net_balance = balances["debit"] - balances["credit"]
            category = self._resolve_category(account_key, net_balance)
            if category == AccountCategory.EXPENSE:
                abs_bal = abs(net_balance)
                display = self._display_name(account_key)
                expense_accounts.append((account_key, display, abs_bal, balances))
                total_expense += Decimal(str(abs_bal))

        if float(total_expense) < CONCENTRATION_MIN_CATEGORY_TOTAL:
            return findings

        for key, display, abs_bal, bals in expense_accounts:
            pct = float(Decimal(str(abs_bal)) / total_expense)
            if pct >= EXPENSE_CONCENTRATION_THRESHOLD:
                is_material = abs_bal >= self.materiality_threshold
                findings.append(
                    {
                        "account": display,
                        "type": "Expense",
                        "issue": f"Expense concentration: {pct:.1%} of total expenses (${float(total_expense):,.0f})",
                        "amount": round(abs_bal, 2),
                        "debit": round(bals["debit"], 2),
                        "credit": round(bals["credit"], 2),
                        "materiality": "material" if is_material else "immaterial",
                        "category": "expense",
                        "confidence": pct,
                        "matched_keywords": [],
                        "requires_review": True,
                        "anomaly_type": "concentration_risk",
                        "concentration_percent": round(pct * 100, 1),
                        "category_total": round(float(total_expense), 2),
                        "severity": "high" if is_material else "medium",
                        "suggestions": [],
                    }
                )

        return findings

    def get_classified_accounts(self) -> dict[str, str]:
        """Get classification for all accounts. Call after process_chunk."""
        classified = {}
        for account_name in self.account_balances.keys():
            balances = self.account_balances[account_name]
            net_balance = balances["debit"] - balances["credit"]
            # Sprint 526: Use resolved category (CSV-provided or heuristic)
            category = self._resolve_category(account_name, net_balance)
            classified[account_name] = category.value
        return classified

    def get_category_totals(self) -> CategoryTotals:
        """Extract aggregate category totals for ratio calculations.

        Sprint 530: Passes raw CSV subtype values so that
        extract_category_totals() can use them for current/non-current
        stratification and COGS recognition.

        Sprint 535: Uses display-name-keyed dicts so keyword fallback
        works when subtype is absent.  Prefers provided_account_subtypes
        (the dedicated subtype column) over provided_account_types
        (the broad type column) for subcategory matching.
        """
        log_secure_operation("DEPLOY-VERIFY-535", "get_category_totals invoked")

        classified_accounts = self.get_classified_accounts()

        # Sprint 535: Build display-name-keyed versions so that
        # extract_category_totals() can do keyword matching on account
        # names (e.g., "inventory", "receivable") as a fallback when
        # no subtype column is available.
        display_balances: dict[str, dict[str, float]] = {}
        display_classifications: dict[str, str] = {}
        display_subtypes: dict[str, str] = {}

        # Prefer dedicated subtype column; fall back to type column
        subtype_source = self.provided_account_subtypes or self.provided_account_types

        for acct_key in self.account_balances:
            display = self._display_name(acct_key)
            display_balances[display] = self.account_balances[acct_key]
            display_classifications[display] = classified_accounts.get(acct_key, "unknown")
            display_subtypes[display] = subtype_source.get(acct_key, "")

        return extract_category_totals(
            display_balances,
            display_classifications,
            account_subtypes=display_subtypes,
        )

    def validate_balance_sheet(self, category_totals: Optional[CategoryTotals] = None) -> dict[str, Any]:
        """
        Validate the fundamental accounting equation: Assets = Liabilities + Equity.

        Sprint 43 - Phase III: Balance Sheet Validator

        Delegates to the standalone validate_balance_sheet_equation function.

        Args:
            category_totals: Optional pre-computed totals. If None, computed fresh.

        Returns:
            Dict with validation result, difference, and recommendation
        """
        if category_totals is None:
            category_totals = self.get_category_totals()

        return validate_balance_sheet_equation(category_totals)

    def clear(self) -> None:
        """Clear all accumulated data and force garbage collection."""
        self.account_balances.clear()
        self.provided_account_subtypes.clear()
        self._debit_chunks.clear()
        self._credit_chunks.clear()
        self.total_rows = 0
        gc.collect()
        log_secure_operation("streaming_clear", "Auditor state cleared")


def _merge_anomalies(
    abnormal_balances: list[dict[str, Any]],
    suspense_accounts: list[dict[str, Any]],
    concentration_risks: list[dict[str, Any]],
    rounding_anomalies: list[dict[str, Any]],
    *,
    related_party: list[dict[str, Any]] | None = None,
    intercompany: list[dict[str, Any]] | None = None,
    equity_signals: list[dict[str, Any]] | None = None,
    revenue_concentration: list[dict[str, Any]] | None = None,
    expense_concentration: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Merge all anomaly types into abnormal balances.

    Avoids duplicates: if an account already exists in abnormal_balances,
    adds flags to the existing entry instead of creating a new one.
    Mutates and returns abnormal_balances.
    """
    existing_accounts = {ab["account"] for ab in abnormal_balances}

    def _merge_list(items: list[dict[str, Any]], flag_key: str, extra_fields: dict[str, str] | None = None) -> None:
        for item in items:
            if item["account"] not in existing_accounts:
                abnormal_balances.append(item)
                existing_accounts.add(item["account"])
            else:
                for entry in abnormal_balances:
                    if entry["account"] == item["account"]:
                        entry[flag_key] = True
                        if extra_fields:
                            for src, dst in extra_fields.items():
                                if src in item:
                                    entry[dst] = item[src]
                        if entry.get("severity") == "low" and item.get("severity") in ("high", "medium"):
                            entry["severity"] = item["severity"]
                        break

    # Sprint 535 P1-2: Finding type priority hierarchy (corrected)
    # Intercompany Imbalance > Related Party > Suspense > Abnormal Balance > Concentration > Round Number
    # Intercompany imbalance is more specific than related party; an account
    # with no offsetting counterpart should surface as an elimination gap,
    # not a generic ASC 850 disclosure item.
    intercompany_accounts: set[str] = set()
    related_party_accounts: set[str] = set()

    if intercompany:
        _merge_list(intercompany, "is_intercompany_imbalance", {"cross_reference_note": "cross_reference_note"})
        intercompany_accounts = {ic["account"] for ic in intercompany}

    if related_party:
        # Exclude accounts already claimed by intercompany imbalance
        filtered_related = [
            rp for rp in related_party
            if rp["account"] not in intercompany_accounts
        ]
        _merge_list(filtered_related, "is_related_party")
        related_party_accounts = {rp["account"] for rp in filtered_related}

    # Promote intercompany accounts: if an account was first added as
    # a different anomaly_type (e.g. natural_balance_violation) and then
    # intercompany metadata was merged as a flag, make intercompany the
    # primary anomaly_type.
    for entry in abnormal_balances:
        if entry.get("is_intercompany_imbalance") and entry.get("anomaly_type") != "intercompany_imbalance":
            entry["anomaly_type"] = "intercompany_imbalance"
            cross_note = entry.get("cross_reference_note", "")
            if cross_note:
                entry["issue"] = f"Intercompany receivable with no offsetting payable — potential consolidation elimination gap. {cross_note}"
            else:
                entry["issue"] = "Intercompany receivable with no offsetting payable — potential consolidation elimination gap"
            entry["severity"] = "high"

    # Suspense: exclude accounts already claimed by intercompany or related party
    filtered_suspense = [
        s for s in suspense_accounts
        if s["account"] not in related_party_accounts and s["account"] not in intercompany_accounts
    ]
    _merge_list(
        filtered_suspense,
        "is_suspense_account",
        {"confidence": "suspense_confidence", "matched_keywords": "suspense_keywords"},
    )

    _merge_list(
        concentration_risks,
        "has_concentration_risk",
        {"concentration_percent": "concentration_percent", "category_total": "category_total"},
    )

    # Round-number: suppress for accounts already claimed by intercompany imbalance
    filtered_rounding = [
        r for r in rounding_anomalies
        if r["account"] not in intercompany_accounts
    ]
    _merge_list(filtered_rounding, "has_rounding_anomaly", {"rounding_pattern": "rounding_pattern"})

    if equity_signals:
        _merge_list(equity_signals, "is_equity_signal", {"cross_reference_note": "cross_reference_note"})
    if revenue_concentration:
        _merge_list(
            revenue_concentration,
            "has_concentration_risk",
            {"concentration_percent": "concentration_percent", "category_total": "category_total"},
        )
    if expense_concentration:
        _merge_list(
            expense_concentration,
            "has_concentration_risk",
            {"concentration_percent": "concentration_percent", "category_total": "category_total"},
        )

    return abnormal_balances


def _build_risk_summary(abnormal_balances: list[dict[str, Any]]) -> dict[str, Any]:
    """Build risk summary dict from merged abnormal balances.

    Counts by severity (high/medium/low) and by anomaly type.
    """
    high_severity = sum(1 for ab in abnormal_balances if ab.get("severity") == "high")
    medium_severity = sum(1 for ab in abnormal_balances if ab.get("severity") == "medium")
    informational_count = sum(1 for ab in abnormal_balances if ab.get("severity") == "informational")
    low_severity = len(abnormal_balances) - high_severity - medium_severity - informational_count
    suspense_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "suspense_account" or ab.get("is_suspense_account")
    )
    concentration_count = sum(
        1
        for ab in abnormal_balances
        if (ab.get("anomaly_type", "").endswith("_concentration")) or ab.get("has_concentration_risk")
    )
    rounding_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "rounding_anomaly" or ab.get("has_rounding_anomaly")
    )
    # Sub-type counts for concentration categories
    revenue_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "revenue_concentration")
    asset_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "asset_concentration")
    liability_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "liability_concentration")
    expense_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "expense_concentration")
    # Sprint 526: Count new anomaly types
    related_party_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "related_party" or ab.get("is_related_party")
    )
    intercompany_count = sum(
        1
        for ab in abnormal_balances
        if ab.get("anomaly_type") == "intercompany_imbalance" or ab.get("is_intercompany_imbalance")
    )
    equity_signal_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "equity_signal" or ab.get("is_equity_signal")
    )

    return {
        "total_anomalies": len(abnormal_balances),
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "low_severity": low_severity,
        "informational_count": informational_count,
        "anomaly_types": {
            "natural_balance_violation": sum(
                1 for ab in abnormal_balances if ab.get("anomaly_type") == "natural_balance_violation"
            ),
            "suspense_account": suspense_count,
            "concentration_risk": concentration_count,
            "revenue_concentration": revenue_concentration,
            "asset_concentration": asset_concentration,
            "liability_concentration": liability_concentration,
            "expense_concentration": expense_concentration,
            "rounding_anomaly": rounding_count,
            "related_party": related_party_count,
            "intercompany_imbalance": intercompany_count,
            "equity_signal": equity_signal_count,
        },
    }


def audit_trial_balance_streaming(
    file_bytes: bytes,
    filename: str,
    materiality_threshold: float = 0.0,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    account_type_overrides: Optional[dict[str, str]] = None,
    column_mapping: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Perform a complete streaming audit of a trial balance file."""
    log_secure_operation("streaming_audit_start", f"Starting streaming audit: {filename}")

    # Create classifier with any user overrides (Zero-Storage: session-only)
    classifier = create_classifier(account_type_overrides)
    if account_type_overrides:
        log_secure_operation(
            "classifier_overrides", f"Using {len(account_type_overrides)} user-provided account type overrides"
        )

    # Parse column mapping if provided (Day 9.2 - Zero-Storage: session-only)
    parsed_column_mapping: Optional[ColumnMapping] = None
    if column_mapping:
        parsed_column_mapping = ColumnMapping.from_dict(column_mapping)
        log_secure_operation("column_mapping_override", f"Using user-provided column mapping: {column_mapping}")

    auditor = StreamingAuditor(
        materiality_threshold=materiality_threshold,
        chunk_size=chunk_size,
        progress_callback=progress_callback,
        classifier=classifier,
        column_mapping=parsed_column_mapping,
    )

    try:
        # Process all chunks
        for chunk, rows_processed in process_tb_chunked(file_bytes, filename, chunk_size):
            auditor.process_chunk(chunk, rows_processed)

            # Explicit chunk cleanup (already done in generator, but be thorough)
            del chunk
            gc.collect()

        # Get final results
        result = auditor.get_balance_result()
        abnormal_balances = auditor.get_abnormal_balances()

        # Sprint 41-42: Detect and merge anomalies
        suspense_accounts = auditor.detect_suspense_accounts()
        concentration_risks = auditor.detect_concentration_risk()
        rounding_anomalies = auditor.detect_rounding_anomalies()

        # Sprint 526: New detection categories (Fix 4d–4h)
        related_party = auditor.detect_related_party_accounts()
        intercompany = auditor.detect_intercompany_imbalances()
        equity_signals = auditor.detect_equity_signals()
        revenue_concentration = auditor.detect_revenue_concentration()
        expense_concentration = auditor.detect_expense_concentration()

        abnormal_balances = _merge_anomalies(
            abnormal_balances,
            suspense_accounts,
            concentration_risks,
            rounding_anomalies,
            related_party=related_party,
            intercompany=intercompany,
            equity_signals=equity_signals,
            revenue_concentration=revenue_concentration,
            expense_concentration=expense_concentration,
        )

        # Add abnormal balance data to result
        result["abnormal_balances"] = abnormal_balances
        result["materiality_threshold"] = materiality_threshold
        result["material_count"] = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
        _informational_count = sum(1 for ab in abnormal_balances if ab.get("severity") == "informational")
        result["immaterial_count"] = len(abnormal_balances) - result["material_count"] - _informational_count
        result["informational_count"] = _informational_count
        result["has_risk_alerts"] = result["material_count"] > 0

        # Add classification summary (Day 9)
        result["classification_summary"] = auditor.get_classification_summary()

        # Day 10: Add risk summary for Risk Dashboard
        result["risk_summary"] = _build_risk_summary(abnormal_balances)

        # Sprint 526 Fix 5: Compute risk score at analysis time so dashboard and PDF agree
        from shared.tb_diagnostic_constants import compute_tb_risk_score, get_risk_tier

        anomaly_types = result["risk_summary"].get("anomaly_types", {})
        _has_suspense = anomaly_types.get("suspense_account", 0) > 0
        _has_credit_balance = any(
            ab.get("anomaly_type") in ("abnormal_balance", "natural_balance_violation")
            and (ab.get("type", "").lower() == "asset")
            for ab in abnormal_balances
        )
        _total_debits = result.get("total_debits", 0)
        _material_items = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
        _flagged_value = sum(abs(ab.get("amount", 0)) for ab in _material_items)
        _coverage_pct = min(_flagged_value / _total_debits * 100, 100.0) if _total_debits > 0 else 0

        risk_score, risk_factors = compute_tb_risk_score(
            result["material_count"],
            result["immaterial_count"],
            _coverage_pct,
            _has_suspense,
            _has_credit_balance,
            abnormal_balances=abnormal_balances,
            informational_count=result["informational_count"],
        )
        result["risk_summary"]["risk_score"] = risk_score
        result["risk_summary"]["risk_tier"] = get_risk_tier(risk_score)
        result["risk_summary"]["risk_factors"] = [(name, pts) for name, pts in risk_factors]
        result["risk_summary"]["coverage_pct"] = round(min(_coverage_pct, 100.0), 1)

        # Sprint 95: Classification Validator — structural COA checks
        # Sprint 528 Fix: Use get_classified_accounts() which routes through
        # _resolve_category() — CSV-provided types take priority over heuristic.
        # Previously called classifier.classify() directly, bypassing CSV types.
        account_classifications = auditor.get_classified_accounts()
        cv_result = run_classification_validation(auditor.account_balances, account_classifications)
        result["classification_quality"] = cv_result.to_dict()

        # Sprint 287: Population Profile
        # Sprint 535 P3-1: Use display-name-keyed dicts so top-account labels
        # show "1010 — Cash and Cash Equivalents" instead of bare "1010".
        from population_profile_engine import compute_population_profile

        pop_display_balances: dict[str, dict[str, float]] = {}
        pop_display_classifications: dict[str, str] = {}
        for _pk in auditor.account_balances:
            _pd = auditor._display_name(_pk)
            pop_display_balances[_pd] = auditor.account_balances[_pk]
            pop_display_classifications[_pd] = account_classifications.get(_pk, "unknown")
        pop_profile = compute_population_profile(pop_display_balances, pop_display_classifications)
        result["population_profile"] = pop_profile.to_dict()

        # Sprint 289: Expense Category Analytical Procedures
        from expense_category_engine import compute_expense_categories

        category_totals_pre = auditor.get_category_totals()
        expense_analytics = compute_expense_categories(
            auditor.account_balances,
            account_classifications,
            category_totals_pre.total_revenue,
            materiality_threshold,
        )
        result["expense_category_analytics"] = expense_analytics.to_dict()

        # Sprint 290: Accrual Completeness Estimator
        from accrual_completeness_engine import compute_accrual_completeness

        accrual_report = compute_accrual_completeness(
            auditor.account_balances,
            account_classifications,
        )
        result["accrual_completeness"] = accrual_report.to_dict()

        # Sprint 357: Lease Account Diagnostic (IFRS 16 / ASC 842)
        from lease_diagnostic_engine import compute_lease_diagnostic

        lease_report = compute_lease_diagnostic(
            auditor.account_balances,
            account_classifications,
            materiality_threshold=materiality_threshold,
        )
        result["lease_diagnostic"] = lease_report.to_dict()

        # Sprint 358: Cutoff Risk Indicator (ISA 501)
        from cutoff_risk_engine import compute_cutoff_risk

        cutoff_report = compute_cutoff_risk(
            auditor.account_balances,
            account_classifications,
            materiality_threshold=materiality_threshold,
        )
        result["cutoff_risk"] = cutoff_report.to_dict()

        # Sprint 360: Going Concern Indicator Profile (ISA 570)
        from going_concern_engine import compute_going_concern_profile

        gc_totals = category_totals_pre
        gc_report = compute_going_concern_profile(
            total_assets=gc_totals.total_assets,
            total_liabilities=gc_totals.total_liabilities,
            total_equity=gc_totals.total_equity,
            current_assets=gc_totals.current_assets,
            current_liabilities=gc_totals.current_liabilities,
            total_revenue=gc_totals.total_revenue,
            total_expenses=gc_totals.total_expenses,
        )
        result["going_concern"] = gc_report.to_dict()

        # Add column detection info (Day 9.2)
        col_detection = auditor.get_column_detection()
        if col_detection:
            result["column_detection"] = col_detection.to_dict()
        else:
            result["column_detection"] = None

        # Sprint 19: Extract category totals and calculate ratios
        category_totals = auditor.get_category_totals()
        analytics = calculate_analytics(category_totals, previous_totals=None)

        result["analytics"] = analytics
        result["category_totals"] = category_totals.to_dict()

        # Sprint 43: Validate balance sheet equation (Assets = Liabilities + Equity)
        balance_sheet_validation = auditor.validate_balance_sheet(category_totals)
        result["balance_sheet_validation"] = balance_sheet_validation

        # Add balance sheet imbalance to risk_summary if applicable
        if not balance_sheet_validation["is_balanced"]:
            result["risk_summary"]["anomaly_types"]["balance_sheet_imbalance"] = 1
            # Adjust severity counts
            bs_severity = balance_sheet_validation["severity"]
            if bs_severity == "high":
                result["risk_summary"]["high_severity"] += 1
            elif bs_severity == "medium":
                result["risk_summary"]["medium_severity"] += 1
            elif bs_severity == "low":
                result["risk_summary"]["low_severity"] += 1
            result["risk_summary"]["total_anomalies"] += 1

        # Sprint 534: Expose full parsed account list for multi-period comparison.
        # lead_sheet_grouping only contains abnormal/flagged accounts, but
        # multi-period comparison needs ALL accounts from the uploaded TB.
        # Sprint 535: Use display names and include subtype for downstream use.
        all_accounts_list = []
        for acct_key, balances in auditor.account_balances.items():
            display = auditor._display_name(acct_key)
            all_accounts_list.append({
                "account": display,
                "debit": balances["debit"],
                "credit": balances["credit"],
                "type": account_classifications.get(acct_key, "unknown"),
            })
        result["all_accounts"] = all_accounts_list

        # Sprint 535 P0-1: Expose account_balances and classified_accounts
        # keyed by display name so consumers get keyword-matchable keys.
        display_balances: dict[str, dict[str, float]] = {}
        display_classifications: dict[str, str] = {}
        display_subtypes: dict[str, str] = {}
        subtype_source = auditor.provided_account_subtypes or auditor.provided_account_types
        for acct_key in auditor.account_balances:
            display = auditor._display_name(acct_key)
            display_balances[display] = auditor.account_balances[acct_key]
            display_classifications[display] = account_classifications.get(acct_key, "unknown")
            display_subtypes[display] = subtype_source.get(acct_key, "")
        result["account_balances"] = display_balances
        result["classified_accounts"] = display_classifications
        result["account_subtypes"] = display_subtypes

        # Sprint 535 P0-2: Compute lead sheet grouping from all accounts.
        # group_by_lead_sheet() takes the same dict format as all_accounts_list.
        from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict

        lead_sheet_result = group_by_lead_sheet(all_accounts_list)
        result["lead_sheet_grouping"] = lead_sheet_grouping_to_dict(lead_sheet_result)

        log_secure_operation(
            "streaming_audit_complete",
            f"Audit complete. Rows: {result['row_count']}, Balanced: {result['balanced']}, "
            f"Material risks: {result['material_count']}, "
            f"BS Equation: {'✓' if balance_sheet_validation['is_balanced'] else '✗'}, "
            f"Column confidence: {col_detection.overall_confidence:.0%}"
            if col_detection
            else "N/A",
        )

        return result

    finally:
        # Ensure cleanup regardless of success/failure
        auditor.clear()
        clear_memory()
        log_secure_operation("streaming_audit_cleanup", "Memory cleared")


def audit_trial_balance_multi_sheet(
    file_bytes: bytes,
    filename: str,
    selected_sheets: list[str],
    materiality_threshold: float = 0.0,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    account_type_overrides: Optional[dict[str, str]] = None,
    column_mapping: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Perform a multi-sheet consolidated audit, aggregating totals across selected sheets.

    Sprint 25 Fix: Column detection now runs independently for each sheet.
    """
    log_secure_operation(
        "multi_sheet_audit_start", f"Starting multi-sheet audit: {filename} ({len(selected_sheets)} sheets)"
    )

    # Create classifier with any user overrides
    classifier = create_classifier(account_type_overrides)

    # Parse column mapping if provided (applies to all sheets if specified)
    parsed_column_mapping: Optional[ColumnMapping] = None
    if column_mapping:
        parsed_column_mapping = ColumnMapping.from_dict(column_mapping)

    # Per-sheet results
    sheet_results: dict[str, dict[str, Any]] = {}

    # Consolidated totals (Summation Consolidation)
    consolidated_debits = 0.0
    consolidated_credits = 0.0
    consolidated_rows = 0
    all_abnormal_balances: list[dict[str, Any]] = []

    # Sprint 25: Track column detection per sheet
    sheet_column_detections: dict[str, dict[str, Any]] = {}
    column_order_warnings: list[str] = []
    first_sheet_columns: Optional[tuple[str, str, str]] = None  # (account, debit, credit)

    # Sprint 19: Consolidated category totals
    consolidated_category_totals = CategoryTotals()

    # Sprint 287: Consolidated account balances for population profile
    consolidated_account_balances: dict[str, dict[str, float]] = {}

    try:
        for sheet_name in selected_sheets:
            log_secure_operation("multi_sheet_processing", f"Processing sheet: {sheet_name}")

            # Create a fresh auditor for each sheet (Sprint 25: independent column detection)
            auditor = StreamingAuditor(
                materiality_threshold=materiality_threshold,
                chunk_size=chunk_size,
                progress_callback=progress_callback,
                classifier=classifier,
                column_mapping=parsed_column_mapping,  # User mapping overrides auto-detection
            )

            # Process this sheet's chunks
            for chunk, rows_processed, current_sheet in read_excel_multi_sheet_chunked(
                file_bytes, [sheet_name], chunk_size
            ):
                auditor.process_chunk(chunk, rows_processed)
                del chunk
                gc.collect()

            # Get sheet results
            sheet_balance = auditor.get_balance_result()
            sheet_abnormals = auditor.get_abnormal_balances()

            # Sprint 41-42: Detect and merge anomalies for this sheet
            sheet_suspense = auditor.detect_suspense_accounts()
            sheet_concentration = auditor.detect_concentration_risk()
            sheet_rounding = auditor.detect_rounding_anomalies()

            # Sprint 526: New detection categories (Fix 4d–4h)
            sheet_related_party = auditor.detect_related_party_accounts()
            sheet_intercompany = auditor.detect_intercompany_imbalances()
            sheet_equity_signals = auditor.detect_equity_signals()
            sheet_revenue_conc = auditor.detect_revenue_concentration()
            sheet_expense_conc = auditor.detect_expense_concentration()

            sheet_abnormals = _merge_anomalies(
                sheet_abnormals,
                sheet_suspense,
                sheet_concentration,
                sheet_rounding,
                related_party=sheet_related_party,
                intercompany=sheet_intercompany,
                equity_signals=sheet_equity_signals,
                revenue_concentration=sheet_revenue_conc,
                expense_concentration=sheet_expense_conc,
            )

            # Add sheet identifier to each abnormal balance
            for entry in sheet_abnormals:
                entry["sheet_name"] = sheet_name

            # Sprint 25: Capture per-sheet column detection
            sheet_col_detection = auditor.get_column_detection()
            if sheet_col_detection:
                sheet_column_detections[sheet_name] = sheet_col_detection.to_dict()

                # Track column order for consistency check
                current_columns = (
                    sheet_col_detection.account_column,
                    sheet_col_detection.debit_column,
                    sheet_col_detection.credit_column,
                )

                if first_sheet_columns is None:
                    first_sheet_columns = current_columns
                elif current_columns != first_sheet_columns:
                    # Column order differs from first sheet
                    warning = (
                        f"Sheet '{sheet_name}' has different column order: "
                        f"Account='{current_columns[0]}', Debit='{current_columns[1]}', Credit='{current_columns[2]}' "
                        f"(first sheet: Account='{first_sheet_columns[0]}', Debit='{first_sheet_columns[1]}', Credit='{first_sheet_columns[2]}')"
                    )
                    column_order_warnings.append(warning)
                    log_secure_operation("multi_sheet_column_mismatch", warning)

            # Store per-sheet results (Sprint 25: include column detection)
            sheet_results[sheet_name] = {
                "balanced": sheet_balance["balanced"],
                "total_debits": sheet_balance["total_debits"],
                "total_credits": sheet_balance["total_credits"],
                "difference": sheet_balance["difference"],
                "row_count": sheet_balance["row_count"],
                "abnormal_count": len(sheet_abnormals),
                "column_detection": sheet_column_detections.get(sheet_name),
            }

            # Aggregate into consolidated totals
            consolidated_debits += sheet_balance["total_debits"]
            consolidated_credits += sheet_balance["total_credits"]
            consolidated_rows += sheet_balance["row_count"]
            all_abnormal_balances.extend(sheet_abnormals)

            # Sprint 19: Aggregate category totals across sheets
            sheet_category_totals = auditor.get_category_totals()
            consolidated_category_totals.total_assets += sheet_category_totals.total_assets
            consolidated_category_totals.current_assets += sheet_category_totals.current_assets
            consolidated_category_totals.inventory += sheet_category_totals.inventory
            consolidated_category_totals.total_liabilities += sheet_category_totals.total_liabilities
            consolidated_category_totals.current_liabilities += sheet_category_totals.current_liabilities
            consolidated_category_totals.total_equity += sheet_category_totals.total_equity
            consolidated_category_totals.total_revenue += sheet_category_totals.total_revenue
            consolidated_category_totals.cost_of_goods_sold += sheet_category_totals.cost_of_goods_sold
            consolidated_category_totals.total_expenses += sheet_category_totals.total_expenses

            # Sprint 287: Accumulate account balances for population profile
            for acct, bals in auditor.account_balances.items():
                if acct not in consolidated_account_balances:
                    consolidated_account_balances[acct] = {"debit": 0.0, "credit": 0.0}
                consolidated_account_balances[acct]["debit"] += bals["debit"]
                consolidated_account_balances[acct]["credit"] += bals["credit"]

            auditor.clear()

        # Calculate consolidated balance check
        consolidated_difference = consolidated_debits - consolidated_credits
        is_consolidated_balanced = abs(Decimal(str(consolidated_difference))) < BALANCE_TOLERANCE

        # Count material/immaterial/informational
        material_count = sum(1 for ab in all_abnormal_balances if ab.get("materiality") == "material")
        ms_informational_count = sum(1 for ab in all_abnormal_balances if ab.get("severity") == "informational")
        immaterial_count = len(all_abnormal_balances) - material_count - ms_informational_count

        # Risk summary (Sprint 41-42: include all anomaly type counts)
        risk_summary = _build_risk_summary(all_abnormal_balances)

        # Sprint 526 Fix 5: Compute risk score at analysis time so dashboard and PDF agree
        from shared.tb_diagnostic_constants import compute_tb_risk_score, get_risk_tier

        ms_anomaly_types = risk_summary.get("anomaly_types", {})
        ms_has_suspense = ms_anomaly_types.get("suspense_account", 0) > 0
        ms_has_credit_balance = any(
            ab.get("anomaly_type") in ("abnormal_balance", "natural_balance_violation")
            and (ab.get("type", "").lower() == "asset")
            for ab in all_abnormal_balances
        )
        ms_material_items = [ab for ab in all_abnormal_balances if ab.get("materiality") == "material"]
        ms_flagged_value = sum(abs(ab.get("amount", 0)) for ab in ms_material_items)
        ms_coverage_pct = min(ms_flagged_value / consolidated_debits * 100, 100.0) if consolidated_debits > 0 else 0

        ms_risk_score, ms_risk_factors = compute_tb_risk_score(
            material_count,
            immaterial_count,
            ms_coverage_pct,
            ms_has_suspense,
            ms_has_credit_balance,
            abnormal_balances=all_abnormal_balances,
            informational_count=ms_informational_count,
        )
        risk_summary["risk_score"] = ms_risk_score
        risk_summary["risk_tier"] = get_risk_tier(ms_risk_score)
        risk_summary["risk_factors"] = [(name, pts) for name, pts in ms_risk_factors]
        risk_summary["coverage_pct"] = round(min(ms_coverage_pct, 100.0), 1)

        # Sprint 25: Use first sheet's detection as primary (for backward compatibility)
        first_sheet_name = selected_sheets[0] if selected_sheets else None
        primary_col_detection = sheet_column_detections.get(first_sheet_name) if first_sheet_name else None

        result = {
            "status": "success",
            "balanced": is_consolidated_balanced,
            "total_debits": round(consolidated_debits, 2),
            "total_credits": round(consolidated_credits, 2),
            "difference": round(consolidated_difference, 2),
            "row_count": consolidated_rows,
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Consolidated trial balance is balanced"
            if is_consolidated_balanced
            else "Consolidated trial balance is OUT OF BALANCE",
            # Multi-sheet specific fields
            "is_consolidated": True,
            "sheet_count": len(selected_sheets),
            "selected_sheets": selected_sheets,
            "sheet_results": sheet_results,
            # Anomaly data
            "abnormal_balances": all_abnormal_balances,
            "materiality_threshold": materiality_threshold,
            "material_count": material_count,
            "immaterial_count": immaterial_count,
            "informational_count": ms_informational_count,
            "has_risk_alerts": material_count > 0,
            # Risk summary
            "risk_summary": risk_summary,
            # Sprint 25: Column detection per sheet + primary for backward compat
            "column_detection": primary_col_detection,
            "sheet_column_detections": sheet_column_detections,
            "column_order_warnings": column_order_warnings,
            "has_column_order_mismatch": len(column_order_warnings) > 0,
        }

        # Sprint 19: Add analytics with consolidated category totals
        analytics = calculate_analytics(consolidated_category_totals, previous_totals=None)
        result["analytics"] = analytics
        result["category_totals"] = consolidated_category_totals.to_dict()

        # Sprint 43: Validate balance sheet equation (Assets = Liabilities + Equity)
        balance_sheet_validation = validate_balance_sheet_equation(consolidated_category_totals)
        result["balance_sheet_validation"] = balance_sheet_validation

        # Add balance sheet imbalance to risk_summary if applicable
        if not balance_sheet_validation["is_balanced"]:
            result["risk_summary"]["anomaly_types"]["balance_sheet_imbalance"] = 1
            # Adjust severity counts
            bs_severity = balance_sheet_validation["severity"]
            if bs_severity == "high":
                result["risk_summary"]["high_severity"] += 1
            elif bs_severity == "medium":
                result["risk_summary"]["medium_severity"] += 1
            elif bs_severity == "low":
                result["risk_summary"]["low_severity"] += 1
            result["risk_summary"]["total_anomalies"] += 1

        # Sprint 287: Population Profile (consolidated across all sheets)
        from population_profile_engine import compute_population_profile

        pop_profile = compute_population_profile(consolidated_account_balances)
        result["population_profile"] = pop_profile.to_dict()
        # Also add classification_quality stub for multi-sheet (not computed per-sheet)
        if "classification_quality" not in result:
            result["classification_quality"] = {
                "issues": [],
                "quality_score": 100.0,
                "issue_counts": {},
                "total_issues": 0,
            }

        # Sprint 534: Expose full parsed account list for multi-period comparison.
        # Uses consolidated_account_balances (already aggregated across sheets).
        ms_classifications = {}
        for acct_name, bals in consolidated_account_balances.items():
            net = bals["debit"] - bals["credit"]
            classifier_instance = create_classifier(account_type_overrides)
            ms_classifications[acct_name] = classifier_instance.classify(acct_name, net).category.value
        all_accounts_list = []
        for acct_name, bals in consolidated_account_balances.items():
            all_accounts_list.append({
                "account": acct_name,
                "debit": bals["debit"],
                "credit": bals["credit"],
                "type": ms_classifications.get(acct_name, "unknown"),
            })
        result["all_accounts"] = all_accounts_list

        log_secure_operation(
            "multi_sheet_audit_complete",
            f"Consolidated audit complete. {len(selected_sheets)} sheets, "
            f"{consolidated_rows} total rows, Balanced: {is_consolidated_balanced}, "
            f"BS Equation: {'✓' if balance_sheet_validation['is_balanced'] else '✗'}, "
            f"Column mismatches: {len(column_order_warnings)}",
        )

        return result

    finally:
        clear_memory()
        log_secure_operation("multi_sheet_audit_cleanup", "Memory cleared")
