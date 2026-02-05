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
from classification_rules import (
    AccountCategory,
    CATEGORY_DISPLAY_NAMES,
    SUSPENSE_KEYWORDS,
    SUSPENSE_CONFIDENCE_THRESHOLD,
    # Sprint 42: Concentration Risk
    CONCENTRATION_THRESHOLD_HIGH,
    CONCENTRATION_THRESHOLD_MEDIUM,
    CONCENTRATION_MIN_CATEGORY_TOTAL,
    CONCENTRATION_CATEGORIES,
    # Sprint 42: Rounding Anomaly
    ROUNDING_MIN_AMOUNT,
    ROUNDING_PATTERNS,
    ROUNDING_MAX_ANOMALIES,
    ROUNDING_EXCLUDE_KEYWORDS,
)
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

    # Performance optimization: Vectorized processing instead of iterrows()
    # Pre-compute all values using pandas vectorized operations
    account_names = df[account_col].astype(str).str.strip()
    account_lower = account_names.str.lower()
    debit_amounts = df[debit_col].values
    credit_amounts = df[credit_col].values
    net_balances = debit_amounts - credit_amounts

    # Vectorized keyword matching for assets and liabilities
    is_asset_mask = account_lower.apply(
        lambda x: any(keyword in x for keyword in ASSET_KEYWORDS)
    )
    is_liability_mask = account_lower.apply(
        lambda x: any(keyword in x for keyword in LIABILITY_KEYWORDS)
    )

    # Process abnormal balances using vectorized conditions
    for i in range(len(df)):
        net_balance = net_balances[i]

        # Skip zero balances
        if abs(net_balance) < 0.01:
            continue

        account_name = account_names.iloc[i]
        debit_amount = float(debit_amounts[i])
        credit_amount = float(credit_amounts[i])

        # Check for asset accounts with net credit balance (abnormal)
        if is_asset_mask.iloc[i] and net_balance < 0:
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
        if is_liability_mask.iloc[i] and net_balance > 0:
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
        # Performance optimization: Use vectorized groupby instead of iterrows()
        # This reduces O(n) row-by-row iteration to O(unique_accounts) after groupby
        if self.account_col:
            # Create temporary DataFrame for vectorized aggregation
            temp_df = pd.DataFrame({
                'account': chunk[self.account_col].astype(str).str.strip(),
                'debit': debits.values,
                'credit': credits.values
            })

            # Vectorized groupby aggregation - O(n) but highly optimized in pandas
            grouped = temp_df.groupby('account', as_index=False).agg({
                'debit': 'sum',
                'credit': 'sum'
            })

            # Merge into running totals - only iterates unique accounts (typically <500)
            for account_name, debit_sum, credit_sum in zip(
                grouped['account'], grouped['debit'], grouped['credit']
            ):
                if account_name not in self.account_balances:
                    self.account_balances[account_name] = {"debit": 0.0, "credit": 0.0}
                self.account_balances[account_name]["debit"] += float(debit_sum)
                self.account_balances[account_name]["credit"] += float(credit_sum)

            # Cleanup temporary DataFrame
            del temp_df, grouped

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
            "suspense_detection",
            f"Scanning {len(self.account_balances)} accounts for suspense indicators"
        )

        suspense_accounts: list[dict[str, Any]] = []

        for account_name, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount

            # Skip zero balances - they're cleared
            if abs(net_balance) < 0.01:
                continue

            # Check against suspense keywords
            account_lower = account_name.lower()
            matched_keywords: list[str] = []
            total_weight = 0.0

            for keyword, weight, is_phrase in SUSPENSE_KEYWORDS:
                if is_phrase:
                    # Phrase must match exactly (word boundaries)
                    if keyword in account_lower:
                        matched_keywords.append(keyword)
                        total_weight += weight
                else:
                    # Single word can be part of compound
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

                # Get classification for context
                result = self.classifier.classify(account_name, net_balance)

                suspense_accounts.append({
                    "account": account_name,
                    "type": CATEGORY_DISPLAY_NAMES.get(result.category, "Unknown"),
                    "issue": "Suspense/clearing account with outstanding balance",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status,
                    "category": result.category.value,
                    "confidence": confidence,
                    "matched_keywords": matched_keywords,
                    "requires_review": True,  # Suspense accounts always need review
                    "anomaly_type": "suspense_account",
                    "expected_balance": "zero",
                    "actual_balance": "debit" if net_balance > 0 else "credit",
                    "severity": "high" if is_material else "medium",  # Suspense is at least medium
                    "suggestions": [],
                    "recommendation": (
                        "Investigate and clear this suspense account. "
                        "Determine proper classification for the outstanding balance."
                    ),
                })

        log_secure_operation(
            "suspense_detection_complete",
            f"Found {len(suspense_accounts)} suspense accounts with balances"
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
            "concentration_detection",
            f"Analyzing {len(self.account_balances)} accounts for concentration risk"
        )

        concentration_risks: list[dict[str, Any]] = []

        # Group accounts by category and calculate totals
        category_accounts: dict[AccountCategory, list[tuple[str, float, float, float]]] = {
            cat: [] for cat in CONCENTRATION_CATEGORIES
        }
        category_totals: dict[AccountCategory, float] = {
            cat: 0.0 for cat in CONCENTRATION_CATEGORIES
        }

        for account_name, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount

            # Skip zero balances
            if abs(net_balance) < 0.01:
                continue

            # Classify the account
            result = self.classifier.classify(account_name, net_balance)

            if result.category in CONCENTRATION_CATEGORIES:
                abs_balance = abs(net_balance)
                category_accounts[result.category].append(
                    (account_name, abs_balance, debit_amount, credit_amount)
                )
                category_totals[result.category] += abs_balance

        # Analyze concentration for each category
        for category in CONCENTRATION_CATEGORIES:
            total = category_totals[category]

            # Skip categories below minimum threshold
            if total < CONCENTRATION_MIN_CATEGORY_TOTAL:
                continue

            for account_name, abs_balance, debit_amount, credit_amount in category_accounts[category]:
                concentration_pct = abs_balance / total

                # Determine severity based on concentration level
                severity = None
                if concentration_pct >= CONCENTRATION_THRESHOLD_HIGH:
                    severity = "high"
                elif concentration_pct >= CONCENTRATION_THRESHOLD_MEDIUM:
                    severity = "medium"

                if severity:
                    is_material = abs_balance >= self.materiality_threshold
                    materiality_status = "material" if is_material else "immaterial"

                    concentration_risks.append({
                        "account": account_name,
                        "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                        "issue": f"Represents {concentration_pct:.1%} of total {category.value}s",
                        "amount": round(abs_balance, 2),
                        "debit": round(debit_amount, 2),
                        "credit": round(credit_amount, 2),
                        "materiality": materiality_status,
                        "category": category.value,
                        "confidence": concentration_pct,  # Use concentration % as confidence
                        "matched_keywords": [],
                        "requires_review": True,
                        "anomaly_type": "concentration_risk",
                        "concentration_percent": round(concentration_pct * 100, 1),
                        "category_total": round(total, 2),
                        "severity": severity,
                        "suggestions": [],
                        "recommendation": (
                            f"This account represents {concentration_pct:.1%} of total {category.value}s. "
                            "Review for over-reliance on a single counterparty and consider "
                            "the impact if this balance becomes uncollectible or disputed."
                        ),
                    })

        # Sort by concentration percentage (highest first)
        concentration_risks.sort(key=lambda x: x["concentration_percent"], reverse=True)

        log_secure_operation(
            "concentration_detection_complete",
            f"Found {len(concentration_risks)} concentration risk accounts"
        )

        return concentration_risks

    def detect_rounding_anomalies(self) -> list[dict[str, Any]]:
        """
        Detect suspicious round numbers that may indicate estimation or manipulation.

        Sprint 42 - Phase III: Rounding Anomaly Detection

        Round numbers in financial data may indicate:
        - Estimates rather than actual transactions
        - Journal entry manipulation or fraud
        - Placeholder amounts awaiting final figures
        - Accrual reversals or adjustments

        Note: Not all round numbers are suspicious. Loans, capital transactions,
        and certain contracts legitimately use round amounts.

        Returns:
            List of rounding anomalies with pattern type and severity
        """
        log_secure_operation(
            "rounding_detection",
            f"Analyzing {len(self.account_balances)} accounts for rounding anomalies"
        )

        rounding_anomalies: list[dict[str, Any]] = []

        for account_name, balances in self.account_balances.items():
            debit_amount = balances["debit"]
            credit_amount = balances["credit"]
            net_balance = debit_amount - credit_amount
            abs_balance = abs(net_balance)

            # Skip amounts below minimum threshold
            if abs_balance < ROUNDING_MIN_AMOUNT:
                continue

            # Check if account should be excluded (legitimate round amounts)
            account_lower = account_name.lower()
            is_excluded = any(
                keyword in account_lower for keyword in ROUNDING_EXCLUDE_KEYWORDS
            )
            if is_excluded:
                continue

            # Check against rounding patterns (most significant first)
            for divisor, pattern_name, pattern_severity in ROUNDING_PATTERNS:
                # Check if amount is exactly divisible (within small tolerance for floats)
                remainder = abs_balance % divisor
                is_round = remainder < 0.01 or (divisor - remainder) < 0.01

                if is_round:
                    # Classify the account for context
                    result = self.classifier.classify(account_name, net_balance)
                    is_material = abs_balance >= self.materiality_threshold
                    materiality_status = "material" if is_material else "immaterial"

                    # Format the round amount description
                    if divisor >= 100000:
                        round_desc = f"${abs_balance / 1000:,.0f}K"
                    else:
                        round_desc = f"${abs_balance:,.0f}"

                    rounding_anomalies.append({
                        "account": account_name,
                        "type": CATEGORY_DISPLAY_NAMES.get(result.category, "Unknown"),
                        "issue": f"Exactly round amount: {round_desc}",
                        "amount": round(abs_balance, 2),
                        "debit": round(debit_amount, 2),
                        "credit": round(credit_amount, 2),
                        "materiality": materiality_status,
                        "category": result.category.value,
                        "confidence": 0.7 if pattern_severity == "high" else 0.5,
                        "matched_keywords": [],
                        "requires_review": True,
                        "anomaly_type": "rounding_anomaly",
                        "rounding_pattern": pattern_name,
                        "rounding_divisor": divisor,
                        "severity": pattern_severity if is_material else "low",
                        "suggestions": [],
                        "recommendation": (
                            f"This balance is an exactly round number ({round_desc}). "
                            "Verify this represents an actual transaction amount and not "
                            "an estimate, placeholder, or potential journal entry manipulation."
                        ),
                    })

                    # Only flag the most significant pattern match
                    break

        # Sort by amount (highest first) and limit results
        rounding_anomalies.sort(key=lambda x: x["amount"], reverse=True)
        if len(rounding_anomalies) > ROUNDING_MAX_ANOMALIES:
            rounding_anomalies = rounding_anomalies[:ROUNDING_MAX_ANOMALIES]

        log_secure_operation(
            "rounding_detection_complete",
            f"Found {len(rounding_anomalies)} rounding anomalies"
        )

        return rounding_anomalies

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

        # Sprint 41: Detect suspense accounts
        suspense_accounts = auditor.detect_suspense_accounts()

        # Merge suspense accounts into abnormal balances
        # (avoiding duplicates - suspense accounts that are also abnormal balance violations)
        existing_accounts = {ab["account"] for ab in abnormal_balances}
        for suspense in suspense_accounts:
            if suspense["account"] not in existing_accounts:
                abnormal_balances.append(suspense)
            else:
                # Account already flagged - add suspense indicator to existing entry
                for ab in abnormal_balances:
                    if ab["account"] == suspense["account"]:
                        ab["is_suspense_account"] = True
                        ab["suspense_confidence"] = suspense["confidence"]
                        ab["suspense_keywords"] = suspense["matched_keywords"]
                        # Elevate severity if it was low
                        if ab.get("severity") == "low":
                            ab["severity"] = "medium"
                        break

        # Sprint 42: Detect concentration risk
        concentration_risks = auditor.detect_concentration_risk()

        # Merge concentration risks into abnormal balances (avoiding duplicates)
        existing_accounts = {ab["account"] for ab in abnormal_balances}
        for conc in concentration_risks:
            if conc["account"] not in existing_accounts:
                abnormal_balances.append(conc)
                existing_accounts.add(conc["account"])
            else:
                # Account already flagged - add concentration indicator
                for ab in abnormal_balances:
                    if ab["account"] == conc["account"]:
                        ab["has_concentration_risk"] = True
                        ab["concentration_percent"] = conc["concentration_percent"]
                        ab["category_total"] = conc["category_total"]
                        break

        # Sprint 42: Detect rounding anomalies
        rounding_anomalies = auditor.detect_rounding_anomalies()

        # Merge rounding anomalies into abnormal balances (avoiding duplicates)
        for rounding in rounding_anomalies:
            if rounding["account"] not in existing_accounts:
                abnormal_balances.append(rounding)
                existing_accounts.add(rounding["account"])
            else:
                # Account already flagged - add rounding indicator
                for ab in abnormal_balances:
                    if ab["account"] == rounding["account"]:
                        ab["has_rounding_anomaly"] = True
                        ab["rounding_pattern"] = rounding["rounding_pattern"]
                        break

        # Add abnormal balance data to result
        result["abnormal_balances"] = abnormal_balances
        result["materiality_threshold"] = materiality_threshold
        result["material_count"] = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
        result["immaterial_count"] = len(abnormal_balances) - result["material_count"]
        result["has_risk_alerts"] = result["material_count"] > 0

        # Add classification summary (Day 9)
        result["classification_summary"] = auditor.get_classification_summary()

        # Day 10: Add risk summary for Risk Dashboard
        # Sprint 41-42: Include all anomaly type counts
        high_severity = sum(1 for ab in abnormal_balances if ab.get("severity") == "high")
        medium_severity = sum(1 for ab in abnormal_balances if ab.get("severity") == "medium")
        low_severity = len(abnormal_balances) - high_severity - medium_severity
        suspense_count = sum(
            1 for ab in abnormal_balances
            if ab.get("anomaly_type") == "suspense_account" or ab.get("is_suspense_account")
        )
        concentration_count = sum(
            1 for ab in abnormal_balances
            if ab.get("anomaly_type") == "concentration_risk" or ab.get("has_concentration_risk")
        )
        rounding_count = sum(
            1 for ab in abnormal_balances
            if ab.get("anomaly_type") == "rounding_anomaly" or ab.get("has_rounding_anomaly")
        )
        result["risk_summary"] = {
            "total_anomalies": len(abnormal_balances),
            "high_severity": high_severity,
            "medium_severity": medium_severity,
            "low_severity": low_severity,
            "anomaly_types": {
                "natural_balance_violation": sum(
                    1 for ab in abnormal_balances
                    if ab.get("anomaly_type") == "natural_balance_violation"
                ),
                "suspense_account": suspense_count,
                "concentration_risk": concentration_count,
                "rounding_anomaly": rounding_count,
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

            # Sprint 41: Detect suspense accounts for this sheet
            sheet_suspense = auditor.detect_suspense_accounts()

            # Merge suspense accounts into sheet abnormals (avoiding duplicates)
            existing_accounts = {ab["account"] for ab in sheet_abnormals}
            for suspense in sheet_suspense:
                if suspense["account"] not in existing_accounts:
                    sheet_abnormals.append(suspense)
                    existing_accounts.add(suspense["account"])
                else:
                    # Account already flagged - add suspense indicator
                    for ab in sheet_abnormals:
                        if ab["account"] == suspense["account"]:
                            ab["is_suspense_account"] = True
                            ab["suspense_confidence"] = suspense["confidence"]
                            ab["suspense_keywords"] = suspense["matched_keywords"]
                            if ab.get("severity") == "low":
                                ab["severity"] = "medium"
                            break

            # Sprint 42: Detect concentration risk for this sheet
            sheet_concentration = auditor.detect_concentration_risk()
            for conc in sheet_concentration:
                if conc["account"] not in existing_accounts:
                    sheet_abnormals.append(conc)
                    existing_accounts.add(conc["account"])
                else:
                    for ab in sheet_abnormals:
                        if ab["account"] == conc["account"]:
                            ab["has_concentration_risk"] = True
                            ab["concentration_percent"] = conc["concentration_percent"]
                            ab["category_total"] = conc["category_total"]
                            break

            # Sprint 42: Detect rounding anomalies for this sheet
            sheet_rounding = auditor.detect_rounding_anomalies()
            for rounding in sheet_rounding:
                if rounding["account"] not in existing_accounts:
                    sheet_abnormals.append(rounding)
                    existing_accounts.add(rounding["account"])
                else:
                    for ab in sheet_abnormals:
                        if ab["account"] == rounding["account"]:
                            ab["has_rounding_anomaly"] = True
                            ab["rounding_pattern"] = rounding["rounding_pattern"]
                            break

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

        # Risk summary (Sprint 41-42: include all anomaly type counts)
        high_severity = sum(1 for ab in all_abnormal_balances if ab.get("severity") == "high")
        medium_severity = sum(1 for ab in all_abnormal_balances if ab.get("severity") == "medium")
        low_severity = len(all_abnormal_balances) - high_severity - medium_severity
        suspense_count = sum(
            1 for ab in all_abnormal_balances
            if ab.get("anomaly_type") == "suspense_account" or ab.get("is_suspense_account")
        )
        concentration_count = sum(
            1 for ab in all_abnormal_balances
            if ab.get("anomaly_type") == "concentration_risk" or ab.get("has_concentration_risk")
        )
        rounding_count = sum(
            1 for ab in all_abnormal_balances
            if ab.get("anomaly_type") == "rounding_anomaly" or ab.get("has_rounding_anomaly")
        )

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

            # Risk summary (Sprint 41-42: include all anomaly type counts)
            "risk_summary": {
                "total_anomalies": len(all_abnormal_balances),
                "high_severity": high_severity,
                "medium_severity": medium_severity,
                "low_severity": low_severity,
                "anomaly_types": {
                    "natural_balance_violation": sum(
                        1 for ab in all_abnormal_balances
                        if ab.get("anomaly_type") == "natural_balance_violation"
                    ),
                    "suspense_account": suspense_count,
                    "concentration_risk": concentration_count,
                    "rounding_anomaly": rounding_count,
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
