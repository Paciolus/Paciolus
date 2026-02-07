"""
AP Testing Engine (Duplicate Payment Detection) - Sprint 73-74

Provides automated accounts payable testing for payment data.
Parses AP files (CSV/Excel), detects columns, runs structural tests,
statistical analysis, and fraud indicator detection.

Sprint 73: AP column detection, dual-date, APTestingConfig, data quality,
  Tier 1 structural tests (AP-T1 to AP-T5)
Sprint 74: Tier 2 statistical tests (AP-T6 to AP-T10),
  Tier 3 fraud indicators (AP-T11 to AP-T13), API endpoint

ZERO-STORAGE COMPLIANCE:
- All AP files processed in-memory only
- Test results are ephemeral (computed on demand)
- No raw payment data is stored

Audit Standards References:
- ISA 240: Auditor's Responsibilities Relating to Fraud
- ISA 500: Audit Evidence (duplicate payments as overstatement risk)
- PCAOB AS 2401: Consideration of Fraud
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, date
from difflib import SequenceMatcher
import re
import math
import statistics


# =============================================================================
# ENUMS (duplicated from JE engine — tools are independent products)
# =============================================================================

class RiskTier(str, Enum):
    """Composite risk tier for AP testing results."""
    LOW = "low"                  # Score 0-9
    ELEVATED = "elevated"        # Score 10-24
    MODERATE = "moderate"        # Score 25-49
    HIGH = "high"                # Score 50-74
    CRITICAL = "critical"        # Score 75+


class TestTier(str, Enum):
    """Test classification tier."""
    STRUCTURAL = "structural"    # Tier 1: Basic structural checks
    STATISTICAL = "statistical"  # Tier 2: Statistical analysis (Sprint 74)
    ADVANCED = "advanced"        # Tier 3: Advanced patterns (Sprint 74)


class Severity(str, Enum):
    """Severity of a flagged payment."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.HIGH: 3.0,
    Severity.MEDIUM: 2.0,
    Severity.LOW: 1.0,
}


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class APTestingConfig:
    """Configurable thresholds for all AP tests.

    Defaults are sensible for most AP datasets.
    """
    # AP-T1: Exact Duplicate Payments
    duplicate_tolerance: float = 0.01        # Amount match tolerance

    # AP-T3: Check Number Gaps
    check_number_gap_enabled: bool = True
    check_number_gap_min_size: int = 2

    # AP-T4: Round Dollar Amounts
    round_amount_threshold: float = 10000.0
    round_amount_max_flags: int = 50

    # AP-T5: Payment Before Invoice
    payment_before_invoice_enabled: bool = True

    # AP-T6: Fuzzy Duplicate Payments
    duplicate_days_window: int = 30

    # AP-T7: Invoice Number Reuse
    invoice_reuse_check: bool = True

    # AP-T8: Unusual Payment Amounts
    unusual_amount_stddev: float = 3.0
    unusual_amount_min_payments: int = 5

    # AP-T9: Weekend Payments
    weekend_payment_enabled: bool = True
    weekend_large_amount_threshold: float = 10000.0

    # AP-T10: High-Frequency Vendors
    high_frequency_vendor_enabled: bool = True
    high_frequency_vendor_daily_threshold: int = 5

    # AP-T11: Vendor Name Variations
    vendor_variation_enabled: bool = True
    vendor_variation_threshold: float = 0.85

    # AP-T12: Just-Below-Threshold
    threshold_proximity_enabled: bool = True
    threshold_proximity_pct: float = 0.05
    approval_thresholds: list[float] = field(default_factory=lambda: [5000.0, 10000.0, 25000.0, 50000.0, 100000.0])

    # AP-T13: Suspicious Descriptions
    suspicious_keyword_enabled: bool = True
    suspicious_keyword_threshold: float = 0.60


# =============================================================================
# AP COLUMN DETECTION
# =============================================================================

class APColumnType(str, Enum):
    """Types of columns in an AP payment file."""
    INVOICE_NUMBER = "invoice_number"
    INVOICE_DATE = "invoice_date"
    PAYMENT_DATE = "payment_date"
    VENDOR_NAME = "vendor_name"
    VENDOR_ID = "vendor_id"
    AMOUNT = "amount"
    CHECK_NUMBER = "check_number"
    DESCRIPTION = "description"
    GL_ACCOUNT = "gl_account"
    PAYMENT_METHOD = "payment_method"
    UNKNOWN = "unknown"


# Weighted regex patterns for AP column detection
# Format: (pattern, weight, is_exact)

AP_INVOICE_NUMBER_PATTERNS = [
    (r"^invoice\s*number$", 1.0, True),
    (r"^invoice\s*no$", 0.98, True),
    (r"^invoice\s*#$", 0.95, True),
    (r"^inv\s*no$", 0.90, True),
    (r"^inv\s*number$", 0.90, True),
    (r"^invoice\s*num$", 0.90, True),
    (r"^bill\s*number$", 0.85, True),
    (r"^bill\s*no$", 0.85, True),
    (r"^document\s*number$", 0.80, True),
    (r"^doc\s*no$", 0.75, True),
    (r"invoice.?n", 0.65, False),
]

AP_INVOICE_DATE_PATTERNS = [
    (r"^invoice\s*date$", 1.0, True),
    (r"^inv\s*date$", 0.95, True),
    (r"^bill\s*date$", 0.90, True),
    (r"^document\s*date$", 0.85, True),
    (r"^doc\s*date$", 0.80, True),
    (r"invoice.?date", 0.70, False),
]

AP_PAYMENT_DATE_PATTERNS = [
    (r"^payment\s*date$", 1.0, True),
    (r"^pay\s*date$", 0.95, True),
    (r"^paid\s*date$", 0.95, True),
    (r"^check\s*date$", 0.90, True),
    (r"^cheque\s*date$", 0.90, True),
    (r"^disbursement\s*date$", 0.85, True),
    (r"^clearing\s*date$", 0.80, True),
    (r"^date$", 0.60, True),
    (r"payment.?date", 0.70, False),
    (r"pay.?date", 0.65, False),
]

AP_VENDOR_NAME_PATTERNS = [
    (r"^vendor\s*name$", 1.0, True),
    (r"^vendor$", 0.95, True),
    (r"^supplier\s*name$", 0.95, True),
    (r"^supplier$", 0.90, True),
    (r"^payee\s*name$", 0.90, True),
    (r"^payee$", 0.85, True),
    (r"^beneficiary$", 0.80, True),
    (r"vendor", 0.60, False),
    (r"supplier", 0.55, False),
]

