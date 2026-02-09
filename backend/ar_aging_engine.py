"""
AR Aging Analysis Engine — Sprint 107

Accounts receivable aging analysis: aging bucket analysis, allowance adequacy,
customer concentration. Accepts TB (for balance-level checks) + optional
AR sub-ledger (for aging detail). Runs 11 tests across structural, statistical,
and advanced tiers.

ZERO-STORAGE COMPLIANCE:
- All files processed in-memory only
- Test results are ephemeral (computed on demand)
- No raw AR data is stored

Audit Standards References:
- ISA 500: Audit Evidence
- ISA 540: Auditing Accounting Estimates (allowance for doubtful accounts)
- PCAOB AS 2501: Auditing Accounting Estimates (estimation uncertainty)

DUAL-INPUT ARCHITECTURE:
- TB file (required): balance-level AR, allowance, revenue accounts
- Sub-ledger file (optional): customer/invoice-level aging detail
- TB-only: 4 tests (AR01, AR02, AR07, AR09)
- TB + sub-ledger: all 11 tests
"""

from dataclasses import dataclass, field
from typing import Optional
import re
import math
import statistics

from shared.testing_enums import RiskTier, TestTier, Severity, SEVERITY_WEIGHTS


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ARAgingConfig:
    """Configurable thresholds for all AR aging tests."""
    # AR-01: Sign anomalies
    sign_anomaly_enabled: bool = True

    # AR-02: Missing allowance
    missing_allowance_enabled: bool = True

    # AR-03: Negative aging buckets
    negative_aging_enabled: bool = True

    # AR-04: Unreconciled AR detail
    reconciliation_threshold_pct: float = 0.01
    reconciliation_threshold_abs: float = 100.0

    # AR-05: Aging bucket concentration
    bucket_concentration_threshold: float = 0.60

    # AR-06: Past-due concentration
    past_due_days: int = 30
    past_due_threshold_pct: float = 0.25
    past_due_high_pct: float = 0.50

    # AR-07: Allowance adequacy ratio
    allowance_low_pct: float = 0.01
    allowance_high_pct: float = 0.10

    # AR-08: Large customer concentration
    customer_concentration_threshold: float = 0.20
    customer_concentration_high: float = 0.40

    # AR-09: DSO trend variance
    dso_variance_threshold: float = 0.20
    dso_high_threshold: float = 0.50
    prior_period_dso: Optional[float] = None
    days_in_period: int = 365

    # AR-10: Roll-forward reconciliation
    beginning_ar_balance: Optional[float] = None
    collections_total: Optional[float] = None
    rollforward_threshold_pct: float = 0.05

    # AR-11: Customer credit limit breaches
    credit_limit_enabled: bool = True
    credit_limit_high_pct: float = 1.50


# =============================================================================
# TB ACCOUNT CLASSIFICATION PATTERNS
# =============================================================================

AR_ACCOUNT_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^accounts?\s*receivable$", 1.0, True),
    (r"^trade\s*receivable", 0.95, True),
    (r"^trade\s*debtor", 0.95, True),
    (r"^customer\s*receivable", 0.90, True),
    (r"^due\s*from\s*customer", 0.90, True),
    (r"^a/?r\b", 0.85, True),
    (r"^accts?\s*rec", 0.85, True),
    (r"receivable", 0.70, False),
    (r"trade\s*debtor", 0.70, False),
]

ALLOWANCE_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^allowance\s*for\s*doubtful", 1.0, True),
    (r"^allowance\s*for\s*bad\s*debt", 1.0, True),
    (r"^provision\s*for\s*bad\s*debt", 0.95, True),
    (r"^provision\s*for\s*doubtful", 0.95, True),
    (r"^bad\s*debt\s*reserve", 0.90, True),
    (r"^expected\s*credit\s*loss", 0.95, True),
    (r"allowance\s*for\s*(doubtful|bad)", 0.85, False),
    (r"provision\s*for\s*(doubtful|bad)", 0.85, False),
    (r"credit\s*loss\s*(allowance|provision|reserve)", 0.80, False),
    (r"^allowance", 0.50, False),
]

REVENUE_ACCOUNT_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^revenue$", 0.95, True),
    (r"^sales\s*revenue", 1.0, True),
    (r"^net\s*revenue", 0.95, True),
    (r"^service\s*(revenue|income)", 0.90, True),
    (r"^fee\s*income", 0.85, True),
    (r"^sales$", 0.80, True),
    (r"^net\s*sales", 0.85, True),
    (r"^turnover$", 0.75, True),
    (r"revenue", 0.60, False),
    (r"^sales", 0.55, False),
]


# =============================================================================
# TB COLUMN DETECTION PATTERNS
# =============================================================================

TB_ACCOUNT_NAME_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^account\s*name$", 1.0, True),
    (r"^account\s*description$", 0.95, True),
    (r"^gl\s*description$", 0.90, True),
    (r"^description$", 0.65, True),
    (r"^name$", 0.60, True),
    (r"acct\s*name", 0.80, False),
    (r"account\s*name", 0.85, False),
]

TB_ACCOUNT_NUMBER_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^account\s*number$", 1.0, True),
    (r"^account\s*(no|#|code)$", 0.95, True),
    (r"^acct\s*(no|#|code|number)$", 0.90, True),
    (r"^gl\s*(code|number|acct)$", 0.85, True),
    (r"account\s*(number|no|code)", 0.80, False),
]

TB_BALANCE_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^ending\s*balance$", 1.0, True),
    (r"^net\s*balance$", 0.95, True),
    (r"^balance$", 0.90, True),
    (r"^amount$", 0.70, True),
    (r"^total$", 0.60, True),
    (r"balance", 0.55, False),
]

TB_DEBIT_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^debit$", 1.0, True),
    (r"^dr\.?$", 0.90, True),
    (r"^debit\s*balance$", 0.95, True),
    (r"debit", 0.60, False),
]

TB_CREDIT_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^credit$", 1.0, True),
    (r"^cr\.?$", 0.90, True),
    (r"^credit\s*balance$", 0.95, True),
    (r"credit", 0.60, False),
]


# =============================================================================
# SUB-LEDGER COLUMN DETECTION PATTERNS
# =============================================================================

SL_CUSTOMER_NAME_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^customer\s*name$", 1.0, True),
    (r"^customer$", 0.90, True),
    (r"^client\s*name$", 0.90, True),
    (r"^debtor\s*name$", 0.90, True),
    (r"^party\s*name$", 0.80, True),
    (r"^name$", 0.55, True),
    (r"customer", 0.60, False),
    (r"debtor", 0.55, False),
]

SL_CUSTOMER_ID_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^customer\s*(id|code|number|no)$", 1.0, True),
    (r"^debtor\s*(id|code|number|no)$", 0.90, True),
    (r"^party\s*(id|code)$", 0.80, True),
    (r"customer\s*(id|code|number)", 0.70, False),
]

SL_INVOICE_NUMBER_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^invoice\s*(number|no|#|num)$", 1.0, True),
    (r"^inv\s*(no|#|number)$", 0.90, True),
    (r"^document\s*(number|no)$", 0.80, True),
    (r"^reference$", 0.55, True),
    (r"invoice", 0.60, False),
]

SL_INVOICE_DATE_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^invoice\s*date$", 1.0, True),
    (r"^document\s*date$", 0.90, True),
    (r"^transaction\s*date$", 0.85, True),
    (r"^date$", 0.60, True),
    (r"invoice.*date", 0.75, False),
]

SL_DUE_DATE_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^due\s*date$", 1.0, True),
    (r"^payment\s*due\s*date$", 0.95, True),
    (r"^maturity\s*date$", 0.85, True),
    (r"due.*date", 0.70, False),
]

