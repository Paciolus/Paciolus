"""
Bank Reconciliation Engine — Sprint 77

Reconciles bank statement transactions against general ledger entries.
Supports column auto-detection, exact matching (V1), and CSV export.

ZERO-STORAGE COMPLIANCE:
- All files processed in-memory only
- Reconciliation results are ephemeral (computed on demand)
- No raw transaction data is stored

Audit Standards References:
- ISA 500: Audit Evidence (bank reconciliation as substantive procedure)
- ISA 330: Auditor's Responses to Assessed Risks
- PCAOB AS 2301: The Auditor's Responses to the Risks of Material Misstatement
"""

import csv
import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from io import StringIO
from typing import Optional

from shared.column_detector import ColumnFieldConfig, detect_columns
from shared.helpers import sanitize_csv_value
from shared.parsing_helpers import parse_date, safe_float, safe_str

# =============================================================================
# ENUMS & CONFIG
# =============================================================================


class MatchType(str, Enum):
    """Type of reconciliation match."""

    MATCHED = "matched"
    BANK_ONLY = "bank_only"
    LEDGER_ONLY = "ledger_only"


@dataclass
class BankRecConfig:
    """Configurable thresholds for bank reconciliation."""

    amount_tolerance: float = 0.01  # Match tolerance in dollars
    date_tolerance_days: int = 0  # Days of date tolerance for matching
    materiality: float = 50_000.0  # Materiality for high-value transaction testing
    performance_materiality: float = 50_000.0  # Performance materiality for risk scoring


# =============================================================================
# COLUMN DETECTION
# =============================================================================

# Weighted regex patterns: (pattern, weight, is_exact)

BANK_DATE_PATTERNS = [
    (r"^date$", 1.0, True),
    (r"^transaction\s*date$", 0.98, True),
    (r"^trans\s*date$", 0.95, True),
    (r"^posting\s*date$", 0.95, True),
    (r"^post\s*date$", 0.90, True),
    (r"^value\s*date$", 0.90, True),
    (r"^effective\s*date$", 0.88, True),
    (r"^entry\s*date$", 0.85, True),
    (r"^cleared\s*date$", 0.85, True),
    (r"^settlement\s*date$", 0.82, True),
    (r"^book\s*date$", 0.80, True),
    (r"^gl\s*date$", 0.80, True),
    (r"^journal\s*date$", 0.78, True),
    (r"date", 0.55, False),
]

BANK_AMOUNT_PATTERNS = [
    (r"^amount$", 0.95, True),
    (r"^transaction\s*amount$", 1.0, True),
    (r"^trans\s*amount$", 0.95, True),
    (r"^debit\s*amount$", 0.85, True),
    (r"^credit\s*amount$", 0.85, True),
    (r"^net\s*amount$", 0.90, True),
    (r"^total\s*amount$", 0.88, True),
    (r"^deposit$", 0.80, True),
    (r"^withdrawal$", 0.80, True),
    (r"^debit$", 0.78, True),
    (r"^credit$", 0.78, True),
    (r"amount", 0.55, False),
]

BANK_DESCRIPTION_PATTERNS = [
    (r"^description$", 1.0, True),
    (r"^transaction\s*description$", 0.98, True),
    (r"^trans\s*description$", 0.95, True),
    (r"^memo$", 0.90, True),
    (r"^narrative$", 0.90, True),
    (r"^narration$", 0.90, True),
    (r"^particulars$", 0.85, True),
    (r"^details$", 0.85, True),
    (r"^payee$", 0.80, True),
    (r"^remarks$", 0.78, True),
    (r"^comment$", 0.75, True),
    (r"description", 0.55, False),
    (r"memo", 0.50, False),
]

BANK_REFERENCE_PATTERNS = [
    (r"^reference$", 1.0, True),
    (r"^ref$", 0.95, True),
    (r"^ref\s*number$", 0.98, True),
    (r"^ref\s*no$", 0.95, True),
    (r"^reference\s*number$", 0.98, True),
    (r"^check\s*number$", 0.90, True),
    (r"^check\s*no$", 0.88, True),
    (r"^cheque\s*number$", 0.90, True),
    (r"^cheque\s*no$", 0.88, True),
    (r"^transaction\s*id$", 0.85, True),
    (r"^trans\s*id$", 0.82, True),
    (r"^document\s*number$", 0.80, True),
    (r"^doc\s*no$", 0.78, True),
    (r"reference", 0.55, False),
    (r"ref.?n", 0.50, False),
]

