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

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, date
import re
import math
import csv
from io import StringIO


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
    amount_tolerance: float = 0.01       # Match tolerance in dollars
    date_tolerance_days: int = 0         # Days of date tolerance for matching


# =============================================================================
# COLUMN DETECTION
# =============================================================================

class BankColumnType(str, Enum):
    """Types of columns in a bank statement or ledger file."""
    DATE = "date"
    AMOUNT = "amount"
    DESCRIPTION = "description"
    REFERENCE = "reference"
    BALANCE = "balance"
    UNKNOWN = "unknown"


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

# Map of column type to patterns — priority order
BANK_COLUMN_PATTERNS: dict[BankColumnType, list] = {
    BankColumnType.DATE: BANK_DATE_PATTERNS,
    BankColumnType.AMOUNT: BANK_AMOUNT_PATTERNS,
    BankColumnType.DESCRIPTION: BANK_DESCRIPTION_PATTERNS,
    BankColumnType.REFERENCE: BANK_REFERENCE_PATTERNS,
    BankColumnType.BALANCE: BANK_BALANCE_PATTERNS,
}


def _match_bank_column(column_name: str, patterns: list[tuple]) -> float:
    """Match a column name against patterns, return best confidence."""
    normalized = column_name.lower().strip()
    best = 0.0
    for pattern, weight, is_exact in patterns:
        if is_exact:
            if re.match(pattern, normalized, re.IGNORECASE):
                best = max(best, weight)
        else:
            if re.search(pattern, normalized, re.IGNORECASE):
                best = max(best, weight)
    return best


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

    Uses greedy assignment to prevent double-mapping.
    """
    columns = [col.strip() for col in column_names]
    notes: list[str] = []
    result = BankColumnDetectionResult(all_columns=columns)

    assigned_columns: set[str] = set()

    # Score all columns for all types
    scored: dict[str, dict[BankColumnType, float]] = {}
    for col in columns:
        scored[col] = {}
        for col_type, patterns in BANK_COLUMN_PATTERNS.items():
            scored[col][col_type] = _match_bank_column(col, patterns)

    def assign_best(col_type: BankColumnType, min_conf: float = 0.0) -> Optional[tuple[str, float]]:
        """Find the best unassigned column for a given type."""
        best_col = None
        best_conf = min_conf
        for col in columns:
            if col in assigned_columns:
                continue
            conf = scored[col].get(col_type, 0.0)
            if conf > best_conf:
                best_col = col
                best_conf = conf
        if best_col:
            assigned_columns.add(best_col)
            return best_col, best_conf
        return None

    # 1. Reference (most specific — assign first to avoid date/description stealing it)
    ref_match = assign_best(BankColumnType.REFERENCE)
    if ref_match:
        result.reference_column = ref_match[0]

    # 2. Balance (specific — assign before amount)
    bal_match = assign_best(BankColumnType.BALANCE)
    if bal_match:
        result.balance_column = bal_match[0]

    # 3. Date (required)
    date_match = assign_best(BankColumnType.DATE)
    if date_match:
        result.date_column = date_match[0]
    else:
        notes.append("Could not identify a Date column")

    # 4. Amount (required)
    amt_match = assign_best(BankColumnType.AMOUNT)
    if amt_match:
        result.amount_column = amt_match[0]
    else:
        notes.append("Could not identify an Amount column")

    # 5. Description
    desc_match = assign_best(BankColumnType.DESCRIPTION)
    if desc_match:
        result.description_column = desc_match[0]

    # Calculate overall confidence (min of required-column confidences)
    required_confidences = []

    if result.date_column and date_match:
        required_confidences.append(date_match[1])
    else:
        required_confidences.append(0.0)

    if result.amount_column and amt_match:
        required_confidences.append(amt_match[1])
    else:
        required_confidences.append(0.0)

    result.overall_confidence = min(required_confidences) if required_confidences else 0.0
    result.detection_notes = notes
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

    def to_dict(self) -> dict:
        return {
            "summary": self.summary.to_dict(),
            "bank_column_detection": self.bank_column_detection.to_dict(),
            "ledger_column_detection": self.ledger_column_detection.to_dict(),
        }


# =============================================================================
# HELPERS (duplicated from AP engine — tools are independent)
# =============================================================================

def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Try to parse a date string into a date object."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
                "%m-%d-%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def _safe_float(value) -> float:
    """Convert value to float, returning 0.0 for non-numeric.

    Handles: plain numbers, currency symbols, parenthetical negatives (1,234.56).
    """
    if value is None:
        return 0.0
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        if isinstance(value, str):
            s = value.strip()
            # Detect accounting-style parenthetical negatives: (1,234.56)
            is_negative = s.startswith("(") and s.endswith(")")
            cleaned = re.sub(r"[,$\s()%]", "", s)
            if cleaned.startswith("-") or cleaned.endswith("-"):
                cleaned = "-" + cleaned.strip("-")
                is_negative = True
            elif is_negative and not cleaned.startswith("-"):
                cleaned = "-" + cleaned
            try:
                return float(cleaned)
            except (ValueError, TypeError):
                return 0.0
        return 0.0


def _safe_str(value) -> Optional[str]:
    """Convert value to string, returning None for empty/NaN."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None
    return s


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
            txn.date = _safe_str(row.get(detection.date_column))
        if detection.amount_column:
            txn.amount = _safe_float(row.get(detection.amount_column))
        if detection.description_column:
            txn.description = _safe_str(row.get(detection.description_column)) or ""
        if detection.reference_column:
            txn.reference = _safe_str(row.get(detection.reference_column))

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
            txn.date = _safe_str(row.get(detection.date_column))
        if detection.amount_column:
            txn.amount = _safe_float(row.get(detection.amount_column))
        if detection.description_column:
            txn.description = _safe_str(row.get(detection.description_column)) or ""
        if detection.reference_column:
            txn.reference = _safe_str(row.get(detection.reference_column))

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
                bank_date = _parse_date(bank_txn.date)
                ledger_date = _parse_date(ledger_txn.date)
                if bank_date and ledger_date and bank_date != ledger_date:
                    continue
                # If either date is None, allow match (date not required)
            else:
                bank_date = _parse_date(bank_txn.date)
                ledger_date = _parse_date(ledger_txn.date)
                if bank_date and ledger_date:
                    days_diff = abs((bank_date - ledger_date).days)
                    if days_diff > config.date_tolerance_days:
                        continue

            # Match found
            matches.append(ReconciliationMatch(
                bank_txn=bank_txn,
                ledger_txn=ledger_txn,
                match_type=MatchType.MATCHED,
                match_confidence=1.0,
            ))
            matched_bank_indices.add(bank_idx)
            matched_ledger_indices.add(ledger_idx)
            break

    # Unmatched bank transactions → BANK_ONLY
    for bank_idx, bank_txn in enumerate(bank_txns):
        if bank_idx not in matched_bank_indices:
            matches.append(ReconciliationMatch(
                bank_txn=bank_txn,
                ledger_txn=None,
                match_type=MatchType.BANK_ONLY,
                match_confidence=0.0,
            ))

    # Unmatched ledger transactions → LEDGER_ONLY
    for ledger_idx, ledger_txn in enumerate(ledger_txns):
        if ledger_idx not in matched_ledger_indices:
            matches.append(ReconciliationMatch(
                bank_txn=None,
                ledger_txn=ledger_txn,
                match_type=MatchType.LEDGER_ONLY,
                match_confidence=0.0,
            ))

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
    writer.writerow([
        "Bank Date", "Bank Description", "Bank Amount", "Bank Reference",
        "Ledger Date", "Ledger Description", "Ledger Amount", "Ledger Reference",
        "Confidence",
    ])

    matched = [m for m in summary.matches if m.match_type == MatchType.MATCHED]
    for m in matched:
        bank = m.bank_txn
        ledger = m.ledger_txn
        writer.writerow([
            bank.date if bank else "",
            bank.description if bank else "",
            f"{bank.amount:.2f}" if bank else "",
            bank.reference if bank else "",
            ledger.date if ledger else "",
            ledger.description if ledger else "",
            f"{ledger.amount:.2f}" if ledger else "",
            ledger.reference if ledger else "",
            f"{m.match_confidence:.2f}",
        ])

    writer.writerow([])

    # Section 2: Outstanding Deposits (Bank Only)
    writer.writerow(["OUTSTANDING DEPOSITS (BANK ONLY)"])
    writer.writerow(["Date", "Description", "Amount", "Reference"])

    bank_only = [m for m in summary.matches if m.match_type == MatchType.BANK_ONLY]
    for m in bank_only:
        txn = m.bank_txn
        if txn:
            writer.writerow([
                txn.date or "",
                txn.description,
                f"{txn.amount:.2f}",
                txn.reference or "",
            ])

    writer.writerow([])

    # Section 3: Outstanding Checks (Ledger Only)
    writer.writerow(["OUTSTANDING CHECKS (LEDGER ONLY)"])
    writer.writerow(["Date", "Description", "Amount", "Reference"])

    ledger_only = [m for m in summary.matches if m.match_type == MatchType.LEDGER_ONLY]
    for m in ledger_only:
        txn = m.ledger_txn
        if txn:
            writer.writerow([
                txn.date or "",
                txn.description,
                f"{txn.amount:.2f}",
                txn.reference or "",
            ])

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

    return BankRecResult(
        summary=summary,
        bank_column_detection=bank_detection,
        ledger_column_detection=ledger_detection,
    )
