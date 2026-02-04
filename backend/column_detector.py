"""
Paciolus Column Detector
Intelligent CSV/Excel column identification with confidence scoring.

Detects which columns represent Account Name, Debit, and Credit values
using weighted pattern matching. Returns confidence scores to trigger
manual mapping when detection is uncertain.

Zero-Storage Compliance: Column mappings exist only in session state.
See: logs/dev-log.md for IP documentation
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import re


class ColumnType(Enum):
    """Types of columns we need to identify in a trial balance."""
    ACCOUNT = "account"
    DEBIT = "debit"
    CREDIT = "credit"
    UNKNOWN = "unknown"


@dataclass
class ColumnMatch:
    """Result of matching a column to a type."""
    column_name: str
    column_type: ColumnType
    confidence: float  # 0.0 to 1.0
    matched_pattern: Optional[str] = None


@dataclass
class ColumnDetectionResult:
    """Complete result of column detection for a file."""
    account_column: Optional[str]
    debit_column: Optional[str]
    credit_column: Optional[str]
    account_confidence: float
    debit_confidence: float
    credit_confidence: float
    overall_confidence: float
    all_columns: list[str]
    detection_notes: list[str]

    @property
    def requires_mapping(self) -> bool:
        """Returns True if confidence is below threshold (80%)."""
        return self.overall_confidence < 0.80

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "account_column": self.account_column,
            "debit_column": self.debit_column,
            "credit_column": self.credit_column,
            "account_confidence": round(self.account_confidence, 2),
            "debit_confidence": round(self.debit_confidence, 2),
            "credit_confidence": round(self.credit_confidence, 2),
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


# Weighted patterns for column detection
# Higher weight = more confident match
# Format: (pattern, weight, is_exact_match)

ACCOUNT_PATTERNS = [
    # Exact matches (highest confidence)
    (r"^account\s*name$", 1.0, True),
    (r"^account$", 0.95, True),
    (r"^gl\s*account$", 0.95, True),
    (r"^account\s*description$", 0.90, True),
    (r"^account\s*title$", 0.90, True),
    (r"^ledger\s*account$", 0.90, True),
    # Partial matches (medium confidence)
    (r"account", 0.70, False),
    (r"name", 0.50, False),
    (r"description", 0.45, False),
    (r"ledger", 0.40, False),
    (r"gl", 0.35, False),
    (r"item", 0.30, False),
]

DEBIT_PATTERNS = [
    # Exact matches (highest confidence)
    (r"^debit$", 1.0, True),
    (r"^debits$", 0.98, True),
    (r"^dr$", 0.95, True),
    (r"^debit\s*amount$", 0.95, True),
    (r"^debit\s*balance$", 0.90, True),
    # Partial matches (medium confidence)
    (r"debit", 0.80, False),
    (r"\bdr\b", 0.70, False),
    (r"amount.*dr", 0.65, False),
    (r"dr.*amount", 0.65, False),
]

CREDIT_PATTERNS = [
    # Exact matches (highest confidence)
    (r"^credit$", 1.0, True),
    (r"^credits$", 0.98, True),
    (r"^cr$", 0.95, True),
    (r"^credit\s*amount$", 0.95, True),
    (r"^credit\s*balance$", 0.90, True),
    # Partial matches (medium confidence)
    (r"credit", 0.80, False),
    (r"\bcr\b", 0.70, False),
    (r"amount.*cr", 0.65, False),
    (r"cr.*amount", 0.65, False),
]


def _match_column(column_name: str, patterns: list[tuple]) -> tuple[float, Optional[str]]:
    """
    Match a column name against patterns and return best confidence score.

    Args:
        column_name: The column name to match
        patterns: List of (pattern, weight, is_exact) tuples

    Returns:
        (confidence, matched_pattern) tuple
    """
    normalized = column_name.lower().strip()
    best_confidence = 0.0
    best_pattern = None

    for pattern, weight, is_exact in patterns:
        if is_exact:
            if re.match(pattern, normalized, re.IGNORECASE):
                if weight > best_confidence:
                    best_confidence = weight
                    best_pattern = pattern
        else:
            if re.search(pattern, normalized, re.IGNORECASE):
                if weight > best_confidence:
                    best_confidence = weight
                    best_pattern = pattern

    return best_confidence, best_pattern


def detect_columns(column_names: list[str]) -> ColumnDetectionResult:
    """
    Detect Account, Debit, and Credit columns from a list of column names.

    Uses weighted pattern matching to assign confidence scores.
    If confidence is below 80%, the frontend should trigger manual mapping.

    Args:
        column_names: List of column names from the file header

    Returns:
        ColumnDetectionResult with detected columns and confidence scores
    """
    # Normalize column names
    columns = [col.strip() for col in column_names]
    notes = []

    # Track best matches for each type
    best_account: Optional[tuple[str, float, str]] = None  # (col, conf, pattern)
    best_debit: Optional[tuple[str, float, str]] = None
    best_credit: Optional[tuple[str, float, str]] = None

    for col in columns:
        # Check account patterns
        acc_conf, acc_pattern = _match_column(col, ACCOUNT_PATTERNS)
        if acc_conf > 0 and (best_account is None or acc_conf > best_account[1]):
            best_account = (col, acc_conf, acc_pattern)

        # Check debit patterns
        deb_conf, deb_pattern = _match_column(col, DEBIT_PATTERNS)
        if deb_conf > 0 and (best_debit is None or deb_conf > best_debit[1]):
            best_debit = (col, deb_conf, deb_pattern)

        # Check credit patterns
        cred_conf, cred_pattern = _match_column(col, CREDIT_PATTERNS)
        if cred_conf > 0 and (best_credit is None or cred_conf > best_credit[1]):
            best_credit = (col, cred_conf, cred_pattern)

    # Extract results
    account_col = best_account[0] if best_account else None
    account_conf = best_account[1] if best_account else 0.0

    debit_col = best_debit[0] if best_debit else None
    debit_conf = best_debit[1] if best_debit else 0.0

    credit_col = best_credit[0] if best_credit else None
    credit_conf = best_credit[1] if best_credit else 0.0

    # Fallback: if no account column found, use first non-numeric looking column
    if account_col is None and columns:
        # Use first column as fallback
        account_col = columns[0]
        account_conf = 0.30  # Low confidence for fallback
        notes.append(f"Using first column '{account_col}' as Account (fallback)")

    # Generate notes
    if account_col and account_conf < 0.80:
        notes.append(f"Account column '{account_col}' has low confidence ({account_conf:.0%})")
    if debit_col and debit_conf < 0.80:
        notes.append(f"Debit column '{debit_col}' has low confidence ({debit_conf:.0%})")
    if credit_col and credit_conf < 0.80:
        notes.append(f"Credit column '{credit_col}' has low confidence ({credit_conf:.0%})")

    if not debit_col:
        notes.append("Could not identify Debit column")
    if not credit_col:
        notes.append("Could not identify Credit column")

    # Calculate overall confidence (minimum of required columns)
    required_confidences = []
    if debit_col:
        required_confidences.append(debit_conf)
    if credit_col:
        required_confidences.append(credit_conf)

    # Overall confidence is the minimum of debit and credit (required columns)
    # Account column is less critical since we use fallback
    if required_confidences:
        overall_conf = min(required_confidences)
    else:
        overall_conf = 0.0
        notes.append("Cannot process file: missing required Debit/Credit columns")

    return ColumnDetectionResult(
        account_column=account_col,
        debit_column=debit_col,
        credit_column=credit_col,
        account_confidence=account_conf,
        debit_confidence=debit_conf,
        credit_confidence=credit_conf,
        overall_confidence=overall_conf,
        all_columns=columns,
        detection_notes=notes,
    )


@dataclass
class ColumnMapping:
    """User-provided column mapping to override auto-detection."""
    account_column: str
    debit_column: str
    credit_column: str

    @classmethod
    def from_dict(cls, data: dict) -> "ColumnMapping":
        """Create from dictionary (API input)."""
        return cls(
            account_column=data.get("account_column", ""),
            debit_column=data.get("debit_column", ""),
            credit_column=data.get("credit_column", ""),
        )

    def is_valid(self, available_columns: list[str]) -> tuple[bool, list[str]]:
        """
        Validate that all mapped columns exist in the file.

        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        normalized_available = [c.strip().lower() for c in available_columns]

        if self.account_column.strip().lower() not in normalized_available:
            errors.append(f"Account column '{self.account_column}' not found in file")
        if self.debit_column.strip().lower() not in normalized_available:
            errors.append(f"Debit column '{self.debit_column}' not found in file")
        if self.credit_column.strip().lower() not in normalized_available:
            errors.append(f"Credit column '{self.credit_column}' not found in file")

        return len(errors) == 0, errors
