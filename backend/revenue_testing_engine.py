"""
Revenue Testing Engine — Sprint 104

Automated revenue recognition testing addressing ISA 240 presumed fraud risk.
Parses revenue GL extracts (CSV/Excel), detects columns, runs 12 tests
across structural, statistical, and advanced tiers.

ZERO-STORAGE COMPLIANCE:
- All files processed in-memory only
- Test results are ephemeral (computed on demand)
- No raw revenue data is stored

Audit Standards References:
- ISA 240: Auditor's Responsibilities Relating to Fraud
  (presumed fraud risk in revenue recognition)
- ISA 500: Audit Evidence
- PCAOB AS 2401: Consideration of Fraud
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, date
import math
import statistics
from collections import Counter

from shared.testing_enums import RiskTier, TestTier, Severity, SEVERITY_WEIGHTS
from shared.testing_enums import score_to_risk_tier  # noqa: F401 — re-export for backward compat
from shared.round_amounts import ROUND_AMOUNT_PATTERNS_4TIER
from shared.parsing_helpers import safe_float, safe_str, parse_date
from shared.column_detector import ColumnFieldConfig, detect_columns
from shared.data_quality import FieldQualityConfig, assess_data_quality as _shared_assess_dq
from shared.test_aggregator import calculate_composite_score as _shared_calc_cs


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class RevenueTestingConfig:
    """Configurable thresholds for all revenue tests."""
    # RT-01: Large manual entries
    large_entry_threshold: float = 50000.0

    # RT-02: Year-end concentration
    year_end_days: int = 7
    year_end_concentration_pct: float = 0.20

    # RT-03: Round amounts
    round_amount_threshold: float = 10000.0
    round_amount_max_flags: int = 50

    # RT-04: Sign anomalies (debit balances in revenue)
    sign_anomaly_enabled: bool = True

    # RT-05: Unclassified entries
    unclassified_enabled: bool = True

    # RT-06: Z-score outliers
    zscore_threshold: float = 2.5
    zscore_min_entries: int = 10

    # RT-07: Revenue trend variance (requires prior_period_total)
    trend_variance_pct: float = 0.30
    prior_period_total: Optional[float] = None

    # RT-08: Concentration risk
    concentration_threshold_pct: float = 0.50

    # RT-09: Cut-off risk (entries near period boundaries)
    cutoff_days: int = 3
    period_start: Optional[str] = None
    period_end: Optional[str] = None

    # RT-10: Benford's Law
    benford_min_entries: int = 50
    benford_chi_sq_threshold: float = 15.507  # df=8, alpha=0.05

    # RT-11: Duplicate entries
    duplicate_enabled: bool = True

    # RT-12: Contra-revenue anomalies
    contra_threshold_pct: float = 0.15
    contra_keywords: list[str] = field(default_factory=lambda: [
        "return", "refund", "allowance", "discount", "rebate",
        "credit memo", "credit note", "reversal", "write-off",
        "write off", "contra", "adjustment",
    ])


# =============================================================================
# REVENUE COLUMN DETECTION
# =============================================================================

REVENUE_DATE_PATTERNS = [
    (r"^date$", 0.90, True),
    (r"^entry\s*date$", 1.0, True),
    (r"^posting\s*date$", 0.98, True),
    (r"^transaction\s*date$", 0.95, True),
    (r"^effective\s*date$", 0.90, True),
    (r"^gl\s*date$", 0.90, True),
    (r"^journal\s*date$", 0.85, True),
    (r"^period\s*date$", 0.80, True),
    (r"date", 0.55, False),
]

REVENUE_AMOUNT_PATTERNS = [
    (r"^amount$", 0.95, True),
    (r"^credit$", 0.90, True),
    (r"^revenue\s*amount$", 1.0, True),
    (r"^net\s*amount$", 0.90, True),
    (r"^gross\s*amount$", 0.85, True),
    (r"^total\s*amount$", 0.85, True),
    (r"^debit$", 0.70, True),
    (r"^balance$", 0.65, True),
    (r"amount", 0.55, False),
]

REVENUE_ACCOUNT_NAME_PATTERNS = [
    (r"^account\s*name$", 1.0, True),
    (r"^account\s*description$", 0.95, True),
    (r"^gl\s*account\s*name$", 0.95, True),
    (r"^account$", 0.80, True),
    (r"^revenue\s*account$", 0.90, True),
    (r"^revenue\s*category$", 0.85, True),
    (r"^revenue\s*type$", 0.80, True),
    (r"account.?name", 0.70, False),
    (r"account.?desc", 0.65, False),
]

REVENUE_ACCOUNT_NUMBER_PATTERNS = [
    (r"^account\s*number$", 1.0, True),
    (r"^account\s*no$", 0.98, True),
    (r"^account\s*#$", 0.95, True),
    (r"^account\s*code$", 0.95, True),
    (r"^gl\s*account$", 0.90, True),
    (r"^gl\s*code$", 0.90, True),
    (r"^gl\s*account\s*number$", 0.95, True),
    (r"account.?num", 0.65, False),
    (r"account.?code", 0.60, False),
]

REVENUE_DESCRIPTION_PATTERNS = [
    (r"^description$", 1.0, True),
    (r"^memo$", 0.90, True),
    (r"^narration$", 0.90, True),
    (r"^narrative$", 0.85, True),
    (r"^line\s*description$", 0.90, True),
    (r"^journal\s*description$", 0.90, True),
    (r"^comment$", 0.75, True),
    (r"^remarks$", 0.75, True),
    (r"description", 0.60, False),
    (r"memo", 0.55, False),
]

REVENUE_ENTRY_TYPE_PATTERNS = [
    (r"^entry\s*type$", 1.0, True),
    (r"^source$", 0.85, True),
    (r"^source\s*type$", 0.90, True),
    (r"^journal\s*type$", 0.90, True),
    (r"^type$", 0.70, True),
    (r"^manual\s*auto$", 0.85, True),
    (r"^origin$", 0.75, True),
    (r"entry.?type", 0.65, False),
    (r"source", 0.50, False),
]

REVENUE_REFERENCE_PATTERNS = [
    (r"^reference$", 0.95, True),
    (r"^reference\s*number$", 1.0, True),
    (r"^ref\s*no$", 0.95, True),
    (r"^journal\s*number$", 0.90, True),
    (r"^journal\s*no$", 0.90, True),
    (r"^document\s*number$", 0.85, True),
    (r"^doc\s*no$", 0.80, True),
    (r"^invoice\s*number$", 0.75, True),
    (r"reference", 0.55, False),
]

REVENUE_POSTED_BY_PATTERNS = [
    (r"^posted\s*by$", 1.0, True),
    (r"^entered\s*by$", 0.98, True),
    (r"^created\s*by$", 0.95, True),
    (r"^user$", 0.75, True),
    (r"^user\s*id$", 0.80, True),
    (r"^preparer$", 0.85, True),
    (r"posted.?by", 0.70, False),
    (r"entered.?by", 0.65, False),
]

# Shared column detector configs (replaces RevenueColumnType + _COLUMN_PATTERNS)
REVENUE_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig("account_number_column", REVENUE_ACCOUNT_NUMBER_PATTERNS, priority=10),
    ColumnFieldConfig("account_name_column", REVENUE_ACCOUNT_NAME_PATTERNS, priority=15),
    ColumnFieldConfig("date_column", REVENUE_DATE_PATTERNS, required=True,
                      missing_note="Could not identify a Date column", priority=20),
    ColumnFieldConfig("amount_column", REVENUE_AMOUNT_PATTERNS, required=True,
                      missing_note="Could not identify an Amount column", priority=30),
    ColumnFieldConfig("description_column", REVENUE_DESCRIPTION_PATTERNS, priority=40),
    ColumnFieldConfig("entry_type_column", REVENUE_ENTRY_TYPE_PATTERNS, priority=50),
    ColumnFieldConfig("reference_column", REVENUE_REFERENCE_PATTERNS, priority=55),
    ColumnFieldConfig("posted_by_column", REVENUE_POSTED_BY_PATTERNS, priority=60),
]


@dataclass
class RevenueColumnDetection:
    """Result of revenue column detection."""
    date_column: Optional[str] = None
    amount_column: Optional[str] = None
    account_name_column: Optional[str] = None
    account_number_column: Optional[str] = None
    description_column: Optional[str] = None
    entry_type_column: Optional[str] = None
    reference_column: Optional[str] = None
    posted_by_column: Optional[str] = None

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
            "account_name_column": self.account_name_column,
            "account_number_column": self.account_number_column,
            "description_column": self.description_column,
            "entry_type_column": self.entry_type_column,
            "reference_column": self.reference_column,
            "posted_by_column": self.posted_by_column,
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


def detect_revenue_columns(column_names: list[str]) -> RevenueColumnDetection:
    """Detect revenue GL columns using shared column detector."""
    detection = detect_columns(column_names, REVENUE_COLUMN_CONFIGS)
    result = RevenueColumnDetection(all_columns=detection.all_columns)

    # Map shared detection results to revenue-specific fields
    result.account_number_column = detection.get_column("account_number_column")
    result.account_name_column = detection.get_column("account_name_column")
    result.date_column = detection.get_column("date_column")
    result.amount_column = detection.get_column("amount_column")
    result.description_column = detection.get_column("description_column")
    result.entry_type_column = detection.get_column("entry_type_column")
    result.reference_column = detection.get_column("reference_column")
    result.posted_by_column = detection.get_column("posted_by_column")

    notes = list(detection.detection_notes)

    # Confidence: min of required columns (date, amount, account identifier)
    required_confs = [
        detection.get_confidence("date_column") if result.date_column else 0.0,
        detection.get_confidence("amount_column") if result.amount_column else 0.0,
    ]
    acct_conf = max(
        detection.get_confidence("account_number_column") if result.account_number_column else 0.0,
        detection.get_confidence("account_name_column") if result.account_name_column else 0.0,
    )
    if acct_conf == 0.0:
        notes.append("Could not identify an Account column")
    required_confs.append(acct_conf)

    result.overall_confidence = min(required_confs) if required_confs else 0.0
    result.detection_notes = notes
    return result


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class RevenueEntry:
    """A single line from the revenue GL extract."""
    date: Optional[str] = None
    amount: float = 0.0
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    description: Optional[str] = None
    entry_type: Optional[str] = None
    reference: Optional[str] = None
    posted_by: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "amount": self.amount,
            "account_name": self.account_name,
            "account_number": self.account_number,
            "description": self.description,
            "entry_type": self.entry_type,
            "reference": self.reference,
            "posted_by": self.posted_by,
            "row_number": self.row_number,
        }


@dataclass
class FlaggedRevenue:
    """A revenue entry flagged by a test."""
    entry: RevenueEntry
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
class RevenueTestResult:
    """Result of a single revenue test."""
    test_name: str
    test_key: str
    test_tier: TestTier
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Severity
    description: str
    flagged_entries: list[FlaggedRevenue] = field(default_factory=list)

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
class RevenueDataQuality:
    """Quality assessment of the revenue data."""
    completeness_score: float
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
class RevenueCompositeScore:
    """Overall revenue testing composite score."""
    score: float
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
class RevenueTestingResult:
    """Complete result of revenue testing."""
    composite_score: RevenueCompositeScore
    test_results: list[RevenueTestResult] = field(default_factory=list)
    data_quality: Optional[RevenueDataQuality] = None
    column_detection: Optional[RevenueColumnDetection] = None

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [t.to_dict() for t in self.test_results],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "column_detection": self.column_detection.to_dict() if self.column_detection else None,
        }




def _is_manual_entry(entry_type: Optional[str]) -> bool:
    """Check if an entry type string indicates a manual entry."""
    if not entry_type:
        return False
    lower = entry_type.lower().strip()
    return lower in ("manual", "man", "m", "manual entry", "manual je", "user")


def _is_contra_revenue(desc: Optional[str], account_name: Optional[str], keywords: list[str]) -> bool:
    """Check if an entry represents contra-revenue (returns, allowances, etc.)."""
    text = ((desc or "") + " " + (account_name or "")).lower()
    return any(kw in text for kw in keywords)


# =============================================================================
# PARSER
# =============================================================================

def parse_revenue_entries(
    rows: list[dict],
    detection: RevenueColumnDetection,
) -> list[RevenueEntry]:
    """Parse raw rows into RevenueEntry objects using detected columns."""
    entries: list[RevenueEntry] = []
    for idx, row in enumerate(rows):
        entry = RevenueEntry(row_number=idx + 1)
        if detection.date_column:
            entry.date = safe_str(row.get(detection.date_column))
        if detection.amount_column:
            entry.amount = safe_float(row.get(detection.amount_column))
        if detection.account_name_column:
            entry.account_name = safe_str(row.get(detection.account_name_column))
        if detection.account_number_column:
            entry.account_number = safe_str(row.get(detection.account_number_column))
        if detection.description_column:
            entry.description = safe_str(row.get(detection.description_column))
        if detection.entry_type_column:
            entry.entry_type = safe_str(row.get(detection.entry_type_column))
        if detection.reference_column:
            entry.reference = safe_str(row.get(detection.reference_column))
        if detection.posted_by_column:
            entry.posted_by = safe_str(row.get(detection.posted_by_column))
        entries.append(entry)
    return entries


# =============================================================================
# DATA QUALITY
# =============================================================================

def assess_revenue_data_quality(
    entries: list[RevenueEntry],
    detection: RevenueColumnDetection,
) -> RevenueDataQuality:
    """Assess quality and completeness of revenue data.

    Delegates to shared data quality engine (Sprint 152).
    """
    configs: list[FieldQualityConfig] = [
        FieldQualityConfig("date", lambda e: e.date, weight=0.30,
                           issue_threshold=0.95, issue_template="Missing date on {unfilled} entries"),
        FieldQualityConfig("amount", lambda e: e.amount != 0, weight=0.35,
                           issue_threshold=0.90, issue_template="{unfilled} entries have zero amount"),
        FieldQualityConfig("account", lambda e: e.account_name or e.account_number, weight=0.25,
                           issue_threshold=0.90, issue_template="Missing account on {unfilled} entries"),
    ]

    if detection.description_column:
        configs.append(FieldQualityConfig("description", lambda e: e.description,
                                          issue_threshold=0.80,
                                          issue_template="Low description fill rate: {fill_pct}"))
    if detection.entry_type_column:
        configs.append(FieldQualityConfig("entry_type", lambda e: e.entry_type))

    result = _shared_assess_dq(entries, configs, optional_weight_pool=0.10)

    return RevenueDataQuality(
        completeness_score=result.completeness_score,
        field_fill_rates=result.field_fill_rates,
        detected_issues=result.detected_issues,
        total_rows=result.total_rows,
    )


# score_to_risk_tier is imported from shared.testing_enums (Sprint 152)


# =============================================================================
# TIER 1 — STRUCTURAL TESTS
# =============================================================================

def test_large_manual_entries(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-01: Large Manual Revenue Entries.

    Flags manual entries exceeding the performance materiality threshold.
    If no entry_type column, all entries above threshold are flagged as LOW.
    """
    flagged: list[FlaggedRevenue] = []

    for e in entries:
        amt = abs(e.amount)
        if amt < config.large_entry_threshold:
            continue

        is_manual = _is_manual_entry(e.entry_type)
        if is_manual:
            severity = Severity.HIGH if amt > config.large_entry_threshold * 2 else Severity.MEDIUM
            confidence = 0.90
        elif e.entry_type is None:
            severity = Severity.LOW
            confidence = 0.60
        else:
            continue

        flagged.append(FlaggedRevenue(
            entry=e,
            test_name="Large Manual Revenue Entries",
            test_key="large_manual_entries",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"{'Manual' if is_manual else 'Unknown source'} revenue entry: ${amt:,.2f}"
                  + (f" by {e.posted_by}" if e.posted_by else ""),
            confidence=confidence,
            details={"amount": amt, "is_manual": is_manual, "entry_type": e.entry_type},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Large Manual Revenue Entries",
        test_key="large_manual_entries",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags manual revenue entries exceeding performance materiality threshold (ISA 240 fraud risk).",
        flagged_entries=flagged,
    )


def test_year_end_concentration(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-02: Year-End Revenue Concentration.

    Flags if >20% of period revenue is recorded in the last 7 days.
    """
    dates = [(e, parse_date(e.date)) for e in entries]
    dated = [(e, d) for e, d in dates if d is not None]

    if len(dated) < 2:
        return RevenueTestResult(
            test_name="Year-End Revenue Concentration",
            test_key="year_end_concentration",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Insufficient dated entries for year-end concentration analysis.",
            flagged_entries=[],
        )

    # Use the last date in the data as period end
    max_date = max(d for _, d in dated)
    cutoff_date = date(max_date.year, max_date.month, max_date.day)

    from datetime import timedelta
    boundary = cutoff_date - timedelta(days=config.year_end_days)

    total_revenue = sum(abs(e.amount) for e, d in dated)
    if total_revenue == 0:
        return RevenueTestResult(
            test_name="Year-End Revenue Concentration",
            test_key="year_end_concentration",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Zero total revenue — concentration analysis not applicable.",
            flagged_entries=[],
        )

    last_week_entries = [(e, d) for e, d in dated if d > boundary]
    last_week_revenue = sum(abs(e.amount) for e, d in last_week_entries)
    concentration_pct = last_week_revenue / total_revenue

    flagged: list[FlaggedRevenue] = []
    if concentration_pct > config.year_end_concentration_pct:
        severity = Severity.HIGH if concentration_pct > 0.40 else Severity.MEDIUM
        for e, d in last_week_entries:
            flagged.append(FlaggedRevenue(
                entry=e,
                test_name="Year-End Revenue Concentration",
                test_key="year_end_concentration",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Revenue entry in last {config.year_end_days} days: ${abs(e.amount):,.2f} on {e.date}"
                      f" ({concentration_pct:.1%} of period total in last week)",
                confidence=0.80,
                details={
                    "concentration_pct": round(concentration_pct, 4),
                    "last_week_revenue": round(last_week_revenue, 2),
                    "total_revenue": round(total_revenue, 2),
                    "boundary_date": str(boundary),
                },
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Year-End Revenue Concentration",
        test_key="year_end_concentration",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags revenue concentrated in the last {config.year_end_days} days (>{config.year_end_concentration_pct:.0%} threshold).",
        flagged_entries=flagged,
    )


def test_round_revenue_amounts(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-03: Round Amount Revenue Entries."""
    flagged: list[FlaggedRevenue] = []

    for e in entries:
        amt = abs(e.amount)
        if amt < config.round_amount_threshold:
            continue

        for divisor, name, severity in ROUND_AMOUNT_PATTERNS_4TIER:
            if amt >= divisor and amt % divisor == 0:
                flagged.append(FlaggedRevenue(
                    entry=e,
                    test_name="Round Revenue Amounts",
                    test_key="round_revenue_amounts",
                    test_tier=TestTier.STRUCTURAL,
                    severity=severity,
                    issue=f"Round amount: ${amt:,.0f} (divisible by ${divisor:,.0f})",
                    confidence=0.70,
                    details={"amount": amt, "pattern": name, "divisor": divisor},
                ))
                break

        if len(flagged) >= config.round_amount_max_flags:
            break

    flagged.sort(key=lambda f: abs(f.entry.amount), reverse=True)

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Round Revenue Amounts",
        test_key="round_revenue_amounts",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.LOW,
        description="Flags revenue entries at round dollar amounts that may indicate estimates.",
        flagged_entries=flagged,
    )


def test_sign_anomalies(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-04: Revenue Account Sign Anomalies.

    Revenue accounts normally have credit (negative) balances.
    Debit (positive) entries in revenue accounts are anomalous
    (unless clearly identified as contra-revenue).
    """
    if not config.sign_anomaly_enabled:
        return RevenueTestResult(
            test_name="Revenue Sign Anomalies",
            test_key="sign_anomalies",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedRevenue] = []
    for e in entries:
        if e.amount <= 0:
            continue  # Credit/zero — normal for revenue

        # Check if it's clearly a contra-revenue entry
        if _is_contra_revenue(e.description, e.account_name, config.contra_keywords):
            continue

        amt = abs(e.amount)
        severity = Severity.HIGH if amt > 50000 else Severity.MEDIUM if amt > 10000 else Severity.LOW

        flagged.append(FlaggedRevenue(
            entry=e,
            test_name="Revenue Sign Anomalies",
            test_key="sign_anomalies",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Debit balance in revenue: ${amt:,.2f} — {e.account_name or e.account_number or 'unknown account'}",
            confidence=0.85,
            details={"amount": e.amount, "account": e.account_name or e.account_number},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Revenue Sign Anomalies",
        test_key="sign_anomalies",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags debit balances in revenue accounts (normally credit).",
        flagged_entries=flagged,
    )


def test_unclassified_entries(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-05: Unclassified Revenue Entries.

    Flags entries missing both account name and account number.
    """
    if not config.unclassified_enabled:
        return RevenueTestResult(
            test_name="Unclassified Revenue Entries",
            test_key="unclassified_entries",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedRevenue] = []
    for e in entries:
        if e.account_name or e.account_number:
            continue
        flagged.append(FlaggedRevenue(
            entry=e,
            test_name="Unclassified Revenue Entries",
            test_key="unclassified_entries",
            test_tier=TestTier.STRUCTURAL,
            severity=Severity.MEDIUM,
            issue=f"Revenue entry ${abs(e.amount):,.2f} has no account classification",
            confidence=0.90,
            details={"amount": e.amount},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Unclassified Revenue Entries",
        test_key="unclassified_entries",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags revenue entries with no account classification (unmapped to lead sheet).",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 2 — STATISTICAL TESTS
# =============================================================================

def test_zscore_outliers(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-06: Revenue Account Z-Score Outliers.

    Flags entries with amounts >2.5 standard deviations from the mean.
    """
    amounts = [abs(e.amount) for e in entries if e.amount != 0]

    if len(amounts) < config.zscore_min_entries:
        return RevenueTestResult(
            test_name="Z-Score Outliers",
            test_key="zscore_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description=f"Requires at least {config.zscore_min_entries} entries for statistical analysis.",
            flagged_entries=[],
        )

    mean = statistics.mean(amounts)
    stdev = statistics.stdev(amounts)
    if stdev == 0:
        return RevenueTestResult(
            test_name="Z-Score Outliers",
            test_key="zscore_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="All amounts identical — no variance to analyze.",
            flagged_entries=[],
        )

    flagged: list[FlaggedRevenue] = []
    for e in entries:
        if e.amount == 0:
            continue
        z = abs(abs(e.amount) - mean) / stdev
        if z < config.zscore_threshold:
            continue

        if z > 5:
            severity = Severity.HIGH
        elif z > 4:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        flagged.append(FlaggedRevenue(
            entry=e,
            test_name="Z-Score Outliers",
            test_key="zscore_outliers",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Outlier: ${abs(e.amount):,.2f} (z-score: {z:.1f}, mean: ${mean:,.2f})",
            confidence=min(0.60 + z * 0.05, 0.95),
            details={"z_score": round(z, 2), "mean": round(mean, 2), "stdev": round(stdev, 2)},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Z-Score Outliers",
        test_key="zscore_outliers",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags revenue entries with amounts >{config.zscore_threshold} standard deviations from mean.",
        flagged_entries=flagged,
    )


def test_revenue_trend_variance(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-07: Revenue Trend Variance.

    Flags >30% YoY change if prior_period_total is provided.
    """
    if config.prior_period_total is None or config.prior_period_total == 0:
        return RevenueTestResult(
            test_name="Revenue Trend Variance",
            test_key="trend_variance",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Prior period total not provided — trend analysis skipped.",
            flagged_entries=[],
        )

    current_total = sum(abs(e.amount) for e in entries)
    variance_pct = (current_total - config.prior_period_total) / abs(config.prior_period_total)

    flagged: list[FlaggedRevenue] = []
    if abs(variance_pct) > config.trend_variance_pct:
        severity = Severity.HIGH if abs(variance_pct) > 0.50 else Severity.MEDIUM
        direction = "increase" if variance_pct > 0 else "decrease"

        # Flag summary entry (not individual entries — this is an aggregate test)
        flagged.append(FlaggedRevenue(
            entry=RevenueEntry(
                amount=current_total,
                account_name="[Aggregate Revenue]",
                row_number=0,
            ),
            test_name="Revenue Trend Variance",
            test_key="trend_variance",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Revenue {direction} of {abs(variance_pct):.1%}: "
                  f"${current_total:,.2f} vs prior ${config.prior_period_total:,.2f}",
            confidence=0.85,
            details={
                "current_total": round(current_total, 2),
                "prior_total": round(config.prior_period_total, 2),
                "variance_pct": round(variance_pct, 4),
                "direction": direction,
            },
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Revenue Trend Variance",
        test_key="trend_variance",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags >{config.trend_variance_pct:.0%} period-over-period revenue change.",
        flagged_entries=flagged,
    )


def test_concentration_risk(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-08: Revenue Concentration Risk.

    Flags if a single account represents >50% of total revenue.
    """
    total_revenue = sum(abs(e.amount) for e in entries)
    if total_revenue == 0:
        return RevenueTestResult(
            test_name="Revenue Concentration Risk",
            test_key="concentration_risk",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Zero total revenue — concentration analysis not applicable.",
            flagged_entries=[],
        )

    # Group by account
    account_totals: dict[str, float] = {}
    account_entries: dict[str, list[RevenueEntry]] = {}
    for e in entries:
        key = (e.account_name or e.account_number or "unknown").lower().strip()
        account_totals[key] = account_totals.get(key, 0) + abs(e.amount)
        account_entries.setdefault(key, []).append(e)

    flagged: list[FlaggedRevenue] = []
    for acct, acct_total in account_totals.items():
        pct = acct_total / total_revenue
        if pct <= config.concentration_threshold_pct:
            continue

        severity = Severity.HIGH if pct > 0.70 else Severity.MEDIUM
        for e in account_entries[acct]:
            flagged.append(FlaggedRevenue(
                entry=e,
                test_name="Revenue Concentration Risk",
                test_key="concentration_risk",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Account '{acct}' represents {pct:.1%} of total revenue (${acct_total:,.2f}/${total_revenue:,.2f})",
                confidence=0.80,
                details={
                    "account": acct,
                    "account_total": round(acct_total, 2),
                    "total_revenue": round(total_revenue, 2),
                    "concentration_pct": round(pct, 4),
                },
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Revenue Concentration Risk",
        test_key="concentration_risk",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags accounts representing >{config.concentration_threshold_pct:.0%} of total revenue.",
        flagged_entries=flagged,
    )


def test_cutoff_risk(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-09: Cut-Off Risk Indicators.

    Flags entries near period start/end boundaries (within cutoff_days).
    Uses explicit period_start/period_end if configured, else infers from data.
    """
    dates = [(e, parse_date(e.date)) for e in entries]
    dated = [(e, d) for e, d in dates if d is not None]

    if len(dated) < 2:
        return RevenueTestResult(
            test_name="Cut-Off Risk",
            test_key="cutoff_risk",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Insufficient dated entries for cut-off analysis.",
            flagged_entries=[],
        )

    from datetime import timedelta

    if config.period_start:
        p_start = parse_date(config.period_start)
    else:
        p_start = min(d for _, d in dated)

    if config.period_end:
        p_end = parse_date(config.period_end)
    else:
        p_end = max(d for _, d in dated)

    if not p_start or not p_end:
        return RevenueTestResult(
            test_name="Cut-Off Risk",
            test_key="cutoff_risk",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Could not determine period boundaries.",
            flagged_entries=[],
        )

    start_boundary = p_start + timedelta(days=config.cutoff_days)
    end_boundary = p_end - timedelta(days=config.cutoff_days)

    flagged: list[FlaggedRevenue] = []
    for e, d in dated:
        near_start = d <= start_boundary
        near_end = d >= end_boundary

        if not near_start and not near_end:
            continue

        boundary_type = "period start" if near_start else "period end"
        amt = abs(e.amount)
        severity = Severity.HIGH if amt > 50000 else Severity.MEDIUM if amt > 10000 else Severity.LOW

        flagged.append(FlaggedRevenue(
            entry=e,
            test_name="Cut-Off Risk",
            test_key="cutoff_risk",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Revenue ${amt:,.2f} near {boundary_type} ({e.date})",
            confidence=0.70,
            details={
                "boundary_type": boundary_type,
                "entry_date": str(d),
                "period_start": str(p_start),
                "period_end": str(p_end),
            },
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Cut-Off Risk",
        test_key="cutoff_risk",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags revenue entries within {config.cutoff_days} days of period start/end boundaries.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 3 — ADVANCED TESTS
# =============================================================================

# Expected Benford's Law first digit distribution
BENFORD_EXPECTED = {
    1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097,
    5: 0.079, 6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046,
}


def test_benford_law(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-10: Benford's Law on Revenue Transaction Leading Digits.

    Chi-squared test against expected first-digit distribution.
    """
    amounts = [abs(e.amount) for e in entries if abs(e.amount) >= 1]

    if len(amounts) < config.benford_min_entries:
        return RevenueTestResult(
            test_name="Benford's Law Analysis",
            test_key="benford_law",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description=f"Requires at least {config.benford_min_entries} entries for Benford's Law analysis.",
            flagged_entries=[],
        )

    # Extract first digits
    digit_counts: Counter = Counter()
    for amt in amounts:
        first_digit = int(str(amt).lstrip("0.")[0]) if amt > 0 else 0
        if 1 <= first_digit <= 9:
            digit_counts[first_digit] += 1

    n = sum(digit_counts.values())
    if n == 0:
        return RevenueTestResult(
            test_name="Benford's Law Analysis",
            test_key="benford_law",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="No valid first digits extracted.",
            flagged_entries=[],
        )

    # Chi-squared statistic
    chi_sq = 0.0
    digit_details: dict[str, dict] = {}
    for digit in range(1, 10):
        observed = digit_counts.get(digit, 0)
        expected = BENFORD_EXPECTED[digit] * n
        if expected > 0:
            chi_sq += (observed - expected) ** 2 / expected
        digit_details[str(digit)] = {
            "observed": observed,
            "expected": round(expected, 1),
            "observed_pct": round(observed / n, 4) if n > 0 else 0,
            "expected_pct": BENFORD_EXPECTED[digit],
        }

    flagged: list[FlaggedRevenue] = []
    if chi_sq > config.benford_chi_sq_threshold:
        severity = Severity.HIGH if chi_sq > config.benford_chi_sq_threshold * 2 else Severity.MEDIUM

        flagged.append(FlaggedRevenue(
            entry=RevenueEntry(
                amount=0,
                account_name="[Benford's Law Analysis]",
                row_number=0,
            ),
            test_name="Benford's Law Analysis",
            test_key="benford_law",
            test_tier=TestTier.ADVANCED,
            severity=severity,
            issue=f"Revenue data deviates from Benford's Law (chi-squared: {chi_sq:.2f}, threshold: {config.benford_chi_sq_threshold:.2f})",
            confidence=min(0.70 + (chi_sq / config.benford_chi_sq_threshold - 1) * 0.1, 0.95),
            details={
                "chi_squared": round(chi_sq, 2),
                "threshold": config.benford_chi_sq_threshold,
                "sample_size": n,
                "digit_analysis": digit_details,
            },
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Benford's Law Analysis",
        test_key="benford_law",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Tests revenue transaction leading digits against Benford's Law expected distribution.",
        flagged_entries=flagged,
    )


def test_duplicate_entries(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-11: Duplicate Revenue Entry Detection.

    Flags entries with same amount + date + account.
    """
    if not config.duplicate_enabled:
        return RevenueTestResult(
            test_name="Duplicate Revenue Entries",
            test_key="duplicate_entries",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    groups: dict[tuple, list[RevenueEntry]] = {}
    for e in entries:
        acct = (e.account_name or e.account_number or "").lower().strip()
        key = (round(e.amount, 2), (e.date or "").strip(), acct)
        groups.setdefault(key, []).append(e)

    flagged: list[FlaggedRevenue] = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        amt, entry_date, acct = key
        severity = Severity.HIGH if abs(amt) > 10000 else Severity.MEDIUM

        for e in group:
            flagged.append(FlaggedRevenue(
                entry=e,
                test_name="Duplicate Revenue Entries",
                test_key="duplicate_entries",
                test_tier=TestTier.ADVANCED,
                severity=severity,
                issue=f"Duplicate: ${abs(amt):,.2f} on {entry_date} in {acct or 'unknown account'} ({len(group)} occurrences)",
                confidence=0.90,
                details={
                    "duplicate_count": len(group),
                    "amount": amt,
                    "date": entry_date,
                    "account": acct,
                },
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Duplicate Revenue Entries",
        test_key="duplicate_entries",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags revenue entries with identical amount, date, and account.",
        flagged_entries=flagged,
    )


def test_contra_revenue_anomalies(
    entries: list[RevenueEntry],
    config: RevenueTestingConfig,
) -> RevenueTestResult:
    """RT-12: Contra-Revenue Anomalies.

    Flags if returns/allowances exceed 15% of gross revenue.
    """
    gross_revenue = 0.0
    contra_revenue = 0.0
    contra_entries: list[RevenueEntry] = []

    for e in entries:
        amt = abs(e.amount)
        if _is_contra_revenue(e.description, e.account_name, config.contra_keywords):
            contra_revenue += amt
            contra_entries.append(e)
        else:
            gross_revenue += amt

    if gross_revenue == 0:
        return RevenueTestResult(
            test_name="Contra-Revenue Anomalies",
            test_key="contra_revenue_anomalies",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Zero gross revenue — contra analysis not applicable.",
            flagged_entries=[],
        )

    contra_pct = contra_revenue / gross_revenue

    flagged: list[FlaggedRevenue] = []
    if contra_pct > config.contra_threshold_pct:
        severity = Severity.HIGH if contra_pct > 0.25 else Severity.MEDIUM

        for e in contra_entries:
            flagged.append(FlaggedRevenue(
                entry=e,
                test_name="Contra-Revenue Anomalies",
                test_key="contra_revenue_anomalies",
                test_tier=TestTier.ADVANCED,
                severity=severity,
                issue=f"Contra-revenue: ${abs(e.amount):,.2f} — total contra is {contra_pct:.1%} of gross revenue",
                confidence=0.80,
                details={
                    "contra_pct": round(contra_pct, 4),
                    "contra_total": round(contra_revenue, 2),
                    "gross_revenue": round(gross_revenue, 2),
                },
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return RevenueTestResult(
        test_name="Contra-Revenue Anomalies",
        test_key="contra_revenue_anomalies",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags if returns/allowances exceed {config.contra_threshold_pct:.0%} of gross revenue.",
        flagged_entries=flagged,
    )


# =============================================================================
# TEST BATTERY + SCORING
# =============================================================================

def run_revenue_test_battery(
    entries: list[RevenueEntry],
    config: Optional[RevenueTestingConfig] = None,
) -> list[RevenueTestResult]:
    """Run all 12 revenue tests."""
    if config is None:
        config = RevenueTestingConfig()

    return [
        # Tier 1 — Structural
        test_large_manual_entries(entries, config),
        test_year_end_concentration(entries, config),
        test_round_revenue_amounts(entries, config),
        test_sign_anomalies(entries, config),
        test_unclassified_entries(entries, config),
        # Tier 2 — Statistical
        test_zscore_outliers(entries, config),
        test_revenue_trend_variance(entries, config),
        test_concentration_risk(entries, config),
        test_cutoff_risk(entries, config),
        # Tier 3 — Advanced
        test_benford_law(entries, config),
        test_duplicate_entries(entries, config),
        test_contra_revenue_anomalies(entries, config),
    ]


def calculate_revenue_composite_score(
    test_results: list[RevenueTestResult],
    total_entries: int,
) -> RevenueCompositeScore:
    """Calculate composite risk score from revenue test results.

    Delegates to shared test aggregator (Sprint 152).
    """
    result = _shared_calc_cs(test_results, total_entries)

    return RevenueCompositeScore(
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

def run_revenue_testing(
    rows: list[dict],
    column_names: list[str],
    config: Optional[RevenueTestingConfig] = None,
    column_mapping: Optional[dict] = None,
) -> RevenueTestingResult:
    """Run the complete revenue testing pipeline.

    Args:
        rows: List of dicts (raw revenue GL data rows)
        column_names: List of column header names
        config: Optional testing configuration
        column_mapping: Optional manual column mapping override

    Returns:
        RevenueTestingResult with composite score, test results, data quality.
    """
    if config is None:
        config = RevenueTestingConfig()

    # 1. Detect columns
    detection = detect_revenue_columns(column_names)

    # Apply manual overrides
    if column_mapping:
        for attr in ("date_column", "amount_column", "account_name_column",
                     "account_number_column", "description_column",
                     "entry_type_column", "reference_column", "posted_by_column"):
            if attr in column_mapping:
                setattr(detection, attr, column_mapping[attr])
        detection.overall_confidence = 1.0

    # 2. Parse entries
    entries = parse_revenue_entries(rows, detection)

    # 3. Assess data quality
    data_quality = assess_revenue_data_quality(entries, detection)

    # 4. Run test battery
    test_results = run_revenue_test_battery(entries, config)

    # 5. Calculate composite score
    composite = calculate_revenue_composite_score(test_results, len(entries))

    return RevenueTestingResult(
        composite_score=composite,
        test_results=test_results,
        data_quality=data_quality,
        column_detection=detection,
    )
