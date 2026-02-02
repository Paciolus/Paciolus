"""
CloseSignify Audit Engine
Trial Balance Analysis and Validation

Supports chunked streaming for memory-efficient processing of large files.
"""

import gc
from datetime import datetime
from typing import Any, Callable, Optional, Generator
import pandas as pd

from security_utils import (
    log_secure_operation,
    process_tb_chunked,
    clear_memory,
    DEFAULT_CHUNK_SIZE
)


# Account type keyword mappings for abnormal balance detection
ASSET_KEYWORDS = ['cash', 'bank', 'receivable', 'inventory', 'prepaid', 'equipment', 'land', 'building', 'vehicle']
LIABILITY_KEYWORDS = ['payable', 'loan', 'tax', 'accrued', 'unearned', 'deferred', 'debt', 'mortgage', 'note payable']


def check_balance(df: pd.DataFrame) -> dict[str, Any]:
    """
    Check if a trial balance is balanced.
    Sum of Debits should equal Sum of Credits.

    Args:
        df: DataFrame containing trial balance with 'Debit' and 'Credit' columns

    Returns:
        JSON report with totals and pass/fail status
    """
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
            "timestamp": datetime.utcnow().isoformat(),
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
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE"
    }


def detect_abnormal_balances(df: pd.DataFrame, materiality_threshold: float = 0.0) -> list[dict[str, Any]]:
    """
    Detect accounts with abnormal balance directions.

    Assets (Cash, Bank, Receivable, Inventory) should have net Debit balances.
    Liabilities (Payable, Loan, Tax) should have net Credit balances.

    Args:
        df: DataFrame containing trial balance data
        materiality_threshold: Dollar amount threshold for materiality classification.
            Balances >= threshold are "material", below are "immaterial" (Indistinct).

    Returns:
        List of flagged accounts with abnormal balances and materiality classification
    """
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
                "materiality": materiality_status
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
                "materiality": materiality_status
            })

    material_count = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
    immaterial_count = len(abnormal_balances) - material_count
    log_secure_operation(
        "detect_abnormal_complete",
        f"Found {len(abnormal_balances)} abnormal balances ({material_count} material, {immaterial_count} indistinct)"
    )

    return abnormal_balances


# =============================================================================
# STREAMING / CHUNKED PROCESSING FUNCTIONS
# =============================================================================