BANK_BALANCE_PATTERNS = [
    (r"^balance$", 1.0, True),
    (r"^running\s*balance$", 0.98, True),
    (r"^closing\s*balance$", 0.95, True),
    (r"^available\s*balance$", 0.92, True),
    (r"^ledger\s*balance$", 0.90, True),
    (r"^book\s*balance$", 0.88, True),
    (r"^ending\s*balance$", 0.88, True),
    (r"balance", 0.55, False),
]

# Column field configs for shared detector — priority ordering prevents
# generic patterns from stealing specific columns
BANK_COLUMN_CONFIGS = [
    ColumnFieldConfig("reference_column", BANK_REFERENCE_PATTERNS, priority=10),
    ColumnFieldConfig("balance_column", BANK_BALANCE_PATTERNS, priority=20),
    ColumnFieldConfig(
        "date_column", BANK_DATE_PATTERNS, required=True, missing_note="Could not identify a Date column", priority=30
    ),
    ColumnFieldConfig(
        "amount_column",
        BANK_AMOUNT_PATTERNS,
        required=True,
        missing_note="Could not identify an Amount column",
        priority=40,
    ),
    ColumnFieldConfig("description_column", BANK_DESCRIPTION_PATTERNS, priority=50),
]


@dataclass
class BankColumnDetectionResult:
    """Result of bank/ledger column detection."""

    date_column: Optional[str] = None
    amount_column: Optional[str] = None
    description_column: Optional[str] = None
    reference_column: Optional[str] = None
    balance_column: Optional[str] = None

    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "date_column": self.date_column,
            "amount_column": self.amount_column,
            "description_column": self.description_column,
            "reference_column": self.reference_column,
            "balance_column": self.balance_column,
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


def detect_bank_columns(column_names: list[str]) -> BankColumnDetectionResult:
    """Detect bank/ledger columns using weighted pattern matching.

    Uses shared column detector with greedy assignment and specificity ordering.
    """
    detection = detect_columns(column_names, BANK_COLUMN_CONFIGS)

    result = BankColumnDetectionResult(all_columns=detection.all_columns)
    result.date_column = detection.get_column("date_column")
    result.amount_column = detection.get_column("amount_column")
    result.description_column = detection.get_column("description_column")
    result.reference_column = detection.get_column("reference_column")
    result.balance_column = detection.get_column("balance_column")

    # Calculate overall confidence (min of required-column confidences)
    required_confidences = [
        detection.get_confidence("date_column") if result.date_column else 0.0,
        detection.get_confidence("amount_column") if result.amount_column else 0.0,
    ]
    result.overall_confidence = min(required_confidences) if required_confidences else 0.0
    result.detection_notes = detection.detection_notes
    return result


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class BankTransaction:
    """A single transaction from the bank statement."""

    date: Optional[str] = None
    description: str = ""
    amount: float = 0.0
    reference: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "reference": self.reference,
            "row_number": self.row_number,
        }


@dataclass
class LedgerTransaction:
    """A single transaction from the general ledger."""

    date: Optional[str] = None
    description: str = ""
    amount: float = 0.0
    reference: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "description": self.description,
            "amount": self.amount,
            "reference": self.reference,
            "row_number": self.row_number,
        }


@dataclass
class ReconciliationMatch:
    """A single reconciliation match or unmatched item."""

    bank_txn: Optional[BankTransaction] = None
    ledger_txn: Optional[LedgerTransaction] = None
    match_type: MatchType = MatchType.MATCHED
    match_confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "bank_txn": self.bank_txn.to_dict() if self.bank_txn else None,
            "ledger_txn": self.ledger_txn.to_dict() if self.ledger_txn else None,
            "match_type": self.match_type.value,
            "match_confidence": round(self.match_confidence, 2),
        }


@dataclass
class ReconciliationSummary:
    """Summary of reconciliation results."""

    matched_count: int = 0
    matched_amount: float = 0.0
    bank_only_count: int = 0
    bank_only_amount: float = 0.0
    ledger_only_count: int = 0
    ledger_only_amount: float = 0.0
    reconciling_difference: float = 0.0
    total_bank: float = 0.0
    total_ledger: float = 0.0
    matches: list[ReconciliationMatch] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "matched_count": self.matched_count,
            "matched_amount": round(self.matched_amount, 2),
            "bank_only_count": self.bank_only_count,
            "bank_only_amount": round(self.bank_only_amount, 2),
            "ledger_only_count": self.ledger_only_count,
            "ledger_only_amount": round(self.ledger_only_amount, 2),
            "reconciling_difference": round(self.reconciling_difference, 2),
            "total_bank": round(self.total_bank, 2),
            "total_ledger": round(self.total_ledger, 2),
            "matches": [m.to_dict() for m in self.matches],
        }


