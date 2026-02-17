"""
Paciolus — Data Quality Pre-Flight Engine
Sprint 283: Phase XXXVIII

Lightweight data quality assessment that runs on a Trial Balance file
BEFORE the full TB diagnostic. Gives users immediate feedback on column
detection, null values, duplicates, encoding issues, and sign conventions.

Pure-Python engine (no Pandas). Takes parsed data from parse_uploaded_file().
"""

import re
from dataclasses import dataclass, field

from column_detector import (
    ACCOUNT_PATTERNS,
    CREDIT_PATTERNS,
    DEBIT_PATTERNS,
    ColumnDetectionResult,
    detect_columns,
)


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
class PreFlightIssue:
    """A single pre-flight quality issue."""
    category: str  # column_detection, null_values, duplicates, encoding, mixed_signs, zero_balance
    severity: str  # "high", "medium", "low"
    message: str
    affected_count: int
    remediation: str


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

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "filename": self.filename,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "readiness_score": round(self.readiness_score, 1),
            "readiness_label": self.readiness_label,
            "columns": [
                {"role": c.role, "detected_name": c.detected_name,
                 "confidence": round(c.confidence, 2), "status": c.status}
                for c in self.columns
            ],
            "issues": [
                {"category": i.category, "severity": i.severity,
                 "message": i.message, "affected_count": i.affected_count,
                 "remediation": i.remediation}
                for i in self.issues
            ],
            "duplicates": [
                {"account_code": d.account_code, "count": d.count}
                for d in self.duplicates
            ],
            "encoding_anomalies": [
                {"row_index": e.row_index, "value": e.value, "column": e.column}
                for e in self.encoding_anomalies[:20]  # Cap for response size
            ],
            "mixed_sign_accounts": [
                {"account": m.account, "positive_count": m.positive_count,
                 "negative_count": m.negative_count}
                for m in self.mixed_sign_accounts
            ],
            "zero_balance_count": self.zero_balance_count,
            "null_counts": self.null_counts,
        }


# ═══════════════════════════════════════════════════════════════
# Check weights for readiness score
# ═══════════════════════════════════════════════════════════════

_CHECK_WEIGHTS = {
    "column_detection": 30,
    "null_values": 20,
    "duplicates": 15,
    "encoding": 10,
    "mixed_signs": 15,
    "zero_balance": 10,
}

# Severity deduction multipliers (fraction of weight)
_SEVERITY_MULTIPLIER = {
    "high": 1.0,
    "medium": 0.5,
    "low": 0.25,
}


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

    # ── Check 1: Column detection confidence (weight 30%) ──
    detection = detect_columns(column_names)
    _check_column_detection(detection, columns_quality, issues)

    # Resolve column names for subsequent checks
    account_col = detection.account_column
    debit_col = detection.debit_column
    credit_col = detection.credit_column

    # ── Check 2: Null/empty values (weight 20%) ──
    null_counts = _check_null_values(rows, column_names, account_col, debit_col, credit_col, issues)

    # ── Check 3: Duplicate account codes (weight 15%) ──
    duplicates = _check_duplicates(rows, account_col, row_count, issues)

    # ── Check 4: Encoding anomalies (weight 10%) ──
    encoding_anomalies = _check_encoding(rows, account_col, row_count, issues)

    # ── Check 5: Mixed debit/credit signs (weight 15%) ──
    mixed_signs = _check_mixed_signs(rows, account_col, debit_col, issues)

    # ── Check 6: Zero-balance rows (weight 10%) ──
    zero_count = _check_zero_balances(rows, debit_col, credit_col, row_count, issues)

    # ── Calculate readiness score ──
    readiness_score = _calculate_readiness(issues)
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
    )


# ═══════════════════════════════════════════════════════════════
# Individual check functions
# ═══════════════════════════════════════════════════════════════

def _check_column_detection(
    detection: ColumnDetectionResult,
    columns_quality: list[ColumnQuality],
    issues: list[PreFlightIssue],
) -> None:
    """Check 1: Column detection confidence."""
    for role, col_name, conf in [
        ("account", detection.account_column, detection.account_confidence),
        ("debit", detection.debit_column, detection.debit_confidence),
        ("credit", detection.credit_column, detection.credit_confidence),
    ]:
        if col_name is None:
            columns_quality.append(ColumnQuality(role, None, 0.0, "missing"))
        elif conf < 0.80:
            columns_quality.append(ColumnQuality(role, col_name, conf, "low_confidence"))
        else:
            columns_quality.append(ColumnQuality(role, col_name, conf, "found"))

    # Issue generation
    missing = [c for c in columns_quality if c.status == "missing"]
    low_conf = [c for c in columns_quality if c.status == "low_confidence"]

    if missing:
        names = ", ".join(c.role for c in missing)
        issues.append(PreFlightIssue(
            category="column_detection",
            severity="high",
            message=f"Required column(s) not detected: {names}",
            affected_count=len(missing),
            remediation="Use column mapping to manually assign the missing column(s), "
                        "or rename columns to standard names (Account, Debit, Credit).",
        ))
    elif detection.overall_confidence < 0.80:
        issues.append(PreFlightIssue(
            category="column_detection",
            severity="high",
            message=f"Overall column detection confidence is low ({detection.overall_confidence:.0%})",
            affected_count=len(low_conf),
            remediation="Review detected columns and use column mapping if assignments are incorrect.",
        ))
    elif detection.overall_confidence < 0.95:
        issues.append(PreFlightIssue(
            category="column_detection",
            severity="medium",
            message=f"Column detection confidence is moderate ({detection.overall_confidence:.0%})",
            affected_count=len(low_conf),
            remediation="Verify detected columns are correct before proceeding.",
        ))


