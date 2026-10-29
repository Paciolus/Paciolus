"""
Fixed Asset Testing Engine — Sprint 114

Automated fixed asset register testing addressing IAS 16/ASC 360 property,
plant and equipment assertions. Parses fixed asset registers (CSV/Excel),
detects columns, runs 10 tests across structural, statistical, and advanced tiers.

ZERO-STORAGE COMPLIANCE:
- All files processed in-memory only
- Test results are ephemeral (computed on demand)
- No raw asset data is stored

Audit Standards References:
- IAS 16: Property, Plant and Equipment
- IAS 36: Impairment of Assets
- ASC 360: Property, Plant, and Equipment
- ISA 500: Audit Evidence
- ISA 540: Auditing Accounting Estimates
"""

import math
import re
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Optional

from engine_framework import AuditEngineBase
from shared.column_detector import ColumnFieldConfig, detect_columns
from shared.data_quality import FieldQualityConfig
from shared.data_quality import assess_data_quality as _shared_assess_dq
from shared.monetary import decimals_to_floats
from shared.parsing_helpers import infer_day_first, parse_date, safe_decimal, safe_str, with_parse_memo
from shared.reference_date import reference_date_label
from shared.test_aggregator import calculate_composite_score as _shared_calc_cs
from shared.testing_enums import (
    RiskTier,
    Severity,
    TestTier,
    score_to_risk_tier,  # noqa: F401 — re-export for backward compat
    zscore_to_severity,
)

# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class FixedAssetTestingConfig:
    """Configurable thresholds for all fixed asset tests."""

    # FA-01: Fully depreciated still in use
    fully_depreciated_enabled: bool = True

    # FA-02: Missing required fields
    missing_fields_enabled: bool = True

    # FA-03: Negative cost or accumulated depreciation
    negative_values_enabled: bool = True

    # FA-04: Depreciation exceeds cost
    over_depreciation_enabled: bool = True

    # FA-05: Useful life outliers
    useful_life_min_years: float = 0.5
    useful_life_max_years: float = 50.0

    # FA-06: Cost Z-score outliers
    zscore_threshold: float = 2.5
    zscore_min_entries: int = 10

    # FA-07: Asset age concentration
    age_concentration_threshold_pct: float = 0.50

    # FA-08: Duplicate asset detection
    duplicate_enabled: bool = True

    # FA-09: Residual value anomalies
    residual_max_pct: float = 0.30
    residual_enabled: bool = True

    # Sprint 816: the as-of date ages are measured to — the period end, not the
    # day the file is processed. Accumulated depreciation and last-movement
    # dates are stated as of period end, so measuring to "today" drifts every
    # result as fieldwork moves past year-end. None = processing date.
    reference_date: Optional[date] = None
    reference_date_source: str = "processing_date"  # "as_of_date" | "engagement_period_end"


# =============================================================================
# FIXED ASSET COLUMN DETECTION
# =============================================================================

FA_ASSET_ID_PATTERNS = [
    (r"^asset\s*id$", 1.0, True),
    (r"^asset\s*number$", 0.98, True),
    (r"^asset\s*no$", 0.95, True),
    (r"^asset\s*#$", 0.95, True),
    (r"^asset\s*code$", 0.90, True),
    (r"^tag\s*number$", 0.85, True),
    (r"^tag\s*no$", 0.85, True),
    (r"^fa\s*number$", 0.90, True),
    (r"^fixed\s*asset\s*id$", 0.95, True),
    (r"asset.?id", 0.70, False),
    (r"asset.?num", 0.65, False),
    (r"asset.?no", 0.60, False),
    (r"tag.?num", 0.55, False),
]

FA_DESCRIPTION_PATTERNS = [
    (r"^description$", 1.0, True),
    (r"^asset\s*description$", 0.98, True),
    (r"^asset\s*name$", 0.95, True),
    (r"^name$", 0.75, True),
    (r"^item\s*description$", 0.85, True),
    (r"^fa\s*description$", 0.90, True),
    (r"description", 0.60, False),
]

FA_COST_PATTERNS = [
    (r"^cost$", 0.95, True),
    (r"^original\s*cost$", 1.0, True),
    (r"^acquisition\s*cost$", 1.0, True),
    (r"^historical\s*cost$", 0.95, True),
    (r"^gross\s*cost$", 0.90, True),
    (r"^purchase\s*price$", 0.85, True),
    (r"^capitalized\s*cost$", 0.90, True),
    (r"^book\s*value$", 0.65, True),
    (r"^gross\s*value$", 0.85, True),
    (r"^asset\s*cost$", 0.95, True),
    (r"cost", 0.55, False),
]

FA_ACCUM_DEPR_PATTERNS = [
    (r"^accumulated\s*depreciation$", 1.0, True),
    (r"^accum\s*depreciation$", 0.98, True),
    (r"^accum\s*depr$", 0.95, True),
    (r"^accumulated\s*depr$", 0.95, True),
    (r"^ad$", 0.60, True),
    (r"^total\s*depreciation$", 0.85, True),
    (r"^depreciation\s*to\s*date$", 0.90, True),
    (r"^depr\s*to\s*date$", 0.85, True),
    (r"^ytd\s*depreciation$", 0.80, True),
    (r"accum.?dep", 0.75, False),
    (r"accumulated.?dep", 0.80, False),
]

FA_ACQUISITION_DATE_PATTERNS = [
    (r"^acquisition\s*date$", 1.0, True),
    (r"^purchase\s*date$", 0.95, True),
    (r"^date\s*acquired$", 0.95, True),
    (r"^date\s*in\s*service$", 0.90, True),
    (r"^in\s*service\s*date$", 0.90, True),
    (r"^capitalization\s*date$", 0.85, True),
    (r"^placed\s*in\s*service$", 0.90, True),
    (r"^start\s*date$", 0.70, True),
    (r"^asset\s*date$", 0.80, True),
    (r"acquisition.?date", 0.75, False),
    (r"purchase.?date", 0.70, False),
    (r"in.?service", 0.60, False),
]

