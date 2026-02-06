"""
Journal Entry Testing Engine - Sprint 64 / Sprint 65 / Sprint 68

Provides automated journal entry testing for general ledger data.
Parses GL files (CSV/Excel), detects columns, runs structural and
statistical tests, scores data quality, and detects multi-currency entries.

Sprint 64 scope:
- GL column detection, dual-date, JETestingConfig, data quality, multi-currency
- Tier 1 structural tests (T1-T5): Unbalanced, Missing, Duplicate, Round, Unusual

Sprint 65 scope:
- T6: Benford's Law first-digit analysis with pre-check validation
- T7: Weekend/Holiday posting detection with amount weighting
- T8: Month-end clustering detection
- Scoring calibration fixtures for LOW/MODERATE/HIGH profiles

Sprint 68 scope:
- Tier 2 tests (T9-T13): Single-User Volume, After-Hours, Numbering Gaps,
  Backdated Entries, Suspicious Keywords
- Configurable thresholds with Conservative/Standard/Permissive presets

ZERO-STORAGE COMPLIANCE:
- All GL files processed in-memory only
- Test results are ephemeral (computed on demand)
- No raw journal entry data is stored

PCAOB / ISA References:
- PCAOB AS 2315: Audit Sampling
- ISA 330: Auditor's Responses to Assessed Risks
- ISA 240: Auditor's Responsibilities Relating to Fraud
- ISA 530: Audit Sampling (Benford's Law as analytical procedure)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, date
from calendar import monthrange
import re
import math
import statistics


# =============================================================================
# ENUMS
# =============================================================================

class RiskTier(str, Enum):
    """Composite risk tier for JE testing results."""
    LOW = "low"                  # Score 0-9
    ELEVATED = "elevated"        # Score 10-24
    MODERATE = "moderate"        # Score 25-49
    HIGH = "high"                # Score 50-74
    CRITICAL = "critical"        # Score 75+


class TestTier(str, Enum):
    """Test classification tier."""
    STRUCTURAL = "structural"    # Tier 1: Basic structural checks
    STATISTICAL = "statistical"  # Tier 2: Statistical analysis (future)
    ADVANCED = "advanced"        # Tier 3: Advanced patterns (future)


class Severity(str, Enum):
    """Severity of a flagged entry."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class JETestingConfig:
    """Configurable thresholds for all JE tests.

    Defaults are sensible for most GL datasets. UI for customization
    is planned for Sprint 68 (Practice Settings integration).
    """
    # T1: Unbalanced Entries
    balance_tolerance: float = 0.01  # Rounding tolerance for debit/credit match

    # T4: Round Dollar Amounts
    round_amount_threshold: float = 10000.0  # Min amount for rounding check
    round_amount_max_flags: int = 50  # Max flags to return

    # T5: Unusual Amounts
    unusual_amount_stddev: float = 3.0  # Std devs from mean to flag
    unusual_amount_min_entries: int = 5  # Min entries per account for stats

    # T6: Benford's Law
    benford_min_entries: int = 500  # Min entries for Benford analysis
    benford_min_magnitude_range: int = 2  # Min orders of magnitude ($10→$1,000+)
    benford_min_amount: float = 1.0  # Exclude sub-dollar entries

    # T7: Weekend posting
    weekend_posting_enabled: bool = True
    weekend_large_amount_threshold: float = 10000.0  # Amount weighting threshold

    # T8: Month-end clustering
    month_end_days: int = 3  # Last N days of month to check
    month_end_volume_multiplier: float = 2.0  # Flag if > Nx average daily

    # T9: Single-User High-Volume
    single_user_volume_pct: float = 0.25  # Flag users posting >25% of entries
    single_user_max_flags: int = 20  # Max flagged entries per high-volume user

    # T10: After-Hours Postings
    after_hours_enabled: bool = True
    after_hours_start: int = 18  # Business hours end (hour, 24h format)
    after_hours_end: int = 6  # Business hours start (hour, 24h format)
    after_hours_large_threshold: float = 10000.0  # Amount for high severity

    # T11: Sequential Numbering Gaps
    numbering_gap_enabled: bool = True
    numbering_gap_min_size: int = 2  # Minimum gap size to flag

    # T12: Backdated Entries
    backdate_enabled: bool = True
    backdate_days_threshold: int = 30  # Days difference to flag

    # T13: Suspicious Keywords
    suspicious_keyword_enabled: bool = True
    suspicious_keyword_threshold: float = 0.60  # Confidence threshold


# =============================================================================
# GL COLUMN DETECTION
# =============================================================================

class GLColumnType(str, Enum):
    """Types of columns in a General Ledger file."""
    DATE = "date"
    ENTRY_DATE = "entry_date"
    POSTING_DATE = "posting_date"
    ACCOUNT = "account"
    DESCRIPTION = "description"
    DEBIT = "debit"
    CREDIT = "credit"
    AMOUNT = "amount"
    REFERENCE = "reference"
    POSTED_BY = "posted_by"
    SOURCE = "source"
    CURRENCY = "currency"
    ENTRY_ID = "entry_id"
    UNKNOWN = "unknown"


# Weighted regex patterns for GL column detection
# Format: (pattern, weight, is_exact)
GL_DATE_PATTERNS = [
    (r"^date$", 0.85, True),
    (r"^transaction\s*date$", 0.95, True),
    (r"^trans\s*date$", 0.90, True),
    (r"^journal\s*date$", 0.90, True),
    (r"^jnl\s*date$", 0.85, True),
    (r"^effective\s*date$", 0.85, True),
    (r"date", 0.50, False),
]

GL_ENTRY_DATE_PATTERNS = [
    (r"^entry\s*date$", 0.98, True),
    (r"^created\s*date$", 0.85, True),
    (r"^entered\s*date$", 0.90, True),
    (r"^input\s*date$", 0.80, True),
    (r"^original\s*date$", 0.80, True),
]

GL_POSTING_DATE_PATTERNS = [
    (r"^posting\s*date$", 0.98, True),
    (r"^post\s*date$", 0.95, True),
    (r"^posted\s*date$", 0.90, True),
    (r"^gl\s*date$", 0.85, True),
    (r"^period\s*date$", 0.80, True),
]

GL_ACCOUNT_PATTERNS = [
    (r"^account\s*name$", 1.0, True),
    (r"^account$", 0.95, True),
    (r"^gl\s*account$", 0.95, True),
    (r"^account\s*description$", 0.90, True),
    (r"^account\s*title$", 0.90, True),
    (r"^ledger\s*account$", 0.90, True),
    (r"^account\s*code$", 0.85, True),
    (r"^acct$", 0.80, True),
    (r"account", 0.60, False),
]

GL_DESCRIPTION_PATTERNS = [
    (r"^description$", 1.0, True),
    (r"^memo$", 0.95, True),
    (r"^narration$", 0.95, True),
    (r"^narrative$", 0.90, True),
    (r"^journal\s*description$", 0.95, True),
    (r"^line\s*description$", 0.90, True),
    (r"^comment$", 0.80, True),
    (r"^remarks$", 0.80, True),
    (r"^text$", 0.50, True),
    (r"description", 0.70, False),
    (r"memo", 0.65, False),
]

GL_DEBIT_PATTERNS = [
    (r"^debit$", 1.0, True),
    (r"^debits$", 0.98, True),
    (r"^dr$", 0.95, True),
    (r"^debit\s*amount$", 0.95, True),
    (r"debit", 0.80, False),
    (r"\bdr\b", 0.70, False),
]

GL_CREDIT_PATTERNS = [
    (r"^credit$", 1.0, True),
    (r"^credits$", 0.98, True),
    (r"^cr$", 0.95, True),
    (r"^credit\s*amount$", 0.95, True),
    (r"credit", 0.80, False),
    (r"\bcr\b", 0.70, False),
]

GL_AMOUNT_PATTERNS = [
    (r"^amount$", 0.95, True),
    (r"^journal\s*amount$", 0.90, True),
    (r"^line\s*amount$", 0.90, True),
    (r"^transaction\s*amount$", 0.90, True),
    (r"^value$", 0.60, True),
    (r"amount", 0.65, False),
]