@dataclass
class BankRecResult:
    """Complete result of bank reconciliation."""

    summary: ReconciliationSummary
    bank_column_detection: BankColumnDetectionResult
    ledger_column_detection: BankColumnDetectionResult
    rec_tests: list["RecTestResult"] = field(default_factory=list)
    outstanding_aging: list["OutstandingItemsAging"] = field(default_factory=list)
    composite_score: Optional[dict] = None

    def to_dict(self) -> dict:
        result = {
            "summary": self.summary.to_dict(),
            "bank_column_detection": self.bank_column_detection.to_dict(),
            "ledger_column_detection": self.ledger_column_detection.to_dict(),
        }
        if self.rec_tests:
            result["rec_tests"] = [t.to_dict() for t in self.rec_tests]
        if self.outstanding_aging:
            result["outstanding_aging"] = [a.to_dict() for a in self.outstanding_aging]
        if self.composite_score is not None:
            result["composite_score"] = self.composite_score
        return result


# =============================================================================
# =============================================================================
# PARSING
# =============================================================================


def parse_bank_transactions(
    rows: list[dict],
    detection: BankColumnDetectionResult,
) -> list[BankTransaction]:
    """Parse raw bank statement rows into BankTransaction objects."""
    transactions: list[BankTransaction] = []

    for idx, row in enumerate(rows):
        txn = BankTransaction(row_number=idx + 1)

        if detection.date_column:
            txn.date = safe_str(row.get(detection.date_column))
        if detection.amount_column:
            txn.amount = safe_float(row.get(detection.amount_column))
        if detection.description_column:
            txn.description = safe_str(row.get(detection.description_column)) or ""
        if detection.reference_column:
            txn.reference = safe_str(row.get(detection.reference_column))

        transactions.append(txn)

    return transactions


def parse_ledger_transactions(
    rows: list[dict],
    detection: BankColumnDetectionResult,
) -> list[LedgerTransaction]:
    """Parse raw ledger rows into LedgerTransaction objects."""
    transactions: list[LedgerTransaction] = []

    for idx, row in enumerate(rows):
        txn = LedgerTransaction(row_number=idx + 1)

        if detection.date_column:
            txn.date = safe_str(row.get(detection.date_column))
        if detection.amount_column:
            txn.amount = safe_float(row.get(detection.amount_column))
        if detection.description_column:
            txn.description = safe_str(row.get(detection.description_column)) or ""
        if detection.reference_column:
            txn.reference = safe_str(row.get(detection.reference_column))

        transactions.append(txn)

    return transactions


# =============================================================================
# MATCHING (V1 — Exact)
# =============================================================================


def match_transactions(
    bank_txns: list[BankTransaction],
    ledger_txns: list[LedgerTransaction],
    config: Optional[BankRecConfig] = None,
) -> list[ReconciliationMatch]:
    """Match bank transactions against ledger transactions.

    V1 Algorithm (Exact Matching):
    - Sort both lists by abs(amount) descending (greedy — largest first)
    - For each bank txn, find first unmatched ledger txn where:
      - Amount within tolerance
      - Dates match (within date_tolerance_days)
    - Remaining unmatched → BANK_ONLY / LEDGER_ONLY entries
    """
    if config is None:
        config = BankRecConfig()

    matches: list[ReconciliationMatch] = []
    matched_ledger_indices: set[int] = set()

    # Sort by absolute amount descending for greedy matching
    sorted_bank = sorted(
        enumerate(bank_txns),
        key=lambda x: abs(x[1].amount),
        reverse=True,
    )
    sorted_ledger = sorted(
        enumerate(ledger_txns),
        key=lambda x: abs(x[1].amount),
        reverse=True,
    )

    matched_bank_indices: set[int] = set()

    for bank_idx, bank_txn in sorted_bank:
        for ledger_idx, ledger_txn in sorted_ledger:
            if ledger_idx in matched_ledger_indices:
                continue

            # Amount match within tolerance
            if abs(bank_txn.amount - ledger_txn.amount) > config.amount_tolerance:
                continue

            # Date match within tolerance
            if config.date_tolerance_days == 0:
                # Exact date match required
                bank_date = parse_date(bank_txn.date)
                ledger_date = parse_date(ledger_txn.date)
                if bank_date and ledger_date and bank_date != ledger_date:
                    continue
                # If either date is None, allow match (date not required)
            else:
                bank_date = parse_date(bank_txn.date)
                ledger_date = parse_date(ledger_txn.date)
                if bank_date and ledger_date:
                    days_diff = abs((bank_date - ledger_date).days)
                    if days_diff > config.date_tolerance_days:
                        continue

            # Match found
            matches.append(
                ReconciliationMatch(
                    bank_txn=bank_txn,
                    ledger_txn=ledger_txn,
                    match_type=MatchType.MATCHED,
                    match_confidence=1.0,
                )
            )
            matched_bank_indices.add(bank_idx)
            matched_ledger_indices.add(ledger_idx)
            break

    # Unmatched bank transactions → BANK_ONLY
    for bank_idx, bank_txn in enumerate(bank_txns):
        if bank_idx not in matched_bank_indices:
            matches.append(
                ReconciliationMatch(
                    bank_txn=bank_txn,
                    ledger_txn=None,
                    match_type=MatchType.BANK_ONLY,
                    match_confidence=0.0,
                )
            )

    # Unmatched ledger transactions → LEDGER_ONLY
    for ledger_idx, ledger_txn in enumerate(ledger_txns):
        if ledger_idx not in matched_ledger_indices:
            matches.append(
                ReconciliationMatch(
                    bank_txn=None,
                    ledger_txn=ledger_txn,
                    match_type=MatchType.LEDGER_ONLY,
                    match_confidence=0.0,
                )
            )

    return matches