FA_USEFUL_LIFE_PATTERNS = [
    (r"^useful\s*life$", 1.0, True),
    (r"^useful\s*life\s*years$", 1.0, True),
    (r"^life\s*years$", 0.90, True),
    (r"^estimated\s*life$", 0.95, True),
    (r"^economic\s*life$", 0.90, True),
    (r"^depreciable\s*life$", 0.90, True),
    (r"^life$", 0.65, True),
    (r"useful.?life", 0.80, False),
    (r"life.?years", 0.65, False),
    # Sprint 855 (A8): month-denominated lives; parse_fa_entries converts them.
    (r"life\b.*\b(months?|mos|mths?)\b", 0.85, False),
]

# Sprint 855 (A8): a useful-life header that names months. 60 in a
# "Useful Life (Months)" column was read as 60 years.
_LIFE_IN_MONTHS = re.compile(r"\b(months?|mos|mths?)\b", re.IGNORECASE)


def life_column_is_months(column: Optional[str]) -> bool:
    """Whether a useful-life column is denominated in months (by its header)."""
    return bool(column and _LIFE_IN_MONTHS.search(column))


FA_DEPRECIATION_METHOD_PATTERNS = [
    (r"^depreciation\s*method$", 1.0, True),
    (r"^depr\s*method$", 0.95, True),
    (r"^method$", 0.65, True),
    (r"^depr\s*type$", 0.85, True),
    (r"^depreciation\s*type$", 0.90, True),
    (r"depr.?method", 0.75, False),
]

FA_RESIDUAL_VALUE_PATTERNS = [
    (r"^residual\s*value$", 1.0, True),
    (r"^salvage\s*value$", 0.98, True),
    (r"^scrap\s*value$", 0.90, True),
    (r"^residual$", 0.80, True),
    (r"^salvage$", 0.80, True),
    (r"^disposal\s*value$", 0.75, True),
    (r"residual.?val", 0.70, False),
    (r"salvage.?val", 0.70, False),
]

FA_LOCATION_PATTERNS = [
    (r"^location$", 1.0, True),
    (r"^asset\s*location$", 0.95, True),
    (r"^site$", 0.80, True),
    (r"^building$", 0.75, True),
    (r"^department$", 0.70, True),
    (r"^facility$", 0.75, True),
    (r"location", 0.55, False),
]

FA_CATEGORY_PATTERNS = [
    (r"^category$", 0.90, True),
    (r"^asset\s*category$", 1.0, True),
    (r"^asset\s*class$", 0.95, True),
    (r"^asset\s*type$", 0.90, True),
    (r"^class$", 0.70, True),
    (r"^type$", 0.60, True),
    (r"^fa\s*category$", 0.95, True),
    (r"^group$", 0.55, True),
    (r"category", 0.55, False),
    (r"asset.?class", 0.65, False),
]

FA_NBV_PATTERNS = [
    (r"^net\s*book\s*value$", 1.0, True),
    (r"^nbv$", 0.95, True),
    (r"^net\s*value$", 0.85, True),
    (r"^carrying\s*value$", 0.90, True),
    (r"^carrying\s*amount$", 0.90, True),
    (r"^book\s*value$", 0.80, True),
    (r"^written\s*down\s*value$", 0.85, True),
    (r"^wdv$", 0.80, True),
    (r"net.?book", 0.70, False),
    (r"carrying.?val", 0.65, False),
]

# Shared column detector configs (replaces FAColumnType + _FA_COLUMN_PATTERNS)
FA_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig("asset_id_column", FA_ASSET_ID_PATTERNS, priority=10),
    ColumnFieldConfig("accumulated_depreciation_column", FA_ACCUM_DEPR_PATTERNS, priority=15),
    ColumnFieldConfig("net_book_value_column", FA_NBV_PATTERNS, priority=20),
    ColumnFieldConfig(
        "cost_column", FA_COST_PATTERNS, required=True, missing_note="Could not identify a Cost column", priority=25
    ),
    ColumnFieldConfig("description_column", FA_DESCRIPTION_PATTERNS, priority=30),
    ColumnFieldConfig("acquisition_date_column", FA_ACQUISITION_DATE_PATTERNS, priority=35),
    ColumnFieldConfig("useful_life_column", FA_USEFUL_LIFE_PATTERNS, priority=40),
    ColumnFieldConfig("depreciation_method_column", FA_DEPRECIATION_METHOD_PATTERNS, priority=45),
    ColumnFieldConfig("residual_value_column", FA_RESIDUAL_VALUE_PATTERNS, priority=50),
    ColumnFieldConfig("location_column", FA_LOCATION_PATTERNS, priority=55),
    ColumnFieldConfig("category_column", FA_CATEGORY_PATTERNS, priority=60),
]


@dataclass
class FAColumnDetection:
    """Result of fixed asset column detection."""

    asset_id_column: Optional[str] = None
    description_column: Optional[str] = None
    cost_column: Optional[str] = None
    accumulated_depreciation_column: Optional[str] = None
    acquisition_date_column: Optional[str] = None
    useful_life_column: Optional[str] = None
    depreciation_method_column: Optional[str] = None
    residual_value_column: Optional[str] = None
    location_column: Optional[str] = None
    category_column: Optional[str] = None
    net_book_value_column: Optional[str] = None

    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "asset_id_column": self.asset_id_column,
            "description_column": self.description_column,
            "cost_column": self.cost_column,
            "accumulated_depreciation_column": self.accumulated_depreciation_column,
            "acquisition_date_column": self.acquisition_date_column,
            "useful_life_column": self.useful_life_column,
            "depreciation_method_column": self.depreciation_method_column,
            "residual_value_column": self.residual_value_column,
            "location_column": self.location_column,
            "category_column": self.category_column,
            "net_book_value_column": self.net_book_value_column,
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


def detect_fa_columns(column_names: list[str]) -> FAColumnDetection:
    """Detect fixed asset register columns using shared column detector."""
    detection = detect_columns(column_names, FA_COLUMN_CONFIGS)
    result = FAColumnDetection(all_columns=detection.all_columns)

    # Map shared detection results to FA-specific fields
    field_names = [
        "asset_id_column",
        "description_column",
        "cost_column",
        "accumulated_depreciation_column",
        "acquisition_date_column",
        "useful_life_column",
        "depreciation_method_column",
        "residual_value_column",
        "location_column",
        "category_column",
        "net_book_value_column",
    ]
    for field_name in field_names:
        col = detection.get_column(field_name)
        if col:
            setattr(result, field_name, col)

    notes = list(detection.detection_notes)

    # Confidence: min of required (cost + at least one identifier)
    required_confs = [
        detection.get_confidence("cost_column") if result.cost_column else 0.0,
    ]
    id_conf = max(
        detection.get_confidence("asset_id_column") if result.asset_id_column else 0.0,
        detection.get_confidence("description_column") if result.description_column else 0.0,
    )
    if id_conf == 0.0:
        notes.append("Could not identify an Asset ID or Description column")
    required_confs.append(id_conf)

    result.overall_confidence = min(required_confs) if required_confs else 0.0
    result.detection_notes = notes
    return result