GL_REFERENCE_PATTERNS = [
    (r"^reference$", 0.95, True),
    (r"^ref$", 0.90, True),
    (r"^document\s*number$", 0.90, True),
    (r"^doc\s*no$", 0.90, True),
    (r"^doc\s*number$", 0.90, True),
    (r"^voucher$", 0.85, True),
    (r"^voucher\s*number$", 0.90, True),
    (r"^journal\s*number$", 0.90, True),
    (r"^journal\s*no$", 0.85, True),
    (r"^jnl\s*no$", 0.85, True),
    (r"^batch\s*number$", 0.80, True),
    (r"^batch\s*no$", 0.80, True),
    (r"reference", 0.65, False),
    (r"voucher", 0.60, False),
]

GL_POSTED_BY_PATTERNS = [
    (r"^posted\s*by$", 0.98, True),
    (r"^entered\s*by$", 0.95, True),
    (r"^created\s*by$", 0.95, True),
    (r"^user$", 0.80, True),
    (r"^user\s*id$", 0.90, True),
    (r"^user\s*name$", 0.90, True),
    (r"^preparer$", 0.85, True),
    (r"posted.?by", 0.70, False),
    (r"entered.?by", 0.70, False),
    (r"created.?by", 0.70, False),
]

GL_SOURCE_PATTERNS = [
    (r"^source$", 0.95, True),
    (r"^source\s*module$", 0.95, True),
    (r"^module$", 0.85, True),
    (r"^journal\s*source$", 0.90, True),
    (r"^origin$", 0.80, True),
    (r"^system$", 0.70, True),
    (r"source", 0.60, False),
]

GL_CURRENCY_PATTERNS = [
    (r"^currency$", 0.98, True),
    (r"^currency\s*code$", 0.95, True),
    (r"^ccy$", 0.90, True),
    (r"^curr$", 0.85, True),
    (r"^fx\s*currency$", 0.90, True),
    (r"currency", 0.70, False),
]

GL_ENTRY_ID_PATTERNS = [
    (r"^entry\s*id$", 0.98, True),
    (r"^journal\s*id$", 0.95, True),
    (r"^je\s*id$", 0.95, True),
    (r"^journal\s*entry\s*id$", 0.98, True),
    (r"^transaction\s*id$", 0.90, True),
    (r"^trans\s*id$", 0.85, True),
    (r"^id$", 0.50, True),
    (r"entry.?id", 0.75, False),
]

# Map of GL column type to its patterns
GL_COLUMN_PATTERNS: dict[GLColumnType, list] = {
    GLColumnType.ENTRY_DATE: GL_ENTRY_DATE_PATTERNS,
    GLColumnType.POSTING_DATE: GL_POSTING_DATE_PATTERNS,
    GLColumnType.DATE: GL_DATE_PATTERNS,
    GLColumnType.ACCOUNT: GL_ACCOUNT_PATTERNS,
    GLColumnType.DESCRIPTION: GL_DESCRIPTION_PATTERNS,
    GLColumnType.DEBIT: GL_DEBIT_PATTERNS,
    GLColumnType.CREDIT: GL_CREDIT_PATTERNS,
    GLColumnType.AMOUNT: GL_AMOUNT_PATTERNS,
    GLColumnType.REFERENCE: GL_REFERENCE_PATTERNS,
    GLColumnType.POSTED_BY: GL_POSTED_BY_PATTERNS,
    GLColumnType.SOURCE: GL_SOURCE_PATTERNS,
    GLColumnType.CURRENCY: GL_CURRENCY_PATTERNS,
    GLColumnType.ENTRY_ID: GL_ENTRY_ID_PATTERNS,
}


def _match_gl_column(column_name: str, patterns: list[tuple]) -> float:
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
class GLColumnDetectionResult:
    """Result of GL column detection."""
    # Required columns
    date_column: Optional[str] = None
    account_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None
    amount_column: Optional[str] = None  # Alternative: single amount column

    # Optional columns
    entry_date_column: Optional[str] = None
    posting_date_column: Optional[str] = None
    description_column: Optional[str] = None
    reference_column: Optional[str] = None
    posted_by_column: Optional[str] = None
    source_column: Optional[str] = None
    currency_column: Optional[str] = None
    entry_id_column: Optional[str] = None

    # Metadata
    has_dual_dates: bool = False
    has_separate_debit_credit: bool = False
    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "date_column": self.date_column,
            "account_column": self.account_column,
            "debit_column": self.debit_column,
            "credit_column": self.credit_column,
            "amount_column": self.amount_column,
            "entry_date_column": self.entry_date_column,
            "posting_date_column": self.posting_date_column,
            "description_column": self.description_column,
            "reference_column": self.reference_column,
            "posted_by_column": self.posted_by_column,
            "source_column": self.source_column,
            "currency_column": self.currency_column,
            "entry_id_column": self.entry_id_column,
            "has_dual_dates": self.has_dual_dates,
            "has_separate_debit_credit": self.has_separate_debit_credit,
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


def detect_gl_columns(column_names: list[str]) -> GLColumnDetectionResult:
    """Detect GL columns using weighted pattern matching.

    Supports:
    - Dual date columns (entry_date + posting_date) or single date
    - Debit/credit pair or single amount column
    - Optional columns: description, reference, posted_by, source, currency, entry_id
    """
    columns = [col.strip() for col in column_names]
    notes: list[str] = []
    result = GLColumnDetectionResult(all_columns=columns)

    # Track best match per column type, preventing double-assignment
    assigned_columns: set[str] = set()

    # Score all columns for all types
    scored: dict[str, dict[GLColumnType, float]] = {}
    for col in columns:
        scored[col] = {}
        for col_type, patterns in GL_COLUMN_PATTERNS.items():
            scored[col][col_type] = _match_gl_column(col, patterns)

    def assign_best(col_type: GLColumnType, min_conf: float = 0.0) -> Optional[tuple[str, float]]:
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

    # 1. Try dual dates first (higher priority patterns)
    entry_date_match = assign_best(GLColumnType.ENTRY_DATE, 0.70)
    posting_date_match = assign_best(GLColumnType.POSTING_DATE, 0.70)

    if entry_date_match and posting_date_match:
        result.entry_date_column = entry_date_match[0]
        result.posting_date_column = posting_date_match[0]
        result.date_column = posting_date_match[0]  # Primary date = posting date
        result.has_dual_dates = True
        notes.append("Dual-date detected: entry_date + posting_date")
    else:
        # Release any partial dual-date assignments
        if entry_date_match:
            assigned_columns.discard(entry_date_match[0])
        if posting_date_match:
            assigned_columns.discard(posting_date_match[0])

        # Fall back to generic date
        date_match = assign_best(GLColumnType.DATE)
        if date_match:
            result.date_column = date_match[0]
        # Also try entry_date or posting_date individually as the main date
        elif entry_date_match:
            assigned_columns.add(entry_date_match[0])
            result.date_column = entry_date_match[0]
            result.entry_date_column = entry_date_match[0]
        elif posting_date_match:
            assigned_columns.add(posting_date_match[0])
            result.date_column = posting_date_match[0]
            result.posting_date_column = posting_date_match[0]

    # 2. Account column (required)
    acct_match = assign_best(GLColumnType.ACCOUNT)
    if acct_match:
        result.account_column = acct_match[0]

    # 3. Debit/Credit pair or single Amount
    debit_match = assign_best(GLColumnType.DEBIT)
    credit_match = assign_best(GLColumnType.CREDIT)

    if debit_match and credit_match:
        result.debit_column = debit_match[0]
        result.credit_column = credit_match[0]
        result.has_separate_debit_credit = True
    else:
        # Release partial assignments
        if debit_match:
            assigned_columns.discard(debit_match[0])
        if credit_match:
            assigned_columns.discard(credit_match[0])

        # Try single amount column
        amt_match = assign_best(GLColumnType.AMOUNT)
        if amt_match:
            result.amount_column = amt_match[0]
        else:
            notes.append("Could not identify Debit/Credit or Amount columns")

    # 4. Entry ID
    eid_match = assign_best(GLColumnType.ENTRY_ID)
    if eid_match:
        result.entry_id_column = eid_match[0]

    # 5. Reference
    ref_match = assign_best(GLColumnType.REFERENCE)
    if ref_match:
        result.reference_column = ref_match[0]

    # 6. Optional columns
    desc_match = assign_best(GLColumnType.DESCRIPTION)
    if desc_match:
        result.description_column = desc_match[0]

    posted_match = assign_best(GLColumnType.POSTED_BY)
    if posted_match:
        result.posted_by_column = posted_match[0]

    source_match = assign_best(GLColumnType.SOURCE)
    if source_match:
        result.source_column = source_match[0]

    currency_match = assign_best(GLColumnType.CURRENCY)
    if currency_match:
        result.currency_column = currency_match[0]

    # Calculate overall confidence
    required_confidences = []
    if result.date_column:
        # Use the confidence from whichever date we found
        if result.has_dual_dates and posting_date_match:
            required_confidences.append(posting_date_match[1])
        else:
            # Re-score: find the confidence of the assigned date column
            date_conf = max(
                scored.get(result.date_column, {}).get(GLColumnType.DATE, 0.0),
                scored.get(result.date_column, {}).get(GLColumnType.ENTRY_DATE, 0.0),
                scored.get(result.date_column, {}).get(GLColumnType.POSTING_DATE, 0.0),
            )
            required_confidences.append(date_conf)
    else:
        required_confidences.append(0.0)
        notes.append("Could not identify a Date column")

    if result.account_column and acct_match:
        required_confidences.append(acct_match[1])
    else:
        required_confidences.append(0.0)
        notes.append("Could not identify an Account column")

    if result.has_separate_debit_credit and debit_match and credit_match:
        required_confidences.append(min(debit_match[1], credit_match[1]))
    elif result.amount_column and amt_match:
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
class JournalEntry:
    """A single journal entry line from the GL."""
    entry_id: Optional[str] = None
    entry_date: Optional[str] = None
    posting_date: Optional[str] = None
    account: str = ""
    description: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    posted_by: Optional[str] = None
    source: Optional[str] = None
    reference: Optional[str] = None
    currency: Optional[str] = None
    row_number: int = 0

    @property
    def net_amount(self) -> float:
        return self.debit - self.credit

    @property
    def abs_amount(self) -> float:
        return max(self.debit, self.credit)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "entry_date": self.entry_date,
            "posting_date": self.posting_date,
            "account": self.account,
            "description": self.description,
            "debit": self.debit,
            "credit": self.credit,
            "posted_by": self.posted_by,
            "source": self.source,
            "reference": self.reference,
            "currency": self.currency,
            "row_number": self.row_number,
        }


