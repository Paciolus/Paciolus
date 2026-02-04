"""Trial balance analysis and validation with chunked streaming for large files."""

import gc
from datetime import datetime, UTC
from typing import Any, Callable, Optional, Generator
import pandas as pd

from security_utils import (
    log_secure_operation,
    process_tb_chunked,
    clear_memory,
    DEFAULT_CHUNK_SIZE,
    read_excel_multi_sheet_chunked
)

from account_classifier import AccountClassifier, create_classifier
from classification_rules import AccountCategory, CATEGORY_DISPLAY_NAMES
from column_detector import (
    detect_columns,
    ColumnDetectionResult,
    ColumnMapping
)
from ratio_engine import (
    CategoryTotals,
    RatioEngine,
    CommonSizeAnalyzer,
    extract_category_totals,
    calculate_analytics
)


# Legacy keyword mappings (kept for backward compatibility, will be removed)
# New system uses weighted heuristics in account_classifier.py
ASSET_KEYWORDS = ['cash', 'bank', 'receivable', 'inventory', 'prepaid', 'equipment', 'land', 'building', 'vehicle']
LIABILITY_KEYWORDS = ['payable', 'loan', 'tax', 'accrued', 'unearned', 'deferred', 'debt', 'mortgage', 'note payable']


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
        if 'debit' in col_lower:
            debit_col = col_original
        if 'credit' in col_lower:
            credit_col = col_original

    if debit_col is None or credit_col is None:
        return {
            "status": "error",
            "message": "Could not find 'Debit' and 'Credit' columns in the file",
            "timestamp": datetime.now(UTC).isoformat(),
            "balanced": False
        }

    # Convert columns to numeric, coercing errors to NaN
    debits = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
    credits = pd.to_numeric(df[credit_col], errors='coerce').fillna(0)

    total_debits = float(debits.sum())
    total_credits = float(credits.sum())
    difference = total_debits - total_credits

    # Check if balanced (using small tolerance for floating point)
    is_balanced = abs(difference) < 0.01

    return {
        "status": "success",
        "balanced": is_balanced,
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "difference": round(difference, 2),
        "row_count": len(df),
        "timestamp": datetime.now(UTC).isoformat(),
        "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE"
    }