# =============================================================================
# DATA MODELS
# =============================================================================


@dataclass
class FixedAssetEntry:
    """A single line from the fixed asset register."""

    asset_id: Optional[str] = None
    description: Optional[str] = None
    cost: Decimal = Decimal("0")
    accumulated_depreciation: Decimal = Decimal("0")
    acquisition_date: Optional[str] = None
    useful_life: Optional[float] = None  # Non-monetary: years (month columns converted on parse)
    depreciation_method: Optional[str] = None
    residual_value: Decimal = Decimal("0")
    location: Optional[str] = None
    category: Optional[str] = None
    net_book_value: Optional[Decimal] = None
    row_number: int = 0
    # Sprint 855 (A4): the register's date column is DD/MM (inferred per column
    # in parse_fa_entries). Not serialised — it changes how the date is read.
    acquisition_date_day_first: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.cost, (int, float)):
            self.cost = Decimal(str(self.cost))
        if isinstance(self.accumulated_depreciation, (int, float)):
            self.accumulated_depreciation = Decimal(str(self.accumulated_depreciation))
        if isinstance(self.residual_value, (int, float)):
            self.residual_value = Decimal(str(self.residual_value))
        if isinstance(self.net_book_value, (int, float)):
            self.net_book_value = Decimal(str(self.net_book_value))

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "description": self.description,
            "cost": float(self.cost),
            "accumulated_depreciation": float(self.accumulated_depreciation),
            "acquisition_date": self.acquisition_date,
            "useful_life": self.useful_life,
            "depreciation_method": self.depreciation_method,
            "residual_value": float(self.residual_value),
            "location": self.location,
            "category": self.category,
            "net_book_value": float(self.net_book_value) if self.net_book_value is not None else None,
            "row_number": self.row_number,
        }


@dataclass
class FlaggedFixedAsset:
    """A fixed asset entry flagged by a test."""

    entry: FixedAssetEntry
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
            "details": decimals_to_floats(self.details),
        }


@dataclass
class FATestResult:
    """Result of a single fixed asset test."""

    test_name: str
    test_key: str
    test_tier: TestTier
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Severity
    description: str
    flagged_entries: list[FlaggedFixedAsset] = field(default_factory=list)

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
class FADataQuality:
    """Quality assessment of the fixed asset data."""

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
class FACompositeScore:
    """Overall fixed asset testing composite score."""

    score: float
    risk_tier: RiskTier
    tests_run: int
    total_entries: int
    total_flagged: int
    flag_rate: float
    flags_by_severity: dict[str, int] = field(default_factory=dict)
    top_findings: list[str] = field(default_factory=list)
    score_basis: list[str] = field(default_factory=list)  # Sprint 831: floors applied

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
            "score_basis": self.score_basis,
        }


@dataclass
class FATestingResult:
    """Complete result of fixed asset testing."""

    composite_score: FACompositeScore
    test_results: list[FATestResult] = field(default_factory=list)
    data_quality: Optional[FADataQuality] = None
    column_detection: Optional[FAColumnDetection] = None

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [t.to_dict() for t in self.test_results],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "column_detection": self.column_detection.to_dict() if self.column_detection else None,
        }