AP_VENDOR_ID_PATTERNS = [
    (r"^vendor\s*id$", 1.0, True),
    (r"^vendor\s*code$", 0.95, True),
    (r"^vendor\s*number$", 0.95, True),
    (r"^vendor\s*no$", 0.90, True),
    (r"^supplier\s*id$", 0.90, True),
    (r"^supplier\s*code$", 0.90, True),
    (r"^payee\s*id$", 0.85, True),
    (r"vendor.?id", 0.70, False),
    (r"vendor.?code", 0.65, False),
]

AP_AMOUNT_PATTERNS = [
    (r"^amount$", 0.95, True),
    (r"^payment\s*amount$", 1.0, True),
    (r"^pay\s*amount$", 0.95, True),
    (r"^invoice\s*amount$", 0.90, True),
    (r"^total\s*amount$", 0.90, True),
    (r"^gross\s*amount$", 0.85, True),
    (r"^net\s*amount$", 0.85, True),
    (r"^disbursement\s*amount$", 0.85, True),
    (r"amount", 0.60, False),
]

AP_CHECK_NUMBER_PATTERNS = [
    (r"^check\s*number$", 1.0, True),
    (r"^check\s*no$", 0.98, True),
    (r"^check\s*#$", 0.95, True),
    (r"^cheque\s*number$", 0.95, True),
    (r"^cheque\s*no$", 0.95, True),
    (r"^chk\s*no$", 0.90, True),
    (r"^chk\s*number$", 0.90, True),
    (r"^payment\s*number$", 0.80, True),
    (r"^payment\s*no$", 0.80, True),
    (r"check.?n", 0.65, False),
    (r"cheque.?n", 0.60, False),
]

AP_DESCRIPTION_PATTERNS = [
    (r"^description$", 1.0, True),
    (r"^memo$", 0.95, True),
    (r"^payment\s*description$", 0.95, True),
    (r"^narration$", 0.90, True),
    (r"^narrative$", 0.90, True),
    (r"^comment$", 0.80, True),
    (r"^remarks$", 0.80, True),
    (r"^line\s*description$", 0.85, True),
    (r"description", 0.65, False),
    (r"memo", 0.60, False),
]

AP_GL_ACCOUNT_PATTERNS = [
    (r"^gl\s*account$", 1.0, True),
    (r"^account\s*code$", 0.95, True),
    (r"^account\s*number$", 0.95, True),
    (r"^account$", 0.85, True),
    (r"^expense\s*account$", 0.90, True),
    (r"^cost\s*center$", 0.80, True),
    (r"^gl\s*code$", 0.90, True),
    (r"gl.?account", 0.70, False),
    (r"account.?code", 0.60, False),
]

AP_PAYMENT_METHOD_PATTERNS = [
    (r"^payment\s*method$", 1.0, True),
    (r"^pay\s*method$", 0.95, True),
    (r"^payment\s*type$", 0.95, True),
    (r"^pay\s*type$", 0.90, True),
    (r"^disbursement\s*type$", 0.85, True),
    (r"^payment\s*mode$", 0.85, True),
    (r"payment.?method", 0.70, False),
    (r"pay.?type", 0.60, False),
]

# Map of AP column type to its patterns — priority order (most specific first)
AP_COLUMN_PATTERNS: dict[APColumnType, list] = {
    APColumnType.INVOICE_NUMBER: AP_INVOICE_NUMBER_PATTERNS,
    APColumnType.INVOICE_DATE: AP_INVOICE_DATE_PATTERNS,
    APColumnType.PAYMENT_DATE: AP_PAYMENT_DATE_PATTERNS,
    APColumnType.VENDOR_NAME: AP_VENDOR_NAME_PATTERNS,
    APColumnType.VENDOR_ID: AP_VENDOR_ID_PATTERNS,
    APColumnType.AMOUNT: AP_AMOUNT_PATTERNS,
    APColumnType.CHECK_NUMBER: AP_CHECK_NUMBER_PATTERNS,
    APColumnType.DESCRIPTION: AP_DESCRIPTION_PATTERNS,
    APColumnType.GL_ACCOUNT: AP_GL_ACCOUNT_PATTERNS,
    APColumnType.PAYMENT_METHOD: AP_PAYMENT_METHOD_PATTERNS,
}


def _match_ap_column(column_name: str, patterns: list[tuple]) -> float:
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


# =============================================================================
# AP COLUMN DETECTION RESULT
# =============================================================================

@dataclass
class APColumnDetectionResult:
    """Result of AP column detection."""
    # Required columns
    vendor_name_column: Optional[str] = None
    amount_column: Optional[str] = None
    payment_date_column: Optional[str] = None

    # Optional columns
    invoice_number_column: Optional[str] = None
    invoice_date_column: Optional[str] = None
    vendor_id_column: Optional[str] = None
    check_number_column: Optional[str] = None
    description_column: Optional[str] = None
    gl_account_column: Optional[str] = None
    payment_method_column: Optional[str] = None

    # Metadata
    has_dual_dates: bool = False
    has_check_numbers: bool = False
    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "vendor_name_column": self.vendor_name_column,
            "amount_column": self.amount_column,
            "payment_date_column": self.payment_date_column,
            "invoice_number_column": self.invoice_number_column,
            "invoice_date_column": self.invoice_date_column,
            "vendor_id_column": self.vendor_id_column,
            "check_number_column": self.check_number_column,
            "description_column": self.description_column,
            "gl_account_column": self.gl_account_column,
            "payment_method_column": self.payment_method_column,
            "has_dual_dates": self.has_dual_dates,
            "has_check_numbers": self.has_check_numbers,
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