# =============================================================================
# SUMMARY
# =============================================================================


def calculate_summary(matches: list[ReconciliationMatch]) -> ReconciliationSummary:
    """Calculate reconciliation summary from matches."""
    matched_count = 0
    matched_amount = 0.0
    bank_only_count = 0
    bank_only_amount = 0.0
    ledger_only_count = 0
    ledger_only_amount = 0.0
    total_bank = 0.0
    total_ledger = 0.0

    for m in matches:
        if m.match_type == MatchType.MATCHED:
            matched_count += 1
            if m.bank_txn:
                matched_amount += abs(m.bank_txn.amount)
                total_bank += m.bank_txn.amount
            if m.ledger_txn:
                total_ledger += m.ledger_txn.amount
        elif m.match_type == MatchType.BANK_ONLY:
            bank_only_count += 1
            if m.bank_txn:
                bank_only_amount += abs(m.bank_txn.amount)
                total_bank += m.bank_txn.amount
        elif m.match_type == MatchType.LEDGER_ONLY:
            ledger_only_count += 1
            if m.ledger_txn:
                ledger_only_amount += abs(m.ledger_txn.amount)
                total_ledger += m.ledger_txn.amount

    reconciling_difference = total_bank - total_ledger

    return ReconciliationSummary(
        matched_count=matched_count,
        matched_amount=round(matched_amount, 2),
        bank_only_count=bank_only_count,
        bank_only_amount=round(bank_only_amount, 2),
        ledger_only_count=ledger_only_count,
        ledger_only_amount=round(ledger_only_amount, 2),
        reconciling_difference=round(reconciling_difference, 2),
        total_bank=round(total_bank, 2),
        total_ledger=round(total_ledger, 2),
        matches=matches,
    )


# =============================================================================
# CSV EXPORT
# =============================================================================