def _safe_float_optional(value: object) -> Optional[float]:
    """Like safe_float but returns None for missing/invalid values."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None
    try:
        f = float(str(value))
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        if isinstance(value, str):
            cleaned = re.sub(r"[,$\s()%]", "", s)
            if cleaned.startswith("-") or cleaned.endswith("-"):
                cleaned = "-" + cleaned.strip("-")
            try:
                return float(cleaned)
            except (ValueError, TypeError):
                return None
        return None


# =============================================================================
# PARSER
# =============================================================================


def parse_fa_entries(
    rows: list[dict],
    detection: FAColumnDetection,
) -> list[FixedAssetEntry]:
    """Parse raw rows into FixedAssetEntry objects using detected columns."""
    entries: list[FixedAssetEntry] = []
    # Sprint 855 (A4): DD/MM registers read month-first gave every day <= 12
    # date the wrong month. Decide the order once for the whole column.
    day_first = bool(detection.acquisition_date_column) and infer_day_first(
        row.get(detection.acquisition_date_column) for row in rows
    )
    life_divisor = 12.0 if life_column_is_months(detection.useful_life_column) else 1.0
    for idx, row in enumerate(rows):
        entry = FixedAssetEntry(row_number=idx + 1)
        if detection.asset_id_column:
            entry.asset_id = safe_str(row.get(detection.asset_id_column))
        if detection.description_column:
            entry.description = safe_str(row.get(detection.description_column))
        if detection.cost_column:
            entry.cost = safe_decimal(row.get(detection.cost_column))
        if detection.accumulated_depreciation_column:
            entry.accumulated_depreciation = safe_decimal(row.get(detection.accumulated_depreciation_column))
        if detection.acquisition_date_column:
            entry.acquisition_date = safe_str(row.get(detection.acquisition_date_column))
            entry.acquisition_date_day_first = day_first
        if detection.useful_life_column:
            life = _safe_float_optional(row.get(detection.useful_life_column))
            entry.useful_life = life / life_divisor if life is not None else None
        if detection.depreciation_method_column:
            entry.depreciation_method = safe_str(row.get(detection.depreciation_method_column))
        if detection.residual_value_column:
            entry.residual_value = safe_decimal(row.get(detection.residual_value_column))
        if detection.location_column:
            entry.location = safe_str(row.get(detection.location_column))
        if detection.category_column:
            entry.category = safe_str(row.get(detection.category_column))
        if detection.net_book_value_column:
            nbv_val = _safe_float_optional(row.get(detection.net_book_value_column))
            entry.net_book_value = Decimal(str(nbv_val)) if nbv_val is not None else None
        entries.append(entry)
    return entries


# =============================================================================
# DATA QUALITY
# =============================================================================


def assess_fa_data_quality(
    entries: list[FixedAssetEntry],
    detection: FAColumnDetection,
) -> FADataQuality:
    """Assess quality and completeness of fixed asset data.

    Delegates to shared data quality engine (Sprint 152).
    """
    configs: list[FieldQualityConfig] = [
        FieldQualityConfig(
            "identifier",
            lambda e: e.asset_id or e.description,
            weight=0.25,
            issue_threshold=0.90,
            issue_template="Missing identifier on {unfilled} entries",
        ),
        FieldQualityConfig(
            "cost",
            lambda e: e.cost != 0,
            weight=0.35,
            issue_threshold=0.90,
            issue_template="{unfilled} entries have zero cost",
        ),
    ]

    if detection.accumulated_depreciation_column:
        configs.append(FieldQualityConfig("accumulated_depreciation", lambda e: e.accumulated_depreciation != 0))
    if detection.acquisition_date_column:
        configs.append(
            FieldQualityConfig(
                "acquisition_date",
                lambda e: e.acquisition_date,
                issue_threshold=0.80,
                issue_template="Low acquisition date fill rate: {fill_pct}",
            )
        )
    if detection.useful_life_column:
        configs.append(FieldQualityConfig("useful_life", lambda e: e.useful_life is not None))
    if detection.category_column:
        configs.append(FieldQualityConfig("category", lambda e: e.category))

    result = _shared_assess_dq(entries, configs, optional_weight_pool=0.40, domain="fixed_asset_testing")

    return FADataQuality(
        completeness_score=result.completeness_score,
        field_fill_rates=result.field_fill_rates,
        detected_issues=result.detected_issues,
        total_rows=result.total_rows,
    )


# score_to_risk_tier is imported from shared.testing_enums (Sprint 152)


# =============================================================================
# TIER 1 — STRUCTURAL TESTS
# =============================================================================


def test_fully_depreciated_assets(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-01: Fully Depreciated Assets Still on Register.

    Flags assets where accumulated depreciation >= cost (NBV = 0 or negative)
    and the asset is still on the register. Indicates potential ghost assets
    or assets that should have been disposed of.
    """
    if not config.fully_depreciated_enabled:
        return FATestResult(
            test_name="Fully Depreciated Assets",
            test_key="fully_depreciated",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedFixedAsset] = []
    for e in entries:
        cost = abs(e.cost)
        accum = abs(e.accumulated_depreciation)
        if cost == 0:
            continue
        if accum < cost:
            continue

        nbv = cost - accum
        severity = Severity.HIGH if cost > 100000 else Severity.MEDIUM if cost > 10000 else Severity.LOW

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Fully Depreciated Assets",
                test_key="fully_depreciated",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Fully depreciated: {e.asset_id or e.description or 'unknown'}"
                f" cost=${cost:,.2f}, accum depr=${accum:,.2f}, NBV=${nbv:,.2f}",
                confidence=0.85,
                details={"cost": float(cost), "accumulated_depreciation": float(accum), "nbv": float(nbv)},
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Fully Depreciated Assets",
        test_key="fully_depreciated",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags assets where accumulated depreciation >= cost (NBV zero or negative).",
        flagged_entries=flagged,
    )


def test_missing_required_fields(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-02: Missing Required Fields.

    Flags entries missing critical register fields (cost, identifier, date).
    """
    if not config.missing_fields_enabled:
        return FATestResult(
            test_name="Missing Required Fields",
            test_key="missing_fields",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedFixedAsset] = []
    for e in entries:
        missing: list[str] = []
        if not e.asset_id and not e.description:
            missing.append("identifier (asset_id or description)")
        if e.cost == 0:
            missing.append("cost")
        if not e.acquisition_date:
            missing.append("acquisition_date")

        if not missing:
            continue

        severity = Severity.HIGH if len(missing) >= 2 else Severity.MEDIUM

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Missing Required Fields",
                test_key="missing_fields",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Missing fields: {', '.join(missing)} — {e.asset_id or e.description or f'row {e.row_number}'}",
                confidence=0.90,
                details={"missing_fields": missing, "missing_count": len(missing)},
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Missing Required Fields",
        test_key="missing_fields",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags fixed asset entries missing critical register fields.",
        flagged_entries=flagged,
    )


def test_negative_values(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-03: Negative Cost or Accumulated Depreciation.

    Flags assets with negative cost or negative accumulated depreciation
    which indicate data entry errors or improper adjustments.
    """
    if not config.negative_values_enabled:
        return FATestResult(
            test_name="Negative Values",
            test_key="negative_values",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedFixedAsset] = []
    for e in entries:
        issues_found: list[str] = []
        if e.cost < 0:
            issues_found.append(f"negative cost=${e.cost:,.2f}")
        if e.accumulated_depreciation < 0:
            issues_found.append(f"negative accum depr=${e.accumulated_depreciation:,.2f}")

        if not issues_found:
            continue

        amt = max(abs(e.cost), abs(e.accumulated_depreciation))
        severity = Severity.HIGH if amt > 50000 else Severity.MEDIUM

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Negative Values",
                test_key="negative_values",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Negative values: {'; '.join(issues_found)}"
                f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                confidence=0.95,
                details={"cost": float(e.cost), "accumulated_depreciation": float(e.accumulated_depreciation)},
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Negative Values",
        test_key="negative_values",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags assets with negative cost or negative accumulated depreciation.",
        flagged_entries=flagged,
    )