def detect_ap_columns(column_names: list[str]) -> APColumnDetectionResult:
    """Detect AP columns using weighted pattern matching.

    Supports:
    - Dual date columns (invoice_date + payment_date) or single payment_date
    - Optional check number, vendor ID, GL account, payment method
    - Greedy assignment prevents double-mapping
    """
    columns = [col.strip() for col in column_names]
    notes: list[str] = []
    result = APColumnDetectionResult(all_columns=columns)

    # Track best match per column type, preventing double-assignment
    assigned_columns: set[str] = set()

    # Score all columns for all types
    scored: dict[str, dict[APColumnType, float]] = {}
    for col in columns:
        scored[col] = {}
        for col_type, patterns in AP_COLUMN_PATTERNS.items():
            scored[col][col_type] = _match_ap_column(col, patterns)

    def assign_best(col_type: APColumnType, min_conf: float = 0.0) -> Optional[tuple[str, float]]:
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

    # 1. Invoice number (most specific — assign first)
    inv_match = assign_best(APColumnType.INVOICE_NUMBER)
    if inv_match:
        result.invoice_number_column = inv_match[0]

    # 2. Invoice date
    inv_date_match = assign_best(APColumnType.INVOICE_DATE)
    if inv_date_match:
        result.invoice_date_column = inv_date_match[0]

    # 3. Payment date (required)
    pay_date_match = assign_best(APColumnType.PAYMENT_DATE)
    if pay_date_match:
        result.payment_date_column = pay_date_match[0]
    else:
        notes.append("Could not identify a Payment Date column")

    # Set dual date flag
    if result.invoice_date_column and result.payment_date_column:
        result.has_dual_dates = True
        notes.append("Dual-date detected: invoice_date + payment_date")

    # 4. Vendor name (required)
    vendor_match = assign_best(APColumnType.VENDOR_NAME)
    if vendor_match:
        result.vendor_name_column = vendor_match[0]
    else:
        notes.append("Could not identify a Vendor Name column")

    # 5. Vendor ID
    vid_match = assign_best(APColumnType.VENDOR_ID)
    if vid_match:
        result.vendor_id_column = vid_match[0]

    # 6. Amount (required)
    amt_match = assign_best(APColumnType.AMOUNT)
    if amt_match:
        result.amount_column = amt_match[0]
    else:
        notes.append("Could not identify an Amount column")

    # 7. Check number
    chk_match = assign_best(APColumnType.CHECK_NUMBER)
    if chk_match:
        result.check_number_column = chk_match[0]
        result.has_check_numbers = True

    # 8. Description
    desc_match = assign_best(APColumnType.DESCRIPTION)
    if desc_match:
        result.description_column = desc_match[0]

    # 9. GL Account
    gl_match = assign_best(APColumnType.GL_ACCOUNT)
    if gl_match:
        result.gl_account_column = gl_match[0]

    # 10. Payment method
    pm_match = assign_best(APColumnType.PAYMENT_METHOD)
    if pm_match:
        result.payment_method_column = pm_match[0]

    # Calculate overall confidence (min of required-column confidences)
    required_confidences = []

    if result.vendor_name_column and vendor_match:
        required_confidences.append(vendor_match[1])
    else:
        required_confidences.append(0.0)

    if result.amount_column and amt_match:
        required_confidences.append(amt_match[1])
    else:
        required_confidences.append(0.0)

    if result.payment_date_column and pay_date_match:
        required_confidences.append(pay_date_match[1])
    else:
        required_confidences.append(0.0)

    result.overall_confidence = min(required_confidences) if required_confidences else 0.0
    result.detection_notes = notes
    return result


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class APPayment:
    """A single payment line from the AP file."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    payment_date: Optional[str] = None
    vendor_name: str = ""
    vendor_id: Optional[str] = None
    amount: float = 0.0           # Single amount (not debit/credit)
    check_number: Optional[str] = None
    description: Optional[str] = None
    gl_account: Optional[str] = None
    payment_method: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "payment_date": self.payment_date,
            "vendor_name": self.vendor_name,
            "vendor_id": self.vendor_id,
            "amount": self.amount,
            "check_number": self.check_number,
            "description": self.description,
            "gl_account": self.gl_account,
            "payment_method": self.payment_method,
            "row_number": self.row_number,
        }


@dataclass
class FlaggedPayment:
    """A payment flagged by one or more tests."""
    entry: APPayment
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
class APTestResult:
    """Result of a single AP test."""
    test_name: str
    test_key: str
    test_tier: TestTier
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Severity
    description: str
    flagged_entries: list[FlaggedPayment] = field(default_factory=list)

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
class APDataQuality:
    """Quality assessment of the AP data."""
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
class APCompositeScore:
    """Overall AP testing composite score."""
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
class APTestingResult:
    """Complete result of AP payment testing."""
    composite_score: APCompositeScore
    test_results: list[APTestResult] = field(default_factory=list)
    data_quality: Optional[APDataQuality] = None
    column_detection: Optional[APColumnDetectionResult] = None

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [t.to_dict() for t in self.test_results],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "column_detection": self.column_detection.to_dict() if self.column_detection else None,
        }


# =============================================================================
# HELPERS (duplicated from JE engine — independent tool)
# =============================================================================

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


# =============================================================================
# AP PARSER
# =============================================================================

def parse_ap_payments(
    rows: list[dict],
    detection: APColumnDetectionResult,
) -> list[APPayment]:
    """Parse raw AP rows into APPayment objects using detected columns.

    Args:
        rows: List of dicts (each row from CSV/Excel)
        detection: Column detection result mapping column names

    Returns:
        List of APPayment objects
    """
    payments: list[APPayment] = []

    for idx, row in enumerate(rows):
        payment = APPayment(row_number=idx + 1)

        # Required fields
        if detection.vendor_name_column:
            payment.vendor_name = _safe_str(row.get(detection.vendor_name_column)) or ""
        if detection.amount_column:
            payment.amount = _safe_float(row.get(detection.amount_column))
        if detection.payment_date_column:
            payment.payment_date = _safe_str(row.get(detection.payment_date_column))

        # Optional fields
        if detection.invoice_number_column:
            payment.invoice_number = _safe_str(row.get(detection.invoice_number_column))
        if detection.invoice_date_column:
            payment.invoice_date = _safe_str(row.get(detection.invoice_date_column))
        if detection.vendor_id_column:
            payment.vendor_id = _safe_str(row.get(detection.vendor_id_column))
        if detection.check_number_column:
            payment.check_number = _safe_str(row.get(detection.check_number_column))
        if detection.description_column:
            payment.description = _safe_str(row.get(detection.description_column))
        if detection.gl_account_column:
            payment.gl_account = _safe_str(row.get(detection.gl_account_column))
        if detection.payment_method_column:
            payment.payment_method = _safe_str(row.get(detection.payment_method_column))

        payments.append(payment)

    return payments


# =============================================================================
# DATA QUALITY SCORING
# =============================================================================

def assess_ap_data_quality(
    payments: list[APPayment],
    detection: APColumnDetectionResult,
) -> APDataQuality:
    """Assess the quality and completeness of AP data.

    Checks fill rates for all detected columns and flags issues.
    """
    total = len(payments)
    if total == 0:
        return APDataQuality(completeness_score=0.0, total_rows=0)

    issues: list[str] = []
    fill_rates: dict[str, float] = {}

    # Required fields
    vendor_filled = sum(1 for p in payments if p.vendor_name)
    fill_rates["vendor_name"] = vendor_filled / total

    amount_filled = sum(1 for p in payments if p.amount != 0)
    fill_rates["amount"] = amount_filled / total

    date_filled = sum(1 for p in payments if p.payment_date)
    fill_rates["payment_date"] = date_filled / total

    # Optional fields
    if detection.invoice_number_column:
        inv_filled = sum(1 for p in payments if p.invoice_number)
        fill_rates["invoice_number"] = inv_filled / total
        if fill_rates["invoice_number"] < 0.80:
            issues.append(
                f"Low invoice number fill rate: {fill_rates['invoice_number']:.0%} "
                f"({total - inv_filled} blank)"
            )

    if detection.invoice_date_column:
        inv_date_filled = sum(1 for p in payments if p.invoice_date)
        fill_rates["invoice_date"] = inv_date_filled / total

    if detection.vendor_id_column:
        vid_filled = sum(1 for p in payments if p.vendor_id)
        fill_rates["vendor_id"] = vid_filled / total

    if detection.check_number_column:
        chk_filled = sum(1 for p in payments if p.check_number)
        fill_rates["check_number"] = chk_filled / total

    if detection.description_column:
        desc_filled = sum(1 for p in payments if p.description)
        fill_rates["description"] = desc_filled / total
        if fill_rates["description"] < 0.80:
            issues.append(
                f"Low description fill rate: {fill_rates['description']:.0%} "
                f"({total - desc_filled} blank)"
            )

    if detection.gl_account_column:
        gl_filled = sum(1 for p in payments if p.gl_account)
        fill_rates["gl_account"] = gl_filled / total

    if detection.payment_method_column:
        pm_filled = sum(1 for p in payments if p.payment_method)
        fill_rates["payment_method"] = pm_filled / total

    # Flag issues on required fields
    if fill_rates.get("vendor_name", 0) < 0.95:
        issues.append(f"Missing vendor name on {total - vendor_filled} payments")

    if fill_rates.get("payment_date", 0) < 0.95:
        issues.append(f"Missing payment date on {total - date_filled} payments")

    if fill_rates.get("amount", 0) < 0.90:
        zero_amt = total - amount_filled
        issues.append(f"{zero_amt} payments have zero amount")

    # Completeness score: weighted average
    weights = {"vendor_name": 0.30, "amount": 0.30, "payment_date": 0.25}
    optional_weight = 0.15 / max(
        len([k for k in fill_rates if k not in weights]), 1
    )
    for k in fill_rates:
        if k not in weights:
            weights[k] = optional_weight

    score = sum(fill_rates.get(k, 0) * w for k, w in weights.items()) * 100

    return APDataQuality(
        completeness_score=min(score, 100.0),
        field_fill_rates=fill_rates,
        detected_issues=issues,
        total_rows=total,
    )


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
# AP ROUND AMOUNT PATTERNS (AP-specific tiers with $25K)
# =============================================================================

AP_ROUND_AMOUNT_PATTERNS: list[tuple[float, str, Severity]] = [
    (100000.0, "hundred_thousand", Severity.HIGH),
    (50000.0, "fifty_thousand", Severity.HIGH),
    (25000.0, "twenty_five_thousand", Severity.MEDIUM),
    (10000.0, "ten_thousand", Severity.LOW),
]


# =============================================================================
# TIER 1 TESTS
# =============================================================================

def test_exact_duplicate_payments(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T1: Exact Duplicate Payment Detection.

    Key: (vendor_name.lower(), invoice_number.lower(), round(amount,2), payment_date)
    Flags all entries in groups with count > 1.

    Exact duplicates are serious — always HIGH severity.
    """
    # Build duplicate groups
    groups: dict[tuple, list[APPayment]] = {}
    for p in payments:
        inv = (p.invoice_number or "").lower().strip()
        vendor = p.vendor_name.lower().strip()
        amt = round(p.amount, 2)
        pay_date = (p.payment_date or "").strip()
        key = (vendor, inv, amt, pay_date)
        groups.setdefault(key, []).append(p)

    flagged: list[FlaggedPayment] = []
    for key, group in groups.items():
        if len(group) > 1:
            vendor, inv, amt, pay_date = key
            for p in group:
                flagged.append(FlaggedPayment(
                    entry=p,
                    test_name="Exact Duplicate Payments",
                    test_key="exact_duplicate_payments",
                    test_tier=TestTier.STRUCTURAL,
                    severity=Severity.HIGH,
                    issue=f"Exact duplicate: vendor={p.vendor_name}, invoice={p.invoice_number}, amount=${amt:,.2f}",
                    confidence=0.95,
                    details={
                        "duplicate_count": len(group),
                        "vendor": vendor,
                        "invoice_number": inv,
                        "amount": amt,
                        "payment_date": pay_date,
                    },
                ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Exact Duplicate Payments",
        test_key="exact_duplicate_payments",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags payments with identical vendor, invoice number, amount, and payment date.",
        flagged_entries=flagged,
    )


def test_missing_critical_fields(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T2: Missing Critical Fields.

    Checks: vendor_name blank → HIGH, amount == 0 → HIGH, payment_date blank → MEDIUM.
    """
    flagged: list[FlaggedPayment] = []

    for p in payments:
        missing_fields: list[str] = []
        severity = Severity.LOW

        if not p.vendor_name.strip():
            missing_fields.append("vendor_name")
            severity = Severity.HIGH
        if p.amount == 0:
            missing_fields.append("amount")
            severity = Severity.HIGH
        if not p.payment_date:
            missing_fields.append("payment_date")
            if severity != Severity.HIGH:
                severity = Severity.MEDIUM

        if missing_fields:
            flagged.append(FlaggedPayment(
                entry=p,
                test_name="Missing Critical Fields",
                test_key="missing_critical_fields",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Missing: {', '.join(missing_fields)}",
                confidence=0.90,
                details={"missing_fields": missing_fields},
            ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Missing Critical Fields",
        test_key="missing_critical_fields",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags payments missing vendor name, amount, or payment date.",
        flagged_entries=flagged,
    )


def _extract_check_number(check_str: Optional[str]) -> Optional[int]:
    """Extract the numeric portion from a check number string."""
    if not check_str:
        return None
    # Strip common prefixes like CHK-, CK-, #
    cleaned = re.sub(r'^[A-Za-z#\-]+', '', check_str.strip())
    # Extract leading digits
    match = re.match(r'(\d+)', cleaned)
    if match:
        return int(match.group(1))
    return None


def test_check_number_gaps(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T3: Check Number Gaps.

    Opt-in: skip if disabled or no check numbers in data.
    Sort by numeric check number, flag gaps >= config threshold.
    """
    if not config.check_number_gap_enabled:
        return APTestResult(
            test_name="Check Number Gaps",
            test_key="check_number_gaps",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    numbered: list[tuple[int, APPayment]] = []
    for p in payments:
        num = _extract_check_number(p.check_number)
        if num is not None:
            numbered.append((num, p))

    if len(numbered) < 2:
        return APTestResult(
            test_name="Check Number Gaps",
            test_key="check_number_gaps",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Requires check number column with numeric sequence (not available or insufficient data).",
            flagged_entries=[],
        )

    numbered.sort(key=lambda x: x[0])
    flagged: list[FlaggedPayment] = []

    for i in range(1, len(numbered)):
        prev_num, _ = numbered[i - 1]
        curr_num, curr_payment = numbered[i]
        gap = curr_num - prev_num

        if gap >= config.check_number_gap_min_size:
            if gap > 100:
                severity = Severity.HIGH
            elif gap > 10:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedPayment(
                entry=curr_payment,
                test_name="Check Number Gaps",
                test_key="check_number_gaps",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Gap of {gap - 1} missing checks before #{curr_num} (previous: #{prev_num})",
                confidence=0.70,
                details={"gap_size": gap - 1, "prev_number": prev_num, "curr_number": curr_num},
            ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Check Number Gaps",
        test_key="check_number_gaps",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags gaps in sequential check numbering that may indicate voided or missing payments.",
        flagged_entries=flagged,
    )


def test_round_dollar_amounts(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T4: Round Dollar Amounts.

    AP-specific tiers: $100K (HIGH), $50K (HIGH), $25K (MEDIUM), $10K (LOW).
    The $25K tier is new — common AP approval threshold.
    """
    flagged: list[FlaggedPayment] = []

    for p in payments:
        amt = abs(p.amount)
        if amt < config.round_amount_threshold:
            continue

        for divisor, name, severity in AP_ROUND_AMOUNT_PATTERNS:
            if amt >= divisor and amt % divisor == 0:
                flagged.append(FlaggedPayment(
                    entry=p,
                    test_name="Round Dollar Amounts",
                    test_key="round_dollar_amounts",
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
    flagged.sort(key=lambda f: abs(f.entry.amount), reverse=True)

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Round Dollar Amounts",
        test_key="round_dollar_amounts",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.LOW,
        description="Flags payments at round dollar amounts that may indicate estimates or manipulation.",
        flagged_entries=flagged,
    )


def test_payment_before_invoice(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T5: Payment Before Invoice Date.

    Opt-in: skip if disabled or no dual dates in data.
    Flags if payment_date < invoice_date.
    Severity: HIGH (>30 days early), MEDIUM (>7 days), LOW (<=7 days).
    """
    if not config.payment_before_invoice_enabled:
        return APTestResult(
            test_name="Payment Before Invoice",
            test_key="payment_before_invoice",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedPayment] = []

    for p in payments:
        pay_date = _parse_date(p.payment_date)
        inv_date = _parse_date(p.invoice_date)

        if not pay_date or not inv_date:
            continue

        if pay_date < inv_date:
            days_early = (inv_date - pay_date).days

            if days_early > 30:
                severity = Severity.HIGH
                confidence = 0.95
            elif days_early > 7:
                severity = Severity.MEDIUM
                confidence = 0.85
            else:
                severity = Severity.LOW
                confidence = 0.70

            flagged.append(FlaggedPayment(
                entry=p,
                test_name="Payment Before Invoice",
                test_key="payment_before_invoice",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Payment {days_early} days before invoice date ({p.payment_date} < {p.invoice_date})",
                confidence=confidence,
                details={
                    "days_early": days_early,
                    "payment_date": p.payment_date,
                    "invoice_date": p.invoice_date,
                },
            ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Payment Before Invoice",
        test_key="payment_before_invoice",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags payments made before the invoice date, which may indicate prepayment errors or fraud.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 2 TESTS — Statistical
# =============================================================================

def test_fuzzy_duplicate_payments(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T6: Fuzzy Duplicate Payment Detection.

    Same vendor + same amount (±tolerance) + different dates within window.
    Unlike T1, this catches near-duplicates across different payment dates.
    """
    flagged: list[FlaggedPayment] = []

    # Group by vendor (lowercase)
    vendor_groups: dict[str, list[APPayment]] = {}
    for p in payments:
        key = p.vendor_name.lower().strip()
        if key:
            vendor_groups.setdefault(key, []).append(p)

    for vendor, group in vendor_groups.items():
        if len(group) < 2:
            continue

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                # Amount match within tolerance
                if abs(a.amount - b.amount) > config.duplicate_tolerance:
                    continue
                # Must be different dates
                date_a = _parse_date(a.payment_date)
                date_b = _parse_date(b.payment_date)
                if not date_a or not date_b:
                    continue
                if date_a == date_b:
                    continue  # Exact duplicates handled by T1
                days_apart = abs((date_a - date_b).days)
                if days_apart > config.duplicate_days_window:
                    continue

                severity = Severity.HIGH if abs(a.amount) > 10000 else Severity.MEDIUM
                for p in (a, b):
                    flagged.append(FlaggedPayment(
                        entry=p,
                        test_name="Fuzzy Duplicate Payments",
                        test_key="fuzzy_duplicate_payments",
                        test_tier=TestTier.STATISTICAL,
                        severity=severity,
                        issue=f"Near-duplicate: vendor={p.vendor_name}, amount=${abs(p.amount):,.2f}, {days_apart} days apart",
                        confidence=0.85,
                        details={
                            "vendor": vendor,
                            "amount": round(p.amount, 2),
                            "days_apart": days_apart,
                            "matched_row": b.row_number if p is a else a.row_number,
                        },
                    ))

    # Deduplicate (a payment may match multiple others)
    seen: set[int] = set()
    unique_flagged: list[FlaggedPayment] = []
    for f in flagged:
        if f.entry.row_number not in seen:
            seen.add(f.entry.row_number)
            unique_flagged.append(f)

    flag_rate = len(unique_flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Fuzzy Duplicate Payments",
        test_key="fuzzy_duplicate_payments",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(unique_flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags payments to the same vendor with matching amounts on different dates within a configurable window.",
        flagged_entries=unique_flagged,
    )


def test_invoice_number_reuse(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T7: Invoice Number Reuse.

    Same invoice number appearing across 2+ different vendors.
    Always HIGH severity — strong indicator of fraud or data entry error.
    """
    if not config.invoice_reuse_check:
        return APTestResult(
            test_name="Invoice Number Reuse",
            test_key="invoice_number_reuse",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    # Group by invoice number (lowercase, stripped)
    inv_groups: dict[str, list[APPayment]] = {}
    for p in payments:
        inv = (p.invoice_number or "").lower().strip()
        if inv:
            inv_groups.setdefault(inv, []).append(p)

    flagged: list[FlaggedPayment] = []
    for inv_num, group in inv_groups.items():
        vendors = {p.vendor_name.lower().strip() for p in group}
        if len(vendors) < 2:
            continue
        for p in group:
            flagged.append(FlaggedPayment(
                entry=p,
                test_name="Invoice Number Reuse",
                test_key="invoice_number_reuse",
                test_tier=TestTier.STATISTICAL,
                severity=Severity.HIGH,
                issue=f"Invoice #{p.invoice_number} used by {len(vendors)} different vendors",
                confidence=0.90,
                details={
                    "invoice_number": inv_num,
                    "vendor_count": len(vendors),
                    "vendors": sorted(vendors),
                },
            ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Invoice Number Reuse",
        test_key="invoice_number_reuse",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags invoice numbers that appear across multiple vendors, indicating possible fraud or data entry errors.",
        flagged_entries=flagged,
    )


def test_unusual_payment_amounts(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T8: Unusual Payment Amounts.

    Per-vendor z-score analysis — flags outlier amounts.
    Requires minimum payments per vendor for statistical validity.
    """
    flagged: list[FlaggedPayment] = []

    # Group by vendor
    vendor_amounts: dict[str, list[APPayment]] = {}
    for p in payments:
        key = p.vendor_name.lower().strip()
        if key:
            vendor_amounts.setdefault(key, []).append(p)

    for vendor, group in vendor_amounts.items():
        if len(group) < config.unusual_amount_min_payments:
            continue

        amounts = [abs(p.amount) for p in group]
        if len(set(amounts)) < 2:
            continue  # All same amount — no variance

        mean = statistics.mean(amounts)
        stdev = statistics.stdev(amounts)
        if stdev == 0:
            continue

        for p in group:
            z = abs(abs(p.amount) - mean) / stdev
            if z < config.unusual_amount_stddev:
                continue

            if z > 5:
                severity = Severity.HIGH
            elif z > 4:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedPayment(
                entry=p,
                test_name="Unusual Payment Amounts",
                test_key="unusual_payment_amounts",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Unusual amount ${abs(p.amount):,.2f} for {p.vendor_name} (z-score: {z:.1f}, mean: ${mean:,.2f})",
                confidence=min(0.60 + z * 0.05, 0.95),
                details={
                    "z_score": round(z, 2),
                    "vendor_mean": round(mean, 2),
                    "vendor_stdev": round(stdev, 2),
                    "vendor_payment_count": len(group),
                },
            ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Unusual Payment Amounts",
        test_key="unusual_payment_amounts",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags payments that are statistical outliers relative to a vendor's typical payment amounts.",
        flagged_entries=flagged,
    )


def test_weekend_payments(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T9: Weekend Payments.

    Flags payments made on Saturday (5) or Sunday (6).
    Severity weighted by amount: large amounts on weekends are higher risk.
    """
    if not config.weekend_payment_enabled:
        return APTestResult(
            test_name="Weekend Payments",
            test_key="weekend_payments",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedPayment] = []

    for p in payments:
        pay_date = _parse_date(p.payment_date)
        if not pay_date:
            continue
        if pay_date.weekday() < 5:
            continue  # Monday-Friday

        day_name = "Saturday" if pay_date.weekday() == 5 else "Sunday"
        severity = Severity.HIGH if abs(p.amount) >= config.weekend_large_amount_threshold else Severity.MEDIUM

        flagged.append(FlaggedPayment(
            entry=p,
            test_name="Weekend Payments",
            test_key="weekend_payments",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Payment on {day_name} ({p.payment_date}): ${abs(p.amount):,.2f} to {p.vendor_name}",
            confidence=0.75,
            details={
                "day_of_week": day_name,
                "payment_date": p.payment_date,
                "amount": round(p.amount, 2),
            },
        ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Weekend Payments",
        test_key="weekend_payments",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags payments processed on weekends, which may indicate unauthorized or unusual activity.",
        flagged_entries=flagged,
    )


def test_high_frequency_vendors(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T10: High-Frequency Vendor Payments.

    Flags vendors receiving 5+ payments in a single day.
    """
    if not config.high_frequency_vendor_enabled:
        return APTestResult(
            test_name="High-Frequency Vendors",
            test_key="high_frequency_vendors",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedPayment] = []

    # Group by (vendor, date)
    vendor_date_groups: dict[tuple[str, str], list[APPayment]] = {}
    for p in payments:
        vendor = p.vendor_name.lower().strip()
        pay_date = (p.payment_date or "").strip()
        if vendor and pay_date:
            vendor_date_groups.setdefault((vendor, pay_date), []).append(p)

    for (vendor, pay_date), group in vendor_date_groups.items():
        count = len(group)
        if count < config.high_frequency_vendor_daily_threshold:
            continue

        severity = Severity.HIGH if count >= 10 else Severity.MEDIUM

        for p in group:
            flagged.append(FlaggedPayment(
                entry=p,
                test_name="High-Frequency Vendors",
                test_key="high_frequency_vendors",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"{p.vendor_name}: {count} payments on {pay_date}",
                confidence=0.80,
                details={
                    "vendor": vendor,
                    "date": pay_date,
                    "daily_count": count,
                },
            ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="High-Frequency Vendors",
        test_key="high_frequency_vendors",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags vendors receiving an unusually high number of payments in a single day.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 3 TESTS — Fraud Indicators
# =============================================================================

AP_SUSPICIOUS_KEYWORDS: list[tuple[str, float, bool]] = [
    ("reimbursement", 0.75, False),
    ("miscellaneous", 0.70, False),
    ("petty cash", 0.85, True),
    ("adjustment", 0.70, False),
    ("rush", 0.80, False),
    ("urgent", 0.75, False),
    ("personal", 0.80, False),
    ("cash advance", 0.85, True),
    ("manual check", 0.85, True),
    ("void reissue", 0.90, True),
    ("duplicate", 0.70, False),
    ("correction", 0.75, False),
    ("override", 0.85, False),
    ("one-time vendor", 0.80, True),
    ("wire transfer", 0.60, False),
    ("expedite", 0.75, False),
]


def test_vendor_name_variations(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T11: Vendor Name Variations.

    Uses SequenceMatcher to find vendor names that are similar but not identical.
    This catches deliberate misspellings used to create ghost vendors.
    """
    if not config.vendor_variation_enabled:
        return APTestResult(
            test_name="Vendor Name Variations",
            test_key="vendor_name_variations",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    # Collect unique vendor names and their total amounts
    vendor_totals: dict[str, float] = {}
    vendor_payments: dict[str, list[APPayment]] = {}
    for p in payments:
        name = p.vendor_name.strip()
        if name:
            lower = name.lower()
            vendor_totals[lower] = vendor_totals.get(lower, 0) + abs(p.amount)
            vendor_payments.setdefault(lower, []).append(p)

    unique_vendors = sorted(vendor_totals.keys())
    if len(unique_vendors) < 2:
        return APTestResult(
            test_name="Vendor Name Variations",
            test_key="vendor_name_variations",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Not enough unique vendors for variation analysis.",
            flagged_entries=[],
        )

    flagged_rows: set[int] = set()
    flagged: list[FlaggedPayment] = []

    for i in range(len(unique_vendors)):
        for j in range(i + 1, len(unique_vendors)):
            name_a = unique_vendors[i]
            name_b = unique_vendors[j]
            if name_a == name_b:
                continue
            ratio = SequenceMatcher(None, name_a, name_b).ratio()
            if ratio < config.vendor_variation_threshold:
                continue

            combined_amount = vendor_totals[name_a] + vendor_totals[name_b]
            severity = Severity.HIGH if combined_amount > 50000 else Severity.MEDIUM

            for p in vendor_payments[name_a] + vendor_payments[name_b]:
                if p.row_number not in flagged_rows:
                    flagged_rows.add(p.row_number)
                    flagged.append(FlaggedPayment(
                        entry=p,
                        test_name="Vendor Name Variations",
                        test_key="vendor_name_variations",
                        test_tier=TestTier.ADVANCED,
                        severity=severity,
                        issue=f"Similar vendor names: '{name_a}' vs '{name_b}' (similarity: {ratio:.0%})",
                        confidence=round(ratio, 2),
                        details={
                            "name_a": name_a,
                            "name_b": name_b,
                            "similarity": round(ratio, 2),
                            "combined_amount": round(combined_amount, 2),
                        },
                    ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Vendor Name Variations",
        test_key="vendor_name_variations",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags similar vendor names that may indicate ghost vendors or deliberate misspellings.",
        flagged_entries=flagged,
    )


def test_just_below_threshold(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T12: Just-Below-Threshold Payments.

    Flags payments within 5% below common approval thresholds.
    Also detects same-vendor same-day splits that aggregate above a threshold.
    """
    if not config.threshold_proximity_enabled:
        return APTestResult(
            test_name="Just-Below-Threshold",
            test_key="just_below_threshold",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged_rows: set[int] = set()
    flagged: list[FlaggedPayment] = []

    # Check proximity to thresholds
    for p in payments:
        amt = abs(p.amount)
        for threshold in config.approval_thresholds:
            lower_bound = threshold * (1 - config.threshold_proximity_pct)
            if lower_bound <= amt < threshold:
                severity = Severity.MEDIUM if threshold < 50000 else Severity.HIGH
                if p.row_number not in flagged_rows:
                    flagged_rows.add(p.row_number)
                    flagged.append(FlaggedPayment(
                        entry=p,
                        test_name="Just-Below-Threshold",
                        test_key="just_below_threshold",
                        test_tier=TestTier.ADVANCED,
                        severity=severity,
                        issue=f"${amt:,.2f} is {((threshold - amt) / threshold):.1%} below ${threshold:,.0f} threshold",
                        confidence=0.75,
                        details={
                            "amount": round(amt, 2),
                            "threshold": threshold,
                            "pct_below": round((threshold - amt) / threshold, 4),
                        },
                    ))
                break  # Only flag the closest threshold

    # Detect same-vendor same-day splits that aggregate above a threshold
    vendor_date_groups: dict[tuple[str, str], list[APPayment]] = {}
    for p in payments:
        vendor = p.vendor_name.lower().strip()
        pay_date = (p.payment_date or "").strip()
        if vendor and pay_date:
            vendor_date_groups.setdefault((vendor, pay_date), []).append(p)

    for (vendor, pay_date), group in vendor_date_groups.items():
        if len(group) < 2:
            continue
        total = sum(abs(p.amount) for p in group)
        for threshold in config.approval_thresholds:
            if total > threshold and all(abs(p.amount) < threshold for p in group):
                for p in group:
                    if p.row_number not in flagged_rows:
                        flagged_rows.add(p.row_number)
                        flagged.append(FlaggedPayment(
                            entry=p,
                            test_name="Just-Below-Threshold",
                            test_key="just_below_threshold",
                            test_tier=TestTier.ADVANCED,
                            severity=Severity.HIGH,
                            issue=f"Split payment: {len(group)} payments to {p.vendor_name} on {pay_date} totaling ${total:,.2f} (above ${threshold:,.0f})",
                            confidence=0.85,
                            details={
                                "split_count": len(group),
                                "split_total": round(total, 2),
                                "threshold": threshold,
                                "vendor": vendor,
                                "date": pay_date,
                            },
                        ))
                break  # Only flag the first threshold exceeded

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Just-Below-Threshold",
        test_key="just_below_threshold",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags payments just below approval thresholds and same-vendor same-day splits exceeding thresholds.",
        flagged_entries=flagged,
    )


def test_suspicious_descriptions(
    payments: list[APPayment],
    config: APTestingConfig,
) -> APTestResult:
    """AP-T13: Suspicious Payment Descriptions.

    Scans payment descriptions for AP-specific fraud indicator keywords.
    Uses weighted keyword matching with phrase support.
    """
    if not config.suspicious_keyword_enabled:
        return APTestResult(
            test_name="Suspicious Descriptions",
            test_key="suspicious_descriptions",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(payments),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedPayment] = []

    for p in payments:
        desc = (p.description or "").lower().strip()
        if not desc:
            continue

        best_weight = 0.0
        matched_keywords: list[str] = []

        for keyword, weight, is_phrase in AP_SUSPICIOUS_KEYWORDS:
            if is_phrase:
                if keyword in desc:
                    if weight > best_weight:
                        best_weight = weight
                    matched_keywords.append(keyword)
            else:
                if re.search(r'\b' + re.escape(keyword) + r'\b', desc):
                    if weight > best_weight:
                        best_weight = weight
                    matched_keywords.append(keyword)

        if best_weight < config.suspicious_keyword_threshold:
            continue

        if best_weight >= 0.85 and abs(p.amount) > 10000:
            severity = Severity.HIGH
        elif best_weight >= 0.75:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        flagged.append(FlaggedPayment(
            entry=p,
            test_name="Suspicious Descriptions",
            test_key="suspicious_descriptions",
            test_tier=TestTier.ADVANCED,
            severity=severity,
            issue=f"Suspicious keywords: {', '.join(matched_keywords)} (confidence: {best_weight:.0%})",
            confidence=round(best_weight, 2),
            details={
                "matched_keywords": matched_keywords,
                "max_weight": round(best_weight, 2),
                "description": p.description,
            },
        ))

    flag_rate = len(flagged) / max(len(payments), 1)
    return APTestResult(
        test_name="Suspicious Descriptions",
        test_key="suspicious_descriptions",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(payments),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags payments with descriptions containing fraud indicator keywords.",
        flagged_entries=flagged,
    )


# =============================================================================
# TEST BATTERY + SCORING
# =============================================================================

def run_ap_test_battery(
    payments: list[APPayment],
    config: Optional[APTestingConfig] = None,
) -> list[APTestResult]:
    """Run all 13 AP tests (Tier 1-3) on the payments.

    Returns list of APTestResult.
    """
    if config is None:
        config = APTestingConfig()

    return [
        # Tier 1 — Structural
        test_exact_duplicate_payments(payments, config),
        test_missing_critical_fields(payments, config),
        test_check_number_gaps(payments, config),
        test_round_dollar_amounts(payments, config),
        test_payment_before_invoice(payments, config),
        # Tier 2 — Statistical
        test_fuzzy_duplicate_payments(payments, config),
        test_invoice_number_reuse(payments, config),
        test_unusual_payment_amounts(payments, config),
        test_weekend_payments(payments, config),
        test_high_frequency_vendors(payments, config),
        # Tier 3 — Fraud Indicators
        test_vendor_name_variations(payments, config),
        test_just_below_threshold(payments, config),
        test_suspicious_descriptions(payments, config),
    ]


def calculate_ap_composite_score(
    test_results: list[APTestResult],
    total_entries: int,
) -> APCompositeScore:
    """Calculate the composite risk score from AP test results.

    Score = weighted sum of (flag_rate x severity_weight) normalized to 0-100.
    Entries flagged by 3+ tests get a 1.25x multiplier.
    """
    if total_entries == 0:
        return APCompositeScore(
            score=0.0,
            risk_tier=RiskTier.LOW,
            tests_run=len(test_results),
            total_entries=0,
            total_flagged=0,
            flag_rate=0.0,
        )

    # Collect all flagged payment row numbers with their test counts
    entry_test_counts: dict[int, int] = {}
    all_flagged_rows: set[int] = set()
    flags_by_severity: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for tr in test_results:
        for fp in tr.flagged_entries:
            row = fp.entry.row_number
            entry_test_counts[row] = entry_test_counts.get(row, 0) + 1
            all_flagged_rows.add(row)
            flags_by_severity[fp.severity.value] = flags_by_severity.get(fp.severity.value, 0) + 1

    # Base score from flag rates weighted by severity
    weighted_sum = 0.0
    for tr in test_results:
        weight = SEVERITY_WEIGHTS.get(tr.severity, 1.0)
        weighted_sum += tr.flag_rate * weight

    # Normalize
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
                f"{tr.test_name}: {tr.entries_flagged} payments flagged ({tr.flag_rate:.1%})"
            )

    total_flagged = len(all_flagged_rows)
    flag_rate = total_flagged / max(total_entries, 1)

    return APCompositeScore(
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

def run_ap_testing(
    rows: list[dict],
    column_names: list[str],
    config: Optional[APTestingConfig] = None,
    column_mapping: Optional[dict] = None,
) -> APTestingResult:
    """Run the complete AP testing pipeline.

    Args:
        rows: List of dicts (raw AP data rows)
        column_names: List of column header names
        config: Optional testing configuration
        column_mapping: Optional manual column mapping override

    Returns:
        APTestingResult with composite score, test results, data quality, etc.
    """
    if config is None:
        config = APTestingConfig()

    # 1. Detect columns
    detection = detect_ap_columns(column_names)

    # Apply manual overrides if provided
    if column_mapping:
        if "vendor_name_column" in column_mapping:
            detection.vendor_name_column = column_mapping["vendor_name_column"]
        if "amount_column" in column_mapping:
            detection.amount_column = column_mapping["amount_column"]
        if "payment_date_column" in column_mapping:
            detection.payment_date_column = column_mapping["payment_date_column"]
        if "invoice_number_column" in column_mapping:
            detection.invoice_number_column = column_mapping["invoice_number_column"]
        if "invoice_date_column" in column_mapping:
            detection.invoice_date_column = column_mapping["invoice_date_column"]
            if detection.payment_date_column:
                detection.has_dual_dates = True
        if "vendor_id_column" in column_mapping:
            detection.vendor_id_column = column_mapping["vendor_id_column"]
        if "check_number_column" in column_mapping:
            detection.check_number_column = column_mapping["check_number_column"]
            detection.has_check_numbers = True
        if "description_column" in column_mapping:
            detection.description_column = column_mapping["description_column"]
        if "gl_account_column" in column_mapping:
            detection.gl_account_column = column_mapping["gl_account_column"]
        if "payment_method_column" in column_mapping:
            detection.payment_method_column = column_mapping["payment_method_column"]
        # Recalculate overall confidence with overrides
        detection.overall_confidence = 1.0

    # 2. Parse payments
    payments = parse_ap_payments(rows, detection)

    # 3. Assess data quality
    data_quality = assess_ap_data_quality(payments, detection)

    # 4. Run test battery
    test_results = run_ap_test_battery(payments, config)

    # 5. Calculate composite score
    composite = calculate_ap_composite_score(test_results, len(payments))

    return APTestingResult(
        composite_score=composite,
        test_results=test_results,
        data_quality=data_quality,
        column_detection=detection,
    )