def export_reconciliation_csv(summary: ReconciliationSummary) -> str:
    """Export reconciliation results as CSV string.

    Sections: MATCHED ITEMS, OUTSTANDING DEPOSITS (BANK ONLY),
    OUTSTANDING CHECKS (LEDGER ONLY), SUMMARY.
    """
    output = StringIO()
    writer = csv.writer(output)

    # Section 1: Matched Items
    writer.writerow(["MATCHED ITEMS"])
    writer.writerow(
        [
            "Bank Date",
            "Bank Description",
            "Bank Amount",
            "Bank Reference",
            "Ledger Date",
            "Ledger Description",
            "Ledger Amount",
            "Ledger Reference",
            "Confidence",
        ]
    )

    matched = [m for m in summary.matches if m.match_type == MatchType.MATCHED]
    for m in matched:
        bank = m.bank_txn
        ledger = m.ledger_txn
        writer.writerow(
            [
                bank.date if bank else "",
                sanitize_csv_value(bank.description) if bank else "",
                f"{bank.amount:.2f}" if bank else "",
                sanitize_csv_value(bank.reference) if bank else "",
                ledger.date if ledger else "",
                sanitize_csv_value(ledger.description) if ledger else "",
                f"{ledger.amount:.2f}" if ledger else "",
                sanitize_csv_value(ledger.reference) if ledger else "",
                f"{m.match_confidence:.2f}",
            ]
        )

    writer.writerow([])

    # Section 2: Outstanding Deposits (Bank Only)
    writer.writerow(["OUTSTANDING DEPOSITS (BANK ONLY)"])
    writer.writerow(["Date", "Description", "Amount", "Reference"])

    bank_only = [m for m in summary.matches if m.match_type == MatchType.BANK_ONLY]
    for m in bank_only:
        txn = m.bank_txn
        if txn:
            writer.writerow(
                [
                    txn.date or "",
                    sanitize_csv_value(txn.description),
                    f"{txn.amount:.2f}",
                    sanitize_csv_value(txn.reference or ""),
                ]
            )

    writer.writerow([])

    # Section 3: Outstanding Checks (Ledger Only)
    writer.writerow(["OUTSTANDING CHECKS (LEDGER ONLY)"])
    writer.writerow(["Date", "Description", "Amount", "Reference"])

    ledger_only = [m for m in summary.matches if m.match_type == MatchType.LEDGER_ONLY]
    for m in ledger_only:
        ledger_txn = m.ledger_txn
        if ledger_txn:
            writer.writerow(
                [
                    ledger_txn.date or "",
                    sanitize_csv_value(ledger_txn.description),
                    f"{ledger_txn.amount:.2f}",
                    sanitize_csv_value(ledger_txn.reference or ""),
                ]
            )

    writer.writerow([])

    # Section 4: Summary
    writer.writerow(["SUMMARY"])
    writer.writerow(["Matched Items", summary.matched_count])
    writer.writerow(["Matched Amount", f"{summary.matched_amount:.2f}"])
    writer.writerow(["Bank Only Items", summary.bank_only_count])
    writer.writerow(["Bank Only Amount", f"{summary.bank_only_amount:.2f}"])
    writer.writerow(["Ledger Only Items", summary.ledger_only_count])
    writer.writerow(["Ledger Only Amount", f"{summary.ledger_only_amount:.2f}"])
    writer.writerow(["Reconciling Difference", f"{summary.reconciling_difference:.2f}"])
    writer.writerow(["Total Bank", f"{summary.total_bank:.2f}"])
    writer.writerow(["Total Ledger", f"{summary.total_ledger:.2f}"])

    return output.getvalue()


# =============================================================================
# RECONCILIATION TESTS (CONTENT-03)
# =============================================================================


@dataclass
class RecFlaggedItem:
    """A single item flagged by a reconciliation test."""

    test_name: str
    description: str
    amount: float = 0.0
    date: Optional[str] = None
    reference: Optional[str] = None
    severity: str = "medium"
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        result: dict = {
            "test_name": self.test_name,
            "description": self.description,
            "amount": round(self.amount, 2),
            "severity": self.severity,
        }
        if self.date:
            result["date"] = self.date
        if self.reference:
            result["reference"] = self.reference
        if self.details:
            result["details"] = self.details
        return result


@dataclass
class RecTestResult:
    """Result of a single reconciliation test."""

    test_name: str
    flagged_count: int = 0
    severity: str = "low"  # "low", "medium", "high"
    flagged_items: list[RecFlaggedItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "flagged_count": self.flagged_count,
            "severity": self.severity,
            "flagged_items": [item.to_dict() for item in self.flagged_items],
        }


@dataclass
class OutstandingItemsAging:
    """Aging statistics for outstanding (unmatched) items."""

    category: str  # "bank_only" or "ledger_only"
    total_count: int = 0
    over_10_days: int = 0
    over_30_days: int = 0
    oldest_item_days: Optional[int] = None
    oldest_item_date: Optional[str] = None
    oldest_item_amount: float = 0.0

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "total_count": self.total_count,
            "over_10_days": self.over_10_days,
            "over_30_days": self.over_30_days,
            "oldest_item_days": self.oldest_item_days,
            "oldest_item_date": self.oldest_item_date,
            "oldest_item_amount": round(self.oldest_item_amount, 2),
        }


def _compute_item_age_days(date_str: Optional[str], reference_date: Optional[date] = None) -> Optional[int]:
    """Compute age in days from a date string relative to reference date."""
    if not date_str:
        return None
    parsed = parse_date(date_str)
    if not parsed:
        return None
    ref = reference_date or date.today()
    return (ref - parsed).days