def test_over_depreciation(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-04: Depreciation Exceeds Cost.

    Flags assets where accumulated depreciation exceeds original cost
    by a meaningful amount (beyond rounding differences).
    Distinct from FA-01: this catches cases where accum depr significantly
    exceeds cost, not just where they are equal.
    """
    if not config.over_depreciation_enabled:
        return FATestResult(
            test_name="Over-Depreciation",
            test_key="over_depreciation",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedFixedAsset] = []
    for e in entries:
        cost = abs(e.cost)
        accum = abs(e.accumulated_depreciation)
        if cost == 0:
            continue

        excess = accum - cost
        # Only flag if excess is > 1% of cost (beyond rounding)
        if excess <= cost * Decimal("0.01"):
            continue

        excess_pct = excess / cost
        severity = Severity.HIGH if excess_pct > 0.10 else Severity.MEDIUM

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Over-Depreciation",
                test_key="over_depreciation",
                test_tier=TestTier.STRUCTURAL,
                severity=severity,
                issue=f"Depreciation exceeds cost by {excess_pct:.1%}: "
                f"cost=${cost:,.2f}, accum=${accum:,.2f}, excess=${excess:,.2f}"
                f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                confidence=0.90,
                details={
                    "cost": cost,
                    "accumulated_depreciation": accum,
                    "excess": round(excess, 2),
                    "excess_pct": round(excess_pct, 4),
                },
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Over-Depreciation",
        test_key="over_depreciation",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags assets where accumulated depreciation exceeds original cost by >1%.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 2 — STATISTICAL TESTS
# =============================================================================


def test_useful_life_outliers(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-05: Useful Life Outliers.

    Flags assets with useful life below 0.5 years or above 50 years,
    which may indicate data entry errors or unreasonable estimates.
    """
    entries_with_life = [e for e in entries if e.useful_life is not None]

    if not entries_with_life:
        return FATestResult(
            test_name="Useful Life Outliers",
            test_key="useful_life_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="No useful life data available for analysis.",
            flagged_entries=[],
        )

    flagged: list[FlaggedFixedAsset] = []
    for e in entries_with_life:
        life = e.useful_life
        if life is None:
            continue

        issue_type = None
        if life < config.useful_life_min_years:
            issue_type = f"below minimum ({config.useful_life_min_years} years)"
            severity = Severity.MEDIUM
        elif life > config.useful_life_max_years:
            issue_type = f"above maximum ({config.useful_life_max_years} years)"
            severity = Severity.MEDIUM if life <= 100 else Severity.HIGH
        else:
            continue

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Useful Life Outliers",
                test_key="useful_life_outliers",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Useful life {life:.1f} years {issue_type}"
                f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                confidence=0.80,
                details={
                    "useful_life": life,
                    "min_threshold": config.useful_life_min_years,
                    "max_threshold": config.useful_life_max_years,
                },
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Useful Life Outliers",
        test_key="useful_life_outliers",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags assets with useful life <{config.useful_life_min_years} or >{config.useful_life_max_years} years.",
        flagged_entries=flagged,
    )


