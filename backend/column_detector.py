"""Intelligent CSV/Excel column identification with confidence scoring.

DEPRECATION NOTE (Sprint 416):
This module now delegates all detection to ``shared.column_detector``.
It preserves the legacy API surface (ColumnDetectionResult, ColumnMapping,
detect_columns) for backward compatibility with 5 consumers
(audit_engine, preflight_engine, expense_category_engine,
population_profile_engine, accrual_completeness_engine).
Direct use of ``shared.column_detector`` is preferred for new code.
Full removal deferred until next major version.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from shared.column_detector import ColumnFieldConfig
from shared.column_detector import detect_columns as _shared_detect


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


# --- Shared detector configs wrapping the legacy patterns ---

TB_ACCOUNT_CONFIG = ColumnFieldConfig(
    field_name="account_column",
    patterns=ACCOUNT_PATTERNS,
    required=False,
    priority=10,
)
TB_DEBIT_CONFIG = ColumnFieldConfig(
    field_name="debit_column",
    patterns=DEBIT_PATTERNS,
    required=True,
    missing_note="Could not identify Debit column",
    priority=20,
)
TB_CREDIT_CONFIG = ColumnFieldConfig(
    field_name="credit_column",
    patterns=CREDIT_PATTERNS,
    required=True,
    missing_note="Could not identify Credit column",
    priority=30,
)
TB_COLUMN_CONFIGS = [TB_ACCOUNT_CONFIG, TB_DEBIT_CONFIG, TB_CREDIT_CONFIG]


def detect_columns(column_names: list[str]) -> ColumnDetectionResult:
    """Detect Account, Debit, and Credit columns using weighted pattern matching.

    Delegates to shared.column_detector for detection, then maps the result
    back into the legacy ColumnDetectionResult shape with TB-specific logic
    (account fallback, low-confidence notes, overall confidence).
    """
    shared_result = _shared_detect(column_names, TB_COLUMN_CONFIGS)

    account_col = shared_result.get_column("account_column")
    account_conf = shared_result.get_confidence("account_column")
    debit_col = shared_result.get_column("debit_column")
    debit_conf = shared_result.get_confidence("debit_column")
    credit_col = shared_result.get_column("credit_column")
    credit_conf = shared_result.get_confidence("credit_column")

    notes = list(shared_result.detection_notes)

    # Preserve legacy fallback: if no account found, use first column
    if account_col is None and shared_result.all_columns:
        account_col = shared_result.all_columns[0]
        account_conf = 0.30
        notes.append(f"Using first column '{account_col}' as Account (fallback)")

    # Preserve legacy low-confidence notes
    if account_col and account_conf < 0.80:
        notes.append(f"Account column '{account_col}' has low confidence ({account_conf:.0%})")
    if debit_col and debit_conf < 0.80:
        notes.append(f"Debit column '{debit_col}' has low confidence ({debit_conf:.0%})")
    if credit_col and credit_conf < 0.80:
        notes.append(f"Credit column '{credit_col}' has low confidence ({credit_conf:.0%})")

    # Overall = min of required (debit/credit) confidences
    required = []
    if debit_col:
        required.append(debit_conf)
    if credit_col:
        required.append(credit_conf)
    overall = min(required) if required else 0.0
    if not required:
        notes.append("Cannot process file: missing required Debit/Credit columns")

    return ColumnDetectionResult(
        account_column=account_col,
        debit_column=debit_col,
        credit_column=credit_col,
        account_confidence=account_conf,
        debit_confidence=debit_conf,
        credit_confidence=credit_conf,
        overall_confidence=overall,
        all_columns=shared_result.all_columns,
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
        """Validate that all mapped columns exist in the file."""
        errors = []
        normalized_available = [c.strip().lower() for c in available_columns]

        if self.account_column.strip().lower() not in normalized_available:
            errors.append(f"Account column '{self.account_column}' not found in file")
        if self.debit_column.strip().lower() not in normalized_available:
            errors.append(f"Debit column '{self.debit_column}' not found in file")
        if self.credit_column.strip().lower() not in normalized_available:
            errors.append(f"Credit column '{self.credit_column}' not found in file")

        return len(errors) == 0, errors