class StreamingAuditor:
    """
    Memory-efficient streaming auditor for large trial balance files.
    Processes data in chunks while maintaining running totals and
    per-account aggregations for abnormal balance detection.
    """

    def __init__(
        self,
        materiality_threshold: float = 0.0,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ):
        """
        Initialize the streaming auditor.

        Args:
            materiality_threshold: Dollar threshold for materiality classification
            chunk_size: Rows per chunk for processing
            progress_callback: Optional callback(rows_processed, status_message)
        """
        self.materiality_threshold = materiality_threshold
        self.chunk_size = chunk_size
        self.progress_callback = progress_callback

        # Running totals for balance check
        self.total_debits = 0.0
        self.total_credits = 0.0
        self.total_rows = 0

        # Per-account aggregation for abnormal balance detection
        # Key: account_name, Value: {"debit": float, "credit": float}
        self.account_balances: dict[str, dict[str, float]] = {}

        # Column mapping (discovered from first chunk)
        self.debit_col: Optional[str] = None
        self.credit_col: Optional[str] = None
        self.account_col: Optional[str] = None
        self.columns_discovered = False

    def _report_progress(self, rows: int, message: str) -> None:
        """Report progress via callback if available."""
        if self.progress_callback:
            self.progress_callback(rows, message)

    def _discover_columns(self, df: pd.DataFrame) -> bool:
        """
        Discover and cache column mappings from the first chunk.
        Returns True if required columns found, False otherwise.
        """
        if self.columns_discovered:
            return True

        df.columns = df.columns.str.strip()
        column_map = {col.lower().strip(): col for col in df.columns}

        # Find debit and credit columns
        for col_lower, col_original in column_map.items():
            if 'debit' in col_lower and self.debit_col is None:
                self.debit_col = col_original
            if 'credit' in col_lower and self.credit_col is None:
                self.credit_col = col_original

        # Find account column
        account_search_terms = ['account', 'name', 'description', 'ledger', 'gl', 'item']
        for col_lower, col_original in column_map.items():
            if any(term in col_lower for term in account_search_terms):
                self.account_col = col_original
                break

        # Fallback: use first column as account
        if self.account_col is None and len(df.columns) > 0:
            self.account_col = df.columns[0]

        self.columns_discovered = True

        log_secure_operation(
            "streaming_columns",
            f"Discovered columns - Account: {self.account_col}, Debit: {self.debit_col}, Credit: {self.credit_col}"
        )

        return self.debit_col is not None and self.credit_col is not None

    def process_chunk(self, chunk: pd.DataFrame, rows_so_far: int) -> None:
        """
        Process a single chunk, updating running totals and account aggregations.

        Args:
            chunk: DataFrame chunk to process
            rows_so_far: Cumulative rows processed so far
        """
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
        """
        Get the balance check result after all chunks processed.
        Returns the same format as the original check_balance function.
        """
        difference = self.total_debits - self.total_credits
        is_balanced = abs(difference) < 0.01

        return {
            "status": "success",
            "balanced": is_balanced,
            "total_debits": round(self.total_debits, 2),
            "total_credits": round(self.total_credits, 2),
            "difference": round(difference, 2),
            "row_count": self.total_rows,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE"
        }

    def get_abnormal_balances(self) -> list[dict[str, Any]]:
        """
        Detect abnormal balances from aggregated account data.
        Returns the same format as the original detect_abnormal_balances function.
        """
        log_secure_operation(
            "streaming_abnormal",
            f"Analyzing {len(self.account_balances)} unique accounts (threshold: ${self.materiality_threshold:,.2f})"
        )

        abnormal_balances = []

        for account_name, balances in self.account_balances.items():
            account_lower = account_name.lower().strip()
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount

            # Skip zero balances
            if abs(net_balance) < 0.01:
                continue

            # Check for asset accounts with net credit balance (abnormal)
            is_asset = any(keyword in account_lower for keyword in ASSET_KEYWORDS)
            if is_asset and net_balance < 0:
                abs_amount = abs(net_balance)
                is_material = abs_amount >= self.materiality_threshold
                materiality_status = "material" if is_material else "immaterial"

                if not is_material:
                    log_secure_operation(
                        "indistinct_balance",
                        f"Indistinct: {account_name} (${abs_amount:,.2f} < ${self.materiality_threshold:,.2f})"
                    )

                abnormal_balances.append({
                    "account": account_name,
                    "type": "Asset",
                    "issue": "Net Credit balance (should be Debit)",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status
                })

            # Check for liability accounts with net debit balance (abnormal)
            is_liability = any(keyword in account_lower for keyword in LIABILITY_KEYWORDS)
            if is_liability and net_balance > 0:
                abs_amount = abs(net_balance)
                is_material = abs_amount >= self.materiality_threshold
                materiality_status = "material" if is_material else "immaterial"

                if not is_material:
                    log_secure_operation(
                        "indistinct_balance",
                        f"Indistinct: {account_name} (${abs_amount:,.2f} < ${self.materiality_threshold:,.2f})"
                    )

                abnormal_balances.append({
                    "account": account_name,
                    "type": "Liability",
                    "issue": "Net Debit balance (should be Credit)",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status
                })

        material_count = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
        immaterial_count = len(abnormal_balances) - material_count
        log_secure_operation(
            "streaming_abnormal_complete",
            f"Found {len(abnormal_balances)} abnormal balances ({material_count} material, {immaterial_count} indistinct)"
        )

        return abnormal_balances

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
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> dict[str, Any]:
    """
    Perform a complete streaming audit of a trial balance file.
    Memory-efficient: processes file in chunks, never loading entire file.

    Args:
        file_bytes: Raw bytes of the uploaded file
        filename: Original filename to determine format
        materiality_threshold: Dollar threshold for materiality classification
        chunk_size: Rows per chunk for processing
        progress_callback: Optional callback(rows_processed, status_message)

    Returns:
        Complete audit result dictionary (same format as non-streaming version)
    """
    log_secure_operation("streaming_audit_start", f"Starting streaming audit: {filename}")

    auditor = StreamingAuditor(
        materiality_threshold=materiality_threshold,
        chunk_size=chunk_size,
        progress_callback=progress_callback
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

        log_secure_operation(
            "streaming_audit_complete",
            f"Audit complete. Rows: {result['row_count']}, Balanced: {result['balanced']}, "
            f"Material risks: {result['material_count']}"
        )

        return result

    finally:
        # Ensure cleanup regardless of success/failure
        auditor.clear()
        clear_memory()
        log_secure_operation("streaming_audit_cleanup", "Memory cleared")