SL_AMOUNT_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^amount$", 0.90, True),
    (r"^balance$", 0.85, True),
    (r"^outstanding\s*(amount|balance)$", 1.0, True),
    (r"^open\s*(amount|balance)$", 0.95, True),
    (r"^invoice\s*amount$", 0.90, True),
    (r"^receivable\s*amount$", 0.90, True),
    (r"amount", 0.55, False),
    (r"balance", 0.50, False),
]

SL_AGING_DAYS_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^aging\s*days$", 1.0, True),
    (r"^days\s*outstanding$", 0.95, True),
    (r"^days\s*overdue$", 0.90, True),
    (r"^days\s*past\s*due$", 0.90, True),
    (r"^age$", 0.70, True),
    (r"aging", 0.60, False),
    (r"days\s*(outstanding|overdue|past)", 0.70, False),
]

SL_AGING_BUCKET_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^aging\s*bucket$", 1.0, True),
    (r"^bucket$", 0.80, True),
    (r"^aging\s*category$", 0.90, True),
    (r"^age\s*range$", 0.85, True),
    (r"aging.*bucket", 0.70, False),
    (r"bucket", 0.50, False),
]

SL_CREDIT_LIMIT_PATTERNS: list[tuple[str, float, bool]] = [
    (r"^credit\s*limit$", 1.0, True),
    (r"^credit\s*line$", 0.90, True),
    (r"^approved\s*credit$", 0.85, True),
    (r"credit\s*limit", 0.80, False),
]


# =============================================================================
# AGING BUCKET DEFINITIONS
# =============================================================================

STANDARD_AGING_BUCKETS = [
    ("current", 0, 30),
    ("31-60", 31, 60),
    ("61-90", 61, 90),
    ("91-120", 91, 120),
    ("over_120", 121, 999999),
]


def classify_aging_bucket(days: int) -> str:
    """Classify aging days into standard bucket."""
    for bucket_name, low, high in STANDARD_AGING_BUCKETS:
        if low <= days <= high:
            return bucket_name
    return "over_120" if days > 120 else "current"


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class TBAccount:
    """A single account from the trial balance."""
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    balance: float = 0.0
    classification: str = "other"  # "ar", "allowance", "revenue", "other"
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "account_name": self.account_name,
            "account_number": self.account_number,
            "balance": self.balance,
            "classification": self.classification,
            "row_number": self.row_number,
        }


@dataclass
class ARSubledgerEntry:
    """A single line from the AR sub-ledger."""
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    amount: float = 0.0
    aging_days: Optional[int] = None
    aging_bucket: Optional[str] = None
    credit_limit: Optional[float] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "customer_name": self.customer_name,
            "customer_id": self.customer_id,
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "amount": self.amount,
            "aging_days": self.aging_days,
            "aging_bucket": self.aging_bucket,
            "credit_limit": self.credit_limit,
            "row_number": self.row_number,
        }


@dataclass
class AREntry:
    """Generic AR entry — can represent a TB account or sub-ledger line."""
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    customer_name: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[str] = None
    amount: float = 0.0
    aging_days: Optional[int] = None
    row_number: int = 0
    entry_source: str = "tb"  # "tb" or "subledger"

    def to_dict(self) -> dict:
        return {
            "account_name": self.account_name,
            "account_number": self.account_number,
            "customer_name": self.customer_name,
            "invoice_number": self.invoice_number,
            "date": self.date,
            "amount": self.amount,
            "aging_days": self.aging_days,
            "row_number": self.row_number,
            "entry_source": self.entry_source,
        }


@dataclass
class FlaggedAR:
    """An AR item flagged by a test."""
    entry: AREntry
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
class ARTestResult:
    """Result of a single AR aging test."""
    test_name: str
    test_key: str
    test_tier: TestTier
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Severity
    description: str
    flagged_entries: list[FlaggedAR] = field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None

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
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
        }


@dataclass
class TBColumnDetection:
    """Result of TB column detection."""
    account_name_column: Optional[str] = None
    account_number_column: Optional[str] = None
    balance_column: Optional[str] = None
    debit_column: Optional[str] = None
    credit_column: Optional[str] = None

    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def has_debit_credit(self) -> bool:
        return self.debit_column is not None and self.credit_column is not None

    def to_dict(self) -> dict:
        return {
            "account_name_column": self.account_name_column,
            "account_number_column": self.account_number_column,
            "balance_column": self.balance_column,
            "debit_column": self.debit_column,
            "credit_column": self.credit_column,
            "has_debit_credit": self.has_debit_credit,
            "overall_confidence": round(self.overall_confidence, 2),
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


@dataclass
class SLColumnDetection:
    """Result of sub-ledger column detection."""
    customer_name_column: Optional[str] = None
    customer_id_column: Optional[str] = None
    invoice_number_column: Optional[str] = None
    invoice_date_column: Optional[str] = None
    due_date_column: Optional[str] = None
    amount_column: Optional[str] = None
    aging_days_column: Optional[str] = None
    aging_bucket_column: Optional[str] = None
    credit_limit_column: Optional[str] = None

    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "customer_name_column": self.customer_name_column,
            "customer_id_column": self.customer_id_column,
            "invoice_number_column": self.invoice_number_column,
            "invoice_date_column": self.invoice_date_column,
            "due_date_column": self.due_date_column,
            "amount_column": self.amount_column,
            "aging_days_column": self.aging_days_column,
            "aging_bucket_column": self.aging_bucket_column,
            "credit_limit_column": self.credit_limit_column,
            "overall_confidence": round(self.overall_confidence, 2),
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


@dataclass
class ARDataQuality:
    """Quality assessment of the AR data."""
    completeness_score: float
    field_fill_rates: dict[str, float] = field(default_factory=dict)
    detected_issues: list[str] = field(default_factory=list)
    total_tb_accounts: int = 0
    total_subledger_entries: int = 0
    has_subledger: bool = False

    def to_dict(self) -> dict:
        return {
            "completeness_score": round(self.completeness_score, 1),
            "field_fill_rates": {k: round(v, 2) for k, v in self.field_fill_rates.items()},
            "detected_issues": self.detected_issues,
            "total_tb_accounts": self.total_tb_accounts,
            "total_subledger_entries": self.total_subledger_entries,
            "has_subledger": self.has_subledger,
        }


@dataclass
class ARCompositeScore:
    """Overall AR aging composite score."""
    score: float
    risk_tier: RiskTier
    tests_run: int
    tests_skipped: int
    total_flagged: int
    flags_by_severity: dict[str, int] = field(default_factory=dict)
    top_findings: list[str] = field(default_factory=list)
    has_subledger: bool = False

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "risk_tier": self.risk_tier.value,
            "tests_run": self.tests_run,
            "tests_skipped": self.tests_skipped,
            "total_flagged": self.total_flagged,
            "flags_by_severity": self.flags_by_severity,
            "top_findings": self.top_findings,
            "has_subledger": self.has_subledger,
        }


@dataclass
class ARAgingResult:
    """Complete result of AR aging analysis."""
    composite_score: ARCompositeScore
    test_results: list[ARTestResult] = field(default_factory=list)
    data_quality: Optional[ARDataQuality] = None
    tb_column_detection: Optional[TBColumnDetection] = None
    sl_column_detection: Optional[SLColumnDetection] = None
    ar_summary: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [t.to_dict() for t in self.test_results],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "tb_column_detection": self.tb_column_detection.to_dict() if self.tb_column_detection else None,
            "sl_column_detection": self.sl_column_detection.to_dict() if self.sl_column_detection else None,
            "ar_summary": self.ar_summary,
        }


