"""
Paciolus — Data Quality Pre-Flight Engine
Sprint 283: Phase XXXVIII
Sprint 510: Balance check, score breakdown, affected items, tests_affected

Lightweight data quality assessment that runs on a Trial Balance file
BEFORE the full TB diagnostic. Gives users immediate feedback on column
detection, null values, duplicates, encoding issues, and sign conventions.

Pure-Python engine (no Pandas). Takes parsed data from parse_uploaded_file().
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from column_detector import (
    ColumnDetectionResult,
    detect_columns,
)
from shared.parsing_helpers import safe_decimal

# ═══════════════════════════════════════════════════════════════
# Dataclasses
# ═══════════════════════════════════════════════════════════════


@dataclass
class ColumnQuality:
    """Detection confidence for a single column role."""

    role: str  # "account", "debit", "credit"
    detected_name: str | None
    confidence: float
    status: str  # "found", "low_confidence", "missing"


@dataclass
class DuplicateEntry:
    """A group of duplicate account codes."""

    account_code: str
    count: int


@dataclass
class EncodingAnomaly:
    """An account name with non-ASCII characters."""

    row_index: int
    value: str
    column: str


@dataclass
class MixedSignAccount:
    """An account with both positive and negative values in debit column."""

    account: str
    positive_count: int
    negative_count: int


@dataclass
class BalanceCheck:
    """Result of the TB debit/credit balance verification."""

    total_debits: float
    total_credits: float
    difference: float
    balanced: bool
    tolerance: float = 0.01


@dataclass
class ScoreComponent:
    """A single component of the readiness score breakdown."""

    component: str
    weight: float  # 0-1 (e.g. 0.25 for 25%)
    score: float  # 0-100
    contribution: float  # weight * score


@dataclass
class PreFlightIssue:
    """A single pre-flight quality issue."""

    category: str  # column_detection, null_values, duplicates, encoding, mixed_signs, zero_balance
    severity: str  # "high", "medium", "low"
    message: str
    affected_count: int
    remediation: str
    downstream_impact: str = ""
    affected_items: list[str] = field(default_factory=list)
    tests_affected: int = 0


@dataclass
class PreFlightReport:
    """Complete pre-flight quality assessment."""

    filename: str
    row_count: int
    column_count: int
    readiness_score: float  # 0-100
    readiness_label: str  # "Ready", "Review Recommended", "Issues Found"
    columns: list[ColumnQuality] = field(default_factory=list)
    issues: list[PreFlightIssue] = field(default_factory=list)
    duplicates: list[DuplicateEntry] = field(default_factory=list)
    encoding_anomalies: list[EncodingAnomaly] = field(default_factory=list)
    mixed_sign_accounts: list[MixedSignAccount] = field(default_factory=list)
    zero_balance_count: int = 0
    null_counts: dict[str, int] = field(default_factory=dict)
    balance_check: BalanceCheck | None = None
    score_breakdown: list[ScoreComponent] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {
            "filename": self.filename,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "readiness_score": round(self.readiness_score, 1),
            "readiness_label": self.readiness_label,
            "columns": [
                {
                    "role": c.role,
                    "detected_name": c.detected_name,
                    "confidence": round(c.confidence, 2),
                    "status": c.status,
                }
                for c in self.columns
            ],
            "issues": [
                {
                    "category": i.category,
                    "severity": i.severity,
                    "message": i.message,
                    "affected_count": i.affected_count,
                    "remediation": i.remediation,
                    "downstream_impact": i.downstream_impact,
                    "affected_items": i.affected_items[:10],
                    "affected_items_truncated": len(i.affected_items) > 10,
                    "affected_items_total": len(i.affected_items),
                    "tests_affected": i.tests_affected,
                }
                for i in self.issues
            ],
            "duplicates": [{"account_code": d.account_code, "count": d.count} for d in self.duplicates],
            "encoding_anomalies": [
                {"row_index": e.row_index, "value": e.value, "column": e.column}
                for e in self.encoding_anomalies[:20]  # Cap for response size
            ],
            "mixed_sign_accounts": [
                {"account": m.account, "positive_count": m.positive_count, "negative_count": m.negative_count}
                for m in self.mixed_sign_accounts
            ],
            "zero_balance_count": self.zero_balance_count,
            "null_counts": self.null_counts,
        }
        if self.balance_check is not None:
            result["balance_check"] = {
                "total_debits": self.balance_check.total_debits,
                "total_credits": self.balance_check.total_credits,
                "difference": self.balance_check.difference,
                "balanced": self.balance_check.balanced,
                "tolerance": self.balance_check.tolerance,
            }
        if self.score_breakdown:
            result["score_breakdown"] = [
                {
                    "component": sc.component,
                    "weight": sc.weight,
                    "score": round(sc.score, 1),
                    "contribution": round(sc.contribution, 1),
                }
                for sc in self.score_breakdown
            ]
        return result


# ═══════════════════════════════════════════════════════════════
# Downstream impact descriptions per issue category
# ═══════════════════════════════════════════════════════════════

DOWNSTREAM_IMPACT: dict[str, str] = {
    "column_detection": "All diagnostic tools depend on correct column mapping. Incorrect detection causes miscalculated balances, failed ratio analysis, and unreliable anomaly detection across every downstream report.",
    "null_values": "Missing values in critical columns produce incomplete trial balance totals, skewed ratio calculations, and may cause accounts to be silently excluded from testing tools.",
    "duplicates": "Duplicate account codes inflate balance totals, distort ratio analysis, and may trigger false anomaly flags in JE Testing, AP Testing, and classification validators.",
    "encoding": "Non-ASCII characters can cause account matching failures in lead sheet mapping, classification rules, and cross-period comparisons (Multi-Period TB analysis).",
    "mixed_signs": "Inconsistent sign conventions produce incorrect debit/credit separation, unreliable balance sheet classification, and distorted abnormal balance detection.",
    "zero_balance": "Zero-balance rows add noise to statistical tests (Benford's Law, sampling), inflate account counts, and reduce the signal-to-noise ratio in anomaly detection.",
    "tb_balance": "An out-of-balance trial balance invalidates all downstream diagnostic results. Debit/credit totals must reconcile before any testing can proceed.",
}

# Number of downstream tests affected per issue category
TESTS_AFFECTED_BY_CATEGORY: dict[str, int] = {
    "column_detection": 12,  # All tools depend on column mapping
    "null_values": 11,  # All amount-based tests
    "duplicates": 8,  # Ratio, Benford, JE, AP, classification, lead sheet, anomaly, sampling
    "encoding": 3,  # Lead sheet matching, classification, multi-period comparison
    "mixed_signs": 7,  # Balance sheet classification, abnormal balance, ratios, JE, AP, sampling, cash flow
    "zero_balance": 4,  # Benford, sampling, anomaly, population profile
    "tb_balance": 12,  # ALL tests — blocker
}


# ═══════════════════════════════════════════════════════════════
# Check weights for readiness score
# ═══════════════════════════════════════════════════════════════

_CHECK_WEIGHTS = {
    "tb_balance": 25,
    "column_detection": 20,
    "null_values": 15,
    "duplicates": 10,
    "encoding": 5,
    "mixed_signs": 15,
    "zero_balance": 10,
}

# Severity deduction multipliers (fraction of weight)
_SEVERITY_MULTIPLIER = {
    "high": 1.0,
    "medium": 0.5,
    "low": 0.25,
}

# Low-confidence threshold for column detection remediation notes
LOW_CONFIDENCE_THRESHOLD = 0.80


# ═══════════════════════════════════════════════════════════════
# Non-ASCII detection pattern (compiled once)
# ═══════════════════════════════════════════════════════════════

_NON_ASCII_RE = re.compile(r"[^\x00-\x7F]")


# ═══════════════════════════════════════════════════════════════
# Main engine function
# ═══════════════════════════════════════════════════════════════


def run_preflight(
    column_names: list[str],
    rows: list[dict],
    filename: str,
) -> PreFlightReport:
    """Run pre-flight data quality assessment.

    Args:
        column_names: Column headers from the parsed file.
        rows: List of row dicts from parse_uploaded_file().
        filename: Original filename for the report.

    Returns:
        PreFlightReport with all quality checks completed.
    """
    row_count = len(rows)
    col_count = len(column_names)
    issues: list[PreFlightIssue] = []
    columns_quality: list[ColumnQuality] = []

    # ── Check 1: Column detection confidence (weight 20%) ──
    detection = detect_columns(column_names)
    _check_column_detection(detection, columns_quality, issues)

    # Resolve column names for subsequent checks
    account_col = detection.account_column
    debit_col = detection.debit_column
    credit_col = detection.credit_column

    # ── Check 0: TB Balance Check (weight 25%) ──
    balance_check = _check_tb_balance(rows, debit_col, credit_col, issues)

    # ── Check 2: Null/empty values (weight 15%) ──
    null_counts = _check_null_values(rows, column_names, account_col, debit_col, credit_col, issues)

    # ── Check 3: Duplicate account codes (weight 10%) ──
    duplicates = _check_duplicates(rows, account_col, row_count, issues)

    # ── Check 4: Encoding anomalies (weight 5%) ──
    encoding_anomalies = _check_encoding(rows, account_col, row_count, issues)

    # ── Check 5: Mixed debit/credit signs (weight 15%) ──
    mixed_signs = _check_mixed_signs(rows, account_col, debit_col, issues)

    # ── Check 6: Zero-balance rows (weight 10%) ──
    zero_count = _check_zero_balances(rows, debit_col, credit_col, row_count, issues)

    # ── Populate downstream impact descriptions and tests_affected ──
    _populate_downstream_impact(issues)

    # ── Calculate readiness score with breakdown ──
    readiness_score, score_breakdown = _calculate_readiness(issues)
    if readiness_score >= 80:
        readiness_label = "Ready"
    elif readiness_score >= 50:
        readiness_label = "Review Recommended"
    else:
        readiness_label = "Issues Found"

    return PreFlightReport(
        filename=filename,
        row_count=row_count,
        column_count=col_count,
        readiness_score=readiness_score,
        readiness_label=readiness_label,
        columns=columns_quality,
        issues=issues,
        duplicates=duplicates,
        encoding_anomalies=encoding_anomalies,
        mixed_sign_accounts=mixed_signs,
        zero_balance_count=zero_count,
        null_counts=null_counts,
        balance_check=balance_check,
        score_breakdown=score_breakdown,
    )


# ═══════════════════════════════════════════════════════════════
# Individual check functions
# ═══════════════════════════════════════════════════════════════


def _coerce_to_decimal(val: object) -> Decimal:
    """Coerce a cell value to Decimal, treating None/empty/NaN as 0.

    Handles common currency formats: $1,234.56  (1,234.56)  -$500
    Returns Decimal("0") for truly unparseable values.
    """
    if val is None:
        return Decimal("0")
    if isinstance(val, str):
        stripped = val.strip()
        if stripped == "":
            return Decimal("0")
        # Handle parenthesised negatives: (1,234.56) → -1234.56
        negative = stripped.startswith("(") and stripped.endswith(")")
        if negative:
            stripped = stripped[1:-1].strip()
        # Strip currency symbols and thousands separators
        cleaned = stripped.replace("$", "").replace(",", "").replace("€", "").replace("£", "").strip()
        if cleaned == "" or cleaned == "-":
            return Decimal("0")
        try:
            result = Decimal(cleaned)
            return -result if negative else result
        except Exception:
            return Decimal("0")
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        import math

        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return Decimal("0")
        return Decimal(str(val))
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0")


def _check_tb_balance(
    rows: list[dict],
    debit_col: str | None,
    credit_col: str | None,
    issues: list[PreFlightIssue],
    tolerance: float = 0.01,
) -> BalanceCheck | None:
    """Check 0: Verify total debits equal total credits.

    Coerces null/empty values to 0.0 before summing — standard for
    one-sided trial balances where each row has a value in either
    the debit or credit column, not both.
    """
    if not debit_col or not credit_col or not rows:
        return None

    total_debits = Decimal("0")
    total_credits = Decimal("0")
    for row in rows:
        try:
            total_debits += _coerce_to_decimal(row.get(debit_col))
        except (ValueError, TypeError, InvalidOperation):
            pass
        try:
            total_credits += _coerce_to_decimal(row.get(credit_col))
        except (ValueError, TypeError, InvalidOperation):
            pass

    difference = total_debits - total_credits
    balanced = abs(difference) <= tolerance

    if not balanced:
        issues.append(
            PreFlightIssue(
                category="tb_balance",
                severity="high",
                message=f"Trial balance is out of balance by ${abs(difference):,.2f}",
                affected_count=len(rows),
                remediation="Obtain a corrected trial balance where total debits equal total credits "
                "before proceeding with any diagnostic testing.",
            )
        )

    return BalanceCheck(
        total_debits=float(total_debits),
        total_credits=float(total_credits),
        difference=float(difference),
        balanced=balanced,
        tolerance=tolerance,
    )


def _check_column_detection(
    detection: ColumnDetectionResult,
    columns_quality: list[ColumnQuality],
    issues: list[PreFlightIssue],
) -> None:
    """Check 1: Column detection confidence.

    Reports all columns from the file — not just the 3 core roles.
    Unmapped columns are shown with role "unmapped" so users can verify
    the engine saw them.
    """
    # Core role mappings
    core_mappings: dict[str, tuple[str | None, float]] = {
        "account": (detection.account_column, detection.account_confidence),
        "debit": (detection.debit_column, detection.debit_confidence),
        "credit": (detection.credit_column, detection.credit_confidence),
    }

    mapped_cols: set[str] = set()
    for role, (col_name, conf) in core_mappings.items():
        if col_name is None:
            columns_quality.append(ColumnQuality(role, None, 0.0, "missing"))
        elif conf < 0.80:
            columns_quality.append(ColumnQuality(role, col_name, conf, "low_confidence"))
            mapped_cols.add(col_name.lower().strip())
        else:
            columns_quality.append(ColumnQuality(role, col_name, conf, "found"))
            mapped_cols.add(col_name.lower().strip())

    # Add unmapped columns so the user can see the full file structure.
    # Infer a descriptive role label from the column name where possible.
    _AUXILIARY_ROLE_HINTS = {
        "account_name": "Account Name",
        "account_type": "Account Type",
        "classification": "Classification",
        "department": "Department",
        "cost_center": "Cost Center",
        "currency": "Currency",
        "balance": "Balance",
        "description": "Description",
        "memo": "Memo",
        "reference": "Reference",
        "date": "Date",
        "period": "Period",
        "entity": "Entity",
        "segment": "Segment",
    }
    for col in detection.all_columns:
        if col.lower().strip() in mapped_cols:
            continue
        col_lower = col.lower().strip().replace(" ", "_").replace("-", "_")
        inferred_role = _AUXILIARY_ROLE_HINTS.get(col_lower, "unmapped")
        columns_quality.append(ColumnQuality(role=inferred_role, detected_name=col, confidence=1.0, status="found"))

    # Issue generation
    missing = [c for c in columns_quality if c.status == "missing"]
    low_conf = [c for c in columns_quality if c.status == "low_confidence"]

    if missing:
        names = ", ".join(c.role for c in missing)
        issues.append(
            PreFlightIssue(
                category="column_detection",
                severity="high",
                message=f"Required column(s) not detected: {names}",
                affected_count=len(missing),
                remediation="Use column mapping to manually assign the missing column(s), "
                "or rename columns to standard names (Account, Debit, Credit).",
            )
        )
    elif detection.overall_confidence < 0.80:
        issues.append(
            PreFlightIssue(
                category="column_detection",
                severity="high",
                message=f"Overall column detection confidence is low ({detection.overall_confidence:.0%})",
                affected_count=len(low_conf),
                remediation="Review detected columns and use column mapping if assignments are incorrect.",
            )
        )
    elif detection.overall_confidence < 0.95:
        issues.append(
            PreFlightIssue(
                category="column_detection",
                severity="medium",
                message=f"Column detection confidence is moderate ({detection.overall_confidence:.0%})",
                affected_count=len(low_conf),
                remediation="Verify detected columns are correct before proceeding.",
            )
        )


def _is_cell_empty(val: object) -> bool:
    """Check if a cell value is null, empty, or NaN."""
    if val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    if isinstance(val, float) and val != val:  # NaN check
        return True
    return False


def _check_null_values(
    rows: list[dict],
    column_names: list[str],
    account_col: str | None,
    debit_col: str | None,
    credit_col: str | None,
    issues: list[PreFlightIssue],
) -> dict[str, int]:
    """Check 2: Null/empty values per column.

    For debit/credit columns, distinguishes between:
    - Structural nulls: one column empty because the other has a value
      (expected in one-sided TB format — not a data quality issue)
    - True nulls: both debit and credit are empty for the same row
      (genuine missing data worth flagging)

    Only true nulls generate issues for debit/credit columns.
    """
    null_counts: dict[str, int] = {}
    row_count = len(rows)
    if row_count == 0:
        return null_counts

    critical_cols: set[str] = {c for c in (account_col, debit_col, credit_col) if c is not None}
    monetary_cols: set[str] = {c for c in (debit_col, credit_col) if c is not None}

    # Track which rows have nulls per column for affected_items
    null_rows_by_col: dict[str, list[str]] = {}

    # First pass: count raw nulls for all columns
    for col in column_names:
        count = 0
        null_rows: list[str] = []
        for i, row in enumerate(rows):
            if _is_cell_empty(row.get(col)):
                count += 1
                if col in critical_cols:
                    acct = row.get(account_col, "") if account_col and col != account_col else ""
                    identifier = str(acct).strip() if acct else f"Row {i + 1}"
                    null_rows.append(identifier)
        if count > 0:
            null_counts[col] = count
            if col in critical_cols:
                null_rows_by_col[col] = null_rows

    # Second pass: for debit/credit columns, count only "true nulls"
    # (rows where BOTH debit and credit are empty — not one-sided structural nulls)
    true_null_counts: dict[str, int] = {}
    true_null_rows: dict[str, list[str]] = {}
    if debit_col and credit_col and debit_col in monetary_cols and credit_col in monetary_cols:
        true_null_counts[debit_col] = 0
        true_null_counts[credit_col] = 0
        true_null_rows[debit_col] = []
        true_null_rows[credit_col] = []
        for i, row in enumerate(rows):
            d_empty = _is_cell_empty(row.get(debit_col))
            c_empty = _is_cell_empty(row.get(credit_col))
            if d_empty and c_empty:
                # Both empty — true null (genuine missing data)
                acct = row.get(account_col, "") if account_col else ""
                identifier = str(acct).strip() if acct else f"Row {i + 1}"
                true_null_counts[debit_col] += 1
                true_null_counts[credit_col] += 1
                true_null_rows[debit_col].append(identifier)
                true_null_rows[credit_col].append(identifier)

    # Issue generation for critical columns
    for col in critical_cols:
        if col in monetary_cols:
            # Use true null count for debit/credit (excludes structural one-sided nulls)
            count = true_null_counts.get(col, 0)
            affected = true_null_rows.get(col, [])
        else:
            # Account column: all nulls are real issues
            count = null_counts.get(col, 0)
            affected = null_rows_by_col.get(col, [])

        if count == 0:
            continue
        pct = count / row_count
        if pct > 0.05:
            severity = "high"
        elif pct > 0.01:
            severity = "medium"
        else:
            severity = "low"
        issues.append(
            PreFlightIssue(
                category="null_values",
                severity=severity,
                message=f"Column '{col}' has {count} rows with missing data ({pct:.1%} of rows)",
                affected_count=count,
                remediation=f"Review rows with missing '{col}' values. "
                "Fill in missing data or remove incomplete rows before analysis.",
                affected_items=affected,
            )
        )

    return null_counts


def _check_duplicates(
    rows: list[dict],
    account_col: str | None,
    row_count: int,
    issues: list[PreFlightIssue],
) -> list[DuplicateEntry]:
    """Check 3: Duplicate account codes."""
    if not account_col or row_count == 0:
        return []

    code_counts: dict[str, int] = {}
    for row in rows:
        val = row.get(account_col)
        if val is not None:
            key = str(val).strip().lower()
            if key:
                code_counts[key] = code_counts.get(key, 0) + 1

    duplicates = [
        DuplicateEntry(account_code=code, count=cnt)
        for code, cnt in sorted(code_counts.items(), key=lambda x: -x[1])
        if cnt > 1
    ]

    if not duplicates:
        return []

    total_dup_rows = sum(d.count for d in duplicates)
    dup_pct = total_dup_rows / row_count if row_count > 0 else 0

    affected_items = [d.account_code for d in duplicates]

    # If >80% rows are duplicates, likely a detailed TB (sub-ledger) — lower severity
    if dup_pct > 0.80:
        issues.append(
            PreFlightIssue(
                category="duplicates",
                severity="low",
                message=f"{len(duplicates)} account codes appear multiple times ({dup_pct:.0%} of rows). "
                "This may indicate a detailed/sub-ledger trial balance.",
                affected_count=len(duplicates),
                remediation="If this is a summarized TB, review for unintended duplicate entries. "
                "Detailed TBs with multiple lines per account are supported.",
                affected_items=affected_items,
            )
        )
    elif dup_pct > 0.10:
        issues.append(
            PreFlightIssue(
                category="duplicates",
                severity="high",
                message=f"{len(duplicates)} duplicate account codes found ({dup_pct:.0%} of rows)",
                affected_count=len(duplicates),
                remediation="Review and consolidate duplicate account entries before analysis. "
                "Duplicates may cause incorrect balance calculations.",
                affected_items=affected_items,
            )
        )
    elif dup_pct > 0.05:
        issues.append(
            PreFlightIssue(
                category="duplicates",
                severity="medium",
                message=f"{len(duplicates)} duplicate account codes found ({dup_pct:.0%} of rows)",
                affected_count=len(duplicates),
                remediation="Verify that duplicate account codes are intentional (e.g., sub-ledger detail).",
                affected_items=affected_items,
            )
        )

    return duplicates


def _check_encoding(
    rows: list[dict],
    account_col: str | None,
    row_count: int,
    issues: list[PreFlightIssue],
) -> list[EncodingAnomaly]:
    """Check 4: Encoding anomalies (non-ASCII in account names)."""
    if not account_col or row_count == 0:
        return []

    anomalies: list[EncodingAnomaly] = []
    for i, row in enumerate(rows):
        val = row.get(account_col)
        if val is not None and isinstance(val, str) and _NON_ASCII_RE.search(val):
            anomalies.append(EncodingAnomaly(row_index=i, value=val, column=account_col))

    if not anomalies:
        return []

    pct = len(anomalies) / row_count
    if pct > 0.10:
        severity = "medium"
    else:
        severity = "low"

    affected_items = [a.value for a in anomalies]

    issues.append(
        PreFlightIssue(
            category="encoding",
            severity=severity,
            message=f"{len(anomalies)} account names contain non-ASCII characters ({pct:.1%} of rows)",
            affected_count=len(anomalies),
            remediation="Non-ASCII characters (accented letters, special symbols) may cause "
            "matching issues. Consider normalizing account names to ASCII.",
            affected_items=affected_items,
        )
    )

    return anomalies


def _check_mixed_signs(
    rows: list[dict],
    account_col: str | None,
    debit_col: str | None,
    issues: list[PreFlightIssue],
) -> list[MixedSignAccount]:
    """Check 5: Mixed debit/credit signs within single accounts."""
    if not account_col or not debit_col:
        return []

    # Track positive/negative counts per account
    account_signs: dict[str, dict[str, int]] = {}
    for row in rows:
        acct = row.get(account_col)
        val = row.get(debit_col)
        if acct is None or val is None:
            continue
        try:
            num = safe_decimal(val)
        except (ValueError, TypeError):
            continue
        if num == 0:
            continue

        key = str(acct).strip()
        if key not in account_signs:
            account_signs[key] = {"positive": 0, "negative": 0}
        if num > 0:
            account_signs[key]["positive"] += 1
        else:
            account_signs[key]["negative"] += 1

    mixed = [
        MixedSignAccount(account=acct, positive_count=signs["positive"], negative_count=signs["negative"])
        for acct, signs in account_signs.items()
        if signs["positive"] > 0 and signs["negative"] > 0
    ]

    if not mixed:
        return []

    total_accounts = len(account_signs)
    pct = len(mixed) / total_accounts if total_accounts > 0 else 0

    if pct > 0.20:
        severity = "high"
    else:
        severity = "medium"

    affected_items = [m.account for m in mixed]

    issues.append(
        PreFlightIssue(
            category="mixed_signs",
            severity=severity,
            message=f"{len(mixed)} accounts have both positive and negative debit values ({pct:.0%} of accounts)",
            affected_count=len(mixed),
            remediation="Mixed signs in the debit column may indicate sign convention inconsistency. "
            "Verify that debits are consistently positive (or consistently negative).",
            affected_items=affected_items,
        )
    )

    return mixed


def _check_zero_balances(
    rows: list[dict],
    debit_col: str | None,
    credit_col: str | None,
    row_count: int,
    issues: list[PreFlightIssue],
) -> int:
    """Check 6: Zero-balance rows (debit=0 AND credit=0)."""
    if not debit_col or not credit_col or row_count == 0:
        return 0

    zero_count = 0
    zero_accounts: list[str] = []
    account_col_candidates = [k for k in (rows[0].keys() if rows else []) if k != debit_col and k != credit_col]
    # Use first non-debit/credit column as account identifier
    acct_col = account_col_candidates[0] if account_col_candidates else None

    for row in rows:
        debit_val = row.get(debit_col)
        credit_val = row.get(credit_col)
        try:
            d = safe_decimal(debit_val)
            c = safe_decimal(credit_val)
        except (ValueError, TypeError):
            continue
        if d == 0 and c == 0:
            zero_count += 1
            if acct_col:
                acct_val = row.get(acct_col, "")
                if acct_val:
                    zero_accounts.append(str(acct_val).strip())

    if zero_count == 0:
        return 0

    pct = zero_count / row_count
    if pct > 0.50:
        severity = "high"
    elif pct > 0.20:
        severity = "medium"
    elif pct > 0:
        severity = "low"
    else:
        return 0

    issues.append(
        PreFlightIssue(
            category="zero_balance",
            severity=severity,
            message=f"{zero_count} rows have zero balance in both debit and credit columns ({pct:.0%} of rows)",
            affected_count=zero_count,
            remediation="Zero-balance rows add noise to the analysis. Consider filtering them "
            "out if they represent closed or inactive accounts.",
            affected_items=zero_accounts,
        )
    )

    return zero_count


# ═══════════════════════════════════════════════════════════════
# Readiness score calculation
# ═══════════════════════════════════════════════════════════════


def _populate_downstream_impact(issues: list[PreFlightIssue]) -> None:
    """Populate downstream_impact and tests_affected fields for all issues."""
    for issue in issues:
        if not issue.downstream_impact:
            issue.downstream_impact = DOWNSTREAM_IMPACT.get(issue.category, "")
        if issue.tests_affected == 0:
            issue.tests_affected = TESTS_AFFECTED_BY_CATEGORY.get(issue.category, 0)


def _calculate_readiness(issues: list[PreFlightIssue]) -> tuple[float, list[ScoreComponent]]:
    """Calculate readiness score (0-100) with component breakdown.

    Start at 100, deduct per issue based on:
    - Category weight (from _CHECK_WEIGHTS)
    - Severity multiplier (high=full, medium=half, low=quarter)

    Multiple issues in the same category take the worst severity.

    Returns:
        Tuple of (score, list of ScoreComponent breakdowns)
    """
    # Track worst severity per category
    worst_by_category: dict[str, str] = {}
    severity_order = {"high": 3, "medium": 2, "low": 1}

    for issue in issues:
        cat = issue.category
        current_worst = worst_by_category.get(cat)
        if current_worst is None or severity_order.get(issue.severity, 0) > severity_order.get(current_worst, 0):
            worst_by_category[cat] = issue.severity

    # Build breakdown
    breakdown: list[ScoreComponent] = []
    total_score = 100.0

    for category, weight in _CHECK_WEIGHTS.items():
        severity = worst_by_category.get(category)
        if severity is None:
            # No issues in this category — full score
            component_score = 100.0
        else:
            multiplier = _SEVERITY_MULTIPLIER.get(severity, 0.25)
            component_score = 100.0 * (1.0 - multiplier)

        weight_fraction = weight / 100.0
        contribution = weight_fraction * component_score
        breakdown.append(
            ScoreComponent(
                component=category,
                weight=weight_fraction,
                score=component_score,
                contribution=contribution,
            )
        )

    total_score = sum(sc.contribution for sc in breakdown)

    return max(0.0, total_score), breakdown
