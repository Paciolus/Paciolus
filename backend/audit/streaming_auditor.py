"""Memory-efficient streaming auditor that processes trial balances in chunks.

The ``StreamingAuditor`` class accumulates per-account balances across
arbitrarily many DataFrame chunks, discovers column mappings on the first
chunk, and exposes detection methods that delegate to the pure functions
in ``audit.anomaly_rules``.  It is the stateful backbone of both the
single-sheet and multi-sheet audit pipelines.
"""

from __future__ import annotations

import gc
import math
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Optional

import pandas as pd

from account_classifier import AccountClassifier, create_classifier
from audit.anomaly_rules import (
    detect_abnormal_balances_streaming,
)
from audit.anomaly_rules import (
    detect_concentration_risk as _detect_concentration_risk,
)
from audit.anomaly_rules import (
    detect_equity_signals as _detect_equity_signals,
)
from audit.anomaly_rules import (
    detect_expense_concentration as _detect_expense_concentration,
)
from audit.anomaly_rules import (
    detect_intercompany_imbalances as _detect_intercompany_imbalances,
)
from audit.anomaly_rules import (
    detect_related_party_accounts as _detect_related_party_accounts,
)
from audit.anomaly_rules import (
    detect_revenue_concentration as _detect_revenue_concentration,
)
from audit.anomaly_rules import (
    detect_rounding_anomalies as _detect_rounding_anomalies,
)
from audit.anomaly_rules import (
    detect_suspense_accounts as _detect_suspense_accounts,
)
from audit.classification import (
    build_display_name,
    resolve_category,
    resolve_csv_type,
    validate_balance_sheet_equation,
)
from classification_rules import (
    ROUND_NUMBER_TIER1_SUPPRESS,
    AccountCategory,
)
from column_detector import ColumnDetectionResult, ColumnMapping, detect_columns
from ratio_engine import CategoryTotals, extract_category_totals
from security_utils import DEFAULT_CHUNK_SIZE, log_secure_operation
from shared.monetary import BALANCE_TOLERANCE, quantize_monetary


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
        self.provided_account_types: dict[str, str] = {}
        self.provided_account_names: dict[str, str] = {}
        # Sprint 535: Provided account subtypes from CSV "subtype" column
        self.provided_account_subtypes: dict[str, str] = {}

        # Column detection result (Day 9.2)
        self.column_detection: Optional[ColumnDetectionResult] = None

        # Legacy backward-compat attributes
        self._CSV_TYPE_MAP = None  # resolved via audit.classification
        self._CSV_TYPE_SUFFIXES = None
        self._csv_type_log_count: int = 0
        self._ROUNDING_TIER1_KEYWORDS: list[str] = ROUND_NUMBER_TIER1_SUPPRESS
        self._ROUNDING_TIER1_CATEGORIES: set[str] = set()
        self._ROUNDING_TIER3_KEYWORDS: list[str] = [
            "suspense",
            "clearing",
            "miscellaneous",
            "sundry",
            "unallocated",
            "unclassified",
        ]

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
            col_map_lower = {col.lower().strip(): col for col in all_columns}

            user_acc = self.user_column_mapping.account_column.lower().strip()
            user_deb = self.user_column_mapping.debit_column.lower().strip()
            user_cred = self.user_column_mapping.credit_column.lower().strip()

            self.account_col = col_map_lower.get(user_acc)
            self.debit_col = col_map_lower.get(user_deb)
            self.credit_col = col_map_lower.get(user_cred)

            self.columns_discovered = True

            supplementary = detect_columns(all_columns)
            self.account_type_col = supplementary.account_type_column
            self.account_name_col = supplementary.account_name_column

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
        chunk.columns = chunk.columns.str.strip()

        if not self._discover_columns(chunk):
            log_secure_operation("streaming_error", "Required columns not found")
            return

        debits = pd.to_numeric(chunk[self.debit_col], errors="coerce").fillna(0)
        credits = pd.to_numeric(chunk[self.credit_col], errors="coerce").fillna(0)

        self._debit_chunks.append(math.fsum(debits.values))
        self._credit_chunks.append(math.fsum(credits.values))
        self.total_rows = rows_so_far

        if self.account_col:
            temp_df = pd.DataFrame(
                {
                    "account": chunk[self.account_col].astype(str).str.strip(),
                    "debit": debits.values,
                    "credit": credits.values,
                }
            )

            grouped = temp_df.groupby("account", as_index=False).agg({"debit": "sum", "credit": "sum"})

            for account_name, debit_sum, credit_sum in zip(grouped["account"], grouped["debit"], grouped["credit"]):
                if account_name not in self.account_balances:
                    self.account_balances[account_name] = {"debit": Decimal("0"), "credit": Decimal("0")}
                self.account_balances[account_name]["debit"] += Decimal(str(debit_sum))
                self.account_balances[account_name]["credit"] += Decimal(str(credit_sum))

            # Sprint 526: Extract account_type values
            if self.account_type_col and self.account_type_col in chunk.columns:
                for acct_key, acct_type in zip(
                    chunk[self.account_col].astype(str).str.strip(),
                    chunk[self.account_type_col].astype(str).str.strip(),
                ):
                    if acct_key and acct_type and acct_type.lower() not in ("", "nan", "none"):
                        self.provided_account_types[acct_key] = acct_type

            # Sprint 526: Extract account_name values
            if self.account_name_col and self.account_name_col in chunk.columns:
                for acct_key, acct_name in zip(
                    chunk[self.account_col].astype(str).str.strip(),
                    chunk[self.account_name_col].astype(str).str.strip(),
                ):
                    if acct_key and acct_name and acct_name.lower() not in ("", "nan", "none"):
                        self.provided_account_names[acct_key] = acct_name

            # Sprint 535: Extract subtype values
            if not hasattr(self, "_subtype_col_resolved"):
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

            del temp_df, grouped

        self._report_progress(rows_so_far, f"Scanning rows: {rows_so_far:,}")

        del debits
        del credits
        gc.collect()

    def _finalize_balances(self) -> None:
        """Convert accumulated Decimal balances to float for downstream rule compatibility."""
        for acct, bals in self.account_balances.items():
            if isinstance(bals["debit"], Decimal):
                bals["debit"] = float(bals["debit"])
            if isinstance(bals["credit"], Decimal):
                bals["credit"] = float(bals["credit"])

    def get_balance_result(self) -> dict[str, Any]:
        """Get the balance check result after all chunks processed."""
        self._finalize_balances()
        total_debits = math.fsum(self._debit_chunks)
        total_credits = math.fsum(self._credit_chunks)
        difference = total_debits - total_credits
        is_balanced = abs(Decimal(str(difference))) < BALANCE_TOLERANCE

        return {
            "status": "success",
            "balanced": is_balanced,
            "total_debits": str(quantize_monetary(total_debits)),
            "total_credits": str(quantize_monetary(total_credits)),
            "difference": str(quantize_monetary(difference)),
            "row_count": self.total_rows,
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Trial balance is balanced" if is_balanced else "Trial balance is OUT OF BALANCE",
        }

    # ── Anomaly detection: delegate to pure functions in anomaly_rules ──

    def get_abnormal_balances(self) -> list[dict[str, Any]]:
        """Detect abnormal balances using CSV-provided types or weighted heuristic classification."""
        abnormal_balances, classification_stats = detect_abnormal_balances_streaming(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )
        self._classification_stats = classification_stats
        return abnormal_balances

    def get_classification_summary(self) -> dict[str, int]:
        """Get classification confidence summary after get_abnormal_balances() is called."""
        return getattr(self, "_classification_stats", {})

    def detect_suspense_accounts(self) -> list[dict[str, Any]]:
        """Detect suspense and clearing accounts with outstanding balances."""
        return _detect_suspense_accounts(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )

    def detect_concentration_risk(self) -> list[dict[str, Any]]:
        """Detect accounts with unusually high concentration within their category."""
        return _detect_concentration_risk(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )

    def detect_rounding_anomalies(self) -> list[dict[str, Any]]:
        """Detect suspicious round numbers that may indicate estimation or manipulation."""
        return _detect_rounding_anomalies(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
            self.provided_account_subtypes,
        )

    def detect_related_party_accounts(self) -> list[dict[str, Any]]:
        """Detect accounts indicating related party activity."""
        return _detect_related_party_accounts(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )

    def detect_intercompany_imbalances(self) -> list[dict[str, Any]]:
        """Detect intercompany accounts with elimination gaps."""
        return _detect_intercompany_imbalances(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )

    def detect_equity_signals(self) -> list[dict[str, Any]]:
        """Detect abnormal equity patterns."""
        return _detect_equity_signals(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )

    def detect_revenue_concentration(self) -> list[dict[str, Any]]:
        """Revenue concentration analysis."""
        return _detect_revenue_concentration(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )

    def detect_expense_concentration(self) -> list[dict[str, Any]]:
        """Expense concentration analysis."""
        return _detect_expense_concentration(
            self.account_balances,
            self.materiality_threshold,
            self.classifier,
            self.provided_account_types,
            self.provided_account_names,
        )

    # ── Classification helpers (delegate to audit.classification) ─────

    def _resolve_csv_type(self, raw_value: str) -> tuple[AccountCategory | None, float]:
        """Resolve a raw CSV account type value to a category and confidence."""
        return resolve_csv_type(raw_value)

    def _resolve_category(self, account_key: str, net_balance: float = 0.0) -> AccountCategory:
        """Resolve the account category -- CSV-provided type takes priority over heuristic."""
        return resolve_category(
            account_key,
            net_balance,
            self.provided_account_types,
            self.provided_account_names,
            self.classifier,
        )

    def _display_name(self, account_key: str) -> str:
        """Build display name: '[code] -- [name]' when account_name column is available."""
        return build_display_name(account_key, self.provided_account_names)

    def _is_balance_abnormal(self, category: AccountCategory, net_balance: float, account_name: str = "") -> bool:
        """Check if balance direction is abnormal for the given category."""
        from audit.classification import is_balance_abnormal

        return is_balance_abnormal(category, net_balance, account_name)

    def get_classified_accounts(self) -> dict[str, str]:
        """Get classification for all accounts. Call after process_chunk."""
        classified = {}
        for account_name in self.account_balances.keys():
            balances = self.account_balances[account_name]
            net_balance = balances["debit"] - balances["credit"]
            category = self._resolve_category(account_name, net_balance)
            classified[account_name] = category.value
        return classified

    def get_category_totals(self, classified_accounts: dict[str, str] | None = None) -> CategoryTotals:
        """Extract aggregate category totals for ratio calculations.

        Args:
            classified_accounts: Pre-computed account classifications. When
                provided the internal ``get_classified_accounts()`` call is
                skipped, avoiding a redundant O(n) pass over all accounts.
        """
        log_secure_operation("DEPLOY-VERIFY-535", "get_category_totals invoked")

        if classified_accounts is None:
            classified_accounts = self.get_classified_accounts()

        display_balances: dict[str, dict[str, float]] = {}
        display_classifications: dict[str, str] = {}
        display_subtypes: dict[str, str] = {}

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
        """Validate the fundamental accounting equation: Assets = Liabilities + Equity."""
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