# =============================================================================
# COLUMN MATCHING UTILITY
# =============================================================================

def _match_column(column_name: str, patterns: list[tuple[str, float, bool]]) -> float:
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


def _assign_best(
    scores: dict[str, dict[str, float]],
    assigned: set[str],
    field_name: str,
) -> Optional[str]:
    """Assign the best-scoring unassigned column for a field."""
    best_col = None
    best_score = 0.0
    for col, field_scores in scores.items():
        if col in assigned:
            continue
        s = field_scores.get(field_name, 0.0)
        if s > best_score:
            best_score = s
            best_col = col
    if best_col and best_score >= 0.50:
        assigned.add(best_col)
        return best_col
    return None


# =============================================================================
# TB COLUMN DETECTION
# =============================================================================

def detect_tb_columns(column_names: list[str]) -> TBColumnDetection:
    """Detect TB column roles using weighted pattern matching."""
    detection = TBColumnDetection(all_columns=list(column_names))

    scores: dict[str, dict[str, float]] = {}
    for col in column_names:
        scores[col] = {
            "account_name": _match_column(col, TB_ACCOUNT_NAME_PATTERNS),
            "account_number": _match_column(col, TB_ACCOUNT_NUMBER_PATTERNS),
            "balance": _match_column(col, TB_BALANCE_PATTERNS),
            "debit": _match_column(col, TB_DEBIT_PATTERNS),
            "credit": _match_column(col, TB_CREDIT_PATTERNS),
        }

    assigned: set[str] = set()

    # Priority: account_name > account_number > balance > debit/credit
    detection.account_name_column = _assign_best(scores, assigned, "account_name")
    detection.account_number_column = _assign_best(scores, assigned, "account_number")
    detection.balance_column = _assign_best(scores, assigned, "balance")
    detection.debit_column = _assign_best(scores, assigned, "debit")
    detection.credit_column = _assign_best(scores, assigned, "credit")

    # Calculate confidence
    required_found = 0
    if detection.account_name_column or detection.account_number_column:
        required_found += 1
    if detection.balance_column or detection.has_debit_credit:
        required_found += 1

    detection.overall_confidence = required_found / 2.0

    if not detection.account_name_column and not detection.account_number_column:
        detection.detection_notes.append("No account name/number column detected")
    if not detection.balance_column and not detection.has_debit_credit:
        detection.detection_notes.append("No balance or debit/credit columns detected")

    return detection


# =============================================================================
# SUB-LEDGER COLUMN DETECTION
# =============================================================================

def detect_sl_columns(column_names: list[str]) -> SLColumnDetection:
    """Detect sub-ledger column roles using weighted pattern matching."""
    detection = SLColumnDetection(all_columns=list(column_names))

    scores: dict[str, dict[str, float]] = {}
    for col in column_names:
        scores[col] = {
            "customer_name": _match_column(col, SL_CUSTOMER_NAME_PATTERNS),
            "customer_id": _match_column(col, SL_CUSTOMER_ID_PATTERNS),
            "invoice_number": _match_column(col, SL_INVOICE_NUMBER_PATTERNS),
            "invoice_date": _match_column(col, SL_INVOICE_DATE_PATTERNS),
            "due_date": _match_column(col, SL_DUE_DATE_PATTERNS),
            "amount": _match_column(col, SL_AMOUNT_PATTERNS),
            "aging_days": _match_column(col, SL_AGING_DAYS_PATTERNS),
            "aging_bucket": _match_column(col, SL_AGING_BUCKET_PATTERNS),
            "credit_limit": _match_column(col, SL_CREDIT_LIMIT_PATTERNS),
        }

    assigned: set[str] = set()

    # Priority: amount > customer > dates > aging > credit_limit
    detection.amount_column = _assign_best(scores, assigned, "amount")
    detection.customer_name_column = _assign_best(scores, assigned, "customer_name")
    detection.customer_id_column = _assign_best(scores, assigned, "customer_id")
    detection.invoice_number_column = _assign_best(scores, assigned, "invoice_number")
    detection.invoice_date_column = _assign_best(scores, assigned, "invoice_date")
    detection.due_date_column = _assign_best(scores, assigned, "due_date")
    detection.aging_bucket_column = _assign_best(scores, assigned, "aging_bucket")
    detection.aging_days_column = _assign_best(scores, assigned, "aging_days")
    detection.credit_limit_column = _assign_best(scores, assigned, "credit_limit")

    # Confidence based on required columns
    required = 0
    total_required = 2
    if detection.amount_column:
        required += 1
    if detection.customer_name_column or detection.customer_id_column:
        required += 1

    detection.overall_confidence = required / total_required

    if not detection.amount_column:
        detection.detection_notes.append("No amount column detected in sub-ledger")
    if not detection.customer_name_column and not detection.customer_id_column:
        detection.detection_notes.append("No customer identification column detected")

    return detection


# =============================================================================
# ACCOUNT CLASSIFICATION
# =============================================================================

def _classify_account(account_name: str) -> tuple[str, float]:
    """Classify a TB account based on name. Returns (classification, confidence)."""
    if not account_name:
        return ("other", 0.0)

    name_lower = account_name.lower().strip()

    # Check allowance first (more specific, subset of receivable keywords)
    allowance_score = _match_column(name_lower, ALLOWANCE_PATTERNS)
    ar_score = _match_column(name_lower, AR_ACCOUNT_PATTERNS)
    revenue_score = _match_column(name_lower, REVENUE_ACCOUNT_PATTERNS)

    best_class = "other"
    best_score = 0.0

    # Allowance takes priority over AR (since "Allowance for Doubtful Accounts" contains "account")
    if allowance_score > best_score:
        best_class = "allowance"
        best_score = allowance_score
    if ar_score > best_score:
        best_class = "ar"
        best_score = ar_score
    if revenue_score > best_score:
        best_class = "revenue"
        best_score = revenue_score

    return (best_class, best_score) if best_score >= 0.50 else ("other", 0.0)


# =============================================================================
# TB PARSING
# =============================================================================

def _safe_float(val) -> float:
    """Convert a value to float, returning 0.0 on failure."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    try:
        cleaned = str(val).strip().replace(",", "").replace("$", "").replace("(", "-").replace(")", "")
        return float(cleaned) if cleaned else 0.0
    except (ValueError, TypeError):
        return 0.0


def _safe_int(val) -> Optional[int]:
    """Convert a value to int, returning None on failure."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None


def parse_tb_accounts(
    rows: list[dict],
    detection: TBColumnDetection,
) -> list[TBAccount]:
    """Parse TB rows into classified account objects."""
    accounts: list[TBAccount] = []

    for i, row in enumerate(rows):
        acct_name = None
        acct_number = None
        balance = 0.0

        if detection.account_name_column:
            raw = row.get(detection.account_name_column)
            acct_name = str(raw).strip() if raw is not None else None

        if detection.account_number_column:
            raw = row.get(detection.account_number_column)
            acct_number = str(raw).strip() if raw is not None else None

        if detection.balance_column:
            balance = _safe_float(row.get(detection.balance_column))
        elif detection.has_debit_credit:
            debit = _safe_float(row.get(detection.debit_column))
            credit = _safe_float(row.get(detection.credit_column))
            balance = debit - credit

        # Skip rows with no identifying info
        if not acct_name and not acct_number:
            continue

        classification, _ = _classify_account(acct_name or "")

        accounts.append(TBAccount(
            account_name=acct_name,
            account_number=acct_number,
            balance=balance,
            classification=classification,
            row_number=i + 1,
        ))

    return accounts