def test_cost_zscore_outliers(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-06: Cost Z-Score Outliers.

    Flags assets with cost >2.5 standard deviations from the mean cost.
    """
    costs = [abs(e.cost) for e in entries if e.cost != 0]

    if len(costs) < config.zscore_min_entries:
        return FATestResult(
            test_name="Cost Z-Score Outliers",
            test_key="cost_zscore_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description=f"Requires at least {config.zscore_min_entries} entries for statistical analysis.",
            flagged_entries=[],
        )

    mean = statistics.mean(costs)
    stdev = statistics.stdev(costs)
    if stdev == 0:
        return FATestResult(
            test_name="Cost Z-Score Outliers",
            test_key="cost_zscore_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="All costs identical — no variance to analyze.",
            flagged_entries=[],
        )

    flagged: list[FlaggedFixedAsset] = []
    for e in entries:
        if e.cost == 0:
            continue
        z = abs(abs(e.cost) - mean) / stdev
        if z < config.zscore_threshold:
            continue

        severity = zscore_to_severity(float(z))

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Cost Z-Score Outliers",
                test_key="cost_zscore_outliers",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Outlier cost: ${abs(e.cost):,.2f} (z-score: {z:.1f}, mean: ${mean:,.2f})"
                f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                confidence=min(0.60 + float(z) * 0.05, 0.95),
                details={"z_score": round(z, 2), "mean": round(mean, 2), "stdev": round(stdev, 2)},
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Cost Z-Score Outliers",
        test_key="cost_zscore_outliers",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags assets with cost >{config.zscore_threshold} standard deviations from mean.",
        flagged_entries=flagged,
    )


def _acquisition_date(e: FixedAssetEntry) -> Optional[date]:
    return parse_date(e.acquisition_date, day_first=e.acquisition_date_day_first)


def _half_year_midpoint(acquired: date, period_end: date) -> date:
    """Midpoint of the fiscal year containing ``acquired``.

    Fiscal years are taken to end on ``period_end``'s month and day, so a June
    year-end register puts the half-year midpoint at 31 December.
    """

    def anniversary(year: int) -> date:
        try:
            return period_end.replace(year=year)
        except ValueError:  # 29 February in a non-leap year
            return period_end.replace(year=year, day=28)

    fy_end = anniversary(acquired.year)
    if fy_end < acquired:
        fy_end = anniversary(acquired.year + 1)
    fy_start = anniversary(fy_end.year - 1) + timedelta(days=1)
    return fy_start + (fy_end - fy_start) / 2


def test_age_concentration(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-07: Asset Age Concentration.

    Flags if >50% of total asset cost is concentrated in a single
    acquisition year, indicating potential bulk capitalization risk.
    """
    dated = [(e, _acquisition_date(e)) for e in entries]
    dated_entries = [(e, d) for e, d in dated if d is not None]

    if not dated_entries:
        return FATestResult(
            test_name="Asset Age Concentration",
            test_key="age_concentration",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="No acquisition dates available for age concentration analysis.",
            flagged_entries=[],
        )

    total_cost = sum((abs(e.cost) for e, _ in dated_entries), Decimal("0"))
    if total_cost == 0:
        return FATestResult(
            test_name="Asset Age Concentration",
            test_key="age_concentration",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Zero total cost — age concentration not applicable.",
            flagged_entries=[],
        )

    # Group by acquisition year
    year_costs: dict[int, Decimal] = {}
    year_entries: dict[int, list[FixedAssetEntry]] = {}
    for e, d in dated_entries:
        yr = d.year
        year_costs[yr] = year_costs.get(yr, Decimal("0")) + abs(e.cost)
        year_entries.setdefault(yr, []).append(e)

    flagged: list[FlaggedFixedAsset] = []
    for yr, yr_cost in year_costs.items():
        pct = yr_cost / total_cost
        if pct <= config.age_concentration_threshold_pct:
            continue

        severity = Severity.HIGH if pct > 0.70 else Severity.MEDIUM

        for e in year_entries[yr]:
            flagged.append(
                FlaggedFixedAsset(
                    entry=e,
                    test_name="Asset Age Concentration",
                    test_key="age_concentration",
                    test_tier=TestTier.STATISTICAL,
                    severity=severity,
                    issue=f"Year {yr} represents {pct:.1%} of total asset cost "
                    f"(${yr_cost:,.2f}/${total_cost:,.2f})"
                    f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                    confidence=0.75,
                    details={
                        "year": yr,
                        "year_cost": round(yr_cost, 2),
                        "total_cost": round(total_cost, 2),
                        "concentration_pct": round(pct, 4),
                    },
                )
            )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Asset Age Concentration",
        test_key="age_concentration",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags if >{config.age_concentration_threshold_pct:.0%} of asset cost is concentrated in a single acquisition year.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 3 — ADVANCED TESTS
# =============================================================================


def test_duplicate_assets(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-08: Duplicate Asset Detection.

    Flags assets with identical cost + description + acquisition date,
    which may indicate double-counting or duplicate capitalization.
    """
    if not config.duplicate_enabled:
        return FATestResult(
            test_name="Duplicate Assets",
            test_key="duplicate_assets",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    groups: dict[tuple, list[FixedAssetEntry]] = {}
    for e in entries:
        desc = (e.description or "").lower().strip()
        key = (round(e.cost, 2), desc, (e.acquisition_date or "").strip())
        if key == (Decimal("0"), "", ""):
            continue  # Skip blank entries
        groups.setdefault(key, []).append(e)

    flagged: list[FlaggedFixedAsset] = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        cost, desc, acq_date = key
        severity = Severity.HIGH if abs(cost) > 50000 else Severity.MEDIUM

        for e in group:
            flagged.append(
                FlaggedFixedAsset(
                    entry=e,
                    test_name="Duplicate Assets",
                    test_key="duplicate_assets",
                    test_tier=TestTier.ADVANCED,
                    severity=severity,
                    issue=f"Potential duplicate: ${abs(cost):,.2f}, '{desc}'"
                    f"{f', acquired {acq_date}' if acq_date else ''}"
                    f" ({len(group)} occurrences)",
                    confidence=0.85,
                    details={
                        "duplicate_count": len(group),
                        "cost": cost,
                        "description": desc,
                        "acquisition_date": acq_date,
                    },
                )
            )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Duplicate Assets",
        test_key="duplicate_assets",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags assets with identical cost, description, and acquisition date.",
        flagged_entries=flagged,
    )


def test_residual_value_anomalies(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-09: Residual Value Anomalies.

    Flags assets where residual value exceeds 30% of original cost,
    which may indicate unreasonable salvage estimates or improper asset valuation.
    Also flags negative residual values.
    """
    if not config.residual_enabled:
        return FATestResult(
            test_name="Residual Value Anomalies",
            test_key="residual_value_anomalies",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedFixedAsset] = []
    for e in entries:
        cost = abs(e.cost)
        if cost == 0:
            continue

        # Check negative residual
        if e.residual_value < 0:
            flagged.append(
                FlaggedFixedAsset(
                    entry=e,
                    test_name="Residual Value Anomalies",
                    test_key="residual_value_anomalies",
                    test_tier=TestTier.ADVANCED,
                    severity=Severity.HIGH,
                    issue=f"Negative residual value: ${e.residual_value:,.2f}"
                    f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                    confidence=0.95,
                    details={"residual_value": e.residual_value, "cost": cost},
                )
            )
            continue

        if e.residual_value == 0:
            continue

        residual_pct = e.residual_value / cost
        if residual_pct <= config.residual_max_pct:
            continue

        severity = Severity.HIGH if residual_pct > 0.50 else Severity.MEDIUM

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Residual Value Anomalies",
                test_key="residual_value_anomalies",
                test_tier=TestTier.ADVANCED,
                severity=severity,
                issue=f"Residual value {residual_pct:.1%} of cost: "
                f"residual=${e.residual_value:,.2f}, cost=${cost:,.2f}"
                f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                confidence=0.80,
                details={
                    "residual_value": e.residual_value,
                    "cost": cost,
                    "residual_pct": round(residual_pct, 4),
                    "threshold_pct": config.residual_max_pct,
                },
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Residual Value Anomalies",
        test_key="residual_value_anomalies",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags assets with residual value >{config.residual_max_pct:.0%} of cost or negative residual values.",
        flagged_entries=flagged,
    )


# Lease indicator keywords for FA-10
_LEASE_KEYWORDS = re.compile(
    r"\b(lease|leased|leasehold|right[\s-]*of[\s-]*use|rou\b|"
    r"finance\s+lease|operating\s+lease|capital\s+lease)",
    re.IGNORECASE,
)


def test_lease_indicators(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-10: Lease Asset Indicators.

    Scans asset descriptions for keywords suggesting operating or finance leases.
    If found, flags for confirmation of ASC 842 treatment (right-of-use asset
    recognition, lease classification, and amortization schedule).
    """
    flagged: list[FlaggedFixedAsset] = []
    for e in entries:
        desc = (e.description or "").strip()
        if not desc:
            continue

        match = _LEASE_KEYWORDS.search(desc)
        if not match:
            continue

        keyword = match.group(0)
        severity = Severity.MEDIUM

        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Lease Asset Indicators",
                test_key="lease_indicators",
                test_tier=TestTier.ADVANCED,
                severity=severity,
                issue=f"Potential lease asset detected (keyword: '{keyword}')"
                f" \u2014 {e.asset_id or e.description or f'row {e.row_number}'}"
                f" \u2014 confirm ASC 842 treatment",
                confidence=0.70,
                details={"keyword": keyword, "description": desc},
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    if flagged:
        description = (
            "Flags assets with descriptions containing lease-related keywords "
            "(lease, ROU, right-of-use, leasehold). Flagged items should be "
            "confirmed for proper ASC 842 / IFRS 16 treatment."
        )
    else:
        description = (
            "No lease indicator keywords detected in asset descriptions. "
            "If the entity has lease arrangements, confirm they are recorded "
            "in a separate lease schedule per ASC 842."
        )

    return FATestResult(
        test_name="Lease Asset Indicators",
        test_key="lease_indicators",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM if flagged else Severity.LOW,
        description=description,
        flagged_entries=flagged,
    )


# =============================================================================
# TEST BATTERY + SCORING
# =============================================================================


def test_depreciation_recalculation(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-T11: Depreciation Recalculation (IAS 16 / ASC 360).

    Sprint 682 — when cost, residual_value, useful_life, and
    depreciation_method are all present, recalculate expected accumulated
    depreciation and flag entries whose reported figure deviates
    materially from it.

    Supported methods:
      * Straight-Line (SL): (cost − residual) / useful_life × t
      * Declining balance (DDB, or 150% DB when the method names "150"):
        cost × (1 − (1 − r)^t) with r = factor / useful_life (Sprint 827)
    Both are capped at the depreciable base.

    ``t`` is measured under two first-year conventions and the closer one
    is used (Sprint 855, A5): actual days from acquisition, and the
    half-year convention (depreciation from the midpoint of the fiscal year
    of acquisition, fiscal years ending on the reference date's month and
    day). The tolerance absorbs rounding only — mid-quarter and mid-month
    registers are not modelled and can still be flagged.

    Rows lacking any required input are silently skipped (not flagged) —
    this test is additive on top of FA-T02 missing-required-fields, which
    is the structural check.
    """
    from datetime import UTC as _UTC
    from datetime import datetime as _dt

    # 5% tolerance — per sprint plan; tighter than typical estimate-based
    # recalcs (10-15%). Sprint 855 (A5): it does *not* absorb a first-year
    # convention — half a year on a five-year asset bought late in the year is
    # a 30%+ difference two years on — so the half-year convention is
    # modelled explicitly below instead of being claimed here.
    SL_TOLERANCE = Decimal("0.05")
    DDB_TOLERANCE = Decimal("0.15")  # wider: switch-to-SL timing varies

    flagged: list[FlaggedFixedAsset] = []
    as_of = config.reference_date or _dt.now(_UTC).date()

    for e in entries:
        if not e.useful_life or e.useful_life <= 0:
            continue
        if e.cost <= 0:
            continue
        if not e.acquisition_date:
            continue
        if not e.depreciation_method:
            continue
        # Sprint 827 (A3): the shared parser. Three hand-listed formats silently
        # skipped every row whose date came from an Excel date cell
        # ("2019-01-01 00:00:00") or was written 2019/01/01 — the test then
        # reported itself as run with nothing flagged. Sprint 855 (A4): read
        # day-first when the register's date column is DD/MM.
        acq_date = _acquisition_date(e)
        if acq_date is None:
            continue

        years_elapsed = (as_of - acq_date).days / 365.25
        if years_elapsed <= 0 or years_elapsed > e.useful_life * 1.5:
            # Asset is either future-dated or already beyond 1.5× life;
            # FA-T01 (fully-depreciated) and FA-T03 (over-depreciation)
            # cover those cases — skip to avoid double-flagging.
            continue

        method = (e.depreciation_method or "").lower()
        # Sprint 827 (A2): accumulated depreciation never exceeds the depreciable
        # base. Uncapped, an asset between 1.0x and 1.5x its life "expected"
        # more depreciation than its cost and was flagged HIGH.
        depreciable_base = e.cost - e.residual_value
        if depreciable_base <= 0:
            continue
        life = Decimal(str(e.useful_life))
        if "straight" in method or method in ("sl", "s/l", "s-l"):
            method_used = "Straight-Line"
            tolerance = SL_TOLERANCE
            rate = Decimal("0")
        elif "declining" in method or "ddb" in method or "double" in method:
            # Sprint 827 (A1): compound declining balance. The previous form took
            # rate x the *current* NBV x years elapsed, which is not DDB at all —
            # every correctly depreciated DDB asset was flagged HIGH (66-304%).
            # Accumulated after t years at rate r is cost x (1 - (1 - r)^t),
            # floored at salvage. "150" in the method selects 150% DB.
            factor = Decimal("1.5") if "150" in method else Decimal("2")
            rate = factor / life
            method_used = "150% Declining Balance" if factor == Decimal("1.5") else "Double-Declining Balance"
            tolerance = DDB_TOLERANCE
        else:
            # Unknown method — skip rather than mis-flag.
            continue

        # Sprint 827 (A6): registers that carry accumulated depreciation as a
        # contra (negative) balance are comparing magnitudes, not signs.
        reported_accum = abs(e.accumulated_depreciation)
        half_year_t = (as_of - _half_year_midpoint(acq_date, as_of)).days / 365.25
        candidates: list[tuple[Decimal, Decimal, str, float]] = []
        for convention, t in (("actual days", years_elapsed), ("half-year", half_year_t)):
            if t <= 0:
                continue
            if rate == 0:
                expected = depreciable_base / life * Decimal(str(t))
            elif rate >= 1:
                # The whole base goes in year one (life <= 2y for DDB, <= 1.5y
                # for 150% DB); the cap brings it to cost - salvage. It was
                # skipped, hiding under-depreciation (PR #206 review).
                expected = e.cost
            else:
                expected = e.cost * (1 - Decimal(str(float(1 - rate) ** t)))
            expected = min(expected, depreciable_base)
            if expected <= 0:
                continue
            candidates.append((abs(reported_accum - expected) / expected, expected, convention, t))
        if not candidates:
            continue
        variance, expected_accum, convention, convention_years = min(candidates, key=lambda c: c[0])
        if variance <= tolerance:
            continue

        severity = Severity.HIGH if variance > Decimal("0.25") else Severity.MEDIUM
        flagged.append(
            FlaggedFixedAsset(
                entry=e,
                test_name="Depreciation Recalculation",
                test_key="depreciation_recalc",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=(
                    f"{method_used}: expected ~${expected_accum:,.2f} accumulated "
                    f"after {convention_years:.1f}y ({convention} convention, the closer of "
                    f"actual days and half-year), but reported "
                    f"${reported_accum:,.2f} (variance {variance:.1%}). "
                    "IAS 16 / ASC 360 — review useful life, method, or salvage value."
                ),
                confidence=0.80,
                details={
                    "method": method_used,
                    "convention": convention,
                    "expected_accum": float(expected_accum),
                    "reported_accum": float(reported_accum),
                    "years_elapsed": round(years_elapsed, 2),
                    "convention_years": round(convention_years, 2),
                    "variance_pct": round(float(variance), 4),
                    "tolerance": float(tolerance),
                },
            )
        )

    flag_rate = len(flagged) / max(len(entries), 1)
    return FATestResult(
        test_name="Depreciation Recalculation",
        test_key="depreciation_recalc",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH if flagged else Severity.LOW,
        description=(
            "Recalculates expected depreciation (IAS 16 / ASC 360) when "
            "cost, useful life, method, and acquisition date are present; "
            "flags variance >5% (SL) or >15% (DDB) under both the actual-days and "
            "half-year conventions. "
            f"Elapsed years measured to {as_of.isoformat()} ({reference_date_label(config.reference_date_source)})."
        ),
        flagged_entries=flagged,
    )


@with_parse_memo
def run_fa_test_battery(
    entries: list[FixedAssetEntry],
    config: Optional[FixedAssetTestingConfig] = None,
) -> list[FATestResult]:
    """Run the fixed-asset test battery.

    Sprint 682: 11 tests (added FA-T11 Depreciation Recalculation).
    """
    if config is None:
        config = FixedAssetTestingConfig()

    return [
        # Tier 1 — Structural
        test_fully_depreciated_assets(entries, config),
        test_missing_required_fields(entries, config),
        test_negative_values(entries, config),
        test_over_depreciation(entries, config),
        # Tier 2 — Statistical
        test_useful_life_outliers(entries, config),
        test_cost_zscore_outliers(entries, config),
        test_age_concentration(entries, config),
        test_depreciation_recalculation(entries, config),  # Sprint 682: FA-T11
        # Tier 3 — Advanced
        test_duplicate_assets(entries, config),
        test_residual_value_anomalies(entries, config),
        test_lease_indicators(entries, config),
    ]


def calculate_fa_composite_score(
    test_results: list[FATestResult],
    total_entries: int,
) -> FACompositeScore:
    """Calculate composite diagnostic score from fixed asset test results.

    Delegates to shared test aggregator (Sprint 152).
    """
    result = _shared_calc_cs(test_results, total_entries)

    return FACompositeScore(
        score=result.score,
        risk_tier=result.risk_tier,
        tests_run=result.tests_run,
        total_entries=result.total_entries,
        total_flagged=result.total_flagged,
        flag_rate=result.flag_rate,
        flags_by_severity=result.flags_by_severity,
        top_findings=result.top_findings,
        score_basis=result.score_basis,
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


class FixedAssetTestingEngine(AuditEngineBase):
    """Fixed-asset testing engine on AuditEngineBase (Sprint 819 item 5).

    Same steps, in the same order, as the procedural ``run_fixed_asset_testing``
    it replaced: each method delegates to the module-level helper that function
    called. No rows are cleared (the base ``cleanup`` is a no-op), as before.
    """

    OVERRIDABLE_COLUMNS = (
        "asset_id_column",
        "description_column",
        "cost_column",
        "accumulated_depreciation_column",
        "acquisition_date_column",
        "useful_life_column",
        "depreciation_method_column",
        "residual_value_column",
        "location_column",
        "category_column",
        "net_book_value_column",
    )

    def __init__(self, config: Optional[FixedAssetTestingConfig] = None):
        super().__init__(config or FixedAssetTestingConfig())

    def detect_columns(self, column_names: list[str]) -> Any:
        return detect_fa_columns(column_names)

    def parse_data(self, rows: list[dict], detection: Any) -> list:
        # Sprint 855 (A8): runs after the manual overrides, so a mapped months column is noted too.
        if life_column_is_months(detection.useful_life_column):
            detection.detection_notes.append(
                f"Useful life column '{detection.useful_life_column}' is in months; converted to years."
            )
        return parse_fa_entries(rows, detection)

    def run_quality_checks(self, entries: list, detection: Any) -> Any:
        return assess_fa_data_quality(entries, detection)

    def run_tests(self, entries: list) -> Any:
        return run_fa_test_battery(entries, self.config)

    def compute_score(self, test_results: list, entry_count: int) -> Any:
        return calculate_fa_composite_score(test_results, entry_count)

    def build_result(
        self,
        composite: Any,
        test_output: Any,
        data_quality: Any,
        detection: Any,
        entries: list,
        enrichment: Any,
    ) -> Any:
        return FATestingResult(
            composite_score=composite,
            test_results=test_output,
            data_quality=data_quality,
            column_detection=detection,
        )


@with_parse_memo
def run_fixed_asset_testing(
    rows: list[dict],
    column_names: list[str],
    config: Optional[FixedAssetTestingConfig] = None,
    column_mapping: Optional[dict] = None,
) -> FATestingResult:
    """Run the complete fixed asset testing pipeline.

    Args:
        rows: List of dicts (raw fixed asset register rows)
        column_names: List of column header names
        config: Optional testing configuration
        column_mapping: Optional manual column mapping override

    Returns:
        FATestingResult with composite score, test results, data quality.
    """
    engine = FixedAssetTestingEngine(config)
    result: FATestingResult = engine.run_pipeline(rows, column_names, column_mapping)
    return result


# =============================================================================
# Sprint 700/703: Anomaly-framework contract registration
# =============================================================================
from shared.engine_contract import DetectionPreconditions, EngineInputContract

ENGINE_CONTRACT = EngineInputContract(
    tool="fixed_asset",
    required_columns=frozenset({"Asset ID", "Cost"}),
    optional_columns=frozenset(
        {
            "Description",
            "Accumulated Depreciation",
            "Useful Life Years",
            "Acquisition Date",
            "Depreciation Method",
            "Residual Value",
        }
    ),
    entry_point="fixed_asset_testing_engine.run_fixed_asset_testing",
    detection_targets={
        "duplicate_assets": DetectionPreconditions(
            requires_columns=frozenset({"Cost", "Description", "Acquisition Date"}),
            scope="standalone",
            description=(
                "FA-08: dedups on (cost, description, acquisition_date). "
                "A distinct asset_id with the same triple is flagged as "
                "double-booked capitalisation."
            ),
            emits_fields=frozenset({"entries_flagged", "flagged_entries"}),
        ),
    },
)
