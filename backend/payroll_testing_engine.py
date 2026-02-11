"""
Payroll & Employee Testing Engine - Sprint 85-86

Provides automated payroll register testing for employee payment data.
Parses payroll files (CSV/Excel), detects columns, runs structural tests,
statistical analysis, and fraud indicator detection (ghost employees).

Sprint 85: Payroll column detection, data model, data quality,
  Tier 1 structural tests (PR-T1 to PR-T5)
Sprint 86: Tier 2 statistical tests (PR-T6 to PR-T8),
  Tier 3 fraud indicators (PR-T9 to PR-T11), API endpoint

ZERO-STORAGE COMPLIANCE:
- All payroll files processed in-memory only
- Test results are ephemeral (computed on demand)
- No raw payroll data is stored

Audit Standards References:
- ISA 240: Auditor's Responsibilities Relating to Fraud
- ISA 500: Audit Evidence
- PCAOB AS 2401: Consideration of Fraud (ghost employee indicators)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime, date, timedelta
from difflib import SequenceMatcher
from collections import Counter
import re
import math
import statistics


# =============================================================================
# ENUMS (imported from shared — Sprint 90)
# =============================================================================

from shared.testing_enums import RiskTier, TestTier, Severity, SEVERITY_WEIGHTS  # noqa: E402
from shared.parsing_helpers import safe_float, safe_str, parse_date


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class PayrollTestingConfig:
    """Configurable thresholds for all payroll tests."""
    # PR-T1: Duplicate Employee IDs
    duplicate_name_similarity: float = 0.85

    # PR-T3: Round Salary Amounts
    round_amount_threshold: float = 10000.0
    round_amount_max_flags: int = 50

    # PR-T4: Pay After Termination
    pay_after_term_enabled: bool = True

    # PR-T5: Check Number Gaps
    check_number_gap_enabled: bool = True
    check_number_gap_min_size: int = 2

    # PR-T6: Unusual Pay Amounts
    unusual_pay_stddev: float = 3.0
    unusual_pay_min_entries: int = 5

    # PR-T7: Pay Frequency Anomalies
    frequency_enabled: bool = True
    frequency_deviation_threshold: float = 0.5  # fraction of expected cadence

    # PR-T8: Benford's Law on Gross Pay
    enable_benford: bool = True
    benford_min_entries: int = 500
    benford_min_magnitude_range: float = 2.0  # orders of magnitude

    # PR-T9: Ghost Employee Indicators
    enable_ghost: bool = True
    ghost_min_indicators: int = 1

    # PR-T10: Duplicate Bank Accounts / Addresses
    enable_duplicates: bool = True
    address_similarity_threshold: float = 0.90

    # PR-T11: Duplicate Tax IDs
    enable_tax_id_duplicates: bool = True


# =============================================================================
# PAYROLL COLUMN DETECTION
# =============================================================================

class PayrollColumnType(str, Enum):
    """Types of columns in a payroll register file."""
    EMPLOYEE_ID = "employee_id"
    EMPLOYEE_NAME = "employee_name"
    DEPARTMENT = "department"
    PAY_DATE = "pay_date"
    GROSS_PAY = "gross_pay"
    NET_PAY = "net_pay"
    DEDUCTIONS = "deductions"
    CHECK_NUMBER = "check_number"
    PAY_TYPE = "pay_type"
    HOURS = "hours"
    RATE = "rate"
    TERM_DATE = "term_date"
    BANK_ACCOUNT = "bank_account"
    ADDRESS = "address"
    TAX_ID = "tax_id"
    UNKNOWN = "unknown"


# Weighted regex patterns for payroll column detection
PAYROLL_EMPLOYEE_ID_PATTERNS = [
    (r"^employee\s*id$", 1.0, True),
    (r"^emp\s*id$", 0.95, True),
    (r"^employee\s*number$", 0.95, True),
    (r"^emp\s*no$", 0.90, True),
    (r"^emp\s*number$", 0.90, True),
    (r"^employee\s*#$", 0.90, True),
    (r"^emp\s*code$", 0.85, True),
    (r"^staff\s*id$", 0.85, True),
    (r"^personnel\s*number$", 0.80, True),
    (r"employee.?id", 0.65, False),
    (r"emp.?id", 0.60, False),
]

PAYROLL_EMPLOYEE_NAME_PATTERNS = [
    (r"^employee\s*name$", 1.0, True),
    (r"^emp\s*name$", 0.95, True),
    (r"^name$", 0.85, True),
    (r"^employee$", 0.80, True),
    (r"^full\s*name$", 0.90, True),
    (r"^payee\s*name$", 0.85, True),
    (r"^payee$", 0.80, True),
    (r"^worker\s*name$", 0.85, True),
    (r"employee.?name", 0.65, False),
]

PAYROLL_DEPARTMENT_PATTERNS = [
    (r"^department$", 1.0, True),
    (r"^dept$", 0.95, True),
    (r"^department\s*name$", 0.95, True),
    (r"^dept\s*name$", 0.90, True),
    (r"^division$", 0.80, True),
    (r"^cost\s*center$", 0.75, True),
    (r"^business\s*unit$", 0.75, True),
    (r"department", 0.60, False),
]

PAYROLL_PAY_DATE_PATTERNS = [
    (r"^pay\s*date$", 1.0, True),
    (r"^payment\s*date$", 0.95, True),
    (r"^check\s*date$", 0.90, True),
    (r"^payroll\s*date$", 0.90, True),
    (r"^period\s*end\s*date$", 0.85, True),
    (r"^pay\s*period\s*end$", 0.85, True),
    (r"^date$", 0.55, True),
    (r"pay.?date", 0.70, False),
]

PAYROLL_GROSS_PAY_PATTERNS = [
    (r"^gross\s*pay$", 1.0, True),
    (r"^gross\s*amount$", 0.95, True),
    (r"^gross\s*earnings$", 0.95, True),
    (r"^gross$", 0.85, True),
    (r"^total\s*earnings$", 0.90, True),
    (r"^total\s*pay$", 0.85, True),
    (r"^salary$", 0.80, True),
    (r"^amount$", 0.55, True),
    (r"gross.?pay", 0.70, False),
    (r"gross.?earn", 0.65, False),
]

PAYROLL_NET_PAY_PATTERNS = [
    (r"^net\s*pay$", 1.0, True),
    (r"^net\s*amount$", 0.95, True),
    (r"^net\s*earnings$", 0.95, True),
    (r"^net$", 0.80, True),
    (r"^take\s*home$", 0.85, True),
    (r"net.?pay", 0.70, False),
]

PAYROLL_DEDUCTIONS_PATTERNS = [
    (r"^deductions$", 1.0, True),
    (r"^total\s*deductions$", 0.95, True),
    (r"^withholding$", 0.80, True),
    (r"^deduction\s*amount$", 0.90, True),
    (r"deduction", 0.60, False),
]

PAYROLL_CHECK_NUMBER_PATTERNS = [
    (r"^check\s*number$", 1.0, True),
    (r"^check\s*no$", 0.98, True),
    (r"^check\s*#$", 0.95, True),
    (r"^cheque\s*number$", 0.95, True),
    (r"^chk\s*no$", 0.90, True),
    (r"^payment\s*number$", 0.80, True),
    (r"check.?n", 0.65, False),
]

PAYROLL_PAY_TYPE_PATTERNS = [
    (r"^pay\s*type$", 1.0, True),
    (r"^earnings\s*type$", 0.95, True),
    (r"^pay\s*code$", 0.90, True),
    (r"^earning\s*code$", 0.90, True),
    (r"^type$", 0.55, True),
    (r"pay.?type", 0.65, False),
]

PAYROLL_HOURS_PATTERNS = [
    (r"^hours$", 1.0, True),
    (r"^hours\s*worked$", 0.95, True),
    (r"^total\s*hours$", 0.90, True),
    (r"^regular\s*hours$", 0.85, True),
    (r"hours", 0.60, False),
]

PAYROLL_RATE_PATTERNS = [
    (r"^rate$", 0.90, True),
    (r"^pay\s*rate$", 1.0, True),
    (r"^hourly\s*rate$", 0.95, True),
    (r"^salary\s*rate$", 0.90, True),
    (r"rate", 0.55, False),
]

PAYROLL_TERM_DATE_PATTERNS = [
    (r"^termination\s*date$", 1.0, True),
    (r"^term\s*date$", 0.95, True),
    (r"^separation\s*date$", 0.90, True),
    (r"^end\s*date$", 0.80, True),
    (r"^last\s*day$", 0.80, True),
    (r"termination", 0.65, False),
    (r"term.?date", 0.60, False),
]

PAYROLL_BANK_ACCOUNT_PATTERNS = [
    (r"^bank\s*account$", 1.0, True),
    (r"^account\s*number$", 0.85, True),
    (r"^bank\s*acct$", 0.95, True),
    (r"^direct\s*deposit\s*account$", 0.90, True),
    (r"^routing.?account$", 0.80, True),
    (r"bank.?account", 0.70, False),
]

PAYROLL_ADDRESS_PATTERNS = [
    (r"^address$", 1.0, True),
    (r"^mailing\s*address$", 0.95, True),
    (r"^home\s*address$", 0.95, True),
    (r"^street\s*address$", 0.90, True),
    (r"^employee\s*address$", 0.90, True),
    (r"address", 0.60, False),
]

PAYROLL_TAX_ID_PATTERNS = [
    (r"^ssn$", 1.0, True),
    (r"^tax\s*id$", 1.0, True),
    (r"^social\s*security$", 0.95, True),
    (r"^tin$", 0.90, True),
    (r"^tax\s*identification$", 0.90, True),
    (r"^employee\s*ssn$", 0.95, True),
    (r"ssn", 0.70, False),
    (r"tax.?id", 0.65, False),
]

# Map of payroll column type to its patterns
PAYROLL_COLUMN_PATTERNS: dict[PayrollColumnType, list] = {
    PayrollColumnType.EMPLOYEE_ID: PAYROLL_EMPLOYEE_ID_PATTERNS,
    PayrollColumnType.EMPLOYEE_NAME: PAYROLL_EMPLOYEE_NAME_PATTERNS,
    PayrollColumnType.DEPARTMENT: PAYROLL_DEPARTMENT_PATTERNS,
    PayrollColumnType.PAY_DATE: PAYROLL_PAY_DATE_PATTERNS,
    PayrollColumnType.GROSS_PAY: PAYROLL_GROSS_PAY_PATTERNS,
    PayrollColumnType.NET_PAY: PAYROLL_NET_PAY_PATTERNS,
    PayrollColumnType.DEDUCTIONS: PAYROLL_DEDUCTIONS_PATTERNS,
    PayrollColumnType.CHECK_NUMBER: PAYROLL_CHECK_NUMBER_PATTERNS,
    PayrollColumnType.PAY_TYPE: PAYROLL_PAY_TYPE_PATTERNS,
    PayrollColumnType.HOURS: PAYROLL_HOURS_PATTERNS,
    PayrollColumnType.RATE: PAYROLL_RATE_PATTERNS,
    PayrollColumnType.TERM_DATE: PAYROLL_TERM_DATE_PATTERNS,
    PayrollColumnType.BANK_ACCOUNT: PAYROLL_BANK_ACCOUNT_PATTERNS,
    PayrollColumnType.ADDRESS: PAYROLL_ADDRESS_PATTERNS,
    PayrollColumnType.TAX_ID: PAYROLL_TAX_ID_PATTERNS,
}


def _match_payroll_column(column_name: str, patterns: list[tuple]) -> float:
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
# PAYROLL COLUMN DETECTION RESULT
# =============================================================================

@dataclass
class PayrollColumnDetectionResult:
    """Result of payroll column detection."""
    # Required columns
    employee_name_column: Optional[str] = None
    gross_pay_column: Optional[str] = None
    pay_date_column: Optional[str] = None

    # Optional columns
    employee_id_column: Optional[str] = None
    department_column: Optional[str] = None
    net_pay_column: Optional[str] = None
    deductions_column: Optional[str] = None
    check_number_column: Optional[str] = None
    pay_type_column: Optional[str] = None
    hours_column: Optional[str] = None
    rate_column: Optional[str] = None
    term_date_column: Optional[str] = None
    bank_account_column: Optional[str] = None
    address_column: Optional[str] = None
    tax_id_column: Optional[str] = None

    # Metadata
    has_check_numbers: bool = False
    has_term_dates: bool = False
    has_bank_accounts: bool = False
    has_addresses: bool = False
    has_tax_ids: bool = False
    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "employee_name_column": self.employee_name_column,
            "gross_pay_column": self.gross_pay_column,
            "pay_date_column": self.pay_date_column,
            "employee_id_column": self.employee_id_column,
            "department_column": self.department_column,
            "net_pay_column": self.net_pay_column,
            "deductions_column": self.deductions_column,
            "check_number_column": self.check_number_column,
            "pay_type_column": self.pay_type_column,
            "hours_column": self.hours_column,
            "rate_column": self.rate_column,
            "term_date_column": self.term_date_column,
            "bank_account_column": self.bank_account_column,
            "address_column": self.address_column,
            "tax_id_column": self.tax_id_column,
            "has_check_numbers": self.has_check_numbers,
            "has_term_dates": self.has_term_dates,
            "has_bank_accounts": self.has_bank_accounts,
            "has_addresses": self.has_addresses,
            "has_tax_ids": self.has_tax_ids,
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


def detect_payroll_columns(column_names: list[str]) -> PayrollColumnDetectionResult:
    """Detect payroll columns using weighted pattern matching with greedy assignment."""
    columns = [col.strip() for col in column_names]
    notes: list[str] = []
    result = PayrollColumnDetectionResult(all_columns=columns)

    assigned_columns: set[str] = set()

    # Score all columns for all types
    scored: dict[str, dict[PayrollColumnType, float]] = {}
    for col in columns:
        scored[col] = {}
        for col_type, patterns in PAYROLL_COLUMN_PATTERNS.items():
            score = _match_payroll_column(col, patterns)
            if score > 0:
                scored[col][col_type] = score

    # Greedy assignment: highest confidence first
    assignments: list[tuple[float, str, PayrollColumnType]] = []
    for col, type_scores in scored.items():
        for col_type, score in type_scores.items():
            assignments.append((score, col, col_type))
    assignments.sort(reverse=True)

    assigned_types: set[PayrollColumnType] = set()
    for score, col, col_type in assignments:
        if col in assigned_columns or col_type in assigned_types:
            continue
        assigned_columns.add(col)
        assigned_types.add(col_type)

        # Assign to result
        field_map = {
            PayrollColumnType.EMPLOYEE_ID: "employee_id_column",
            PayrollColumnType.EMPLOYEE_NAME: "employee_name_column",
            PayrollColumnType.DEPARTMENT: "department_column",
            PayrollColumnType.PAY_DATE: "pay_date_column",
            PayrollColumnType.GROSS_PAY: "gross_pay_column",
            PayrollColumnType.NET_PAY: "net_pay_column",
            PayrollColumnType.DEDUCTIONS: "deductions_column",
            PayrollColumnType.CHECK_NUMBER: "check_number_column",
            PayrollColumnType.PAY_TYPE: "pay_type_column",
            PayrollColumnType.HOURS: "hours_column",
            PayrollColumnType.RATE: "rate_column",
            PayrollColumnType.TERM_DATE: "term_date_column",
            PayrollColumnType.BANK_ACCOUNT: "bank_account_column",
            PayrollColumnType.ADDRESS: "address_column",
            PayrollColumnType.TAX_ID: "tax_id_column",
        }
        field_name = field_map.get(col_type)
        if field_name:
            setattr(result, field_name, col)

    # Set boolean flags
    result.has_check_numbers = result.check_number_column is not None
    result.has_term_dates = result.term_date_column is not None
    result.has_bank_accounts = result.bank_account_column is not None
    result.has_addresses = result.address_column is not None
    result.has_tax_ids = result.tax_id_column is not None

    # Calculate confidence
    required_found = sum(1 for c in [
        result.employee_name_column, result.gross_pay_column, result.pay_date_column,
    ] if c is not None)
    result.overall_confidence = required_found / 3.0

    if not result.employee_name_column and not result.employee_id_column:
        notes.append("No employee identifier column detected")
    if not result.gross_pay_column:
        notes.append("No gross pay / amount column detected")
    if not result.pay_date_column:
        notes.append("No pay date column detected")

    result.detection_notes = notes
    return result


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class PayrollEntry:
    """A single payroll entry."""
    employee_id: str = ""
    employee_name: str = ""
    department: str = ""
    pay_date: Optional[date] = None
    gross_pay: float = 0.0
    net_pay: float = 0.0
    deductions: float = 0.0
    check_number: str = ""
    pay_type: str = ""
    hours: float = 0.0
    rate: float = 0.0
    term_date: Optional[date] = None
    bank_account: str = ""
    address: str = ""
    tax_id: str = ""
    _row_index: int = 0

    def to_dict(self) -> dict:
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "department": self.department,
            "pay_date": self.pay_date.isoformat() if self.pay_date else None,
            "gross_pay": self.gross_pay,
            "net_pay": self.net_pay,
            "deductions": self.deductions,
            "check_number": self.check_number,
            "pay_type": self.pay_type,
            "hours": self.hours,
            "rate": self.rate,
            "term_date": self.term_date.isoformat() if self.term_date else None,
            "bank_account": self.bank_account,
            "address": self.address,
            "tax_id": self.tax_id,
            "row_index": self._row_index,
        }


@dataclass
class FlaggedEmployee:
    """A payroll entry flagged by a test."""
    entry: PayrollEntry
    test_name: str = ""
    test_key: str = ""
    test_tier: str = ""
    severity: str = "medium"
    issue: str = ""
    confidence: float = 0.0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "entry": self.entry.to_dict(),
            "test_name": self.test_name,
            "test_key": self.test_key,
            "test_tier": self.test_tier,
            "severity": self.severity,
            "issue": self.issue,
            "confidence": round(self.confidence, 2),
            "details": self.details,
        }


@dataclass
class PayrollTestResult:
    """Result of a single payroll test."""
    test_name: str
    test_key: str
    test_tier: str
    entries_flagged: int = 0
    total_entries: int = 0
    flag_rate: float = 0.0
    severity: str = "medium"
    description: str = ""
    flagged_entries: list[FlaggedEmployee] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "test_key": self.test_key,
            "test_tier": self.test_tier,
            "entries_flagged": self.entries_flagged,
            "total_entries": self.total_entries,
            "flag_rate": round(self.flag_rate, 4),
            "severity": self.severity,
            "description": self.description,
            "flagged_entries": [f.to_dict() for f in self.flagged_entries],
        }


@dataclass
class PayrollDataQuality:
    """Data quality assessment for payroll data."""
    completeness_score: float = 0.0
    field_fill_rates: dict[str, float] = field(default_factory=dict)
    detected_issues: list[str] = field(default_factory=list)
    total_rows: int = 0

    def to_dict(self) -> dict:
        return {
            "completeness_score": round(self.completeness_score, 2),
            "field_fill_rates": {k: round(v, 2) for k, v in self.field_fill_rates.items()},
            "detected_issues": self.detected_issues,
            "total_rows": self.total_rows,
        }


@dataclass
class PayrollCompositeScore:
    """Composite risk score for payroll testing."""
    score: float = 0.0
    risk_tier: str = "low"
    tests_run: int = 0
    total_entries: int = 0
    total_flagged: int = 0
    flag_rate: float = 0.0
    flags_by_severity: dict[str, int] = field(default_factory=dict)
    top_findings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "risk_tier": self.risk_tier,
            "tests_run": self.tests_run,
            "total_entries": self.total_entries,
            "total_flagged": self.total_flagged,
            "flag_rate": round(self.flag_rate, 4),
            "flags_by_severity": self.flags_by_severity,
            "top_findings": self.top_findings,
        }


@dataclass
class PayrollTestingResult:
    """Complete payroll testing result."""
    composite_score: PayrollCompositeScore
    test_results: list[PayrollTestResult]
    data_quality: PayrollDataQuality
    column_detection: PayrollColumnDetectionResult
    filename: str = ""

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [r.to_dict() for r in self.test_results],
            "data_quality": self.data_quality.to_dict(),
            "column_detection": self.column_detection.to_dict(),
            "filename": self.filename,
        }




# =============================================================================
# PAYROLL FILE PARSER
# =============================================================================

def parse_payroll_entries(
    rows: list[dict],
    detection: PayrollColumnDetectionResult,
) -> list[PayrollEntry]:
    """Parse raw rows into PayrollEntry objects using detected column mapping."""
    entries: list[PayrollEntry] = []

    for idx, row in enumerate(rows):
        entry = PayrollEntry(_row_index=idx + 1)

        if detection.employee_id_column:
            entry.employee_id = safe_str(row.get(detection.employee_id_column, "")) or ""
        if detection.employee_name_column:
            entry.employee_name = safe_str(row.get(detection.employee_name_column, "")) or ""
        if detection.department_column:
            entry.department = safe_str(row.get(detection.department_column, "")) or ""
        if detection.pay_date_column:
            entry.pay_date = parse_date(row.get(detection.pay_date_column))
        if detection.gross_pay_column:
            entry.gross_pay = safe_float(row.get(detection.gross_pay_column))
        if detection.net_pay_column:
            entry.net_pay = safe_float(row.get(detection.net_pay_column))
        if detection.deductions_column:
            entry.deductions = safe_float(row.get(detection.deductions_column))
        if detection.check_number_column:
            entry.check_number = safe_str(row.get(detection.check_number_column, "")) or ""
        if detection.pay_type_column:
            entry.pay_type = safe_str(row.get(detection.pay_type_column, "")) or ""
        if detection.hours_column:
            entry.hours = safe_float(row.get(detection.hours_column))
        if detection.rate_column:
            entry.rate = safe_float(row.get(detection.rate_column))
        if detection.term_date_column:
            entry.term_date = parse_date(row.get(detection.term_date_column))
        if detection.bank_account_column:
            entry.bank_account = safe_str(row.get(detection.bank_account_column, "")) or ""
        if detection.address_column:
            entry.address = safe_str(row.get(detection.address_column, "")) or ""
        if detection.tax_id_column:
            entry.tax_id = safe_str(row.get(detection.tax_id_column, "")) or ""

        entries.append(entry)

    return entries


# =============================================================================
# DATA QUALITY ASSESSMENT
# =============================================================================

def assess_payroll_data_quality(
    entries: list[PayrollEntry],
    detection: PayrollColumnDetectionResult,
) -> PayrollDataQuality:
    """Assess data quality of parsed payroll entries."""
    if not entries:
        return PayrollDataQuality(total_rows=0, completeness_score=0.0)

    total = len(entries)
    issues: list[str] = []
    fill_rates: dict[str, float] = {}

    # Required fields
    name_filled = sum(1 for e in entries if e.employee_name) / total
    fill_rates["employee_name"] = name_filled
    if name_filled < 0.90:
        issues.append(f"Employee name fill rate low: {name_filled:.0%}")

    pay_filled = sum(1 for e in entries if e.gross_pay != 0) / total
    fill_rates["gross_pay"] = pay_filled
    if pay_filled < 0.90:
        issues.append(f"Gross pay fill rate low: {pay_filled:.0%}")

    date_filled = sum(1 for e in entries if e.pay_date is not None) / total
    fill_rates["pay_date"] = date_filled
    if date_filled < 0.90:
        issues.append(f"Pay date fill rate low: {date_filled:.0%}")

    # Optional fields
    if detection.employee_id_column:
        id_filled = sum(1 for e in entries if e.employee_id) / total
        fill_rates["employee_id"] = id_filled

    if detection.department_column:
        dept_filled = sum(1 for e in entries if e.department) / total
        fill_rates["department"] = dept_filled

    if detection.check_number_column:
        check_filled = sum(1 for e in entries if e.check_number) / total
        fill_rates["check_number"] = check_filled

    # Weighted completeness
    completeness = (name_filled * 0.30 + pay_filled * 0.30 + date_filled * 0.25)
    optional_weight = 0.15
    optional_scores = [v for k, v in fill_rates.items() if k not in ("employee_name", "gross_pay", "pay_date")]
    if optional_scores:
        completeness += (sum(optional_scores) / len(optional_scores)) * optional_weight
    else:
        completeness += optional_weight  # If no optional fields, give full credit

    # Zero-pay entries
    zero_pay = sum(1 for e in entries if e.gross_pay == 0)
    if zero_pay > 0:
        issues.append(f"{zero_pay} entries with zero gross pay")

    return PayrollDataQuality(
        completeness_score=min(completeness, 1.0),
        field_fill_rates=fill_rates,
        detected_issues=issues,
        total_rows=total,
    )


# =============================================================================
# TIER 1 TESTS — STRUCTURAL
# =============================================================================

def _test_duplicate_employee_ids(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T1: Duplicate Employee IDs — flag exact ID duplicates with different names."""
    flagged: list[FlaggedEmployee] = []

    # Group by employee_id
    id_groups: dict[str, list[PayrollEntry]] = {}
    for entry in entries:
        eid = entry.employee_id.strip().lower()
        if eid:
            id_groups.setdefault(eid, []).append(entry)

    for eid, group in id_groups.items():
        # Get unique names for this ID
        names = set()
        for e in group:
            name = e.employee_name.strip().lower()
            if name:
                names.add(name)

        if len(names) > 1:
            # Multiple different names for same ID — flag all entries
            for entry in group:
                flagged.append(FlaggedEmployee(
                    entry=entry,
                    test_name="Duplicate Employee IDs",
                    test_key="PR-T1",
                    test_tier=TestTier.STRUCTURAL.value,
                    severity=Severity.HIGH.value,
                    issue=f"Employee ID '{entry.employee_id}' has {len(names)} different names",
                    confidence=0.95,
                    details={"names": sorted(names), "entry_count": len(group)},
                ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Duplicate Employee IDs",
        test_key="PR-T1",
        test_tier=TestTier.STRUCTURAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.HIGH.value,
        description="Flag employee IDs associated with multiple different names",
        flagged_entries=flagged,
    )


def _test_missing_critical_fields(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T2: Missing Critical Fields — flag blank name, zero pay, blank date."""
    flagged: list[FlaggedEmployee] = []

    for entry in entries:
        issues: list[str] = []
        severity = Severity.MEDIUM

        if not entry.employee_name.strip():
            issues.append("Employee name is blank")
            severity = Severity.HIGH

        if entry.gross_pay == 0:
            issues.append("Gross pay is zero")
            severity = Severity.HIGH

        if entry.pay_date is None:
            issues.append("Pay date is blank")

        if issues:
            flagged.append(FlaggedEmployee(
                entry=entry,
                test_name="Missing Critical Fields",
                test_key="PR-T2",
                test_tier=TestTier.STRUCTURAL.value,
                severity=severity.value,
                issue="; ".join(issues),
                confidence=0.90,
                details={"missing_fields": issues},
            ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Missing Critical Fields",
        test_key="PR-T2",
        test_tier=TestTier.STRUCTURAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.HIGH.value,
        description="Flag entries with blank name, zero gross pay, or missing pay date",
        flagged_entries=flagged,
    )


def _test_round_salary_amounts(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T3: Round Salary Amounts — $100K/$50K/$25K/$10K patterns."""
    flagged: list[FlaggedEmployee] = []

    # Sort by amount descending for consistent flagging
    sorted_entries = sorted(entries, key=lambda e: abs(e.gross_pay), reverse=True)

    for entry in sorted_entries:
        if len(flagged) >= config.round_amount_max_flags:
            break

        amount = abs(entry.gross_pay)
        if amount < config.round_amount_threshold:
            continue

        if amount >= 100000 and amount % 100000 == 0:
            severity = Severity.HIGH
            issue = f"Round amount: ${amount:,.0f} (multiple of $100K)"
        elif amount >= 50000 and amount % 50000 == 0:
            severity = Severity.HIGH
            issue = f"Round amount: ${amount:,.0f} (multiple of $50K)"
        elif amount >= 25000 and amount % 25000 == 0:
            severity = Severity.MEDIUM
            issue = f"Round amount: ${amount:,.0f} (multiple of $25K)"
        elif amount >= 10000 and amount % 10000 == 0:
            severity = Severity.LOW
            issue = f"Round amount: ${amount:,.0f} (multiple of $10K)"
        else:
            continue

        flagged.append(FlaggedEmployee(
            entry=entry,
            test_name="Round Salary Amounts",
            test_key="PR-T3",
            test_tier=TestTier.STRUCTURAL.value,
            severity=severity.value,
            issue=issue,
            confidence=0.70,
            details={"amount": amount},
        ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Round Salary Amounts",
        test_key="PR-T3",
        test_tier=TestTier.STRUCTURAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.MEDIUM.value,
        description="Flag round-dollar pay amounts ($100K, $50K, $25K, $10K multiples)",
        flagged_entries=flagged,
    )


def _test_pay_after_termination(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T4: Pay After Termination Date — payments after term_date."""
    flagged: list[FlaggedEmployee] = []

    if not config.pay_after_term_enabled:
        return PayrollTestResult(
            test_name="Pay After Termination",
            test_key="PR-T4",
            test_tier=TestTier.STRUCTURAL.value,
            total_entries=len(entries),
            description="Disabled by configuration",
        )

    for entry in entries:
        if entry.term_date is None or entry.pay_date is None:
            continue

        if entry.pay_date > entry.term_date:
            days_after = (entry.pay_date - entry.term_date).days

            if days_after > 30:
                severity = Severity.HIGH
            elif days_after > 7:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedEmployee(
                entry=entry,
                test_name="Pay After Termination",
                test_key="PR-T4",
                test_tier=TestTier.STRUCTURAL.value,
                severity=severity.value,
                issue=f"Payment {days_after} days after termination ({entry.term_date.isoformat()})",
                confidence=0.90,
                details={"days_after": days_after, "term_date": entry.term_date.isoformat()},
            ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Pay After Termination",
        test_key="PR-T4",
        test_tier=TestTier.STRUCTURAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.HIGH.value,
        description="Flag payments made after the employee's termination date",
        flagged_entries=flagged,
    )


def _test_check_number_gaps(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T5: Check Number Gaps — sequential gaps in payroll check numbers."""
    flagged: list[FlaggedEmployee] = []

    if not config.check_number_gap_enabled:
        return PayrollTestResult(
            test_name="Check Number Gaps",
            test_key="PR-T5",
            test_tier=TestTier.STRUCTURAL.value,
            total_entries=len(entries),
            description="Disabled by configuration",
        )

    # Extract numeric check numbers
    check_entries: list[tuple[int, PayrollEntry]] = []
    for entry in entries:
        s = entry.check_number.strip()
        if s:
            try:
                num = int(re.sub(r"[^0-9]", "", s))
                check_entries.append((num, entry))
            except ValueError:
                continue

    if len(check_entries) < 2:
        return PayrollTestResult(
            test_name="Check Number Gaps",
            test_key="PR-T5",
            test_tier=TestTier.STRUCTURAL.value,
            total_entries=len(entries),
            description="Insufficient check numbers for gap analysis",
        )

    check_entries.sort(key=lambda x: x[0])

    for i in range(1, len(check_entries)):
        prev_num, prev_entry = check_entries[i - 1]
        curr_num, curr_entry = check_entries[i]
        gap = curr_num - prev_num

        if gap >= config.check_number_gap_min_size:
            if gap > 10:
                severity = Severity.HIGH
            elif gap > 5:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedEmployee(
                entry=curr_entry,
                test_name="Check Number Gaps",
                test_key="PR-T5",
                test_tier=TestTier.STRUCTURAL.value,
                severity=severity.value,
                issue=f"Gap of {gap} in check sequence ({prev_num} → {curr_num})",
                confidence=0.75,
                details={"gap_size": gap, "previous_check": prev_num, "current_check": curr_num},
            ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Check Number Gaps",
        test_key="PR-T5",
        test_tier=TestTier.STRUCTURAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.MEDIUM.value,
        description="Detect gaps in sequential payroll check numbers",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 2 TESTS — STATISTICAL
# =============================================================================

def _test_unusual_pay_amounts(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T6: Unusual Pay Amounts — per-department z-score outliers."""
    flagged: list[FlaggedEmployee] = []

    # Group by department (or "Unknown" if no department)
    dept_groups: dict[str, list[PayrollEntry]] = {}
    for entry in entries:
        dept = entry.department.strip() if entry.department.strip() else "Unknown"
        dept_groups.setdefault(dept, []).append(entry)

    for dept, group in dept_groups.items():
        amounts = [e.gross_pay for e in group if e.gross_pay > 0]
        if len(amounts) < config.unusual_pay_min_entries:
            continue

        mean_amt = statistics.mean(amounts)
        stdev_amt = statistics.stdev(amounts) if len(amounts) > 1 else 0.0
        if stdev_amt == 0:
            continue

        for entry in group:
            if entry.gross_pay <= 0:
                continue
            z_score = (entry.gross_pay - mean_amt) / stdev_amt

            if abs(z_score) < config.unusual_pay_stddev:
                continue

            if abs(z_score) > 5:
                severity = Severity.HIGH
            elif abs(z_score) > 4:
                severity = Severity.MEDIUM
            else:
                severity = Severity.LOW

            flagged.append(FlaggedEmployee(
                entry=entry,
                test_name="Unusual Pay Amounts",
                test_key="PR-T6",
                test_tier=TestTier.STATISTICAL.value,
                severity=severity.value,
                issue=f"Pay ${entry.gross_pay:,.2f} is {abs(z_score):.1f}σ from dept '{dept}' mean (${mean_amt:,.2f})",
                confidence=min(abs(z_score) / 6.0, 1.0),
                details={
                    "z_score": round(z_score, 2),
                    "department": dept,
                    "dept_mean": round(mean_amt, 2),
                    "dept_stdev": round(stdev_amt, 2),
                },
            ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Unusual Pay Amounts",
        test_key="PR-T6",
        test_tier=TestTier.STATISTICAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.MEDIUM.value,
        description="Flag pay amounts that are statistical outliers within their department",
        flagged_entries=flagged,
    )


def _test_pay_frequency_anomalies(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T7: Pay Frequency Anomalies — flag employees with irregular pay spacing."""
    flagged: list[FlaggedEmployee] = []

    if not config.frequency_enabled:
        return PayrollTestResult(
            test_name="Pay Frequency Anomalies",
            test_key="PR-T7",
            test_tier=TestTier.STATISTICAL.value,
            total_entries=len(entries),
            description="Disabled by configuration",
        )

    # Group by employee identifier (prefer ID, fallback to name)
    emp_groups: dict[str, list[PayrollEntry]] = {}
    for entry in entries:
        key = (entry.employee_id.strip().lower() if entry.employee_id.strip()
               else entry.employee_name.strip().lower())
        if key:
            emp_groups.setdefault(key, []).append(entry)

    # Detect population cadence: find most common pay interval
    all_intervals: list[int] = []
    for key, group in emp_groups.items():
        dated = sorted([e for e in group if e.pay_date], key=lambda e: e.pay_date)
        for i in range(1, len(dated)):
            delta = (dated[i].pay_date - dated[i - 1].pay_date).days
            if 1 <= delta <= 60:
                all_intervals.append(delta)

    if not all_intervals:
        return PayrollTestResult(
            test_name="Pay Frequency Anomalies",
            test_key="PR-T7",
            test_tier=TestTier.STATISTICAL.value,
            total_entries=len(entries),
            description="Insufficient date data for frequency analysis",
        )

    # Most common interval = expected cadence
    interval_counts = Counter(all_intervals)
    expected_cadence = interval_counts.most_common(1)[0][0]

    # Allow deviation threshold (e.g., 50% of expected cadence)
    min_interval = expected_cadence * (1 - config.frequency_deviation_threshold)
    max_interval = expected_cadence * (1 + config.frequency_deviation_threshold)

    flagged_rows: set[int] = set()

    for key, group in emp_groups.items():
        dated = sorted([e for e in group if e.pay_date], key=lambda e: e.pay_date)
        if len(dated) < 3:
            continue

        for i in range(1, len(dated)):
            delta = (dated[i].pay_date - dated[i - 1].pay_date).days
            if delta < min_interval or delta > max_interval:
                entry = dated[i]
                if entry._row_index in flagged_rows:
                    continue
                flagged_rows.add(entry._row_index)

                if delta < min_interval:
                    severity = Severity.MEDIUM if delta < expected_cadence * 0.3 else Severity.LOW
                    issue = f"Pay interval {delta}d is shorter than expected {expected_cadence}d cadence"
                else:
                    severity = Severity.LOW
                    issue = f"Pay interval {delta}d is longer than expected {expected_cadence}d cadence"

                flagged.append(FlaggedEmployee(
                    entry=entry,
                    test_name="Pay Frequency Anomalies",
                    test_key="PR-T7",
                    test_tier=TestTier.STATISTICAL.value,
                    severity=severity.value,
                    issue=issue,
                    confidence=0.65,
                    details={
                        "interval_days": delta,
                        "expected_cadence": expected_cadence,
                        "employee_key": key,
                    },
                ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Pay Frequency Anomalies",
        test_key="PR-T7",
        test_tier=TestTier.STATISTICAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.LOW.value,
        description=f"Flag irregular pay intervals (expected cadence: {expected_cadence}d)",
        flagged_entries=flagged,
    )


# Benford's Law expected first-digit distribution (Newcomb-Benford)
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

# MAD thresholds per Nigrini (2012)
BENFORD_MAD_CONFORMING = 0.006
BENFORD_MAD_ACCEPTABLE = 0.012
BENFORD_MAD_MARGINALLY_ACCEPTABLE = 0.015


def _get_first_digit(value: float) -> Optional[int]:
    """Extract the first significant digit (1-9) from a number."""
    if value == 0:
        return None
    abs_val = abs(value)
    s = f"{abs_val:.10f}".lstrip("0").lstrip(".")
    for ch in s:
        if ch.isdigit() and ch != "0":
            return int(ch)
    return None


def _test_benford_gross_pay(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
) -> PayrollTestResult:
    """PR-T8: Benford's Law on Gross Pay — first-digit distribution analysis."""
    if not config.enable_benford:
        return PayrollTestResult(
            test_name="Benford's Law — Gross Pay",
            test_key="PR-T8",
            test_tier=TestTier.STATISTICAL.value,
            total_entries=len(entries),
            description="Disabled by configuration",
        )

    # Extract eligible amounts (>= $1, non-zero)
    amounts: list[float] = []
    amount_entries: list[PayrollEntry] = []
    for e in entries:
        amt = abs(e.gross_pay)
        if amt >= 1.0:
            amounts.append(amt)
            amount_entries.append(e)

    eligible_count = len(amounts)
    total = len(entries)

    # Pre-check 1: Minimum entry count
    if eligible_count < config.benford_min_entries:
        return PayrollTestResult(
            test_name="Benford's Law — Gross Pay",
            test_key="PR-T8",
            test_tier=TestTier.STATISTICAL.value,
            total_entries=total,
            description=f"Insufficient data: {eligible_count} eligible entries (minimum {config.benford_min_entries} required)",
        )

    # Pre-check 2: Magnitude range
    min_amt = min(amounts)
    max_amt = max(amounts)
    if min_amt > 0 and max_amt > 0:
        magnitude_range = math.log10(max_amt) - math.log10(min_amt)
    else:
        magnitude_range = 0.0

    if magnitude_range < config.benford_min_magnitude_range:
        return PayrollTestResult(
            test_name="Benford's Law — Gross Pay",
            test_key="PR-T8",
            test_tier=TestTier.STATISTICAL.value,
            total_entries=total,
            description=f"Insufficient magnitude range: {magnitude_range:.1f} orders (minimum {config.benford_min_magnitude_range} required)",
        )

    # Calculate first-digit distribution
    digit_counts: dict[int, int] = {d: 0 for d in range(1, 10)}
    entry_by_digit: dict[int, list[PayrollEntry]] = {d: [] for d in range(1, 10)}

    for amt, entry in zip(amounts, amount_entries):
        digit = _get_first_digit(amt)
        if digit and 1 <= digit <= 9:
            digit_counts[digit] += 1
            entry_by_digit[digit].append(entry)

    counted_total = sum(digit_counts.values())
    if counted_total == 0:
        return PayrollTestResult(
            test_name="Benford's Law — Gross Pay",
            test_key="PR-T8",
            test_tier=TestTier.STATISTICAL.value,
            total_entries=total,
            description="No valid first digits found",
        )

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

    # Most deviated digits
    sorted_deviations = sorted(
        range(1, 10), key=lambda d: abs(deviation[d]), reverse=True
    )
    most_deviated = [d for d in sorted_deviations[:3] if abs(deviation[d]) > mad]

    # Flag entries from most-deviated digit buckets (only if nonconforming/marginal)
    flagged: list[FlaggedEmployee] = []
    if conformity in ("marginally_acceptable", "nonconforming"):
        for digit in most_deviated:
            dev_pct = deviation[digit]
            if dev_pct > 0:  # Only flag overrepresented digits
                for entry in entry_by_digit[digit]:
                    flagged.append(FlaggedEmployee(
                        entry=entry,
                        test_name="Benford's Law — Gross Pay",
                        test_key="PR-T8",
                        test_tier=TestTier.STATISTICAL.value,
                        severity=Severity.MEDIUM.value if conformity == "nonconforming" else Severity.LOW.value,
                        issue=f"First digit {digit} overrepresented ({actual_dist[digit]:.1%} vs expected {BENFORD_EXPECTED[digit]:.1%})",
                        confidence=min(abs(dev_pct) / 0.05, 1.0),
                        details={
                            "first_digit": digit,
                            "actual_pct": round(actual_dist[digit], 4),
                            "expected_pct": round(BENFORD_EXPECTED[digit], 4),
                            "deviation": round(dev_pct, 4),
                        },
                    ))

    # Overall severity
    if conformity == "nonconforming":
        overall_severity = Severity.HIGH.value
    elif conformity == "marginally_acceptable":
        overall_severity = Severity.MEDIUM.value
    else:
        overall_severity = Severity.LOW.value

    return PayrollTestResult(
        test_name="Benford's Law — Gross Pay",
        test_key="PR-T8",
        test_tier=TestTier.STATISTICAL.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=overall_severity,
        description=f"First-digit distribution analysis (MAD={mad:.4f}, {conformity}, χ²={chi_sq:.2f})",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 3 TESTS — FRAUD INDICATORS
# =============================================================================

# Keywords for ghost employee pattern detection
PAYROLL_SUSPICIOUS_KEYWORDS = [
    ("terminated", 0.80, False),
    ("inactive", 0.80, False),
    ("no department", 0.75, True),
    ("temp", 0.60, False),
    ("temporary", 0.65, False),
    ("contractor", 0.50, False),
    ("unknown", 0.70, False),
    ("unassigned", 0.75, False),
    ("n/a", 0.60, True),
]


def _test_ghost_employee_indicators(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
    detection: PayrollColumnDetectionResult,
) -> PayrollTestResult:
    """PR-T9: Ghost Employee Indicators — flag employees with multiple fraud indicators.

    Indicators:
    1. No department assignment (if department column exists)
    2. Pay entries only in first/last month of period (boundary-only employees)
    3. Single pay entry (one-time payroll fraud pattern)
    """
    flagged: list[FlaggedEmployee] = []

    if not config.enable_ghost:
        return PayrollTestResult(
            test_name="Ghost Employee Indicators",
            test_key="PR-T9",
            test_tier=TestTier.ADVANCED.value,
            total_entries=len(entries),
            description="Disabled by configuration",
        )

    has_dept = detection.department_column is not None

    # Group by employee identifier
    emp_groups: dict[str, list[PayrollEntry]] = {}
    for entry in entries:
        key = (entry.employee_id.strip().lower() if entry.employee_id.strip()
               else entry.employee_name.strip().lower())
        if key:
            emp_groups.setdefault(key, []).append(entry)

    # Determine period boundaries from all entries
    all_dates = [e.pay_date for e in entries if e.pay_date]
    if not all_dates:
        return PayrollTestResult(
            test_name="Ghost Employee Indicators",
            test_key="PR-T9",
            test_tier=TestTier.ADVANCED.value,
            total_entries=len(entries),
            description="No date data for ghost employee analysis",
        )

    min_date = min(all_dates)
    max_date = max(all_dates)
    first_month = (min_date.year, min_date.month)
    last_month = (max_date.year, max_date.month)

    flagged_rows: set[int] = set()

    for emp_key, group in emp_groups.items():
        indicators: list[str] = []

        # Indicator 1: No department (if column exists)
        if has_dept:
            all_no_dept = all(not e.department.strip() for e in group)
            if all_no_dept:
                indicators.append("No department assignment")

        # Indicator 2: Single pay entry
        if len(group) == 1:
            indicators.append("Single pay entry in period")

        # Indicator 3: Payments only in first/last month
        dated_entries = [e for e in group if e.pay_date]
        if dated_entries and len(dated_entries) > 1 and first_month != last_month:
            entry_months = set((e.pay_date.year, e.pay_date.month) for e in dated_entries)
            if entry_months <= {first_month, last_month}:
                indicators.append("Pay entries only in first/last month of period")

        if len(indicators) < config.ghost_min_indicators:
            continue

        # Severity: multiple indicators → HIGH, single → MEDIUM
        if len(indicators) >= 2:
            severity = Severity.HIGH
        else:
            severity = Severity.MEDIUM

        for entry in group:
            if entry._row_index in flagged_rows:
                continue
            flagged_rows.add(entry._row_index)
            flagged.append(FlaggedEmployee(
                entry=entry,
                test_name="Ghost Employee Indicators",
                test_key="PR-T9",
                test_tier=TestTier.ADVANCED.value,
                severity=severity.value,
                issue=f"Ghost indicators: {'; '.join(indicators)}",
                confidence=min(0.50 + len(indicators) * 0.15, 1.0),
                details={
                    "indicators": indicators,
                    "indicator_count": len(indicators),
                    "employee_key": emp_key,
                    "entry_count": len(group),
                },
            ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Ghost Employee Indicators",
        test_key="PR-T9",
        test_tier=TestTier.ADVANCED.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.MEDIUM.value,
        description="Flag employees with ghost employee fraud indicators",
        flagged_entries=flagged,
    )


def _test_duplicate_bank_accounts(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
    detection: PayrollColumnDetectionResult,
) -> PayrollTestResult:
    """PR-T10: Duplicate Bank Accounts / Addresses — flag employees sharing bank/address."""
    flagged: list[FlaggedEmployee] = []

    if not config.enable_duplicates:
        return PayrollTestResult(
            test_name="Duplicate Bank Accounts / Addresses",
            test_key="PR-T10",
            test_tier=TestTier.ADVANCED.value,
            total_entries=len(entries),
            description="Disabled by configuration",
        )

    flagged_rows: set[int] = set()

    # Part A: Duplicate bank accounts (exact match)
    if detection.has_bank_accounts:
        bank_groups: dict[str, list[PayrollEntry]] = {}
        for entry in entries:
            acct = entry.bank_account.strip().lower()
            if acct:
                bank_groups.setdefault(acct, []).append(entry)

        for acct, group in bank_groups.items():
            # Get unique employee names for this account
            emp_names = set()
            for e in group:
                name = e.employee_name.strip().lower()
                if name:
                    emp_names.add(name)

            if len(emp_names) > 1:
                for entry in group:
                    if entry._row_index not in flagged_rows:
                        flagged_rows.add(entry._row_index)
                        flagged.append(FlaggedEmployee(
                            entry=entry,
                            test_name="Duplicate Bank Accounts / Addresses",
                            test_key="PR-T10",
                            test_tier=TestTier.ADVANCED.value,
                            severity=Severity.HIGH.value,
                            issue=f"Bank account shared by {len(emp_names)} employees",
                            confidence=0.90,
                            details={
                                "match_type": "bank_account",
                                "shared_employees": sorted(emp_names),
                                "account_masked": acct[:4] + "****",
                            },
                        ))

    # Part B: Duplicate addresses (fuzzy match)
    if detection.has_addresses:
        # Get unique employee-address pairs
        emp_addresses: dict[str, str] = {}
        emp_entries: dict[str, list[PayrollEntry]] = {}
        for entry in entries:
            name = entry.employee_name.strip().lower()
            addr = entry.address.strip().lower()
            if name and addr and len(addr) > 5:
                # Use first occurrence
                if name not in emp_addresses:
                    emp_addresses[name] = addr
                emp_entries.setdefault(name, []).append(entry)

        unique_emps = sorted(emp_addresses.keys())
        for i in range(len(unique_emps)):
            for j in range(i + 1, len(unique_emps)):
                name_a = unique_emps[i]
                name_b = unique_emps[j]
                addr_a = emp_addresses[name_a]
                addr_b = emp_addresses[name_b]

                ratio = SequenceMatcher(None, addr_a, addr_b).ratio()
                if ratio >= config.address_similarity_threshold:
                    for entry in emp_entries[name_a] + emp_entries[name_b]:
                        if entry._row_index not in flagged_rows:
                            flagged_rows.add(entry._row_index)
                            flagged.append(FlaggedEmployee(
                                entry=entry,
                                test_name="Duplicate Bank Accounts / Addresses",
                                test_key="PR-T10",
                                test_tier=TestTier.ADVANCED.value,
                                severity=Severity.MEDIUM.value,
                                issue=f"Address similarity {ratio:.0%} between '{name_a}' and '{name_b}'",
                                confidence=round(ratio, 2),
                                details={
                                    "match_type": "address",
                                    "name_a": name_a,
                                    "name_b": name_b,
                                    "similarity": round(ratio, 2),
                                },
                            ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Duplicate Bank Accounts / Addresses",
        test_key="PR-T10",
        test_tier=TestTier.ADVANCED.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.HIGH.value,
        description="Flag employees sharing bank accounts or addresses",
        flagged_entries=flagged,
    )


def _test_duplicate_tax_ids(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
    detection: PayrollColumnDetectionResult,
) -> PayrollTestResult:
    """PR-T11: Duplicate Tax IDs — flag employees sharing same tax_id."""
    flagged: list[FlaggedEmployee] = []

    if not config.enable_tax_id_duplicates:
        return PayrollTestResult(
            test_name="Duplicate Tax IDs",
            test_key="PR-T11",
            test_tier=TestTier.ADVANCED.value,
            total_entries=len(entries),
            description="Disabled by configuration",
        )

    if not detection.has_tax_ids:
        return PayrollTestResult(
            test_name="Duplicate Tax IDs",
            test_key="PR-T11",
            test_tier=TestTier.ADVANCED.value,
            total_entries=len(entries),
            description="No tax ID column detected",
        )

    # Group by tax ID
    tax_groups: dict[str, list[PayrollEntry]] = {}
    for entry in entries:
        tid = entry.tax_id.strip().lower()
        if tid:
            tax_groups.setdefault(tid, []).append(entry)

    flagged_rows: set[int] = set()

    for tid, group in tax_groups.items():
        emp_names = set()
        for e in group:
            name = e.employee_name.strip().lower()
            if name:
                emp_names.add(name)

        if len(emp_names) > 1:
            for entry in group:
                if entry._row_index not in flagged_rows:
                    flagged_rows.add(entry._row_index)
                    flagged.append(FlaggedEmployee(
                        entry=entry,
                        test_name="Duplicate Tax IDs",
                        test_key="PR-T11",
                        test_tier=TestTier.ADVANCED.value,
                        severity=Severity.HIGH.value,
                        issue=f"Tax ID shared by {len(emp_names)} employees: {', '.join(sorted(emp_names))}",
                        confidence=0.95,
                        details={
                            "shared_employees": sorted(emp_names),
                            "tax_id_masked": tid[:3] + "****",
                            "entry_count": len(group),
                        },
                    ))

    total = len(entries)
    return PayrollTestResult(
        test_name="Duplicate Tax IDs",
        test_key="PR-T11",
        test_tier=TestTier.ADVANCED.value,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=Severity.HIGH.value,
        description="Flag employees sharing the same tax identification number",
        flagged_entries=flagged,
    )


# =============================================================================
# TEST BATTERY & SCORING
# =============================================================================

def run_payroll_test_battery(
    entries: list[PayrollEntry],
    config: PayrollTestingConfig,
    detection: PayrollColumnDetectionResult,
) -> list[PayrollTestResult]:
    """Run all payroll tests in sequence."""
    results: list[PayrollTestResult] = []

    # Tier 1 — Structural
    results.append(_test_duplicate_employee_ids(entries, config))
    results.append(_test_missing_critical_fields(entries, config))
    results.append(_test_round_salary_amounts(entries, config))

    # PR-T4: only if term_date column exists
    if detection.has_term_dates:
        results.append(_test_pay_after_termination(entries, config))

    # PR-T5: only if check_number column exists
    if detection.has_check_numbers:
        results.append(_test_check_number_gaps(entries, config))

    # Tier 2 — Statistical
    results.append(_test_unusual_pay_amounts(entries, config))
    results.append(_test_pay_frequency_anomalies(entries, config))
    results.append(_test_benford_gross_pay(entries, config))

    # Tier 3 — Fraud Indicators
    results.append(_test_ghost_employee_indicators(entries, config, detection))

    # PR-T10: only if bank_account or address column exists
    if detection.has_bank_accounts or detection.has_addresses:
        results.append(_test_duplicate_bank_accounts(entries, config, detection))

    # PR-T11: only if tax_id column exists
    if detection.has_tax_ids:
        results.append(_test_duplicate_tax_ids(entries, config, detection))

    return results


def calculate_payroll_composite_score(
    test_results: list[PayrollTestResult],
    total_entries: int,
) -> PayrollCompositeScore:
    """Calculate composite risk score from test results."""
    if total_entries == 0:
        return PayrollCompositeScore(score=0.0, risk_tier=RiskTier.LOW.value)

    total_flagged = 0
    flags_by_severity: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    weighted_sum = 0.0

    # Count flags by severity
    for result in test_results:
        for flagged in result.flagged_entries:
            total_flagged += 1
            sev = flagged.severity
            flags_by_severity[sev] = flags_by_severity.get(sev, 0) + 1
            weight = SEVERITY_WEIGHTS.get(Severity(sev), 1.0)
            weighted_sum += weight

    # Normalize to 0-100 scale
    flag_rate = total_flagged / total_entries if total_entries > 0 else 0.0

    # Multi-flag multiplier: entries flagged by 3+ tests get 1.25x
    entry_flag_counts: dict[int, int] = {}
    for result in test_results:
        for flagged in result.flagged_entries:
            row = flagged.entry._row_index
            entry_flag_counts[row] = entry_flag_counts.get(row, 0) + 1

    multi_flag_entries = sum(1 for c in entry_flag_counts.values() if c >= 3)
    multiplier = 1.0 + (multi_flag_entries / max(total_entries, 1)) * 0.25

    # Score calculation
    base_score = (weighted_sum / total_entries) * 100 * multiplier
    score = min(base_score, 100.0)

    # Risk tier
    if score >= 75:
        risk_tier = RiskTier.CRITICAL.value
    elif score >= 50:
        risk_tier = RiskTier.HIGH.value
    elif score >= 25:
        risk_tier = RiskTier.MODERATE.value
    elif score >= 10:
        risk_tier = RiskTier.ELEVATED.value
    else:
        risk_tier = RiskTier.LOW.value

    # Top findings
    all_flagged: list[FlaggedEmployee] = []
    for result in test_results:
        all_flagged.extend(result.flagged_entries)

    all_flagged.sort(key=lambda f: SEVERITY_WEIGHTS.get(Severity(f.severity), 0), reverse=True)
    top_findings = [
        {
            "employee": f.entry.employee_name,
            "test": f.test_name,
            "issue": f.issue,
            "severity": f.severity,
            "amount": f.entry.gross_pay,
        }
        for f in all_flagged[:10]
    ]

    return PayrollCompositeScore(
        score=score,
        risk_tier=risk_tier,
        tests_run=len(test_results),
        total_entries=total_entries,
        total_flagged=total_flagged,
        flag_rate=flag_rate,
        flags_by_severity=flags_by_severity,
        top_findings=top_findings,
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_payroll_testing(
    headers: list[str],
    rows: list[dict],
    config: Optional[PayrollTestingConfig] = None,
    column_mapping: Optional[dict[str, str]] = None,
    filename: str = "",
) -> PayrollTestingResult:
    """Run complete payroll testing pipeline.

    Args:
        headers: Column header names
        rows: List of row dicts (key=column name)
        config: Optional custom configuration
        column_mapping: Optional manual column mapping override
        filename: Source filename for reporting

    Returns:
        PayrollTestingResult with composite score, test results, data quality
    """
    if config is None:
        config = PayrollTestingConfig()

    # Column detection (or manual mapping)
    if column_mapping:
        detection = PayrollColumnDetectionResult(all_columns=headers)
        mapping_fields = {
            "employee_id": "employee_id_column",
            "employee_name": "employee_name_column",
            "department": "department_column",
            "pay_date": "pay_date_column",
            "gross_pay": "gross_pay_column",
            "net_pay": "net_pay_column",
            "deductions": "deductions_column",
            "check_number": "check_number_column",
            "pay_type": "pay_type_column",
            "hours": "hours_column",
            "rate": "rate_column",
            "term_date": "term_date_column",
            "bank_account": "bank_account_column",
            "address": "address_column",
            "tax_id": "tax_id_column",
        }
        for key, attr in mapping_fields.items():
            if key in column_mapping:
                setattr(detection, attr, column_mapping[key])
        detection.has_check_numbers = detection.check_number_column is not None
        detection.has_term_dates = detection.term_date_column is not None
        detection.has_bank_accounts = detection.bank_account_column is not None
        detection.has_addresses = detection.address_column is not None
        detection.has_tax_ids = detection.tax_id_column is not None
        detection.overall_confidence = 1.0
    else:
        detection = detect_payroll_columns(headers)

    # Parse entries
    entries = parse_payroll_entries(rows, detection)

    # Data quality
    data_quality = assess_payroll_data_quality(entries, detection)

    # Run test battery
    test_results = run_payroll_test_battery(entries, config, detection)

    # Composite score
    composite = calculate_payroll_composite_score(test_results, len(entries))

    # Clear memory (Zero-Storage)
    rows.clear()

    return PayrollTestingResult(
        composite_score=composite,
        test_results=test_results,
        data_quality=data_quality,
        column_detection=detection,
        filename=filename,
    )