def _test_stale_deposits(
    bank_only_items: list[ReconciliationMatch],
    reference_date: Optional[date] = None,
) -> RecTestResult:
    """Flag bank-only items older than 10 days (stale deposits in transit)."""
    flagged: list[RecFlaggedItem] = []
    for m in bank_only_items:
        txn = m.bank_txn
        if not txn:
            continue
        age = _compute_item_age_days(txn.date, reference_date)
        if age is not None and age > 10:
            item_severity = "high" if age > 30 else "medium"
            flagged.append(
                RecFlaggedItem(
                    test_name="Stale Deposits",
                    description=f"Deposit outstanding {age} days: {txn.description[:50]}",
                    amount=txn.amount,
                    date=txn.date,
                    reference=txn.reference,
                    severity=item_severity,
                    details={"age_days": age},
                )
            )

    # Overall severity: highest individual item severity
    has_high = any(f.severity == "high" for f in flagged)
    severity = "high" if has_high else ("medium" if len(flagged) > 0 else "low")
    return RecTestResult(
        test_name="Stale Deposits (>10 days)",
        flagged_count=len(flagged),
        severity=severity,
        flagged_items=flagged,
    )


def _test_stale_checks(
    ledger_only_items: list[ReconciliationMatch],
    reference_date: Optional[date] = None,
) -> RecTestResult:
    """Flag ledger-only items older than 90 days (stale outstanding checks)."""
    flagged: list[RecFlaggedItem] = []
    for m in ledger_only_items:
        txn = m.ledger_txn
        if not txn:
            continue
        age = _compute_item_age_days(txn.date, reference_date)
        if age is not None and age > 90:
            flagged.append(
                RecFlaggedItem(
                    test_name="Stale Checks",
                    description=f"Check outstanding {age} days: {txn.description[:50]}",
                    amount=txn.amount,
                    date=txn.date,
                    reference=txn.reference,
                    severity="medium",
                    details={"age_days": age},
                )
            )

    severity = "medium" if len(flagged) > 0 else "low"
    return RecTestResult(
        test_name="Stale Checks (>90 days)",
        flagged_count=len(flagged),
        severity=severity,
        flagged_items=flagged,
    )


_NSF_KEYWORDS = re.compile(
    r"\b(nsf|return|returned|bounced|insufficient|r01|r02|chargeback|charge\s*back|reversed|dishono[u]?red)\b",
    re.IGNORECASE,
)


def _test_nsf_items(
    all_items: list[ReconciliationMatch],
) -> RecTestResult:
    """Flag items with NSF/returned/bounced/chargeback keywords in descriptions."""
    flagged: list[RecFlaggedItem] = []
    for m in all_items:
        for txn_source, txn in [("bank", m.bank_txn), ("ledger", m.ledger_txn)]:
            if not txn:
                continue
            if _NSF_KEYWORDS.search(txn.description):
                flagged.append(
                    RecFlaggedItem(
                        test_name="NSF/Returned Items",
                        description=f"NSF keyword in {txn_source}: {txn.description[:60]}",
                        amount=txn.amount,
                        date=txn.date,
                        reference=txn.reference,
                        severity="high",
                        details={"source": txn_source},
                    )
                )

    severity = "high" if len(flagged) > 0 else "low"
    return RecTestResult(
        test_name="NSF / Returned Items",
        flagged_count=len(flagged),
        severity=severity,
        flagged_items=flagged,
    )


def _test_interbank_transfers(
    all_items: list[ReconciliationMatch],
    threshold: float = 10_000.0,
) -> RecTestResult:
    """Flag same-day debit/credit pairs exceeding threshold (potential interbank transfers)."""
    flagged: list[RecFlaggedItem] = []

    # Collect all transactions with dates
    txns_by_date: dict[str, list[tuple[str, BankTransaction | LedgerTransaction]]] = {}
    for m in all_items:
        for source, txn in [("bank", m.bank_txn), ("ledger", m.ledger_txn)]:
            if txn and txn.date:
                txns_by_date.setdefault(txn.date, []).append((source, txn))

    for txn_date, day_txns in txns_by_date.items():
        debits = [(s, t) for s, t in day_txns if t.amount < 0 and abs(t.amount) >= threshold]
        credits = [(s, t) for s, t in day_txns if t.amount > 0 and t.amount >= threshold]

        for d_src, d_txn in debits:
            for c_src, c_txn in credits:
                if abs(abs(d_txn.amount) - c_txn.amount) <= 1.00:
                    flagged.append(
                        RecFlaggedItem(
                            test_name="Interbank Transfers",
                            description=(f"Same-day debit/credit pair on {txn_date}: ${abs(d_txn.amount):,.2f}"),
                            amount=abs(d_txn.amount),
                            date=txn_date,
                            severity="high",
                            details={
                                "debit_description": d_txn.description[:40],
                                "credit_description": c_txn.description[:40],
                            },
                        )
                    )

    severity = "high" if len(flagged) > 0 else "low"
    return RecTestResult(
        test_name="Interbank Transfers",
        flagged_count=len(flagged),
        severity=severity,
        flagged_items=flagged,
    )


