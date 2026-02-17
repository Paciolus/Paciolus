"""
Journal Entry Testing Engine - Sprint 64 / Sprint 65 / Sprint 68 / Sprint 69

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

Sprint 69 scope:
- Tier 3 tests (T14-T18): Reciprocal Entries, Just-Below-Threshold,
  Account Frequency Anomaly, Description Length Anomaly, Unusual Account Combos
- Stratified Sampling Engine with CSPRNG (secrets module)
- Preview strata + execute sampling with reproducible seeds

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

import re
import secrets
import statistics
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from shared.benford import BenfordAnalysis, analyze_benford, get_first_digit  # noqa: E402
from shared.column_detector import ColumnFieldConfig, detect_columns  # noqa: E402
from shared.data_quality import FieldQualityConfig  # noqa: E402
from shared.data_quality import assess_data_quality as _shared_assess_dq
from shared.parsing_helpers import parse_date, safe_float, safe_str  # noqa: E402
from shared.test_aggregator import calculate_composite_score as _shared_calc_cs

# =============================================================================
# ENUMS (imported from shared — Sprint 90)
# =============================================================================
from shared.testing_enums import (  # noqa: E402
    RiskTier,
    Severity,
    TestTier,
    score_to_risk_tier,  # noqa: E402, F401 — re-export for backward compat
    zscore_to_severity,  # noqa: E402
)

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

    # T14: Reciprocal Entries
    reciprocal_enabled: bool = True
    reciprocal_days_window: int = 7  # Days window for matching pairs
    reciprocal_min_amount: float = 1000.0  # Min amount to check

    # T15: Just-Below-Threshold
    threshold_proximity_enabled: bool = True
    threshold_proximity_pct: float = 0.05  # 5% below threshold
    approval_thresholds: list[float] = field(
        default_factory=lambda: [5000.0, 10000.0, 25000.0, 50000.0, 100000.0]
    )

    # T16: Account Frequency Anomaly
    frequency_anomaly_enabled: bool = True
    frequency_anomaly_stddev: float = 2.5  # Std devs from mean to flag
    frequency_anomaly_min_periods: int = 3  # Min periods per account

    # T17: Description Length Anomaly
    desc_length_enabled: bool = True
    desc_length_min_entries: int = 5  # Min entries per account for baseline
    desc_length_stddev: float = 2.0  # Std devs below mean to flag

    # T18: Unusual Account Combinations
    unusual_combo_enabled: bool = True
    unusual_combo_max_frequency: int = 2  # Flag combos seen <= this many times
    unusual_combo_min_total_entries: int = 20  # Min entries with entry_id for analysis

    # Stratified Sampling
    sampling_default_rate: float = 0.10  # 10% default sample rate


# =============================================================================
# GL COLUMN DETECTION
# =============================================================================

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

# Shared column detector configs (replaces GLColumnType enum + GL_COLUMN_PATTERNS)
# Priority ordering: most specific fields first to prevent greedy misassignment
GL_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig("entry_date_column", GL_ENTRY_DATE_PATTERNS, priority=5),
    ColumnFieldConfig("posting_date_column", GL_POSTING_DATE_PATTERNS, priority=10),
    ColumnFieldConfig("date_column", GL_DATE_PATTERNS, priority=15),
    ColumnFieldConfig("entry_id_column", GL_ENTRY_ID_PATTERNS, priority=20),
    ColumnFieldConfig("reference_column", GL_REFERENCE_PATTERNS, priority=25),
    ColumnFieldConfig("account_column", GL_ACCOUNT_PATTERNS, required=True,
                      missing_note="Could not identify an Account column", priority=30),
    ColumnFieldConfig("debit_column", GL_DEBIT_PATTERNS, priority=35),
    ColumnFieldConfig("credit_column", GL_CREDIT_PATTERNS, priority=40),
    ColumnFieldConfig("amount_column", GL_AMOUNT_PATTERNS, priority=45),
    ColumnFieldConfig("description_column", GL_DESCRIPTION_PATTERNS, priority=50),
    ColumnFieldConfig("posted_by_column", GL_POSTED_BY_PATTERNS, priority=55),
    ColumnFieldConfig("source_column", GL_SOURCE_PATTERNS, priority=60),
    ColumnFieldConfig("currency_column", GL_CURRENCY_PATTERNS, priority=65),
]


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
    """Detect GL columns using shared column detector.

    Supports:
    - Dual date columns (entry_date + posting_date) or single date
    - Debit/credit pair or single amount column
    - Optional columns: description, reference, posted_by, source, currency, entry_id
    """
    detection = detect_columns(column_names, GL_COLUMN_CONFIGS)
    result = GLColumnDetectionResult(all_columns=detection.all_columns)
    notes: list[str] = []

    # --- Dual-date logic (JE-specific pair detection with threshold) ---
    entry_date_col = detection.get_column("entry_date_column")
    posting_date_col = detection.get_column("posting_date_column")
    generic_date_col = detection.get_column("date_column")
    entry_date_conf = detection.get_confidence("entry_date_column")
    posting_date_conf = detection.get_confidence("posting_date_column")

    if entry_date_col and posting_date_col and entry_date_conf >= 0.70 and posting_date_conf >= 0.70:
        result.entry_date_column = entry_date_col
        result.posting_date_column = posting_date_col
        result.date_column = posting_date_col  # Primary date = posting date
        result.has_dual_dates = True
        notes.append("Dual-date detected: entry_date + posting_date")
    elif generic_date_col:
        result.date_column = generic_date_col
    elif entry_date_col:
        result.date_column = entry_date_col
        result.entry_date_column = entry_date_col
    elif posting_date_col:
        result.date_column = posting_date_col
        result.posting_date_column = posting_date_col

    # --- Debit/Credit pair or single Amount (JE-specific pair detection) ---
    debit_col = detection.get_column("debit_column")
    credit_col = detection.get_column("credit_column")
    amount_col = detection.get_column("amount_column")

    if debit_col and credit_col:
        result.debit_column = debit_col
        result.credit_column = credit_col
        result.has_separate_debit_credit = True
    elif amount_col:
        result.amount_column = amount_col
    else:
        notes.append("Could not identify Debit/Credit or Amount columns")

    # --- Non-conflicting fields ---
    result.account_column = detection.get_column("account_column")
    result.entry_id_column = detection.get_column("entry_id_column")
    result.reference_column = detection.get_column("reference_column")
    result.description_column = detection.get_column("description_column")
    result.posted_by_column = detection.get_column("posted_by_column")
    result.source_column = detection.get_column("source_column")
    result.currency_column = detection.get_column("currency_column")

    # --- Overall confidence ---
    required_confidences: list[float] = []

    if result.date_column:
        if result.has_dual_dates:
            required_confidences.append(posting_date_conf)
        else:
            date_conf = max(
                detection.get_confidence("date_column"),
                detection.get_confidence("entry_date_column"),
                detection.get_confidence("posting_date_column"),
            )
            required_confidences.append(date_conf)
    else:
        required_confidences.append(0.0)
        notes.append("Could not identify a Date column")

    if result.account_column:
        required_confidences.append(detection.get_confidence("account_column"))
    else:
        required_confidences.append(0.0)
        if "Could not identify an Account column" not in notes:
            notes.append("Could not identify an Account column")

    if result.has_separate_debit_credit:
        required_confidences.append(min(
            detection.get_confidence("debit_column"),
            detection.get_confidence("credit_column"),
        ))
    elif result.amount_column:
        required_confidences.append(detection.get_confidence("amount_column"))
    else:
        required_confidences.append(0.0)

    result.overall_confidence = min(required_confidences) if required_confidences else 0.0
    result.detection_notes = notes + list(detection.detection_notes)
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


# BenfordResult is now BenfordAnalysis from shared.benford (Sprint 153)
# Type alias for backward compatibility — identical fields and to_dict() output
BenfordResult = BenfordAnalysis


@dataclass
@dataclass
class SamplingStratum:
    """A single stratum in stratified sampling."""
    name: str
    criteria: str  # e.g., "account=Cash", "amount=$1K-$10K"
    population_size: int
    sample_size: int
    sampled_rows: list[int] = field(default_factory=list)  # Row numbers

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "criteria": self.criteria,
            "population_size": self.population_size,
            "sample_size": self.sample_size,
            "sampled_rows": self.sampled_rows,
        }


@dataclass
class SamplingResult:
    """Result of stratified sampling."""
    total_population: int
    total_sampled: int
    strata: list[SamplingStratum] = field(default_factory=list)
    sampled_entries: list[JournalEntry] = field(default_factory=list)
    sampling_seed: str = ""  # Hex seed for reproducibility
    parameters: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_population": self.total_population,
            "total_sampled": self.total_sampled,
            "strata": [s.to_dict() for s in self.strata],
            "sampled_entries": [e.to_dict() for e in self.sampled_entries],
            "sampling_seed": self.sampling_seed,
            "parameters": self.parameters,
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
    sampling_result: Optional[SamplingResult] = None

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [t.to_dict() for t in self.test_results],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "multi_currency_warning": self.multi_currency_warning.to_dict() if self.multi_currency_warning else None,
            "column_detection": self.column_detection.to_dict() if self.column_detection else None,
            "benford_result": self.benford_result.to_dict() if self.benford_result else None,
            "sampling_result": self.sampling_result.to_dict() if self.sampling_result else None,
        }


# score_to_risk_tier is imported from shared.testing_enums (Sprint 152)


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
            entry.entry_date = safe_str(row.get(detection.entry_date_column))
        if detection.posting_date_column:
            entry.posting_date = safe_str(row.get(detection.posting_date_column))
        if detection.date_column and not entry.posting_date:
            entry.posting_date = safe_str(row.get(detection.date_column))
        if not entry.entry_date and detection.date_column:
            entry.entry_date = safe_str(row.get(detection.date_column))

        # Account
        if detection.account_column:
            entry.account = safe_str(row.get(detection.account_column)) or ""

        # Amounts
        if detection.has_separate_debit_credit:
            entry.debit = safe_float(row.get(detection.debit_column))
            entry.credit = safe_float(row.get(detection.credit_column))
        elif detection.amount_column:
            amt = safe_float(row.get(detection.amount_column))
            if amt >= 0:
                entry.debit = amt
            else:
                entry.credit = abs(amt)

        # Optional fields
        if detection.description_column:
            entry.description = safe_str(row.get(detection.description_column))
        if detection.reference_column:
            entry.reference = safe_str(row.get(detection.reference_column))
        if detection.posted_by_column:
            entry.posted_by = safe_str(row.get(detection.posted_by_column))
        if detection.source_column:
            entry.source = safe_str(row.get(detection.source_column))
        if detection.currency_column:
            entry.currency = safe_str(row.get(detection.currency_column))
        if detection.entry_id_column:
            entry.entry_id = safe_str(row.get(detection.entry_id_column))

        entries.append(entry)

    return entries


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

    Delegates to shared data quality engine (Sprint 152).
    """
    # Build field configs based on detected columns
    configs: list[FieldQualityConfig] = [
        FieldQualityConfig("date", lambda e: e.posting_date or e.entry_date, weight=0.30,
                           issue_threshold=0.95, issue_template="Missing dates on {unfilled} entries"),
        FieldQualityConfig("account", lambda e: e.account, weight=0.30,
                           issue_threshold=0.95, issue_template="Missing account on {unfilled} entries"),
        FieldQualityConfig("amount", lambda e: e.debit > 0 or e.credit > 0, weight=0.25,
                           issue_threshold=0.90,
                           issue_template="{unfilled} entries have zero amount (both debit and credit are 0)"),
    ]

    if detection.description_column:
        configs.append(FieldQualityConfig("description", lambda e: e.description,
                                          issue_threshold=0.80,
                                          issue_template="Low description fill rate: {fill_pct} ({unfilled} blank)"))
    if detection.reference_column:
        configs.append(FieldQualityConfig("reference", lambda e: e.reference,
                                          issue_threshold=0.80,
                                          issue_template="Low reference fill rate: {fill_pct}"))
    if detection.posted_by_column:
        configs.append(FieldQualityConfig("posted_by", lambda e: e.posted_by,
                                          issue_threshold=0.50,
                                          issue_template="Low posted_by fill rate: {fill_pct}"))
    if detection.entry_id_column:
        configs.append(FieldQualityConfig("entry_id", lambda e: e.entry_id))
    if detection.source_column:
        configs.append(FieldQualityConfig("source", lambda e: e.source))

    result = _shared_assess_dq(entries, configs, optional_weight_pool=0.15)

    return GLDataQuality(
        completeness_score=result.completeness_score,
        field_fill_rates=result.field_fill_rates,
        detected_issues=result.detected_issues,
        total_rows=result.total_rows,
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

# Rounding patterns for T4 — imported from shared (Sprint 90)
from shared.round_amounts import ROUND_AMOUNT_PATTERNS_3TIER as ROUND_AMOUNT_PATTERNS  # noqa: E402


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
                    severity=zscore_to_severity(z_score),
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

# Re-export for backward compatibility with test files (Sprint 153)
_get_first_digit = get_first_digit

# Benford constants re-exported from shared.benford for any direct importers
from shared.benford import BENFORD_EXPECTED  # noqa: E402, F401


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
    Delegates statistical analysis to shared.benford.analyze_benford().
    """
    total_count = len(entries)

    # Extract eligible amounts (>= min_amount, non-zero) + parallel entry list
    amounts: list[float] = []
    amount_entries: list[JournalEntry] = []
    for e in entries:
        amt = e.abs_amount
        if amt >= config.benford_min_amount:
            amounts.append(amt)
            amount_entries.append(e)

    # Run shared Benford analysis
    benford = analyze_benford(
        amounts,
        total_count=total_count,
        min_entries=config.benford_min_entries,
        min_amount=config.benford_min_amount,
        min_magnitude_range=config.benford_min_magnitude_range,
    )

    if not benford.passed_prechecks:
        return TestResult(
            test_name="Benford's Law",
            test_key="benford_law",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=total_count,
            flag_rate=0.0,
            severity=Severity.LOW,
            description=benford.precheck_message or "Benford prechecks failed.",
            flagged_entries=[],
        ), benford

    # Build entry-to-digit map for flagging
    entry_by_first_digit: dict[int, list[JournalEntry]] = {d: [] for d in range(1, 10)}
    for amt, entry in zip(amounts, amount_entries):
        digit = get_first_digit(amt)
        if digit and 1 <= digit <= 9:
            entry_by_first_digit[digit].append(entry)

    # Flag entries from most-deviated digit buckets
    flagged: list[FlaggedEntry] = []
    conformity = benford.conformity_level
    if conformity in ("marginally_acceptable", "nonconforming"):
        for digit in benford.most_deviated_digits:
            dev_pct = benford.deviation_by_digit[digit]
            if dev_pct > 0:
                for e in entry_by_first_digit[digit]:
                    flagged.append(FlaggedEntry(
                        entry=e,
                        test_name="Benford's Law",
                        test_key="benford_law",
                        test_tier=TestTier.STATISTICAL,
                        severity=Severity.MEDIUM if conformity == "nonconforming" else Severity.LOW,
                        issue=f"First digit {digit} is overrepresented ({benford.actual_distribution[digit]:.1%} vs expected {benford.expected_distribution[digit]:.1%})",
                        confidence=min(abs(dev_pct) / 0.05, 1.0),
                        details={
                            "first_digit": digit,
                            "actual_pct": round(benford.actual_distribution[digit], 4),
                            "expected_pct": round(benford.expected_distribution[digit], 4),
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

    return TestResult(
        test_name="Benford's Law",
        test_key="benford_law",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total_count,
        flag_rate=flag_rate,
        severity=severity,
        description=f"First-digit distribution analysis (MAD={benford.mad:.4f}, {conformity}).",
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
        d = parse_date(e.posting_date) or parse_date(e.entry_date)
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
        d = parse_date(e.posting_date) or parse_date(e.entry_date)
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

        posting = parse_date(e.posting_date)
        entry = parse_date(e.entry_date)
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
# TIER 3 — ADVANCED / FRAUD INDICATORS (T14-T18)
# =============================================================================

def test_reciprocal_entries(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T14: Flag matching debit/credit pairs posted close together.

    Detects potential round-tripping: a debit to Account A followed by
    a credit of the same amount within a configurable time window.
    Enhanced: detects cross-account patterns.
    """
    if not config.reciprocal_enabled:
        return TestResult(
            test_name="Reciprocal Entries",
            test_key="reciprocal_entries",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Test disabled.", flagged_entries=[],
        )

    # Index entries by absolute amount (rounded to 2 decimals) for matching
    amount_buckets: dict[float, list[JournalEntry]] = {}
    for e in entries:
        amt = round(e.abs_amount, 2)
        if amt < config.reciprocal_min_amount:
            continue
        amount_buckets.setdefault(amt, []).append(e)

    flagged: list[FlaggedEntry] = []
    seen_pairs: set[tuple[int, int]] = set()

    for amt, bucket in amount_buckets.items():
        if len(bucket) < 2:
            continue

        debits = [e for e in bucket if e.debit > 0]
        credits = [e for e in bucket if e.credit > 0]

        for d_entry in debits:
            d_date = parse_date(d_entry.posting_date or d_entry.entry_date)
            if not d_date:
                continue

            for c_entry in credits:
                if d_entry.row_number == c_entry.row_number:
                    continue
                pair_key = (min(d_entry.row_number, c_entry.row_number),
                            max(d_entry.row_number, c_entry.row_number))
                if pair_key in seen_pairs:
                    continue

                c_date = parse_date(c_entry.posting_date or c_entry.entry_date)
                if not c_date:
                    continue

                days_apart = abs((d_date - c_date).days)
                if days_apart <= config.reciprocal_days_window:
                    seen_pairs.add(pair_key)
                    # Cross-account check (stronger indicator)
                    cross_account = d_entry.account != c_entry.account
                    severity = Severity.HIGH if cross_account else Severity.MEDIUM

                    for entry in (d_entry, c_entry):
                        flagged.append(FlaggedEntry(
                            entry=entry,
                            test_name="Reciprocal Entries",
                            test_key="reciprocal_entries",
                            test_tier=TestTier.ADVANCED,
                            severity=severity,
                            issue=f"Matching {'cross-account ' if cross_account else ''}pair: ${amt:,.2f} within {days_apart} days",
                            confidence=0.9 if cross_account else 0.7,
                            details={
                                "matched_amount": amt,
                                "days_apart": days_apart,
                                "cross_account": cross_account,
                                "debit_account": d_entry.account,
                                "credit_account": c_entry.account,
                            },
                        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Reciprocal Entries",
        test_key="reciprocal_entries",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description=f"Flags matching debit/credit pairs within {config.reciprocal_days_window} days (round-tripping indicator).",
        flagged_entries=flagged,
    )


def test_just_below_threshold(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T15: Flag entries just below common approval thresholds.

    Entries clustering just below $5K, $10K, $25K, $50K, $100K may indicate
    intentional structuring to avoid approval requirements.
    Enhanced: detects split transactions to same account summing above threshold.
    """
    if not config.threshold_proximity_enabled:
        return TestResult(
            test_name="Just-Below-Threshold",
            test_key="just_below_threshold",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Test disabled.", flagged_entries=[],
        )

    flagged: list[FlaggedEntry] = []
    margin = config.threshold_proximity_pct

    for e in entries:
        amt = e.abs_amount
        if amt == 0:
            continue

        for threshold in config.approval_thresholds:
            lower_bound = threshold * (1 - margin)
            if lower_bound <= amt < threshold:
                severity = Severity.HIGH if threshold >= 50000 else Severity.MEDIUM
                flagged.append(FlaggedEntry(
                    entry=e,
                    test_name="Just-Below-Threshold",
                    test_key="just_below_threshold",
                    test_tier=TestTier.ADVANCED,
                    severity=severity,
                    issue=f"Amount ${amt:,.2f} is {((threshold - amt) / threshold):.1%} below ${threshold:,.0f} threshold",
                    confidence=0.8,
                    details={"amount": amt, "threshold": threshold, "gap_pct": round((threshold - amt) / threshold, 4)},
                ))
                break  # Only flag once per entry (closest threshold)

    # Enhanced: detect split transactions
    account_daily: dict[tuple[str, str], list[JournalEntry]] = {}
    for e in entries:
        d = e.posting_date or e.entry_date or ""
        if d and e.account:
            key = (e.account.lower(), d)
            account_daily.setdefault(key, []).append(e)

    for (acct, day), day_entries in account_daily.items():
        if len(day_entries) < 2:
            continue
        total = sum(e.abs_amount for e in day_entries)
        for threshold in config.approval_thresholds:
            if total > threshold and all(e.abs_amount < threshold for e in day_entries):
                # Split detected: individual entries below threshold, total above
                for e in day_entries:
                    flagged.append(FlaggedEntry(
                        entry=e,
                        test_name="Just-Below-Threshold",
                        test_key="just_below_threshold",
                        test_tier=TestTier.ADVANCED,
                        severity=Severity.HIGH,
                        issue=f"Potential split: {len(day_entries)} entries to '{acct}' on {day} total ${total:,.2f} (>${threshold:,.0f} threshold)",
                        confidence=0.85,
                        details={"split_total": total, "threshold": threshold, "entry_count": len(day_entries), "date": day},
                    ))
                break

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Just-Below-Threshold",
        test_key="just_below_threshold",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags entries just below approval thresholds and split transactions.",
        flagged_entries=flagged,
    )


def test_account_frequency_anomaly(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T16: Flag accounts receiving entries at unusual frequency.

    Calculates monthly posting frequency per account and flags
    months where frequency deviates significantly from the norm.
    """
    if not config.frequency_anomaly_enabled:
        return TestResult(
            test_name="Account Frequency Anomaly",
            test_key="account_frequency_anomaly",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Test disabled.", flagged_entries=[],
        )

    # Group entries by (account, month)
    account_months: dict[str, dict[str, list[JournalEntry]]] = {}
    for e in entries:
        if not e.account:
            continue
        d = parse_date(e.posting_date or e.entry_date)
        if not d:
            continue
        month_key = f"{d.year}-{d.month:02d}"
        acct = e.account.lower()
        account_months.setdefault(acct, {}).setdefault(month_key, []).append(e)

    flagged: list[FlaggedEntry] = []

    for acct, months in account_months.items():
        if len(months) < config.frequency_anomaly_min_periods:
            continue

        counts = [len(entries_list) for entries_list in months.values()]
        if len(counts) < 2:
            continue

        mean_freq = statistics.mean(counts)
        stdev_freq = statistics.stdev(counts) if len(counts) > 1 else 0

        if stdev_freq == 0:
            continue

        threshold = mean_freq + (config.frequency_anomaly_stddev * stdev_freq)

        for month_key, month_entries in months.items():
            count = len(month_entries)
            if count > threshold:
                z_score = (count - mean_freq) / stdev_freq
                severity = Severity.HIGH if z_score > 4 else Severity.MEDIUM
                # Flag the largest entry in the anomalous month as representative
                representative = max(month_entries, key=lambda e: e.abs_amount)
                flagged.append(FlaggedEntry(
                    entry=representative,
                    test_name="Account Frequency Anomaly",
                    test_key="account_frequency_anomaly",
                    test_tier=TestTier.ADVANCED,
                    severity=severity,
                    issue=f"Account '{acct}' had {count} entries in {month_key} (avg: {mean_freq:.1f}, z-score: {z_score:.1f})",
                    confidence=min(z_score / 5.0, 1.0),
                    details={"account": acct, "month": month_key, "count": count, "mean": round(mean_freq, 1), "z_score": round(z_score, 2)},
                ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Account Frequency Anomaly",
        test_key="account_frequency_anomaly",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags accounts with monthly posting frequency >{config.frequency_anomaly_stddev:.1f} std devs above normal.",
        flagged_entries=flagged,
    )


def test_description_length_anomaly(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T17: Flag entries with unusually short or blank descriptions.

    Calculates average description length per account and flags entries
    that are significantly shorter than the account norm.
    """
    if not config.desc_length_enabled:
        return TestResult(
            test_name="Description Length Anomaly",
            test_key="description_length_anomaly",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Test disabled.", flagged_entries=[],
        )

    # Group description lengths by account
    account_desc: dict[str, list[tuple[int, JournalEntry]]] = {}
    entries_with_desc = 0
    for e in entries:
        if not e.account:
            continue
        acct = e.account.lower()
        desc_len = len((e.description or "").strip())
        if e.description is not None:
            entries_with_desc += 1
        account_desc.setdefault(acct, []).append((desc_len, e))

    if entries_with_desc == 0:
        return TestResult(
            test_name="Description Length Anomaly",
            test_key="description_length_anomaly",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="No entries have description data.",
            flagged_entries=[],
        )

    flagged: list[FlaggedEntry] = []

    for acct, desc_entries in account_desc.items():
        if len(desc_entries) < config.desc_length_min_entries:
            continue

        lengths = [d for d, _ in desc_entries]
        non_zero_lengths = [l for l in lengths if l > 0]

        if len(non_zero_lengths) < 2:
            continue

        mean_len = statistics.mean(non_zero_lengths)
        stdev_len = statistics.stdev(non_zero_lengths) if len(non_zero_lengths) > 1 else 0

        # Flag blank descriptions when account typically has them
        if mean_len > 5:
            for desc_len, e in desc_entries:
                if desc_len == 0:
                    flagged.append(FlaggedEntry(
                        entry=e,
                        test_name="Description Length Anomaly",
                        test_key="description_length_anomaly",
                        test_tier=TestTier.ADVANCED,
                        severity=Severity.MEDIUM,
                        issue=f"Blank description for account '{acct}' (avg length: {mean_len:.0f} chars)",
                        confidence=0.8,
                        details={"account": acct, "desc_length": 0, "mean_length": round(mean_len, 1)},
                    ))
                elif stdev_len > 0:
                    z_score = (mean_len - desc_len) / stdev_len
                    if z_score > config.desc_length_stddev and desc_len < mean_len * 0.3:
                        flagged.append(FlaggedEntry(
                            entry=e,
                            test_name="Description Length Anomaly",
                            test_key="description_length_anomaly",
                            test_tier=TestTier.ADVANCED,
                            severity=Severity.LOW,
                            issue=f"Short description ({desc_len} chars) for account '{acct}' (avg: {mean_len:.0f} chars)",
                            confidence=min(z_score / 4.0, 1.0),
                            details={"account": acct, "desc_length": desc_len, "mean_length": round(mean_len, 1), "z_score": round(z_score, 2)},
                        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Description Length Anomaly",
        test_key="description_length_anomaly",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags entries with unusually short or blank descriptions vs account norms.",
        flagged_entries=flagged,
    )


def test_unusual_account_combinations(
    entries: list[JournalEntry],
    config: JETestingConfig,
) -> TestResult:
    """T18: Flag rarely-seen debit/credit account pairings.

    Groups entries by entry_id to identify which accounts appear together
    in journal entries, then flags rare combinations.
    """
    if not config.unusual_combo_enabled:
        return TestResult(
            test_name="Unusual Account Combinations",
            test_key="unusual_account_combinations",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Test disabled.", flagged_entries=[],
        )

    # Group entries by entry_id
    id_groups: dict[str, list[JournalEntry]] = {}
    for e in entries:
        if e.entry_id:
            id_groups.setdefault(e.entry_id.strip(), []).append(e)

    if len(id_groups) < config.unusual_combo_min_total_entries:
        return TestResult(
            test_name="Unusual Account Combinations",
            test_key="unusual_account_combinations",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Requires entry_id column with sufficient grouped entries.",
            flagged_entries=[],
        )

    # Count account pair frequencies
    pair_counts: dict[tuple[str, str], int] = {}
    pair_entries: dict[tuple[str, str], list[JournalEntry]] = {}

    for entry_id, group in id_groups.items():
        debit_accounts = sorted(set(e.account.lower() for e in group if e.debit > 0 and e.account))
        credit_accounts = sorted(set(e.account.lower() for e in group if e.credit > 0 and e.account))

        for da in debit_accounts:
            for ca in credit_accounts:
                pair = (da, ca)
                pair_counts[pair] = pair_counts.get(pair, 0) + 1
                pair_entries.setdefault(pair, []).extend(group)

    flagged: list[FlaggedEntry] = []
    flagged_rows: set[int] = set()

    for pair, count in pair_counts.items():
        if count <= config.unusual_combo_max_frequency:
            for e in pair_entries[pair]:
                if e.row_number in flagged_rows:
                    continue
                flagged_rows.add(e.row_number)
                severity = Severity.HIGH if e.abs_amount > 10000 else Severity.MEDIUM
                flagged.append(FlaggedEntry(
                    entry=e,
                    test_name="Unusual Account Combinations",
                    test_key="unusual_account_combinations",
                    test_tier=TestTier.ADVANCED,
                    severity=severity,
                    issue=f"Rare account pairing: DR '{pair[0]}' / CR '{pair[1]}' (seen {count}x)",
                    confidence=0.7 if count == 1 else 0.5,
                    details={"debit_account": pair[0], "credit_account": pair[1], "pair_frequency": count},
                ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return TestResult(
        test_name="Unusual Account Combinations",
        test_key="unusual_account_combinations",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags journal entries with account pairings seen <={config.unusual_combo_max_frequency} times.",
        flagged_entries=flagged,
    )


# =============================================================================
# STRATIFIED SAMPLING ENGINE
# =============================================================================

def _amount_range_label(amt: float) -> str:
    """Classify amount into a range bucket for stratification."""
    if amt < 100:
        return "$0-$100"
    elif amt < 1000:
        return "$100-$1K"
    elif amt < 10000:
        return "$1K-$10K"
    elif amt < 100000:
        return "$10K-$100K"
    else:
        return "$100K+"


def preview_sampling_strata(
    entries: list[JournalEntry],
    stratify_by: list[str],
) -> list[dict]:
    """Preview stratum counts without running sampling.

    Args:
        entries: Parsed journal entries
        stratify_by: List of criteria: "account", "amount_range", "period", "user"

    Returns list of strata dicts with name, criteria, and population_size.
    """
    strata: dict[str, list[JournalEntry]] = {}

    for e in entries:
        keys = []
        for criterion in stratify_by:
            if criterion == "account":
                keys.append(e.account or "Unknown")
            elif criterion == "amount_range":
                keys.append(_amount_range_label(e.abs_amount))
            elif criterion == "period":
                d = parse_date(e.posting_date or e.entry_date)
                keys.append(f"{d.year}-{d.month:02d}" if d else "Unknown")
            elif criterion == "user":
                keys.append(e.posted_by or "Unknown")

        stratum_key = " | ".join(keys) if keys else "All"
        strata.setdefault(stratum_key, []).append(e)

    return [
        {"name": key, "criteria": " & ".join(stratify_by), "population_size": len(group)}
        for key, group in sorted(strata.items(), key=lambda x: -len(x[1]))
    ]


def run_stratified_sampling(
    entries: list[JournalEntry],
    stratify_by: list[str],
    sample_rate: float = 0.10,
    fixed_per_stratum: Optional[int] = None,
) -> SamplingResult:
    """Run stratified random sampling using CSPRNG.

    Args:
        entries: Full population of journal entries
        stratify_by: Stratification criteria
        sample_rate: Percentage to sample (0.0-1.0), used if fixed_per_stratum is None
        fixed_per_stratum: Fixed count per stratum (overrides sample_rate)

    Returns SamplingResult with strata and sampled entries.
    """
    # Generate cryptographic seed for reproducibility
    seed_bytes = secrets.token_bytes(16)
    sampling_seed = seed_bytes.hex()

    # Build strata
    strata_groups: dict[str, list[JournalEntry]] = {}
    for e in entries:
        keys = []
        for criterion in stratify_by:
            if criterion == "account":
                keys.append(e.account or "Unknown")
            elif criterion == "amount_range":
                keys.append(_amount_range_label(e.abs_amount))
            elif criterion == "period":
                d = parse_date(e.posting_date or e.entry_date)
                keys.append(f"{d.year}-{d.month:02d}" if d else "Unknown")
            elif criterion == "user":
                keys.append(e.posted_by or "Unknown")
        stratum_key = " | ".join(keys) if keys else "All"
        strata_groups.setdefault(stratum_key, []).append(e)

    strata_results: list[SamplingStratum] = []
    all_sampled: list[JournalEntry] = []

    for stratum_name, population in sorted(strata_groups.items()):
        pop_size = len(population)
        if fixed_per_stratum is not None:
            sample_size = min(fixed_per_stratum, pop_size)
        else:
            sample_size = max(1, round(pop_size * sample_rate))
            sample_size = min(sample_size, pop_size)

        # CSPRNG selection using secrets.SystemRandom
        rng = secrets.SystemRandom()
        sampled = rng.sample(population, sample_size)
        sampled_rows = [e.row_number for e in sampled]

        strata_results.append(SamplingStratum(
            name=stratum_name,
            criteria=" & ".join(stratify_by),
            population_size=pop_size,
            sample_size=sample_size,
            sampled_rows=sampled_rows,
        ))
        all_sampled.extend(sampled)

    return SamplingResult(
        total_population=len(entries),
        total_sampled=len(all_sampled),
        strata=strata_results,
        sampled_entries=all_sampled,
        sampling_seed=sampling_seed,
        parameters={
            "stratify_by": stratify_by,
            "sample_rate": sample_rate,
            "fixed_per_stratum": fixed_per_stratum,
        },
    )


# =============================================================================
# TEST BATTERY
# =============================================================================

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

    # Tier 3 — Advanced / Fraud Indicators (T14-T18)
    results.append(test_reciprocal_entries(entries, config))
    results.append(test_just_below_threshold(entries, config))
    results.append(test_account_frequency_anomaly(entries, config))
    results.append(test_description_length_anomaly(entries, config))
    results.append(test_unusual_account_combinations(entries, config))

    return results, benford_data


def calculate_composite_score(
    test_results: list[TestResult],
    total_entries: int,
) -> CompositeScore:
    """Calculate the composite risk score from test results.

    Delegates to shared test aggregator (Sprint 152).
    """
    result = _shared_calc_cs(test_results, total_entries)

    return CompositeScore(
        score=result.score,
        risk_tier=result.risk_tier,
        tests_run=result.tests_run,
        total_entries=result.total_entries,
        total_flagged=result.total_flagged,
        flag_rate=result.flag_rate,
        flags_by_severity=result.flags_by_severity,
        top_findings=result.top_findings,
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