def detect_abnormal_balances(df: pd.DataFrame, materiality_threshold: float = 0.0) -> list[dict[str, Any]]:
    """Detect accounts with abnormal balance directions (e.g., assets with credit balances)."""
    log_secure_operation("detect_abnormal", f"Scanning for abnormal balances (threshold: ${materiality_threshold:,.2f})")

    abnormal_balances = []

    # Work on a copy to avoid modifying the original
    df = df.copy()

    # Normalize column names (strip whitespace, case-insensitive matching)
    df.columns = df.columns.str.strip()
    column_map = {col.lower().strip(): col for col in df.columns}

    log_secure_operation("detect_abnormal_cols", f"Columns found: {list(df.columns)}")

    # Find account name column with expanded search terms
    account_col = None
    account_search_terms = ['account', 'name', 'description', 'ledger', 'gl', 'item']
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
        if 'debit' in col_lower:
            debit_col = col_original
        if 'credit' in col_lower:
            credit_col = col_original

    log_secure_operation("detect_abnormal_mapping", f"Account: {account_col}, Debit: {debit_col}, Credit: {credit_col}")

    if account_col is None or debit_col is None or credit_col is None:
        log_secure_operation("detect_abnormal_error", "Missing required columns")
        return []

    # Convert to numeric (on the copy)
    df[debit_col] = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
    df[credit_col] = pd.to_numeric(df[credit_col], errors='coerce').fillna(0)

    for _, row in df.iterrows():
        account_name = str(row[account_col]).strip()
        account_lower = account_name.lower().strip()
        debit_amount = float(row[debit_col])
        credit_amount = float(row[credit_col])
        net_balance = debit_amount - credit_amount

        # Skip zero balances
        if abs(net_balance) < 0.01:
            continue

        # Check for asset accounts with net credit balance (abnormal)
        is_asset = any(keyword in account_lower for keyword in ASSET_KEYWORDS)
        if is_asset and net_balance < 0:
            abs_amount = abs(net_balance)
            is_material = abs_amount >= materiality_threshold
            materiality_status = "material" if is_material else "immaterial"

            if not is_material:
                log_secure_operation("indistinct_balance", f"Indistinct: {account_name} (${abs_amount:,.2f} < ${materiality_threshold:,.2f})")

            abnormal_balances.append({
                "account": account_name,
                "type": "Asset",
                "issue": "Net Credit balance (should be Debit)",
                "amount": round(abs_amount, 2),
                "debit": round(debit_amount, 2),
                "credit": round(credit_amount, 2),
                "materiality": materiality_status,
                "suggestions": [],  # Sprint 31: Legacy function, no suggestions
            })

        # Check for liability accounts with net debit balance (abnormal)
        is_liability = any(keyword in account_lower for keyword in LIABILITY_KEYWORDS)
        if is_liability and net_balance > 0:
            abs_amount = abs(net_balance)
            is_material = abs_amount >= materiality_threshold
            materiality_status = "material" if is_material else "immaterial"

            if not is_material:
                log_secure_operation("indistinct_balance", f"Indistinct: {account_name} (${abs_amount:,.2f} < ${materiality_threshold:,.2f})")

            abnormal_balances.append({
                "account": account_name,
                "type": "Liability",
                "issue": "Net Debit balance (should be Credit)",
                "amount": round(abs_amount, 2),
                "debit": round(debit_amount, 2),
                "credit": round(credit_amount, 2),
                "materiality": materiality_status,
                "suggestions": [],  # Sprint 31: Legacy function, no suggestions
            })

    material_count = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
    immaterial_count = len(abnormal_balances) - material_count
    log_secure_operation(
        "detect_abnormal_complete",
        f"Found {len(abnormal_balances)} abnormal balances ({material_count} material, {immaterial_count} indistinct)"
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
        column_mapping: Optional[ColumnMapping] = None
    ):
        self.materiality_threshold = materiality_threshold
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback

        # Weighted heuristic classifier (Day 9)
        self.classifier = classifier or create_classifier()

        # User-provided column mapping (Day 9.2 - Zero-Storage: session-only)
        self.user_column_mapping = column_mapping

        # Running totals for balance check
        self.total_debits = 0.0
        self.total_credits = 0.0
        self.total_rows = 0

        # Per-account aggregation for abnormal balance detection
        # Key: account_name, Value: {"debit": float, "credit": float}
        self.account_balances: dict[str, dict[str, float]] = {}

        # Column mapping (discovered from first chunk or user-provided)
        self.debit_col: Optional[str] = None
        self.credit_col: Optional[str] = None
        self.account_col: Optional[str] = None
        self.columns_discovered = False

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
            )

            log_secure_operation(
                "streaming_columns_user",
                f"User mapping - Account: {self.account_col}, Debit: {self.debit_col}, Credit: {self.credit_col}"
            )

            return self.debit_col is not None and self.credit_col is not None

        # Priority 2: Use intelligent column detection (Day 9.2)
        self.column_detection = detect_columns(all_columns)

        self.account_col = self.column_detection.account_column
        self.debit_col = self.column_detection.debit_column
        self.credit_col = self.column_detection.credit_column

        self.columns_discovered = True

        log_secure_operation(
            "streaming_columns_auto",
            f"Auto-detected - Account: {self.account_col} ({self.column_detection.account_confidence:.0%}), "
            f"Debit: {self.debit_col} ({self.column_detection.debit_confidence:.0%}), "
            f"Credit: {self.credit_col} ({self.column_detection.credit_confidence:.0%}), "
            f"Overall: {self.column_detection.overall_confidence:.0%}"
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
        debits = pd.to_numeric(chunk[self.debit_col], errors='coerce').fillna(0)
        credits = pd.to_numeric(chunk[self.credit_col], errors='coerce').fillna(0)

        # Update running totals
        self.total_debits += float(debits.sum())
        self.total_credits += float(credits.sum())
        self.total_rows = rows_so_far

        # Aggregate per-account balances for abnormal detection
        if self.account_col:
            for idx, row in chunk.iterrows():
                account_name = str(row[self.account_col]).strip()
                debit_val = float(debits.loc[idx]) if idx in debits.index else 0.0
                credit_val = float(credits.loc[idx]) if idx in credits.index else 0.0

                if account_name not in self.account_balances:
                    self.account_balances[account_name] = {"debit": 0.0, "credit": 0.0}

                self.account_balances[account_name]["debit"] += debit_val
                self.account_balances[account_name]["credit"] += credit_val

        self._report_progress(rows_so_far, f"Scanning rows: {rows_so_far:,}")

        # Explicit cleanup
        del debits
        del credits
        gc.collect()

    def get_balance_result(self) -> dict[str, Any]:
        """Get the balance check result after all chunks processed."""
        difference = self.total_debits - self.total_credits
        is_balanced = abs(difference) < 0.01

        return {
            "status": "success",
            "balanced": is_balanced,
            "total_debits": round(self.total_debits, 2),
            "total_credits": round(self.total_credits, 2),
            "difference": round(difference, 2),
            "row_count": self.total_rows,
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE"
        }

    def get_abnormal_balances(self) -> list[dict[str, Any]]:
        """Detect abnormal balances using weighted heuristic classification."""
        log_secure_operation(
            "streaming_abnormal",
            f"Analyzing {len(self.account_balances)} unique accounts (threshold: ${self.materiality_threshold:,.2f})"
        )

        abnormal_balances = []
        classification_stats = {"high": 0, "medium": 0, "low": 0, "unknown": 0}

        for account_name, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount

            # Skip zero balances
            if abs(net_balance) < 0.01:
                continue

            # Classify using weighted heuristics
            result = self.classifier.classify(account_name, net_balance)

            # Track classification confidence stats
            if result.category == AccountCategory.UNKNOWN:
                classification_stats["unknown"] += 1
            elif result.confidence >= 0.7:
                classification_stats["high"] += 1
            elif result.confidence >= 0.4:
                classification_stats["medium"] += 1
            else:
                classification_stats["low"] += 1

            # Only flag if abnormal AND classified (not UNKNOWN)
            if result.is_abnormal and result.category != AccountCategory.UNKNOWN:
                abs_amount = abs(net_balance)
                is_material = abs_amount >= self.materiality_threshold
                materiality_status = "material" if is_material else "immaterial"

                # Determine human-readable issue description
                expected_balance = "Debit" if result.normal_balance.value == "debit" else "Credit"
                actual_balance = "Credit" if net_balance < 0 else "Debit"

                if not is_material:
                    log_secure_operation(
                        "indistinct_balance",
                        f"Indistinct: {account_name} (${abs_amount:,.2f} < ${self.materiality_threshold:,.2f})"
                    )

                abnormal_balances.append({
                    # EXISTING FIELDS (backward compatible)
                    "account": account_name,
                    "type": CATEGORY_DISPLAY_NAMES.get(result.category, "Unknown"),
                    "issue": f"Net {actual_balance} balance (should be {expected_balance})",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status,
                    # NEW FIELDS (Day 9 - additive)
                    "category": result.category.value,
                    "confidence": result.confidence,
                    "matched_keywords": result.matched_keywords,
                    "requires_review": result.requires_review,
                    # Day 10: Anomaly categorization for Risk Dashboard
                    "anomaly_type": "natural_balance_violation",
                    "expected_balance": expected_balance.lower(),
                    "actual_balance": actual_balance.lower(),
                    "severity": "high" if is_material else "low",
                    # Sprint 31: Classification suggestions for low-confidence accounts
                    "suggestions": [
                        {
                            "category": s.category.value,
                            "confidence": s.confidence,
                            "reason": s.reason,
                            "matched_keywords": s.matched_keywords,
                        }
                        for s in result.suggestions
                    ] if result.suggestions else [],
                })

        material_count = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
        immaterial_count = len(abnormal_balances) - material_count
        log_secure_operation(
            "streaming_abnormal_complete",
            f"Found {len(abnormal_balances)} abnormal balances ({material_count} material, {immaterial_count} indistinct). "
            f"Classification: {classification_stats}"
        )

        # Store stats for response
        self._classification_stats = classification_stats

        return abnormal_balances

    def get_classification_summary(self) -> dict[str, int]:
        """Get classification confidence summary after get_abnormal_balances() is called."""
        return getattr(self, '_classification_stats', {})

    def get_classified_accounts(self) -> dict[str, str]:
        """Get classification for all accounts. Call after process_chunk."""
        classified = {}
        for account_name in self.account_balances.keys():
            balances = self.account_balances[account_name]
            net_balance = balances["debit"] - balances["credit"]
            result = self.classifier.classify(account_name, net_balance)
            classified[account_name] = result.category.value
        return classified

    def get_category_totals(self) -> CategoryTotals:
        """Extract aggregate category totals for ratio calculations."""
        classified_accounts = self.get_classified_accounts()
        return extract_category_totals(self.account_balances, classified_accounts)

    def clear(self) -> None:
        """Clear all accumulated data and force garbage collection."""
        self.account_balances.clear()
        self.total_debits = 0.0
        self.total_credits = 0.0
        self.total_rows = 0
        gc.collect()
        log_secure_operation("streaming_clear", "Auditor state cleared")


def audit_trial_balance_streaming(
    file_bytes: bytes,
    filename: str,
    materiality_threshold: float = 0.0,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    account_type_overrides: Optional[dict[str, str]] = None,
    column_mapping: Optional[dict[str, str]] = None
) -> dict[str, Any]:
    """Perform a complete streaming audit of a trial balance file."""
    log_secure_operation("streaming_audit_start", f"Starting streaming audit: {filename}")

    # Create classifier with any user overrides (Zero-Storage: session-only)
    classifier = create_classifier(account_type_overrides)
    if account_type_overrides:
        log_secure_operation(
            "classifier_overrides",
            f"Using {len(account_type_overrides)} user-provided account type overrides"
        )

    # Parse column mapping if provided (Day 9.2 - Zero-Storage: session-only)
    parsed_column_mapping: Optional[ColumnMapping] = None
    if column_mapping:
        parsed_column_mapping = ColumnMapping.from_dict(column_mapping)
        log_secure_operation(
            "column_mapping_override",
            f"Using user-provided column mapping: {column_mapping}"
        )

    auditor = StreamingAuditor(
        materiality_threshold=materiality_threshold,
        chunk_size=chunk_size,
        progress_callback=progress_callback,
        classifier=classifier,
        column_mapping=parsed_column_mapping
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

        # Add abnormal balance data to result
        result["abnormal_balances"] = abnormal_balances
        result["materiality_threshold"] = materiality_threshold
        result["material_count"] = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
        result["immaterial_count"] = len(abnormal_balances) - result["material_count"]
        result["has_risk_alerts"] = result["material_count"] > 0

        # Add classification summary (Day 9)
        result["classification_summary"] = auditor.get_classification_summary()

        # Day 10: Add risk summary for Risk Dashboard
        high_severity = sum(1 for ab in abnormal_balances if ab.get("severity") == "high")
        low_severity = len(abnormal_balances) - high_severity
        result["risk_summary"] = {
            "total_anomalies": len(abnormal_balances),
            "high_severity": high_severity,
            "low_severity": low_severity,
            "anomaly_types": {
                "natural_balance_violation": sum(
                    1 for ab in abnormal_balances
                    if ab.get("anomaly_type") == "natural_balance_violation"
                )
            }
        }

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

        log_secure_operation(
            "streaming_audit_complete",
            f"Audit complete. Rows: {result['row_count']}, Balanced: {result['balanced']}, "
            f"Material risks: {result['material_count']}, "
            f"Column confidence: {col_detection.overall_confidence:.0%}" if col_detection else "N/A"
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
    column_mapping: Optional[dict[str, str]] = None
) -> dict[str, Any]:
    """Perform a multi-sheet consolidated audit, aggregating totals across selected sheets.

    Sprint 25 Fix: Column detection now runs independently for each sheet.
    """
    log_secure_operation(
        "multi_sheet_audit_start",
        f"Starting multi-sheet audit: {filename} ({len(selected_sheets)} sheets)"
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

    try:
        for sheet_name in selected_sheets:
            log_secure_operation("multi_sheet_processing", f"Processing sheet: {sheet_name}")

            # Create a fresh auditor for each sheet (Sprint 25: independent column detection)
            auditor = StreamingAuditor(
                materiality_threshold=materiality_threshold,
                chunk_size=chunk_size,
                progress_callback=progress_callback,
                classifier=classifier,
                column_mapping=parsed_column_mapping  # User mapping overrides auto-detection
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

            # Add sheet identifier to each abnormal balance
            for ab in sheet_abnormals:
                ab["sheet_name"] = sheet_name

            # Sprint 25: Capture per-sheet column detection
            sheet_col_detection = auditor.get_column_detection()
            if sheet_col_detection:
                sheet_column_detections[sheet_name] = sheet_col_detection.to_dict()

                # Track column order for consistency check
                current_columns = (
                    sheet_col_detection.account_column,
                    sheet_col_detection.debit_column,
                    sheet_col_detection.credit_column
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

            auditor.clear()

        # Calculate consolidated balance check
        consolidated_difference = consolidated_debits - consolidated_credits
        is_consolidated_balanced = abs(consolidated_difference) < 0.01

        # Count material/immaterial
        material_count = sum(1 for ab in all_abnormal_balances if ab.get("materiality") == "material")
        immaterial_count = len(all_abnormal_balances) - material_count

        # Risk summary
        high_severity = sum(1 for ab in all_abnormal_balances if ab.get("severity") == "high")
        low_severity = len(all_abnormal_balances) - high_severity

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
            "message": "Consolidated trial balance is balanced" if is_consolidated_balanced
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
            "has_risk_alerts": material_count > 0,

            # Risk summary
            "risk_summary": {
                "total_anomalies": len(all_abnormal_balances),
                "high_severity": high_severity,
                "low_severity": low_severity,
                "anomaly_types": {
                    "natural_balance_violation": sum(
                        1 for ab in all_abnormal_balances
                        if ab.get("anomaly_type") == "natural_balance_violation"
                    )
                }
            },

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

        log_secure_operation(
            "multi_sheet_audit_complete",
            f"Consolidated audit complete. {len(selected_sheets)} sheets, "
            f"{consolidated_rows} total rows, Balanced: {is_consolidated_balanced}, "
            f"Column mismatches: {len(column_order_warnings)}"
        )

        return result

    finally:
        clear_memory()
        log_secure_operation("multi_sheet_audit_cleanup", "Memory cleared")