def _test_high_value_transactions(
    all_items: list[ReconciliationMatch],
    materiality: float = 50_000.0,
) -> RecTestResult:
    """Flag single transactions exceeding the materiality threshold."""
    flagged: list[RecFlaggedItem] = []
    for m in all_items:
        for source, txn in [("bank", m.bank_txn), ("ledger", m.ledger_txn)]:
            if not txn:
                continue
            if abs(txn.amount) >= materiality:
                flagged.append(
                    RecFlaggedItem(
                        test_name="High Value Transactions",
                        description=f"{source.title()} txn >= materiality: {txn.description[:50]}",
                        amount=txn.amount,
                        date=txn.date,
                        reference=txn.reference,
                        severity="medium",
                        details={"source": source, "materiality": materiality},
                    )
                )

    severity = "medium" if len(flagged) > 0 else "low"
    return RecTestResult(
        test_name="High Value (>Materiality)",
        flagged_count=len(flagged),
        severity=severity,
        flagged_items=flagged,
    )


def run_reconciliation_tests(
    matches: list[ReconciliationMatch],
    materiality: float = 50_000.0,
    reference_date: Optional[date] = None,
) -> list[RecTestResult]:
    """Run all 5 reconciliation tests on the match results."""
    bank_only = [m for m in matches if m.match_type == MatchType.BANK_ONLY]
    ledger_only = [m for m in matches if m.match_type == MatchType.LEDGER_ONLY]

    return [
        _test_stale_deposits(bank_only, reference_date),
        _test_stale_checks(ledger_only, reference_date),
        _test_nsf_items(matches),
        _test_interbank_transfers(matches),
        _test_high_value_transactions(matches, materiality),
    ]


def compute_outstanding_items_aging(
    matches: list[ReconciliationMatch],
    reference_date: Optional[date] = None,
) -> list[OutstandingItemsAging]:
    """Compute aging statistics for bank-only and ledger-only items."""
    results: list[OutstandingItemsAging] = []

    for category, match_type, txn_attr in [
        ("bank_only", MatchType.BANK_ONLY, "bank_txn"),
        ("ledger_only", MatchType.LEDGER_ONLY, "ledger_txn"),
    ]:
        items = [m for m in matches if m.match_type == match_type]
        aging = OutstandingItemsAging(category=category, total_count=len(items))

        oldest_days: Optional[int] = None
        for m in items:
            txn = getattr(m, txn_attr)
            if not txn:
                continue
            age = _compute_item_age_days(txn.date, reference_date)
            if age is None:
                continue
            if age > 10:
                aging.over_10_days += 1
            if age > 30:
                aging.over_30_days += 1
            if oldest_days is None or age > oldest_days:
                oldest_days = age
                aging.oldest_item_days = age
                aging.oldest_item_date = txn.date
                aging.oldest_item_amount = txn.amount

        results.append(aging)

    return results


# =============================================================================
# RISK SCORING
# =============================================================================