def _check_null_values(
    rows: list[dict],
    column_names: list[str],
    account_col: str | None,
    debit_col: str | None,
    credit_col: str | None,
    issues: list[PreFlightIssue],
) -> dict[str, int]:
    """Check 2: Null/empty values per column."""
    null_counts: dict[str, int] = {}
    row_count = len(rows)
    if row_count == 0:
        return null_counts

    critical_cols = {account_col, debit_col, credit_col} - {None}

    for col in column_names:
        count = 0
        for row in rows:
            val = row.get(col)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                count += 1
            elif isinstance(val, float) and val != val:  # NaN check
                count += 1
        if count > 0:
            null_counts[col] = count

    # Issue generation for critical columns
    for col in critical_cols:
        count = null_counts.get(col, 0)
        if count == 0:
            continue
        pct = count / row_count
        if pct > 0.05:
            severity = "high"
        elif pct > 0.01:
            severity = "medium"
        else:
            severity = "low"
        issues.append(PreFlightIssue(
            category="null_values",
            severity=severity,
            message=f"Column '{col}' has {count} null/empty values ({pct:.1%} of rows)",
            affected_count=count,
            remediation=f"Review rows with missing '{col}' values. "
                        "Fill in missing data or remove incomplete rows before analysis.",
        ))

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

    # If >80% rows are duplicates, likely a detailed TB (sub-ledger) — lower severity
    if dup_pct > 0.80:
        issues.append(PreFlightIssue(
            category="duplicates",
            severity="low",
            message=f"{len(duplicates)} account codes appear multiple times ({dup_pct:.0%} of rows). "
                    "This may indicate a detailed/sub-ledger trial balance.",
            affected_count=len(duplicates),
            remediation="If this is a summarized TB, review for unintended duplicate entries. "
                        "Detailed TBs with multiple lines per account are supported.",
        ))
    elif dup_pct > 0.10:
        issues.append(PreFlightIssue(
            category="duplicates",
            severity="high",
            message=f"{len(duplicates)} duplicate account codes found ({dup_pct:.0%} of rows)",
            affected_count=len(duplicates),
            remediation="Review and consolidate duplicate account entries before analysis. "
                        "Duplicates may cause incorrect balance calculations.",
        ))
    elif dup_pct > 0.05:
        issues.append(PreFlightIssue(
            category="duplicates",
            severity="medium",
            message=f"{len(duplicates)} duplicate account codes found ({dup_pct:.0%} of rows)",
            affected_count=len(duplicates),
            remediation="Verify that duplicate account codes are intentional (e.g., sub-ledger detail).",
        ))

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

    issues.append(PreFlightIssue(
        category="encoding",
        severity=severity,
        message=f"{len(anomalies)} account names contain non-ASCII characters ({pct:.1%} of rows)",
        affected_count=len(anomalies),
        remediation="Non-ASCII characters (accented letters, special symbols) may cause "
                    "matching issues. Consider normalizing account names to ASCII.",
    ))

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
            num = float(val)
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

    issues.append(PreFlightIssue(
        category="mixed_signs",
        severity=severity,
        message=f"{len(mixed)} accounts have both positive and negative debit values ({pct:.0%} of accounts)",
        affected_count=len(mixed),
        remediation="Mixed signs in the debit column may indicate sign convention inconsistency. "
                    "Verify that debits are consistently positive (or consistently negative).",
    ))

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
    for row in rows:
        debit_val = row.get(debit_col)
        credit_val = row.get(credit_col)
        try:
            d = float(debit_val) if debit_val is not None else 0.0
            c = float(credit_val) if credit_val is not None else 0.0
        except (ValueError, TypeError):
            continue
        if d == 0 and c == 0:
            zero_count += 1

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

    issues.append(PreFlightIssue(
        category="zero_balance",
        severity=severity,
        message=f"{zero_count} rows have zero balance in both debit and credit columns ({pct:.0%} of rows)",
        affected_count=zero_count,
        remediation="Zero-balance rows add noise to the analysis. Consider filtering them "
                    "out if they represent closed or inactive accounts.",
    ))

    return zero_count


# ═══════════════════════════════════════════════════════════════
# Readiness score calculation
# ═══════════════════════════════════════════════════════════════

def _calculate_readiness(issues: list[PreFlightIssue]) -> float:
    """Calculate readiness score (0-100).

    Start at 100, deduct per issue based on:
    - Category weight (from _CHECK_WEIGHTS)
    - Severity multiplier (high=full, medium=half, low=quarter)

    Multiple issues in the same category take the worst severity.
    """
    # Track worst severity per category
    worst_by_category: dict[str, str] = {}
    severity_order = {"high": 3, "medium": 2, "low": 1}

    for issue in issues:
        cat = issue.category
        current_worst = worst_by_category.get(cat)
        if current_worst is None or severity_order.get(issue.severity, 0) > severity_order.get(current_worst, 0):
            worst_by_category[cat] = issue.severity

    score = 100.0
    for category, severity in worst_by_category.items():
        weight = _CHECK_WEIGHTS.get(category, 10)
        multiplier = _SEVERITY_MULTIPLIER.get(severity, 0.25)
        score -= weight * multiplier

    return max(0.0, score)