# =============================================================================
# SUB-LEDGER PARSING
# =============================================================================

def _parse_date_to_str(val) -> Optional[str]:
    """Normalize a date value to string."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _compute_aging_days(due_date_str: Optional[str], reference_date_str: Optional[str] = None) -> Optional[int]:
    """Compute aging days from due date. Positive = past due."""
    if not due_date_str:
        return None
    from datetime import datetime, date
    try:
        # Try common date formats
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y"):
            try:
                due = datetime.strptime(due_date_str.strip(), fmt).date()
                break
            except ValueError:
                continue
        else:
            return None

        if reference_date_str:
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                try:
                    ref = datetime.strptime(reference_date_str.strip(), fmt).date()
                    break
                except ValueError:
                    continue
            else:
                ref = date.today()
        else:
            ref = date.today()

        return (ref - due).days
    except Exception:
        return None


def _parse_aging_bucket_to_days(bucket_str: Optional[str]) -> Optional[int]:
    """Estimate aging days from a bucket string like '31-60' or 'Over 120'."""
    if not bucket_str:
        return None
    s = bucket_str.lower().strip()

    # "current" or "0-30"
    if "current" in s or re.match(r"0\s*[-–]\s*30", s):
        return 15
    # "31-60"
    m = re.match(r"(\d+)\s*[-–]\s*(\d+)", s)
    if m:
        low, high = int(m.group(1)), int(m.group(2))
        return (low + high) // 2
    # "over 120", "120+"
    if re.search(r"over|>|\+", s):
        m2 = re.search(r"(\d+)", s)
        if m2:
            return int(m2.group(1)) + 30
    return None


def parse_sl_entries(
    rows: list[dict],
    detection: SLColumnDetection,
) -> list[ARSubledgerEntry]:
    """Parse sub-ledger rows into entry objects."""
    entries: list[ARSubledgerEntry] = []

    for i, row in enumerate(rows):
        customer_name = None
        customer_id = None
        invoice_number = None
        invoice_date = None
        due_date = None
        amount = 0.0
        aging_days = None
        aging_bucket = None
        credit_limit = None

        if detection.customer_name_column:
            raw = row.get(detection.customer_name_column)
            customer_name = str(raw).strip() if raw is not None else None

        if detection.customer_id_column:
            raw = row.get(detection.customer_id_column)
            customer_id = str(raw).strip() if raw is not None else None

        if detection.invoice_number_column:
            raw = row.get(detection.invoice_number_column)
            invoice_number = str(raw).strip() if raw is not None else None

        if detection.invoice_date_column:
            invoice_date = _parse_date_to_str(row.get(detection.invoice_date_column))

        if detection.due_date_column:
            due_date = _parse_date_to_str(row.get(detection.due_date_column))

        if detection.amount_column:
            amount = _safe_float(row.get(detection.amount_column))

        if detection.aging_days_column:
            aging_days = _safe_int(row.get(detection.aging_days_column))

        if detection.aging_bucket_column:
            raw = row.get(detection.aging_bucket_column)
            aging_bucket = str(raw).strip() if raw is not None else None

        if detection.credit_limit_column:
            raw_limit = _safe_float(row.get(detection.credit_limit_column))
            credit_limit = raw_limit if raw_limit > 0 else None

        # Compute aging_days if not provided
        if aging_days is None and due_date:
            aging_days = _compute_aging_days(due_date)
        if aging_days is None and aging_bucket:
            aging_days = _parse_aging_bucket_to_days(aging_bucket)

        # Assign bucket if not provided
        if aging_bucket is None and aging_days is not None:
            aging_bucket = classify_aging_bucket(aging_days)

        # Skip empty rows
        if amount == 0.0 and not customer_name and not customer_id:
            continue

        entries.append(ARSubledgerEntry(
            customer_name=customer_name,
            customer_id=customer_id,
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            due_date=due_date,
            amount=amount,
            aging_days=aging_days,
            aging_bucket=aging_bucket,
            credit_limit=credit_limit,
            row_number=i + 1,
        ))

    return entries


# =============================================================================
# DATA QUALITY ASSESSMENT
# =============================================================================

def assess_data_quality(
    accounts: list[TBAccount],
    sl_entries: list[ARSubledgerEntry],
    has_subledger: bool,
) -> ARDataQuality:
    """Assess quality of the provided data."""
    issues: list[str] = []
    fill_rates: dict[str, float] = {}

    # TB fill rates
    if accounts:
        n = len(accounts)
        fill_rates["account_name"] = sum(1 for a in accounts if a.account_name) / n
        fill_rates["account_number"] = sum(1 for a in accounts if a.account_number) / n

        ar_count = sum(1 for a in accounts if a.classification == "ar")
        if ar_count == 0:
            issues.append("No accounts receivable accounts detected in trial balance")

    # Sub-ledger fill rates
    if has_subledger and sl_entries:
        n = len(sl_entries)
        fill_rates["customer_name"] = sum(1 for e in sl_entries if e.customer_name) / n
        fill_rates["amount"] = sum(1 for e in sl_entries if e.amount != 0) / n
        fill_rates["aging_days"] = sum(1 for e in sl_entries if e.aging_days is not None) / n
        fill_rates["due_date"] = sum(1 for e in sl_entries if e.due_date) / n
        fill_rates["credit_limit"] = sum(1 for e in sl_entries if e.credit_limit is not None) / n

        if fill_rates.get("aging_days", 0) < 0.5 and fill_rates.get("due_date", 0) < 0.5:
            issues.append("Sub-ledger lacks aging days and due dates — aging analysis limited")

    # Completeness score
    if fill_rates:
        completeness = (sum(fill_rates.values()) / len(fill_rates)) * 100
    else:
        completeness = 0.0

    return ARDataQuality(
        completeness_score=completeness,
        field_fill_rates=fill_rates,
        detected_issues=issues,
        total_tb_accounts=len(accounts),
        total_subledger_entries=len(sl_entries),
        has_subledger=has_subledger,
    )


# =============================================================================
# HELPER: Convert TB account to AREntry
# =============================================================================

def _tb_to_entry(acct: TBAccount) -> AREntry:
    return AREntry(
        account_name=acct.account_name,
        account_number=acct.account_number,
        amount=acct.balance,
        row_number=acct.row_number,
        entry_source="tb",
    )


def _sl_to_entry(e: ARSubledgerEntry) -> AREntry:
    return AREntry(
        customer_name=e.customer_name,
        invoice_number=e.invoice_number,
        date=e.invoice_date or e.due_date,
        amount=e.amount,
        aging_days=e.aging_days,
        row_number=e.row_number,
        entry_source="subledger",
    )


# =============================================================================
# TEST BATTERY — TIER 1: STRUCTURAL
# =============================================================================

def test_ar_sign_anomalies(
    accounts: list[TBAccount],
    config: ARAgingConfig,
) -> ARTestResult:
    """T1-AR01: Flag AR accounts with credit (negative) balances."""
    ar_accounts = [a for a in accounts if a.classification == "ar"]
    flagged: list[FlaggedAR] = []

    if config.sign_anomaly_enabled:
        for acct in ar_accounts:
            # AR should have debit (positive) balance; credit = anomaly
            if acct.balance < 0:
                severity = Severity.HIGH if abs(acct.balance) > 10000 else Severity.MEDIUM
                flagged.append(FlaggedAR(
                    entry=_tb_to_entry(acct),
                    test_name="AR Balance Sign Anomalies",
                    test_key="ar_sign_anomalies",
                    test_tier=TestTier.STRUCTURAL,
                    severity=severity,
                    issue=f"AR account has credit balance of {acct.balance:,.2f} — expected debit",
                    details={"balance": acct.balance},
                ))

    total = len(ar_accounts)
    return ARTestResult(
        test_name="AR Balance Sign Anomalies",
        test_key="ar_sign_anomalies",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="AR accounts with credit balances indicating potential misclassification, overpayment, or contra-AR entries",
        flagged_entries=flagged,
    )


def test_missing_allowance(
    accounts: list[TBAccount],
    config: ARAgingConfig,
) -> ARTestResult:
    """T1-AR02: Check if an Allowance for Doubtful Accounts exists."""
    ar_accounts = [a for a in accounts if a.classification == "ar"]
    allowance_accounts = [a for a in accounts if a.classification == "allowance"]
    flagged: list[FlaggedAR] = []

    if config.missing_allowance_enabled and ar_accounts and not allowance_accounts:
        # Flag the largest AR account as the representative flag
        largest_ar = max(ar_accounts, key=lambda a: abs(a.balance))
        flagged.append(FlaggedAR(
            entry=_tb_to_entry(largest_ar),
            test_name="Missing Contra-Account",
            test_key="missing_allowance",
            test_tier=TestTier.STRUCTURAL,
            severity=Severity.HIGH,
            issue="No Allowance for Doubtful Accounts detected in trial balance — required under IFRS 9/ASC 326",
            confidence=0.90,
            details={"total_ar": sum(a.balance for a in ar_accounts)},
        ))

    total = len(ar_accounts)
    return ARTestResult(
        test_name="Missing Contra-Account",
        test_key="missing_allowance",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=1.0 if flagged else 0.0,
        severity=Severity.HIGH if flagged else Severity.LOW,
        description="Check for existence of Allowance for Doubtful Accounts (contra-AR account)",
        flagged_entries=flagged,
    )


def test_negative_aging(
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
) -> ARTestResult:
    """T1-AR03: Flag sub-ledger entries with negative aging days (date logic errors)."""
    flagged: list[FlaggedAR] = []

    if config.negative_aging_enabled:
        for e in sl_entries:
            if e.aging_days is not None and e.aging_days < 0:
                flagged.append(FlaggedAR(
                    entry=_sl_to_entry(e),
                    test_name="Negative Aging Buckets",
                    test_key="negative_aging",
                    test_tier=TestTier.STRUCTURAL,
                    severity=Severity.MEDIUM,
                    issue=f"Aging days is negative ({e.aging_days}) — due date is in the future or date logic error",
                    details={"aging_days": e.aging_days, "due_date": e.due_date},
                ))

    total = len(sl_entries)
    return ARTestResult(
        test_name="Negative Aging Buckets",
        test_key="negative_aging",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="Sub-ledger entries with negative aging days indicating date logic errors",
        flagged_entries=flagged,
    )


def test_unreconciled_detail(
    accounts: list[TBAccount],
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
) -> ARTestResult:
    """T1-AR04: Check if sub-ledger total matches TB AR balance."""
    ar_accounts = [a for a in accounts if a.classification == "ar"]
    tb_ar_total = sum(a.balance for a in ar_accounts)
    sl_total = sum(e.amount for e in sl_entries)
    flagged: list[FlaggedAR] = []

    difference = abs(tb_ar_total - sl_total)
    threshold = max(
        abs(tb_ar_total) * config.reconciliation_threshold_pct,
        config.reconciliation_threshold_abs,
    )

    if difference > threshold and tb_ar_total != 0:
        severity = Severity.HIGH if difference > abs(tb_ar_total) * 0.05 else Severity.MEDIUM
        # Flag the difference as a conceptual entry
        flagged.append(FlaggedAR(
            entry=AREntry(
                account_name="Reconciliation Difference",
                amount=tb_ar_total - sl_total,
                entry_source="reconciliation",
            ),
            test_name="Unreconciled AR Detail",
            test_key="unreconciled_detail",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Sub-ledger total ({sl_total:,.2f}) differs from TB AR balance ({tb_ar_total:,.2f}) by {difference:,.2f}",
            details={"tb_ar_total": tb_ar_total, "sl_total": sl_total, "difference": difference},
        ))

    total = len(ar_accounts) + len(sl_entries)
    return ARTestResult(
        test_name="Unreconciled AR Detail",
        test_key="unreconciled_detail",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=1.0 if flagged else 0.0,
        severity=Severity.HIGH if flagged and flagged[0].severity == Severity.HIGH else (Severity.MEDIUM if flagged else Severity.LOW),
        description="Reconciliation of sub-ledger detail to TB AR balance",
        flagged_entries=flagged,
    )


# =============================================================================
# TEST BATTERY — TIER 2: STATISTICAL
# =============================================================================

def test_bucket_concentration(
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
) -> ARTestResult:
    """T2-AR05: Flag when >60% of AR is concentrated in a single aging bucket."""
    flagged: list[FlaggedAR] = []
    total_ar = sum(e.amount for e in sl_entries)

    if total_ar <= 0:
        return ARTestResult(
            test_name="Aging Bucket Concentration",
            test_key="bucket_concentration",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0, total_entries=len(sl_entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Concentration of AR balance across aging buckets",
        )

    # Group by bucket
    bucket_totals: dict[str, float] = {}
    bucket_entries: dict[str, list[ARSubledgerEntry]] = {}
    for e in sl_entries:
        bucket = e.aging_bucket or "unknown"
        bucket_totals[bucket] = bucket_totals.get(bucket, 0.0) + e.amount
        bucket_entries.setdefault(bucket, []).append(e)

    for bucket, amount in bucket_totals.items():
        pct = amount / total_ar
        if pct > config.bucket_concentration_threshold:
            # Concentration in old buckets is worse
            is_old = bucket in ("91-120", "over_120")
            severity = Severity.HIGH if is_old else Severity.MEDIUM

            # Flag representative entries from this bucket (top 5 by amount)
            top_entries = sorted(bucket_entries[bucket], key=lambda x: abs(x.amount), reverse=True)[:5]
            for entry in top_entries:
                flagged.append(FlaggedAR(
                    entry=_sl_to_entry(entry),
                    test_name="Aging Bucket Concentration",
                    test_key="bucket_concentration",
                    test_tier=TestTier.STATISTICAL,
                    severity=severity,
                    issue=f"Bucket '{bucket}' holds {pct:.1%} of total AR ({amount:,.2f} of {total_ar:,.2f})",
                    details={"bucket": bucket, "bucket_pct": round(pct, 4), "bucket_total": amount},
                ))

    total = len(sl_entries)
    return ARTestResult(
        test_name="Aging Bucket Concentration",
        test_key="bucket_concentration",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="Concentration of AR balance across aging buckets",
        flagged_entries=flagged,
    )


def test_past_due_concentration(
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
) -> ARTestResult:
    """T2-AR06: Flag when >25% of AR is past due (>30 days)."""
    flagged: list[FlaggedAR] = []
    total_ar = sum(e.amount for e in sl_entries)

    if total_ar <= 0:
        return ARTestResult(
            test_name="Past-Due Concentration",
            test_key="past_due_concentration",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0, total_entries=len(sl_entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Concentration of AR balance in past-due categories",
        )

    past_due = [e for e in sl_entries if e.aging_days is not None and e.aging_days > config.past_due_days]
    past_due_total = sum(e.amount for e in past_due)
    past_due_pct = past_due_total / total_ar

    if past_due_pct > config.past_due_threshold_pct:
        severity = Severity.HIGH if past_due_pct > config.past_due_high_pct else Severity.MEDIUM

        # Flag top past-due entries
        top_entries = sorted(past_due, key=lambda x: abs(x.amount), reverse=True)[:10]
        for entry in top_entries:
            flagged.append(FlaggedAR(
                entry=_sl_to_entry(entry),
                test_name="Past-Due Concentration",
                test_key="past_due_concentration",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Past-due {entry.aging_days} days — {past_due_pct:.1%} of AR is past due (>{config.past_due_days} days)",
                details={"aging_days": entry.aging_days, "past_due_pct": round(past_due_pct, 4)},
            ))

    total = len(sl_entries)
    return ARTestResult(
        test_name="Past-Due Concentration",
        test_key="past_due_concentration",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="Concentration of AR balance in past-due categories",
        flagged_entries=flagged,
    )


def test_allowance_adequacy(
    accounts: list[TBAccount],
    config: ARAgingConfig,
) -> ARTestResult:
    """T2-AR07: Check if allowance/AR ratio is within reasonable range."""
    ar_accounts = [a for a in accounts if a.classification == "ar"]
    allowance_accounts = [a for a in accounts if a.classification == "allowance"]
    flagged: list[FlaggedAR] = []

    total_ar = sum(a.balance for a in ar_accounts)
    # Allowance is typically a credit (negative) balance in TB
    total_allowance = abs(sum(a.balance for a in allowance_accounts))

    if total_ar > 0 and allowance_accounts:
        ratio = total_allowance / total_ar

        if ratio < config.allowance_low_pct:
            flagged.append(FlaggedAR(
                entry=AREntry(
                    account_name="Allowance Adequacy",
                    amount=total_allowance,
                    entry_source="analysis",
                ),
                test_name="Allowance Adequacy Ratio",
                test_key="allowance_adequacy",
                test_tier=TestTier.STATISTICAL,
                severity=Severity.HIGH,
                issue=f"Allowance/AR ratio is {ratio:.2%} — below {config.allowance_low_pct:.0%} threshold (potential under-provisioning)",
                details={"ratio": round(ratio, 4), "total_ar": total_ar, "total_allowance": total_allowance},
            ))
        elif ratio > config.allowance_high_pct:
            flagged.append(FlaggedAR(
                entry=AREntry(
                    account_name="Allowance Adequacy",
                    amount=total_allowance,
                    entry_source="analysis",
                ),
                test_name="Allowance Adequacy Ratio",
                test_key="allowance_adequacy",
                test_tier=TestTier.STATISTICAL,
                severity=Severity.MEDIUM,
                issue=f"Allowance/AR ratio is {ratio:.2%} — above {config.allowance_high_pct:.0%} threshold (potential over-provisioning)",
                details={"ratio": round(ratio, 4), "total_ar": total_ar, "total_allowance": total_allowance},
            ))

    total = len(ar_accounts)
    return ARTestResult(
        test_name="Allowance Adequacy Ratio",
        test_key="allowance_adequacy",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=1.0 if flagged else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="Ratio of allowance for doubtful accounts to total AR balance",
        flagged_entries=flagged,
    )


def test_customer_concentration(
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
) -> ARTestResult:
    """T2-AR08: Flag when a single customer exceeds 20% of total AR."""
    flagged: list[FlaggedAR] = []
    total_ar = sum(e.amount for e in sl_entries)

    if total_ar <= 0:
        return ARTestResult(
            test_name="Customer Concentration",
            test_key="customer_concentration",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0, total_entries=len(sl_entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Concentration of AR balance by customer",
        )

    # Group by customer
    customer_totals: dict[str, float] = {}
    customer_entries: dict[str, list[ARSubledgerEntry]] = {}
    for e in sl_entries:
        key = e.customer_name or e.customer_id or "Unknown"
        customer_totals[key] = customer_totals.get(key, 0.0) + e.amount
        customer_entries.setdefault(key, []).append(e)

    for customer, amount in customer_totals.items():
        pct = amount / total_ar
        if pct > config.customer_concentration_threshold:
            severity = Severity.HIGH if pct > config.customer_concentration_high else Severity.MEDIUM

            # Flag representative entries
            top = sorted(customer_entries[customer], key=lambda x: abs(x.amount), reverse=True)[:3]
            for entry in top:
                flagged.append(FlaggedAR(
                    entry=_sl_to_entry(entry),
                    test_name="Customer Concentration",
                    test_key="customer_concentration",
                    test_tier=TestTier.STATISTICAL,
                    severity=severity,
                    issue=f"Customer '{customer}' holds {pct:.1%} of total AR ({amount:,.2f} of {total_ar:,.2f})",
                    details={"customer": customer, "customer_pct": round(pct, 4), "customer_total": amount},
                ))

    total = len(sl_entries)
    return ARTestResult(
        test_name="Customer Concentration",
        test_key="customer_concentration",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="Concentration of AR balance by customer",
        flagged_entries=flagged,
    )


def test_dso_trend(
    accounts: list[TBAccount],
    config: ARAgingConfig,
) -> ARTestResult:
    """T2-AR09: Check DSO trend variance against prior period."""
    ar_accounts = [a for a in accounts if a.classification == "ar"]
    revenue_accounts = [a for a in accounts if a.classification == "revenue"]
    flagged: list[FlaggedAR] = []

    total_ar = sum(a.balance for a in ar_accounts)
    # Revenue is typically credit (negative) in TB
    total_revenue = abs(sum(a.balance for a in revenue_accounts))

    current_dso = None
    if total_revenue > 0:
        current_dso = (total_ar / total_revenue) * config.days_in_period

    if current_dso is not None and config.prior_period_dso is not None and config.prior_period_dso > 0:
        change = (current_dso - config.prior_period_dso) / config.prior_period_dso

        if abs(change) > config.dso_variance_threshold:
            severity = Severity.HIGH if abs(change) > config.dso_high_threshold else Severity.MEDIUM
            direction = "increased" if change > 0 else "decreased"

            flagged.append(FlaggedAR(
                entry=AREntry(
                    account_name="DSO Trend Analysis",
                    amount=total_ar,
                    entry_source="analysis",
                ),
                test_name="DSO Trend Variance",
                test_key="dso_trend",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"DSO {direction} {abs(change):.1%}: current {current_dso:.1f} days vs prior {config.prior_period_dso:.1f} days",
                details={
                    "current_dso": round(current_dso, 1),
                    "prior_dso": config.prior_period_dso,
                    "change_pct": round(change, 4),
                    "total_ar": total_ar,
                    "total_revenue": total_revenue,
                },
            ))

    total = len(ar_accounts)
    return ARTestResult(
        test_name="DSO Trend Variance",
        test_key="dso_trend",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=1.0 if flagged else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="Days Sales Outstanding trend analysis vs prior period",
        flagged_entries=flagged,
        skipped=config.prior_period_dso is None,
        skip_reason="No prior period DSO provided" if config.prior_period_dso is None else None,
    )


# =============================================================================
# TEST BATTERY — TIER 3: ADVANCED
# =============================================================================

def test_rollforward_reconciliation(
    accounts: list[TBAccount],
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
) -> ARTestResult:
    """T3-AR10: Validate AR roll-forward (beginning + sales - collections ≈ ending)."""
    ar_accounts = [a for a in accounts if a.classification == "ar"]
    revenue_accounts = [a for a in accounts if a.classification == "revenue"]
    flagged: list[FlaggedAR] = []

    ending_ar = sum(a.balance for a in ar_accounts)
    total_revenue = abs(sum(a.balance for a in revenue_accounts))

    if config.beginning_ar_balance is not None and config.collections_total is not None:
        expected_ending = config.beginning_ar_balance + total_revenue - config.collections_total
        difference = abs(ending_ar - expected_ending)
        threshold = max(abs(ending_ar) * config.rollforward_threshold_pct, 100.0)

        if difference > threshold:
            severity = Severity.HIGH if difference > abs(ending_ar) * 0.10 else Severity.MEDIUM
            flagged.append(FlaggedAR(
                entry=AREntry(
                    account_name="Roll-Forward Reconciliation",
                    amount=difference,
                    entry_source="analysis",
                ),
                test_name="Roll-Forward Reconciliation",
                test_key="rollforward_reconciliation",
                test_tier=TestTier.ADVANCED,
                severity=severity,
                issue=(
                    f"Roll-forward difference: {difference:,.2f}. "
                    f"Beginning ({config.beginning_ar_balance:,.2f}) + Revenue ({total_revenue:,.2f}) "
                    f"- Collections ({config.collections_total:,.2f}) = {expected_ending:,.2f} "
                    f"vs Ending AR ({ending_ar:,.2f})"
                ),
                details={
                    "beginning_ar": config.beginning_ar_balance,
                    "revenue": total_revenue,
                    "collections": config.collections_total,
                    "expected_ending": expected_ending,
                    "actual_ending": ending_ar,
                    "difference": difference,
                },
            ))

    skipped = config.beginning_ar_balance is None or config.collections_total is None
    total = len(ar_accounts)
    return ARTestResult(
        test_name="Roll-Forward Reconciliation",
        test_key="rollforward_reconciliation",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=1.0 if flagged else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="AR roll-forward: beginning balance + sales - collections = ending balance",
        flagged_entries=flagged,
        skipped=skipped,
        skip_reason="Beginning AR balance or collections total not provided" if skipped else None,
    )


def test_credit_limit_breaches(
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
) -> ARTestResult:
    """T3-AR11: Flag customers whose total AR exceeds their credit limit."""
    flagged: list[FlaggedAR] = []

    if not config.credit_limit_enabled:
        return ARTestResult(
            test_name="Credit Limit Breaches",
            test_key="credit_limit_breaches",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(sl_entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Customer AR balances exceeding approved credit limits",
            skipped=True,
            skip_reason="Credit limit testing disabled",
        )

    # Group by customer and check limits
    customer_totals: dict[str, float] = {}
    customer_limits: dict[str, float] = {}
    customer_entries: dict[str, list[ARSubledgerEntry]] = {}

    for e in sl_entries:
        key = e.customer_name or e.customer_id or "Unknown"
        customer_totals[key] = customer_totals.get(key, 0.0) + e.amount
        customer_entries.setdefault(key, []).append(e)
        if e.credit_limit is not None:
            customer_limits[key] = e.credit_limit

    if not customer_limits:
        return ARTestResult(
            test_name="Credit Limit Breaches",
            test_key="credit_limit_breaches",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0, total_entries=len(sl_entries),
            flag_rate=0.0, severity=Severity.LOW,
            description="Customer AR balances exceeding approved credit limits",
            skipped=True,
            skip_reason="No credit limit data in sub-ledger",
        )

    for customer, total in customer_totals.items():
        limit = customer_limits.get(customer)
        if limit is None or limit <= 0:
            continue
        if total > limit:
            ratio = total / limit
            severity = Severity.HIGH if ratio > config.credit_limit_high_pct else Severity.MEDIUM

            top = sorted(customer_entries[customer], key=lambda x: abs(x.amount), reverse=True)[:3]
            for entry in top:
                flagged.append(FlaggedAR(
                    entry=_sl_to_entry(entry),
                    test_name="Credit Limit Breaches",
                    test_key="credit_limit_breaches",
                    test_tier=TestTier.ADVANCED,
                    severity=severity,
                    issue=f"Customer '{customer}' AR ({total:,.2f}) exceeds credit limit ({limit:,.2f}) — {ratio:.0%} utilized",
                    details={"customer": customer, "total_ar": total, "credit_limit": limit, "utilization": round(ratio, 2)},
                ))

    total = len(sl_entries)
    return ARTestResult(
        test_name="Credit Limit Breaches",
        test_key="credit_limit_breaches",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=total,
        flag_rate=len(flagged) / total if total > 0 else 0.0,
        severity=max((f.severity for f in flagged), default=Severity.LOW, key=lambda s: SEVERITY_WEIGHTS[s]),
        description="Customer AR balances exceeding approved credit limits",
        flagged_entries=flagged,
    )


# =============================================================================
# SKIPPED TEST RESULT FACTORY
# =============================================================================

def _skipped_result(
    test_name: str,
    test_key: str,
    test_tier: TestTier,
    description: str,
    reason: str,
) -> ARTestResult:
    """Create a skipped test result when sub-ledger is not provided."""
    return ARTestResult(
        test_name=test_name,
        test_key=test_key,
        test_tier=test_tier,
        entries_flagged=0,
        total_entries=0,
        flag_rate=0.0,
        severity=Severity.LOW,
        description=description,
        skipped=True,
        skip_reason=reason,
    )


# =============================================================================
# TEST BATTERY ORCHESTRATOR
# =============================================================================

def run_ar_test_battery(
    accounts: list[TBAccount],
    sl_entries: list[ARSubledgerEntry],
    config: ARAgingConfig,
    has_subledger: bool,
) -> list[ARTestResult]:
    """Run the full 11-test AR aging battery."""
    results: list[ARTestResult] = []

    # T1 — Structural (always run AR01, AR02; sub-ledger for AR03, AR04)
    results.append(test_ar_sign_anomalies(accounts, config))
    results.append(test_missing_allowance(accounts, config))

    if has_subledger:
        results.append(test_negative_aging(sl_entries, config))
        results.append(test_unreconciled_detail(accounts, sl_entries, config))
    else:
        results.append(_skipped_result(
            "Negative Aging Buckets", "negative_aging", TestTier.STRUCTURAL,
            "Sub-ledger entries with negative aging days", "Requires sub-ledger file",
        ))
        results.append(_skipped_result(
            "Unreconciled AR Detail", "unreconciled_detail", TestTier.STRUCTURAL,
            "Reconciliation of sub-ledger to TB", "Requires sub-ledger file",
        ))

    # T2 — Statistical (AR05, AR06, AR08 need sub-ledger; AR07, AR09 are TB-only)
    if has_subledger:
        results.append(test_bucket_concentration(sl_entries, config))
        results.append(test_past_due_concentration(sl_entries, config))
    else:
        results.append(_skipped_result(
            "Aging Bucket Concentration", "bucket_concentration", TestTier.STATISTICAL,
            "Concentration of AR balance across aging buckets", "Requires sub-ledger file",
        ))
        results.append(_skipped_result(
            "Past-Due Concentration", "past_due_concentration", TestTier.STATISTICAL,
            "Concentration of AR balance in past-due categories", "Requires sub-ledger file",
        ))

    results.append(test_allowance_adequacy(accounts, config))

    if has_subledger:
        results.append(test_customer_concentration(sl_entries, config))
    else:
        results.append(_skipped_result(
            "Customer Concentration", "customer_concentration", TestTier.STATISTICAL,
            "Concentration of AR balance by customer", "Requires sub-ledger file",
        ))

    results.append(test_dso_trend(accounts, config))

    # T3 — Advanced (AR10, AR11 need sub-ledger)
    if has_subledger:
        results.append(test_rollforward_reconciliation(accounts, sl_entries, config))
        results.append(test_credit_limit_breaches(sl_entries, config))
    else:
        results.append(_skipped_result(
            "Roll-Forward Reconciliation", "rollforward_reconciliation", TestTier.ADVANCED,
            "AR roll-forward reconciliation", "Requires sub-ledger file",
        ))
        results.append(_skipped_result(
            "Credit Limit Breaches", "credit_limit_breaches", TestTier.ADVANCED,
            "Customer credit limit breach detection", "Requires sub-ledger file",
        ))

    return results


# =============================================================================
# AR SUMMARY
# =============================================================================

def build_ar_summary(
    accounts: list[TBAccount],
    sl_entries: list[ARSubledgerEntry],
    has_subledger: bool,
) -> dict:
    """Build a summary of the AR data for the response."""
    ar_accounts = [a for a in accounts if a.classification == "ar"]
    allowance_accounts = [a for a in accounts if a.classification == "allowance"]
    revenue_accounts = [a for a in accounts if a.classification == "revenue"]

    total_ar = sum(a.balance for a in ar_accounts)
    total_allowance = abs(sum(a.balance for a in allowance_accounts))
    total_revenue = abs(sum(a.balance for a in revenue_accounts))

    summary: dict = {
        "total_ar_balance": round(total_ar, 2),
        "ar_account_count": len(ar_accounts),
        "total_allowance": round(total_allowance, 2),
        "allowance_account_count": len(allowance_accounts),
        "total_revenue": round(total_revenue, 2),
        "has_subledger": has_subledger,
    }

    if total_revenue > 0:
        summary["dso"] = round((total_ar / total_revenue) * 365, 1)

    if total_ar > 0 and total_allowance > 0:
        summary["allowance_ratio"] = round(total_allowance / total_ar, 4)

    if has_subledger and sl_entries:
        summary["subledger_entry_count"] = len(sl_entries)
        summary["subledger_total"] = round(sum(e.amount for e in sl_entries), 2)

        # Aging distribution
        bucket_dist: dict[str, float] = {}
        for e in sl_entries:
            bucket = e.aging_bucket or "unknown"
            bucket_dist[bucket] = bucket_dist.get(bucket, 0.0) + e.amount
        summary["aging_distribution"] = {k: round(v, 2) for k, v in sorted(bucket_dist.items())}

        # Customer count
        customers = set()
        for e in sl_entries:
            key = e.customer_name or e.customer_id
            if key:
                customers.add(key)
        summary["unique_customers"] = len(customers)

    return summary


# =============================================================================
# COMPOSITE SCORING
# =============================================================================

def score_to_risk_tier(score: float) -> RiskTier:
    """Map numeric score to risk tier."""
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


def calculate_ar_composite_score(
    test_results: list[ARTestResult],
    has_subledger: bool,
) -> ARCompositeScore:
    """Calculate composite score from test results."""
    # Only score non-skipped tests
    active_results = [r for r in test_results if not r.skipped]

    if not active_results:
        return ARCompositeScore(
            score=0.0,
            risk_tier=RiskTier.LOW,
            tests_run=0,
            tests_skipped=len(test_results),
            total_flagged=0,
            has_subledger=has_subledger,
        )

    # Count flags by severity
    flags_by_severity: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    total_flagged = 0
    entry_test_counts: dict[int, int] = {}

    for tr in active_results:
        for fp in tr.flagged_entries:
            flags_by_severity[fp.severity.value] = flags_by_severity.get(fp.severity.value, 0) + 1
            total_flagged += 1
            row = fp.entry.row_number
            if row > 0:
                entry_test_counts[row] = entry_test_counts.get(row, 0) + 1

    # Weighted base score
    weighted_sum = 0.0
    for tr in active_results:
        weight = SEVERITY_WEIGHTS.get(tr.severity, 1.0)
        weighted_sum += tr.flag_rate * weight

    max_possible = sum(SEVERITY_WEIGHTS.get(tr.severity, 1.0) for tr in active_results)
    base_score = (weighted_sum / max_possible) * 100 if max_possible > 0 else 0.0

    # Multi-flag multiplier
    multi_flag_count = sum(1 for c in entry_test_counts.values() if c >= 2)
    total_entries = max(sum(tr.total_entries for tr in active_results), 1)
    multi_flag_ratio = multi_flag_count / total_entries
    multiplier = 1.0 + (multi_flag_ratio * 0.25)

    score = min(base_score * multiplier, 100.0)

    # Top findings
    top_findings: list[str] = []
    for tr in sorted(active_results, key=lambda r: r.entries_flagged, reverse=True):
        if tr.entries_flagged > 0 and len(top_findings) < 5:
            top_findings.append(f"{tr.test_name}: {tr.entries_flagged} flagged")

    skipped_count = sum(1 for r in test_results if r.skipped)

    return ARCompositeScore(
        score=score,
        risk_tier=score_to_risk_tier(score),
        tests_run=len(active_results),
        tests_skipped=skipped_count,
        total_flagged=total_flagged,
        flags_by_severity=flags_by_severity,
        top_findings=top_findings,
        has_subledger=has_subledger,
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_ar_aging(
    tb_rows: list[dict],
    tb_columns: list[str],
    sl_rows: Optional[list[dict]] = None,
    sl_columns: Optional[list[str]] = None,
    config: Optional[ARAgingConfig] = None,
    tb_column_mapping: Optional[dict] = None,
    sl_column_mapping: Optional[dict] = None,
) -> ARAgingResult:
    """Run the complete AR aging analysis pipeline.

    Args:
        tb_rows: Trial balance data rows (required).
        tb_columns: TB column names.
        sl_rows: Sub-ledger data rows (optional).
        sl_columns: Sub-ledger column names.
        config: Test configuration overrides.
        tb_column_mapping: Manual TB column mapping.
        sl_column_mapping: Manual sub-ledger column mapping.

    Returns:
        ARAgingResult with composite score, test results, and data quality.
    """
    if config is None:
        config = ARAgingConfig()

    # 1. Detect TB columns
    tb_detection = detect_tb_columns(tb_columns)
    if tb_column_mapping:
        for attr in ("account_name_column", "account_number_column", "balance_column",
                      "debit_column", "credit_column"):
            if attr in tb_column_mapping:
                setattr(tb_detection, attr, tb_column_mapping[attr])
        tb_detection.overall_confidence = 1.0

    # 2. Parse and classify TB accounts
    accounts = parse_tb_accounts(tb_rows, tb_detection)

    # 3. Parse sub-ledger (if provided)
    has_subledger = sl_rows is not None and len(sl_rows) > 0
    sl_detection = None
    sl_entries: list[ARSubledgerEntry] = []

    if has_subledger:
        sl_detection = detect_sl_columns(sl_columns or [])
        if sl_column_mapping:
            for attr in ("customer_name_column", "customer_id_column", "invoice_number_column",
                          "invoice_date_column", "due_date_column", "amount_column",
                          "aging_days_column", "aging_bucket_column", "credit_limit_column"):
                if attr in sl_column_mapping:
                    setattr(sl_detection, attr, sl_column_mapping[attr])
            sl_detection.overall_confidence = 1.0

        sl_entries = parse_sl_entries(sl_rows, sl_detection)

    # 4. Assess data quality
    data_quality = assess_data_quality(accounts, sl_entries, has_subledger)

    # 5. Run test battery
    test_results = run_ar_test_battery(accounts, sl_entries, config, has_subledger)

    # 6. Build AR summary
    ar_summary = build_ar_summary(accounts, sl_entries, has_subledger)

    # 7. Calculate composite score
    composite = calculate_ar_composite_score(test_results, has_subledger)

    return ARAgingResult(
        composite_score=composite,
        test_results=test_results,
        data_quality=data_quality,
        tb_column_detection=tb_detection,
        sl_column_detection=sl_detection,
        ar_summary=ar_summary,
    )