@dataclass
class FlaggedEntry:
    """An entry flagged by one or more tests."""
    entry: JournalEntry
    test_name: str
    test_key: str
    test_tier: TestTier
    severity: Severity
    issue: str
    confidence: float = 1.0
    details: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "entry": self.entry.to_dict(),
            "test_name": self.test_name,
            "test_key": self.test_key,
            "test_tier": self.test_tier.value,
            "severity": self.severity.value,
            "issue": self.issue,
            "confidence": round(self.confidence, 2),
            "details": self.details,
        }


@dataclass
class TestResult:
    """Result of a single test."""
    test_name: str
    test_key: str
    test_tier: TestTier
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Severity
    description: str
    flagged_entries: list[FlaggedEntry] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "test_key": self.test_key,
            "test_tier": self.test_tier.value,
            "entries_flagged": self.entries_flagged,
            "total_entries": self.total_entries,
            "flag_rate": round(self.flag_rate, 4),
            "severity": self.severity.value,
            "description": self.description,
            "flagged_entries": [f.to_dict() for f in self.flagged_entries],
        }


@dataclass
class GLDataQuality:
    """Quality assessment of the GL data."""
    completeness_score: float  # 0-100
    field_fill_rates: dict[str, float] = field(default_factory=dict)
    detected_issues: list[str] = field(default_factory=list)
    total_rows: int = 0

    def to_dict(self) -> dict:
        return {
            "completeness_score": round(self.completeness_score, 1),
            "field_fill_rates": {k: round(v, 2) for k, v in self.field_fill_rates.items()},
            "detected_issues": self.detected_issues,
            "total_rows": self.total_rows,
        }


@dataclass
class MultiCurrencyWarning:
    """Warning when multiple currencies are detected in GL data."""
    currencies_found: list[str] = field(default_factory=list)
    primary_currency: Optional[str] = None
    entry_counts_by_currency: dict[str, int] = field(default_factory=dict)
    warning_message: str = ""

    def to_dict(self) -> dict:
        return {
            "currencies_found": self.currencies_found,
            "primary_currency": self.primary_currency,
            "entry_counts_by_currency": self.entry_counts_by_currency,
            "warning_message": self.warning_message,
        }


@dataclass
class CompositeScore:
    """Overall JE testing composite score."""
    score: float  # 0-100
    risk_tier: RiskTier
    tests_run: int
    total_entries: int
    total_flagged: int
    flag_rate: float
    flags_by_severity: dict[str, int] = field(default_factory=dict)
    top_findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "risk_tier": self.risk_tier.value,
            "tests_run": self.tests_run,
            "total_entries": self.total_entries,
            "total_flagged": self.total_flagged,
            "flag_rate": round(self.flag_rate, 4),
            "flags_by_severity": self.flags_by_severity,
            "top_findings": self.top_findings,
        }


@dataclass
class BenfordResult:
    """Results of Benford's Law first-digit analysis (Sprint 65)."""
    passed_prechecks: bool
    precheck_message: Optional[str] = None
    eligible_count: int = 0
    total_count: int = 0
    expected_distribution: dict[int, float] = field(default_factory=dict)
    actual_distribution: dict[int, float] = field(default_factory=dict)
    actual_counts: dict[int, int] = field(default_factory=dict)
    deviation_by_digit: dict[int, float] = field(default_factory=dict)
    mad: float = 0.0
    chi_squared: float = 0.0
    conformity_level: str = ""  # conforming, acceptable, marginally_acceptable, nonconforming
    most_deviated_digits: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed_prechecks": self.passed_prechecks,
            "precheck_message": self.precheck_message,
            "eligible_count": self.eligible_count,
            "total_count": self.total_count,
            "expected_distribution": {str(k): round(v, 5) for k, v in self.expected_distribution.items()},
            "actual_distribution": {str(k): round(v, 5) for k, v in self.actual_distribution.items()},
            "actual_counts": {str(k): v for k, v in self.actual_counts.items()},
            "deviation_by_digit": {str(k): round(v, 5) for k, v in self.deviation_by_digit.items()},
            "mad": round(self.mad, 5),
            "chi_squared": round(self.chi_squared, 3),
            "conformity_level": self.conformity_level,
            "most_deviated_digits": self.most_deviated_digits,
        }


@dataclass
class JETestingResult:
    """Complete result of journal entry testing."""
    composite_score: CompositeScore
    test_results: list[TestResult] = field(default_factory=list)
    data_quality: Optional[GLDataQuality] = None
    multi_currency_warning: Optional[MultiCurrencyWarning] = None
    column_detection: Optional[GLColumnDetectionResult] = None
    benford_result: Optional[BenfordResult] = None

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [t.to_dict() for t in self.test_results],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "multi_currency_warning": self.multi_currency_warning.to_dict() if self.multi_currency_warning else None,
            "column_detection": self.column_detection.to_dict() if self.column_detection else None,
            "benford_result": self.benford_result.to_dict() if self.benford_result else None,
        }


# =============================================================================
# RISK TIER CALCULATION
# =============================================================================

def score_to_risk_tier(score: float) -> RiskTier:
    """Map a composite score (0-100) to a risk tier."""
    if score < 10:
        return RiskTier.LOW
    elif score < 25:
        return RiskTier.ELEVATED
    elif score < 50:
        return RiskTier.MODERATE
    elif score < 75:
        return RiskTier.HIGH
    else:
        return RiskTier.CRITICAL


# =============================================================================
# GL PARSER
# =============================================================================

def parse_gl_entries(
    rows: list[dict],
    detection: GLColumnDetectionResult,
) -> list[JournalEntry]:
    """Parse raw GL rows into JournalEntry objects using detected columns.

    Args:
        rows: List of dicts (each row from CSV/Excel)
        detection: Column detection result mapping column names

    Returns:
        List of JournalEntry objects
    """
    entries: list[JournalEntry] = []

    for idx, row in enumerate(rows):
        entry = JournalEntry(row_number=idx + 1)

        # Date fields
        if detection.entry_date_column:
            entry.entry_date = _safe_str(row.get(detection.entry_date_column))
        if detection.posting_date_column:
            entry.posting_date = _safe_str(row.get(detection.posting_date_column))
        if detection.date_column and not entry.posting_date:
            entry.posting_date = _safe_str(row.get(detection.date_column))
        if not entry.entry_date and detection.date_column:
            entry.entry_date = _safe_str(row.get(detection.date_column))

        # Account
        if detection.account_column:
            entry.account = _safe_str(row.get(detection.account_column)) or ""

        # Amounts
        if detection.has_separate_debit_credit:
            entry.debit = _safe_float(row.get(detection.debit_column))
            entry.credit = _safe_float(row.get(detection.credit_column))
        elif detection.amount_column:
            amt = _safe_float(row.get(detection.amount_column))
            if amt >= 0:
                entry.debit = amt
            else:
                entry.credit = abs(amt)

        # Optional fields
        if detection.description_column:
            entry.description = _safe_str(row.get(detection.description_column))
        if detection.reference_column:
            entry.reference = _safe_str(row.get(detection.reference_column))
        if detection.posted_by_column:
            entry.posted_by = _safe_str(row.get(detection.posted_by_column))
        if detection.source_column:
            entry.source = _safe_str(row.get(detection.source_column))
        if detection.currency_column:
            entry.currency = _safe_str(row.get(detection.currency_column))
        if detection.entry_id_column:
            entry.entry_id = _safe_str(row.get(detection.entry_id_column))

        entries.append(entry)

    return entries