def compute_bank_rec_risk_score(
    rec_tests: list[RecTestResult],
    summary: ReconciliationSummary,
    performance_materiality: float = 50_000.0,
) -> dict:
    """Compute composite risk score for bank reconciliation.

    Returns dict with score, risk_tier, total_flagged, flags_by_severity,
    flag_rate, tests_run, and top_findings.
    """
    score = 0.0

    has_diff = abs(summary.reconciling_difference) > 0.01
    if has_diff:
        score += 15
        if abs(summary.reconciling_difference) > performance_materiality:
            score += 10

    total_outstanding = summary.bank_only_count + summary.ledger_only_count
    if total_outstanding > 20:
        score += 8
    elif total_outstanding > 10:
        score += 4

    # Count stale items from test results
    stale_deposit_count = 0
    stale_check_count = 0
    nsf_detected = False
    kiting_detected = False
    high_value_count = 0

    for t in rec_tests:
        if "Stale Deposits" in t.test_name:
            stale_deposit_count = t.flagged_count
        elif "Stale Checks" in t.test_name:
            stale_check_count = t.flagged_count
        elif "NSF" in t.test_name:
            nsf_detected = t.flagged_count > 0
        elif "Interbank" in t.test_name:
            kiting_detected = t.flagged_count > 0
        elif "High Value" in t.test_name:
            high_value_count = t.flagged_count

    if stale_deposit_count > 0:
        score += 6
    if stale_check_count > 0:
        score += 4
    if nsf_detected:
        score += 10
    if kiting_detected:
        score += 15
    if high_value_count > 0:
        score += 5

    score = min(score, 100)

    # Risk tier (global scale)
    if score <= 10:
        tier = "low"
    elif score <= 25:
        tier = "moderate"
    elif score <= 50:
        tier = "elevated"
    else:
        tier = "high"

    # Aggregate severity counts
    high_sev = 0
    med_sev = 0
    low_sev = 0
    total_flagged = 0
    top_findings: list[str] = []

    for t in rec_tests:
        total_flagged += t.flagged_count
        if t.flagged_count > 0:
            top_findings.append(f"{t.test_name}: {t.flagged_count} items flagged")
        for item in t.flagged_items:
            sev = item.severity if hasattr(item, "severity") else "medium"
            if sev == "high":
                high_sev += 1
            elif sev == "medium":
                med_sev += 1
            else:
                low_sev += 1

    total_txns = summary.matched_count + summary.bank_only_count + summary.ledger_only_count
    flag_rate = total_flagged / total_txns if total_txns > 0 else 0.0

    return {
        "score": round(score, 1),
        "risk_tier": tier,
        "total_flagged": total_flagged,
        "flag_rate": flag_rate,
        "flags_by_severity": {"high": high_sev, "medium": med_sev, "low": low_sev},
        "tests_run": 8,
        "total_entries": total_txns,
        "top_findings": top_findings,
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def reconcile_bank_statement(
    bank_rows: list[dict],
    ledger_rows: list[dict],
    bank_columns: list[str],
    ledger_columns: list[str],
    config: Optional[BankRecConfig] = None,
    bank_mapping: Optional[dict] = None,
    ledger_mapping: Optional[dict] = None,
) -> BankRecResult:
    """Run the complete bank reconciliation pipeline.

    Args:
        bank_rows: List of dicts (raw bank statement rows)
        ledger_rows: List of dicts (raw ledger rows)
        bank_columns: Column headers from bank file
        ledger_columns: Column headers from ledger file
        config: Optional reconciliation configuration
        bank_mapping: Optional manual column mapping for bank file
        ledger_mapping: Optional manual column mapping for ledger file

    Returns:
        BankRecResult with summary, column detection results
    """
    if config is None:
        config = BankRecConfig()

    # 1. Detect columns for both files
    bank_detection = detect_bank_columns(bank_columns)
    ledger_detection = detect_bank_columns(ledger_columns)

    # Apply manual overrides if provided
    if bank_mapping:
        if "date_column" in bank_mapping:
            bank_detection.date_column = bank_mapping["date_column"]
        if "amount_column" in bank_mapping:
            bank_detection.amount_column = bank_mapping["amount_column"]
        if "description_column" in bank_mapping:
            bank_detection.description_column = bank_mapping["description_column"]
        if "reference_column" in bank_mapping:
            bank_detection.reference_column = bank_mapping["reference_column"]
        if "balance_column" in bank_mapping:
            bank_detection.balance_column = bank_mapping["balance_column"]
        bank_detection.overall_confidence = 1.0

    if ledger_mapping:
        if "date_column" in ledger_mapping:
            ledger_detection.date_column = ledger_mapping["date_column"]
        if "amount_column" in ledger_mapping:
            ledger_detection.amount_column = ledger_mapping["amount_column"]
        if "description_column" in ledger_mapping:
            ledger_detection.description_column = ledger_mapping["description_column"]
        if "reference_column" in ledger_mapping:
            ledger_detection.reference_column = ledger_mapping["reference_column"]
        if "balance_column" in ledger_mapping:
            ledger_detection.balance_column = ledger_mapping["balance_column"]
        ledger_detection.overall_confidence = 1.0

    # 2. Parse transactions
    bank_txns = parse_bank_transactions(bank_rows, bank_detection)
    ledger_txns = parse_ledger_transactions(ledger_rows, ledger_detection)

    # 3. Match transactions
    matches = match_transactions(bank_txns, ledger_txns, config)

    # 4. Calculate summary
    summary = calculate_summary(matches)

    # 5. Run reconciliation tests
    rec_tests = run_reconciliation_tests(matches, materiality=config.materiality)

    # 6. Compute outstanding items aging
    outstanding_aging = compute_outstanding_items_aging(matches)

    # 7. Compute composite risk score
    composite_score = compute_bank_rec_risk_score(
        rec_tests, summary, performance_materiality=config.performance_materiality
    )

    return BankRecResult(
        summary=summary,
        bank_column_detection=bank_detection,
        ledger_column_detection=ledger_detection,
        rec_tests=rec_tests,
        outstanding_aging=outstanding_aging,
        composite_score=composite_score,
    )