def _safe_str(value) -> Optional[str]:
    """Convert value to string, returning None for empty/NaN."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None
    return s


def _safe_float(value) -> float:
    """Convert value to float, returning 0.0 for non-numeric."""
    if value is None:
        return 0.0
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        # Try stripping currency symbols
        if isinstance(value, str):
            cleaned = re.sub(r"[,$\s()%]", "", value)
            if cleaned.startswith("-") or cleaned.endswith("-"):
                cleaned = "-" + cleaned.strip("-")
            try:
                return float(cleaned)
            except (ValueError, TypeError):
                return 0.0
        return 0.0


# =============================================================================
# DATA QUALITY SCORING
# =============================================================================

def assess_data_quality(
    entries: list[JournalEntry],
    detection: GLColumnDetectionResult,
) -> GLDataQuality:
    """Assess the quality and completeness of GL data.

    Checks fill rates for all detected columns and flags issues
    like blank descriptions, missing references, etc.
    """
    total = len(entries)
    if total == 0:
        return GLDataQuality(completeness_score=0.0, total_rows=0)

    issues: list[str] = []
    fill_rates: dict[str, float] = {}

    # Check fill rates for key fields
    date_filled = sum(1 for e in entries if e.posting_date or e.entry_date)
    fill_rates["date"] = date_filled / total

    acct_filled = sum(1 for e in entries if e.account)
    fill_rates["account"] = acct_filled / total

    amount_filled = sum(1 for e in entries if e.debit > 0 or e.credit > 0)
    fill_rates["amount"] = amount_filled / total

    if detection.description_column:
        desc_filled = sum(1 for e in entries if e.description)
        fill_rates["description"] = desc_filled / total
        if fill_rates["description"] < 0.80:
            issues.append(
                f"Low description fill rate: {fill_rates['description']:.0%} "
                f"({total - desc_filled} blank)"
            )

    if detection.reference_column:
        ref_filled = sum(1 for e in entries if e.reference)
        fill_rates["reference"] = ref_filled / total
        if fill_rates["reference"] < 0.80:
            issues.append(
                f"Low reference fill rate: {fill_rates['reference']:.0%}"
            )

    if detection.posted_by_column:
        user_filled = sum(1 for e in entries if e.posted_by)
        fill_rates["posted_by"] = user_filled / total
        if fill_rates["posted_by"] < 0.50:
            issues.append(
                f"Low posted_by fill rate: {fill_rates['posted_by']:.0%}"
            )

    if detection.entry_id_column:
        eid_filled = sum(1 for e in entries if e.entry_id)
        fill_rates["entry_id"] = eid_filled / total

    if detection.source_column:
        src_filled = sum(1 for e in entries if e.source)
        fill_rates["source"] = src_filled / total

    # Flag issues
    if fill_rates.get("date", 0) < 0.95:
        issues.append(f"Missing dates on {total - date_filled} entries")

    if fill_rates.get("account", 0) < 0.95:
        issues.append(f"Missing account on {total - acct_filled} entries")

    if fill_rates.get("amount", 0) < 0.90:
        zero_amt = total - amount_filled
        issues.append(f"{zero_amt} entries have zero amount (both debit and credit are 0)")

    # Completeness score: weighted average of required + optional fill rates
    weights = {"date": 0.30, "account": 0.30, "amount": 0.25}
    optional_weight = 0.15 / max(
        len([k for k in fill_rates if k not in weights]), 1
    )
    for k in fill_rates:
        if k not in weights:
            weights[k] = optional_weight

    score = sum(fill_rates.get(k, 0) * w for k, w in weights.items()) * 100

    return GLDataQuality(
        completeness_score=min(score, 100.0),
        field_fill_rates=fill_rates,
        detected_issues=issues,
        total_rows=total,
    )


# =============================================================================
# MULTI-CURRENCY DETECTION
# =============================================================================

def detect_multi_currency(entries: list[JournalEntry]) -> Optional[MultiCurrencyWarning]:
    """Detect if GL contains multiple currencies. Warn only — no conversion.

    Returns None if no currency column detected or only one currency present.
    """
    currencies: dict[str, int] = {}
    for e in entries:
        if e.currency:
            cur = e.currency.upper().strip()
            if cur:
                currencies[cur] = currencies.get(cur, 0) + 1

    if len(currencies) <= 1:
        return None

    # Find primary currency (most entries)
    primary = max(currencies, key=currencies.get)  # type: ignore[arg-type]
    sorted_currencies = sorted(currencies.keys())

    return MultiCurrencyWarning(
        currencies_found=sorted_currencies,
        primary_currency=primary,
        entry_counts_by_currency=currencies,
        warning_message=(
            f"Multi-currency GL detected ({len(currencies)} currencies: "
            f"{', '.join(sorted_currencies)}). "
            f"Results may be affected by exchange rate differences. "
            f"Primary currency: {primary} ({currencies[primary]} entries)."
        ),
    )


# =============================================================================
# TIER 1 TESTS — STRUCTURAL
# =============================================================================

# Rounding patterns for T4 (reuse pattern from Sprint 42)
ROUND_AMOUNT_PATTERNS: list[tuple[float, str, Severity]] = [
    (100000.0, "hundred_thousand", Severity.HIGH),
    (50000.0, "fifty_thousand", Severity.MEDIUM),
    (10000.0, "ten_thousand", Severity.LOW),
]


def test_unbalanced_entries(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T1: Flag journal entries where total debits != total credits.

    Groups entries by entry_id (or reference as fallback).
    An unbalanced entry is a serious structural issue.
    """
    # Group by entry_id or reference
    groups: dict[str, list[JournalEntry]] = {}
    ungrouped: list[JournalEntry] = []

    for e in entries:
        key = e.entry_id or e.reference
        if key:
            groups.setdefault(key, []).append(e)
        else:
            ungrouped.append(e)

    flagged: list[FlaggedEntry] = []
    total_groups = len(groups)

    for group_key, group_entries in groups.items():
        total_debit = sum(e.debit for e in group_entries)
        total_credit = sum(e.credit for e in group_entries)
        diff = abs(total_debit - total_credit)

        if diff > config.balance_tolerance:
            severity = Severity.HIGH if diff > 1000 else (
                Severity.MEDIUM if diff > 10 else Severity.LOW
            )
            for e in group_entries:
                flagged.append(FlaggedEntry(
                    entry=e,
                    test_name="Unbalanced Entries",
                    test_key="unbalanced_entries",
                    test_tier=TestTier.STRUCTURAL,
                    severity=severity,
                    issue=f"Entry {group_key}: debits ({total_debit:,.2f}) != credits ({total_credit:,.2f}), difference: {diff:,.2f}",
                    details={
                        "group_key": group_key,
                        "total_debit": total_debit,
                        "total_credit": total_credit,
                        "difference": diff,
                    },
                ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Unbalanced Entries",
        test_key="unbalanced_entries",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags journal entries where total debits do not equal total credits (grouped by entry ID or reference).",
        flagged_entries=flagged,
    )


def test_missing_fields(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T2: Flag entries with blank required fields (account, date, amount)."""
    flagged: list[FlaggedEntry] = []

    for e in entries:
        missing = []
        if not e.account:
            missing.append("account")
        if not e.posting_date and not e.entry_date:
            missing.append("date")
        if e.debit == 0 and e.credit == 0:
            missing.append("amount")

        if missing:
            flagged.append(FlaggedEntry(
                entry=e,
                test_name="Missing Fields",
                test_key="missing_fields",
                test_tier=TestTier.STRUCTURAL,
                severity=Severity.MEDIUM if "account" in missing or "date" in missing else Severity.LOW,
                issue=f"Missing required fields: {', '.join(missing)}",
                details={"missing_fields": missing},
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Missing Fields",
        test_key="missing_fields",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags entries with blank account, date, or amount fields.",
        flagged_entries=flagged,
    )


def test_duplicate_entries(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T3: Flag exact duplicate entries (same date + account + amount + description)."""
    seen: dict[tuple, list[int]] = {}

    for idx, e in enumerate(entries):
        key = (
            e.posting_date or e.entry_date or "",
            e.account.lower().strip(),
            round(e.debit, 2),
            round(e.credit, 2),
            (e.description or "").lower().strip(),
        )
        seen.setdefault(key, []).append(idx)

    flagged: list[FlaggedEntry] = []
    for key, indices in seen.items():
        if len(indices) > 1:
            for idx in indices:
                e = entries[idx]
                flagged.append(FlaggedEntry(
                    entry=e,
                    test_name="Duplicate Entries",
                    test_key="duplicate_entries",
                    test_tier=TestTier.STRUCTURAL,
                    severity=Severity.MEDIUM,
                    issue=f"Duplicate entry: {len(indices)} identical entries found (date={key[0]}, account={key[1]}, amount={key[2] or key[3]:.2f})",
                    confidence=0.90,
                    details={
                        "duplicate_count": len(indices),
                        "row_numbers": [entries[i].row_number for i in indices],
                    },
                ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Duplicate Entries",
        test_key="duplicate_entries",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags exact duplicate entries with matching date, account, amount, and description.",
        flagged_entries=flagged,
    )


def test_round_amounts(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T4: Flag entries at round dollar amounts ($X,000 or $X0,000).

    Reuses rounding detection pattern from Sprint 42.
    """
    flagged: list[FlaggedEntry] = []

    for e in entries:
        amt = e.abs_amount
        if amt < config.round_amount_threshold:
            continue

        for divisor, name, severity in ROUND_AMOUNT_PATTERNS:
            if amt >= divisor and amt % divisor == 0:
                flagged.append(FlaggedEntry(
                    entry=e,
                    test_name="Round Dollar Amounts",
                    test_key="round_amounts",
                    test_tier=TestTier.STRUCTURAL,
                    severity=severity,
                    issue=f"Round amount: ${amt:,.0f} (divisible by ${divisor:,.0f})",
                    confidence=0.70,
                    details={"amount": amt, "pattern": name, "divisor": divisor},
                ))
                break  # Only flag the largest pattern match

        if len(flagged) >= config.round_amount_max_flags:
            break

    # Sort by amount descending
    flagged.sort(key=lambda f: f.entry.abs_amount, reverse=True)

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Round Dollar Amounts",
        test_key="round_amounts",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.LOW,
        description="Flags entries at round dollar amounts that may indicate estimates or manipulation.",
        flagged_entries=flagged,
    )


def test_unusual_amounts(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T5: Flag entries exceeding N standard deviations from account mean.

    Groups entries by account, calculates mean and stddev per account,
    then flags entries that are statistical outliers.
    """
    # Group amounts by account
    account_amounts: dict[str, list[float]] = {}
    account_entries: dict[str, list[JournalEntry]] = {}

    for e in entries:
        acct = e.account.lower().strip()
        if not acct:
            continue
        amt = e.abs_amount
        if amt == 0:
            continue
        account_amounts.setdefault(acct, []).append(amt)
        account_entries.setdefault(acct, []).append(e)

    flagged: list[FlaggedEntry] = []

    for acct, amounts in account_amounts.items():
        if len(amounts) < config.unusual_amount_min_entries:
            continue

        mean = statistics.mean(amounts)
        if len(amounts) < 2:
            continue
        stdev = statistics.stdev(amounts)
        if stdev == 0:
            continue

        threshold = mean + (config.unusual_amount_stddev * stdev)

        for e in account_entries[acct]:
            amt = e.abs_amount
            if amt > threshold:
                z_score = (amt - mean) / stdev
                flagged.append(FlaggedEntry(
                    entry=e,
                    test_name="Unusual Amounts",
                    test_key="unusual_amounts",
                    test_tier=TestTier.STRUCTURAL,
                    severity=Severity.HIGH if z_score > 5 else (
                        Severity.MEDIUM if z_score > 4 else Severity.LOW
                    ),
                    issue=f"Amount ${amt:,.2f} is {z_score:.1f} standard deviations from account mean (${mean:,.2f})",
                    confidence=min(0.50 + (z_score - config.unusual_amount_stddev) * 0.10, 1.0),
                    details={
                        "amount": amt,
                        "account_mean": round(mean, 2),
                        "account_stdev": round(stdev, 2),
                        "z_score": round(z_score, 2),
                        "threshold": round(threshold, 2),
                    },
                ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Unusual Amounts",
        test_key="unusual_amounts",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags entries exceeding {config.unusual_amount_stddev}x standard deviations from the account's typical posting amount.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 1 TESTS — STATISTICAL (Sprint 65)
# =============================================================================

# Benford's Law expected first-digit distribution
BENFORD_EXPECTED: dict[int, float] = {
    1: 0.30103,
    2: 0.17609,
    3: 0.12494,
    4: 0.09691,
    5: 0.07918,
    6: 0.06695,
    7: 0.05799,
    8: 0.05115,
    9: 0.04576,
}

# MAD (Mean Absolute Deviation) thresholds per Nigrini (2012)
BENFORD_MAD_CONFORMING = 0.006
BENFORD_MAD_ACCEPTABLE = 0.012
BENFORD_MAD_MARGINALLY_ACCEPTABLE = 0.015
# Above 0.015 = nonconforming


def _get_first_digit(value: float) -> Optional[int]:
    """Extract the first significant digit (1-9) from a number."""
    if value == 0:
        return None
    abs_val = abs(value)
    # Get the first digit by converting to string
    s = f"{abs_val:.10f}".lstrip("0").lstrip(".")
    for ch in s:
        if ch.isdigit() and ch != "0":
            return int(ch)
    return None


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Try to parse a date string into a date object."""
    if not date_str:
        return None
    # Try common formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d",
                "%m-%d-%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def test_benford_law(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> tuple[TestResult, BenfordResult]:
    """T6: Benford's Law first-digit distribution analysis.

    Pre-checks:
    - Minimum entry count (default 500)
    - Minimum magnitude range (2+ orders of magnitude)
    - Exclude sub-dollar amounts

    Returns both a TestResult and a detailed BenfordResult.
    """
    total_count = len(entries)

    # Extract eligible amounts (>= min_amount, non-zero)
    amounts: list[float] = []
    amount_entries: list[JournalEntry] = []
    for e in entries:
        amt = e.abs_amount
        if amt >= config.benford_min_amount:
            amounts.append(amt)
            amount_entries.append(e)

    eligible_count = len(amounts)

    # Pre-check 1: Minimum entry count
    if eligible_count < config.benford_min_entries:
        benford = BenfordResult(
            passed_prechecks=False,
            precheck_message=f"Insufficient data: {eligible_count} eligible entries (minimum {config.benford_min_entries} required).",
            eligible_count=eligible_count,
            total_count=total_count,
        )
        return TestResult(
            test_name="Benford's Law",
            test_key="benford_law",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=total_count,
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Insufficient data for Benford's Law analysis.",
            flagged_entries=[],
        ), benford

    # Pre-check 2: Magnitude range
    min_amt = min(amounts)
    max_amt = max(amounts)
    if min_amt > 0 and max_amt > 0:
        magnitude_range = math.log10(max_amt) - math.log10(min_amt)
    else:
        magnitude_range = 0.0

    if magnitude_range < config.benford_min_magnitude_range:
        benford = BenfordResult(
            passed_prechecks=False,
            precheck_message=f"Insufficient magnitude range: {magnitude_range:.1f} orders (minimum {config.benford_min_magnitude_range} required).",
            eligible_count=eligible_count,
            total_count=total_count,
        )
        return TestResult(
            test_name="Benford's Law",
            test_key="benford_law",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=total_count,
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Insufficient magnitude range for Benford's Law analysis.",
            flagged_entries=[],
        ), benford

    # Calculate first-digit distribution
    digit_counts: dict[int, int] = {d: 0 for d in range(1, 10)}
    entry_by_first_digit: dict[int, list[JournalEntry]] = {d: [] for d in range(1, 10)}

    for amt, entry in zip(amounts, amount_entries):
        digit = _get_first_digit(amt)
        if digit and 1 <= digit <= 9:
            digit_counts[digit] += 1
            entry_by_first_digit[digit].append(entry)

    counted_total = sum(digit_counts.values())
    if counted_total == 0:
        benford = BenfordResult(
            passed_prechecks=False,
            precheck_message="No valid first digits found.",
            eligible_count=eligible_count,
            total_count=total_count,
        )
        return TestResult(
            test_name="Benford's Law",
            test_key="benford_law",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=total_count,
            flag_rate=0.0,
            severity=Severity.LOW,
            description="No valid first digits found for Benford analysis.",
        ), benford

    # Actual distribution
    actual_dist: dict[int, float] = {
        d: digit_counts[d] / counted_total for d in range(1, 10)
    }

    # Deviation by digit
    deviation: dict[int, float] = {
        d: actual_dist[d] - BENFORD_EXPECTED[d] for d in range(1, 10)
    }

    # MAD
    mad = sum(abs(deviation[d]) for d in range(1, 10)) / 9

    # Chi-squared
    chi_sq = sum(
        ((digit_counts[d] - BENFORD_EXPECTED[d] * counted_total) ** 2)
        / (BENFORD_EXPECTED[d] * counted_total)
        for d in range(1, 10)
    )

    # Conformity level
    if mad < BENFORD_MAD_CONFORMING:
        conformity = "conforming"
    elif mad < BENFORD_MAD_ACCEPTABLE:
        conformity = "acceptable"
    elif mad < BENFORD_MAD_MARGINALLY_ACCEPTABLE:
        conformity = "marginally_acceptable"
    else:
        conformity = "nonconforming"

    # Most deviated digits (absolute deviation > 2x MAD or top 3)
    sorted_deviations = sorted(
        range(1, 10), key=lambda d: abs(deviation[d]), reverse=True
    )
    most_deviated = [d for d in sorted_deviations[:3] if abs(deviation[d]) > mad]

    # Flag entries from most-deviated digit buckets
    flagged: list[FlaggedEntry] = []
    if conformity in ("marginally_acceptable", "nonconforming"):
        for digit in most_deviated:
            dev_pct = deviation[digit]
            # Only flag digits with excess entries (positive deviation)
            if dev_pct > 0:
                for e in entry_by_first_digit[digit]:
                    flagged.append(FlaggedEntry(
                        entry=e,
                        test_name="Benford's Law",
                        test_key="benford_law",
                        test_tier=TestTier.STATISTICAL,
                        severity=Severity.MEDIUM if conformity == "nonconforming" else Severity.LOW,
                        issue=f"First digit {digit} is overrepresented ({actual_dist[digit]:.1%} vs expected {BENFORD_EXPECTED[digit]:.1%})",
                        confidence=min(abs(dev_pct) / 0.05, 1.0),
                        details={
                            "first_digit": digit,
                            "actual_pct": round(actual_dist[digit], 4),
                            "expected_pct": round(BENFORD_EXPECTED[digit], 4),
                            "deviation": round(dev_pct, 4),
                        },
                    ))

    flag_rate = len(flagged) / max(total_count, 1)

    # Determine overall severity
    if conformity == "nonconforming":
        severity = Severity.HIGH
    elif conformity == "marginally_acceptable":
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW

    benford = BenfordResult(
        passed_prechecks=True,
        eligible_count=eligible_count,
        total_count=total_count,
        expected_distribution=dict(BENFORD_EXPECTED),
        actual_distribution=actual_dist,
        actual_counts=digit_counts,
        deviation_by_digit=deviation,
        mad=mad,
        chi_squared=chi_sq,
        conformity_level=conformity,
        most_deviated_digits=most_deviated,
    )

    return TestResult(
        test_name="Benford's Law",
        test_key="benford_law",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total_count,
        flag_rate=flag_rate,
        severity=severity,
        description=f"First-digit distribution analysis (MAD={mad:.4f}, {conformity}).",
        flagged_entries=flagged,
    ), benford


def test_weekend_postings(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T7: Flag entries posted on Saturday/Sunday.

    Weights by amount: large weekend entries get higher severity.
    Configurable via config.weekend_posting_enabled.
    """
    if not config.weekend_posting_enabled:
        return TestResult(
            test_name="Weekend Postings",
            test_key="weekend_postings",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Weekend posting test disabled.",
        )

    flagged: list[FlaggedEntry] = []

    for e in entries:
        d = _parse_date(e.posting_date) or _parse_date(e.entry_date)
        if d is None:
            continue
        weekday = d.weekday()  # 0=Mon, 5=Sat, 6=Sun
        if weekday >= 5:
            day_name = "Saturday" if weekday == 5 else "Sunday"
            amt = e.abs_amount
            # Weight by amount
            if amt >= config.weekend_large_amount_threshold:
                severity = Severity.HIGH
            elif amt >= config.weekend_large_amount_threshold / 5:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedEntry(
                entry=e,
                test_name="Weekend Postings",
                test_key="weekend_postings",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Entry posted on {day_name} ({d.isoformat()}), amount: ${amt:,.2f}",
                confidence=0.80,
                details={
                    "day_of_week": day_name,
                    "date": d.isoformat(),
                    "amount": amt,
                },
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Weekend Postings",
        test_key="weekend_postings",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.LOW,
        description="Flags entries posted on Saturday or Sunday, weighted by amount.",
        flagged_entries=flagged,
    )


def test_month_end_clustering(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T8: Flag unusual concentration of entries in last N days of month.

    Compares last-N-day volume to monthly average daily volume.
    Significance threshold: >Nx average daily volume (configurable).
    """
    # Parse dates and group by month
    monthly_entries: dict[tuple[int, int], list[tuple[date, JournalEntry]]] = {}

    for e in entries:
        d = _parse_date(e.posting_date) or _parse_date(e.entry_date)
        if d is None:
            continue
        month_key = (d.year, d.month)
        monthly_entries.setdefault(month_key, []).append((d, e))

    flagged: list[FlaggedEntry] = []
    flagged_months: list[str] = []

    for (year, month), dated_entries in monthly_entries.items():
        total_in_month = len(dated_entries)
        if total_in_month < 10:
            continue  # Too few entries for meaningful analysis

        days_in_month = monthrange(year, month)[1]
        avg_daily = total_in_month / days_in_month

        # Count entries in last N days
        cutoff_day = days_in_month - config.month_end_days + 1
        month_end_entries = [
            (d, e) for d, e in dated_entries if d.day >= cutoff_day
        ]
        month_end_count = len(month_end_entries)
        month_end_daily = month_end_count / config.month_end_days

        if month_end_daily > avg_daily * config.month_end_volume_multiplier:
            ratio = month_end_daily / avg_daily if avg_daily > 0 else 0
            month_label = f"{year}-{month:02d}"
            flagged_months.append(month_label)

            for d, e in month_end_entries:
                flagged.append(FlaggedEntry(
                    entry=e,
                    test_name="Month-End Clustering",
                    test_key="month_end_clustering",
                    test_tier=TestTier.STATISTICAL,
                    severity=Severity.MEDIUM if ratio > 4 else Severity.LOW,
                    issue=f"Month-end entry ({d.isoformat()}): {month_end_count} entries in last {config.month_end_days} days of {month_label} ({ratio:.1f}x avg daily volume)",
                    confidence=min(ratio / 5.0, 1.0),
                    details={
                        "month": month_label,
                        "month_end_count": month_end_count,
                        "avg_daily": round(avg_daily, 1),
                        "month_end_daily": round(month_end_daily, 1),
                        "ratio": round(ratio, 2),
                    },
                ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Month-End Clustering",
        test_key="month_end_clustering",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.LOW,
        description=f"Flags months with >{config.month_end_volume_multiplier}x average daily volume in last {config.month_end_days} days.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 2 — USER / TIME / PATTERN TESTS (T9-T13)
# =============================================================================

# Suspicious keyword list for T13.
# Format: (keyword, weight, is_phrase)
SUSPICIOUS_KEYWORDS: list[tuple[str, float, bool]] = [
    # Manual override / correction indicators
    ("manual adjustment", 0.90, True),
    ("manual entry", 0.85, True),
    ("manual", 0.60, False),
    ("adjusting entry", 0.85, True),
    ("adjustment", 0.70, False),
    ("error correction", 0.90, True),
    ("correction", 0.75, False),
    ("reclassification", 0.80, False),
    ("reclass", 0.75, False),
    ("reversal", 0.80, False),
    ("reverse", 0.70, False),
    ("override", 0.85, False),
    ("write-off", 0.80, True),
    ("write off", 0.80, True),
    # Placeholder / test indicators
    ("test entry", 0.90, True),
    ("dummy", 0.85, False),
    ("placeholder", 0.85, False),
    ("tbd", 0.75, False),
    ("to be determined", 0.80, True),
    # Unusual activity
    ("related party", 0.90, True),
    ("intercompany", 0.60, False),
    ("personal", 0.70, False),
    ("loan to officer", 0.90, True),
    ("cash advance", 0.75, True),
]


def _extract_hour(date_str: Optional[str]) -> Optional[int]:
    """Extract hour from a datetime string. Returns None if no time component."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%d %H:%M", "%m/%d/%Y %H:%M"):
        try:
            return datetime.strptime(date_str.strip(), fmt).hour
        except (ValueError, AttributeError):
            continue
    return None


def _extract_number(entry_id: Optional[str]) -> Optional[int]:
    """Extract the numeric portion from an entry ID string."""
    if not entry_id:
        return None
    # Strip common prefixes like JE-, JV-, GJ-, #
    cleaned = re.sub(r'^[A-Za-z#\-]+', '', entry_id.strip())
    # Extract leading digits
    match = re.match(r'(\d+)', cleaned)
    if match:
        return int(match.group(1))
    return None


def test_single_user_high_volume(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T9: Flag users who posted a disproportionate share of entries.

    Opt-in: requires posted_by column data. Helps identify segregation-of-duties
    risks per PCAOB AS 2201 / ISA 315.
    """
    entries_with_user = [e for e in entries if e.posted_by]
    if not entries_with_user:
        return TestResult(
            test_name="Single-User High Volume",
            test_key="single_user_high_volume",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Requires posted_by column (not available).",
            flagged_entries=[],
        )

    total = len(entries_with_user)
    user_counts: dict[str, int] = {}
    for e in entries_with_user:
        user = (e.posted_by or "").strip().lower()
        if user:
            user_counts[user] = user_counts.get(user, 0) + 1

    flagged: list[FlaggedEntry] = []
    high_volume_users: list[tuple[str, int, float]] = []

    for user, count in user_counts.items():
        pct = count / total
        if pct > config.single_user_volume_pct:
            high_volume_users.append((user, count, pct))

    # For each high-volume user, flag their top entries by amount
    for user, count, pct in high_volume_users:
        user_entries = sorted(
            [e for e in entries_with_user if (e.posted_by or "").strip().lower() == user],
            key=lambda e: e.abs_amount,
            reverse=True,
        )
        severity = Severity.HIGH if pct > 0.50 else Severity.MEDIUM
        for e in user_entries[:config.single_user_max_flags]:
            flagged.append(FlaggedEntry(
                entry=e,
                test_name="Single-User High Volume",
                test_key="single_user_high_volume",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"User '{user}' posted {pct:.0%} of entries ({count}/{total})",
                confidence=min(pct / config.single_user_volume_pct, 1.0),
                details={"user": user, "count": count, "total": total, "pct": round(pct, 4)},
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Single-User High Volume",
        test_key="single_user_high_volume",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags users posting >{config.single_user_volume_pct:.0%} of all entries.",
        flagged_entries=flagged,
    )


def test_after_hours_postings(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T10: Flag entries posted outside business hours.

    Opt-in: requires timestamp data (not just date). Entries with date-only
    fields are skipped. Business hours default to 06:00-18:00.
    """
    if not config.after_hours_enabled:
        return TestResult(
            test_name="After-Hours Postings",
            test_key="after_hours_postings",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedEntry] = []
    entries_with_time = 0

    for e in entries:
        hour = _extract_hour(e.posting_date) or _extract_hour(e.entry_date)
        if hour is None:
            continue
        entries_with_time += 1

        # Within business hours: after_hours_end <= hour < after_hours_start
        if config.after_hours_end <= hour < config.after_hours_start:
            continue  # Normal hours

        amt = e.abs_amount
        if amt > config.after_hours_large_threshold:
            severity = Severity.HIGH
        elif amt > 1000:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        flagged.append(FlaggedEntry(
            entry=e,
            test_name="After-Hours Postings",
            test_key="after_hours_postings",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Entry posted at {hour:02d}:00 (outside {config.after_hours_end:02d}:00-{config.after_hours_start:02d}:00 business hours)",
            confidence=0.8 if amt > config.after_hours_large_threshold else 0.6,
            details={"hour": hour, "amount": amt},
        ))

    if entries_with_time == 0:
        return TestResult(
            test_name="After-Hours Postings",
            test_key="after_hours_postings",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Requires timestamp data (date fields have no time component).",
            flagged_entries=[],
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="After-Hours Postings",
        test_key="after_hours_postings",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags entries posted outside {config.after_hours_end:02d}:00-{config.after_hours_start:02d}:00.",
        flagged_entries=flagged,
    )


def test_numbering_gaps(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T11: Flag gaps in sequential entry numbering.

    Opt-in: requires entry_id column with numeric component.
    Gaps may indicate deleted or unrecorded entries.
    """
    if not config.numbering_gap_enabled:
        return TestResult(
            test_name="Sequential Numbering Gaps",
            test_key="numbering_gaps",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    numbered: list[tuple[int, JournalEntry]] = []
    for e in entries:
        num = _extract_number(e.entry_id)
        if num is not None:
            numbered.append((num, e))

    if len(numbered) < 2:
        return TestResult(
            test_name="Sequential Numbering Gaps",
            test_key="numbering_gaps",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Requires entry_id column with numeric sequence (not available or insufficient data).",
            flagged_entries=[],
        )

    numbered.sort(key=lambda x: x[0])
    flagged: list[FlaggedEntry] = []

    for i in range(1, len(numbered)):
        prev_num, _ = numbered[i - 1]
        curr_num, curr_entry = numbered[i]
        gap = curr_num - prev_num

        if gap >= config.numbering_gap_min_size:
            if gap > 100:
                severity = Severity.HIGH
            elif gap > 10:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedEntry(
                entry=curr_entry,
                test_name="Sequential Numbering Gaps",
                test_key="numbering_gaps",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Gap of {gap - 1} missing entries before #{curr_num} (previous: #{prev_num})",
                confidence=min(gap / 100.0, 1.0),
                details={"gap_size": gap - 1, "prev_number": prev_num, "curr_number": curr_num},
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Sequential Numbering Gaps",
        test_key="numbering_gaps",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags gaps in sequential entry numbering that may indicate deleted entries.",
        flagged_entries=flagged,
    )


def test_backdated_entries(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T12: Flag entries where posting_date significantly differs from entry_date.

    Opt-in: requires dual dates (both posting_date and entry_date).
    Large discrepancies may indicate period manipulation.
    """
    if not config.backdate_enabled:
        return TestResult(
            test_name="Backdated Entries",
            test_key="backdated_entries",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedEntry] = []
    dual_date_count = 0

    for e in entries:
        if not e.posting_date or not e.entry_date:
            continue

        posting = _parse_date(e.posting_date)
        entry = _parse_date(e.entry_date)
        if not posting or not entry:
            continue

        dual_date_count += 1
        days_diff = abs((posting - entry).days)

        if days_diff >= config.backdate_days_threshold:
            if days_diff > 90:
                severity = Severity.HIGH
            elif days_diff > 30:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedEntry(
                entry=e,
                test_name="Backdated Entries",
                test_key="backdated_entries",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Posting date differs from entry date by {days_diff} days (posting: {e.posting_date}, entered: {e.entry_date})",
                confidence=min(days_diff / 90.0, 1.0),
                details={"days_diff": days_diff, "posting_date": e.posting_date, "entry_date": e.entry_date},
            ))

    if dual_date_count == 0:
        return TestResult(
            test_name="Backdated Entries",
            test_key="backdated_entries",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Requires dual dates (posting_date and entry_date, not available).",
            flagged_entries=[],
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Backdated Entries",
        test_key="backdated_entries",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags entries where posting date differs from entry date by >{config.backdate_days_threshold} days.",
        flagged_entries=flagged,
    )


def test_suspicious_keywords(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T13: Flag entries with suspicious description keywords.

    Scans description field for keywords associated with manual adjustments,
    overrides, corrections, and other audit-sensitive language.
    Reuses weighted-keyword pattern from classification_rules.py.
    """
    if not config.suspicious_keyword_enabled:
        return TestResult(
            test_name="Suspicious Keywords",
            test_key="suspicious_keywords",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedEntry] = []
    entries_with_desc = 0

    for e in entries:
        if not e.description:
            continue
        entries_with_desc += 1

        desc_lower = e.description.lower().strip()
        best_confidence = 0.0
        matched_keyword = ""

        for keyword, weight, is_phrase in SUSPICIOUS_KEYWORDS:
            if is_phrase:
                if keyword in desc_lower:
                    if weight > best_confidence:
                        best_confidence = weight
                        matched_keyword = keyword
            else:
                if keyword in desc_lower:
                    if weight > best_confidence:
                        best_confidence = weight
                        matched_keyword = keyword

        if best_confidence >= config.suspicious_keyword_threshold:
            amt = e.abs_amount
            # Severity based on confidence + amount
            if best_confidence >= 0.85 and amt > 10000:
                severity = Severity.HIGH
            elif best_confidence >= 0.70 or amt > 5000:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedEntry(
                entry=e,
                test_name="Suspicious Keywords",
                test_key="suspicious_keywords",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Description contains '{matched_keyword}' (confidence: {best_confidence:.0%})",
                confidence=best_confidence,
                details={"matched_keyword": matched_keyword, "amount": amt},
            ))

    if entries_with_desc == 0:
        return TestResult(
            test_name="Suspicious Keywords",
            test_key="suspicious_keywords",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="No entries have description data.",
            flagged_entries=[],
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Suspicious Keywords",
        test_key="suspicious_keywords",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags entries with descriptions containing audit-sensitive keywords.",
        flagged_entries=flagged,
    )


# =============================================================================
# TEST BATTERY
# =============================================================================

# Severity weights for composite scoring
SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.HIGH: 3.0,
    Severity.MEDIUM: 2.0,
    Severity.LOW: 1.0,
}


def run_test_battery(
    entries: list[JournalEntry],
    config: Optional[JETestingConfig] = None,
) -> tuple[list[TestResult], Optional[BenfordResult]]:
    """Run all structural + statistical tests on the entries.

    Returns (test_results, benford_result).
    Benford result is separate because it contains detailed distribution data.
    """
    if config is None:
        config = JETestingConfig()

    results = [
        # Tier 1 — Structural (T1-T5)
        test_unbalanced_entries(entries, config),
        test_missing_fields(entries, config),
        test_duplicate_entries(entries, config),
        test_round_amounts(entries, config),
        test_unusual_amounts(entries, config),
    ]

    # Tier 1 — Statistical (T6-T8)
    benford_test_result, benford_data = test_benford_law(entries, config)
    results.append(benford_test_result)
    results.append(test_weekend_postings(entries, config))
    results.append(test_month_end_clustering(entries, config))

    # Tier 2 — User / Time / Pattern (T9-T13)
    results.append(test_single_user_high_volume(entries, config))
    results.append(test_after_hours_postings(entries, config))
    results.append(test_numbering_gaps(entries, config))
    results.append(test_backdated_entries(entries, config))
    results.append(test_suspicious_keywords(entries, config))

    return results, benford_data


def calculate_composite_score(
    test_results: list[TestResult],
    total_entries: int,
) -> CompositeScore:
    """Calculate the composite risk score from test results.

    Score = weighted sum of (flag_rate × severity_weight) normalized to 0-100.
    Entries flagged by 3+ tests get a 1.25x multiplier.
    """
    if total_entries == 0:
        return CompositeScore(
            score=0.0,
            risk_tier=RiskTier.LOW,
            tests_run=len(test_results),
            total_entries=0,
            total_flagged=0,
            flag_rate=0.0,
        )

    # Collect all flagged entry row numbers with their test counts
    entry_test_counts: dict[int, int] = {}
    all_flagged_rows: set[int] = set()
    flags_by_severity: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for tr in test_results:
        for fe in tr.flagged_entries:
            row = fe.entry.row_number
            entry_test_counts[row] = entry_test_counts.get(row, 0) + 1
            all_flagged_rows.add(row)
            flags_by_severity[fe.severity.value] = flags_by_severity.get(fe.severity.value, 0) + 1

    # Base score from flag rates weighted by severity
    weighted_sum = 0.0
    for tr in test_results:
        weight = SEVERITY_WEIGHTS.get(tr.severity, 1.0)
        weighted_sum += tr.flag_rate * weight

    # Normalize: typical maximum weighted_sum with all tests at 100% flag rate
    # would be sum of all weights. Scale to 0-100.
    max_possible = sum(SEVERITY_WEIGHTS.get(tr.severity, 1.0) for tr in test_results)
    if max_possible > 0:
        base_score = (weighted_sum / max_possible) * 100
    else:
        base_score = 0.0

    # Multi-flag multiplier: entries flagged by 3+ tests
    multi_flag_count = sum(1 for c in entry_test_counts.values() if c >= 3)
    multi_flag_ratio = multi_flag_count / max(total_entries, 1)
    multiplier = 1.0 + (multi_flag_ratio * 0.25)  # Up to 1.25x

    score = min(base_score * multiplier, 100.0)

    # Top findings
    top_findings: list[str] = []
    for tr in sorted(test_results, key=lambda t: t.flag_rate, reverse=True):
        if tr.entries_flagged > 0:
            top_findings.append(
                f"{tr.test_name}: {tr.entries_flagged} entries flagged ({tr.flag_rate:.1%})"
            )

    total_flagged = len(all_flagged_rows)
    flag_rate = total_flagged / max(total_entries, 1)

    return CompositeScore(
        score=score,
        risk_tier=score_to_risk_tier(score),
        tests_run=len(test_results),
        total_entries=total_entries,
        total_flagged=total_flagged,
        flag_rate=flag_rate,
        flags_by_severity=flags_by_severity,
        top_findings=top_findings[:5],
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_je_testing(
    rows: list[dict],
    column_names: list[str],
    config: Optional[JETestingConfig] = None,
    column_mapping: Optional[dict] = None,
) -> JETestingResult:
    """Run the complete JE testing pipeline.

    Args:
        rows: List of dicts (raw GL data rows)
        column_names: List of column header names
        config: Optional testing configuration
        column_mapping: Optional manual column mapping override

    Returns:
        JETestingResult with composite score, test results, data quality, etc.
    """
    if config is None:
        config = JETestingConfig()

    # 1. Detect columns
    detection = detect_gl_columns(column_names)

    # Apply manual overrides if provided
    if column_mapping:
        if "date_column" in column_mapping:
            detection.date_column = column_mapping["date_column"]
        if "account_column" in column_mapping:
            detection.account_column = column_mapping["account_column"]
        if "debit_column" in column_mapping:
            detection.debit_column = column_mapping["debit_column"]
            detection.has_separate_debit_credit = True
        if "credit_column" in column_mapping:
            detection.credit_column = column_mapping["credit_column"]
            detection.has_separate_debit_credit = True
        if "amount_column" in column_mapping:
            detection.amount_column = column_mapping["amount_column"]
            detection.has_separate_debit_credit = False
        if "description_column" in column_mapping:
            detection.description_column = column_mapping["description_column"]
        if "reference_column" in column_mapping:
            detection.reference_column = column_mapping["reference_column"]
        if "posted_by_column" in column_mapping:
            detection.posted_by_column = column_mapping["posted_by_column"]
        if "entry_id_column" in column_mapping:
            detection.entry_id_column = column_mapping["entry_id_column"]
        if "currency_column" in column_mapping:
            detection.currency_column = column_mapping["currency_column"]
        if "source_column" in column_mapping:
            detection.source_column = column_mapping["source_column"]
        if "entry_date_column" in column_mapping:
            detection.entry_date_column = column_mapping["entry_date_column"]
        if "posting_date_column" in column_mapping:
            detection.posting_date_column = column_mapping["posting_date_column"]
        # Recalculate overall confidence with overrides
        detection.overall_confidence = 1.0

    # 2. Parse entries
    entries = parse_gl_entries(rows, detection)

    # 3. Assess data quality
    data_quality = assess_data_quality(entries, detection)

    # 4. Detect multi-currency
    multi_currency = detect_multi_currency(entries)

    # 5. Run test battery
    test_results, benford_data = run_test_battery(entries, config)

    # 6. Calculate composite score
    composite = calculate_composite_score(test_results, len(entries))

    return JETestingResult(
        composite_score=composite,
        test_results=test_results,
        data_quality=data_quality,
        multi_currency_warning=multi_currency,
        column_detection=detection,
        benford_result=benford_data,
    )
