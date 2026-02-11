"""
Fixed Asset Testing Engine — Sprint 114

Automated fixed asset register testing addressing IAS 16/ASC 360 property,
plant and equipment assertions. Parses fixed asset registers (CSV/Excel),
detects columns, runs 9 tests across structural, statistical, and advanced tiers.

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

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, date
import math
import statistics

from shared.testing_enums import RiskTier, TestTier, Severity, SEVERITY_WEIGHTS
from shared.parsing_helpers import safe_float, safe_str, parse_date
from shared.column_detector import ColumnFieldConfig, detect_columns


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
]

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
    ColumnFieldConfig("cost_column", FA_COST_PATTERNS, required=True,
                      missing_note="Could not identify a Cost column", priority=25),
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
        "asset_id_column", "description_column", "cost_column",
        "accumulated_depreciation_column", "acquisition_date_column",
        "useful_life_column", "depreciation_method_column",
        "residual_value_column", "location_column", "category_column",
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
    cost: float = 0.0
    accumulated_depreciation: float = 0.0
    acquisition_date: Optional[str] = None
    useful_life: Optional[float] = None
    depreciation_method: Optional[str] = None
    residual_value: float = 0.0
    location: Optional[str] = None
    category: Optional[str] = None
    net_book_value: Optional[float] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "description": self.description,
            "cost": self.cost,
            "accumulated_depreciation": self.accumulated_depreciation,
            "acquisition_date": self.acquisition_date,
            "useful_life": self.useful_life,
            "depreciation_method": self.depreciation_method,
            "residual_value": self.residual_value,
            "location": self.location,
            "category": self.category,
            "net_book_value": self.net_book_value,
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
            "details": self.details,
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


def _safe_float_optional(value) -> Optional[float]:
    """Like safe_float but returns None for missing/invalid values."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None
    try:
        f = float(value)
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


def _asset_age_years(acquisition_date_str: Optional[str], reference_date: Optional[date] = None) -> Optional[float]:
    """Calculate age of an asset in years from acquisition date."""
    d = parse_date(acquisition_date_str)
    if d is None:
        return None
    ref = reference_date or date.today()
    delta = ref - d
    return delta.days / 365.25


# =============================================================================
# PARSER
# =============================================================================

def parse_fa_entries(
    rows: list[dict],
    detection: FAColumnDetection,
) -> list[FixedAssetEntry]:
    """Parse raw rows into FixedAssetEntry objects using detected columns."""
    entries: list[FixedAssetEntry] = []
    for idx, row in enumerate(rows):
        entry = FixedAssetEntry(row_number=idx + 1)
        if detection.asset_id_column:
            entry.asset_id = safe_str(row.get(detection.asset_id_column))
        if detection.description_column:
            entry.description = safe_str(row.get(detection.description_column))
        if detection.cost_column:
            entry.cost = safe_float(row.get(detection.cost_column))
        if detection.accumulated_depreciation_column:
            entry.accumulated_depreciation = safe_float(row.get(detection.accumulated_depreciation_column))
        if detection.acquisition_date_column:
            entry.acquisition_date = safe_str(row.get(detection.acquisition_date_column))
        if detection.useful_life_column:
            entry.useful_life = _safe_float_optional(row.get(detection.useful_life_column))
        if detection.depreciation_method_column:
            entry.depreciation_method = safe_str(row.get(detection.depreciation_method_column))
        if detection.residual_value_column:
            entry.residual_value = safe_float(row.get(detection.residual_value_column))
        if detection.location_column:
            entry.location = safe_str(row.get(detection.location_column))
        if detection.category_column:
            entry.category = safe_str(row.get(detection.category_column))
        if detection.net_book_value_column:
            entry.net_book_value = _safe_float_optional(row.get(detection.net_book_value_column))
        entries.append(entry)
    return entries


# =============================================================================
# DATA QUALITY
# =============================================================================

def assess_fa_data_quality(
    entries: list[FixedAssetEntry],
    detection: FAColumnDetection,
) -> FADataQuality:
    """Assess quality and completeness of fixed asset data."""
    total = len(entries)
    if total == 0:
        return FADataQuality(completeness_score=0.0, total_rows=0)

    issues: list[str] = []
    fill_rates: dict[str, float] = {}

    id_filled = sum(1 for e in entries if e.asset_id or e.description)
    fill_rates["identifier"] = id_filled / total

    cost_filled = sum(1 for e in entries if e.cost != 0)
    fill_rates["cost"] = cost_filled / total

    if detection.accumulated_depreciation_column:
        depr_filled = sum(1 for e in entries if e.accumulated_depreciation != 0)
        fill_rates["accumulated_depreciation"] = depr_filled / total

    if detection.acquisition_date_column:
        date_filled = sum(1 for e in entries if e.acquisition_date)
        fill_rates["acquisition_date"] = date_filled / total
        if fill_rates["acquisition_date"] < 0.80:
            issues.append(f"Low acquisition date fill rate: {fill_rates['acquisition_date']:.0%}")

    if detection.useful_life_column:
        life_filled = sum(1 for e in entries if e.useful_life is not None)
        fill_rates["useful_life"] = life_filled / total

    if detection.category_column:
        cat_filled = sum(1 for e in entries if e.category)
        fill_rates["category"] = cat_filled / total

    if fill_rates.get("identifier", 0) < 0.90:
        issues.append(f"Missing identifier on {total - id_filled} entries")
    if fill_rates.get("cost", 0) < 0.90:
        issues.append(f"{total - cost_filled} entries have zero cost")

    # Weighted score
    weights = {"identifier": 0.25, "cost": 0.35}
    optional_fields = [k for k in fill_rates if k not in weights]
    optional_weight = 0.40 / max(len(optional_fields), 1)
    for k in optional_fields:
        weights[k] = optional_weight

    score = sum(fill_rates.get(k, 0) * w for k, w in weights.items()) * 100

    return FADataQuality(
        completeness_score=min(score, 100.0),
        field_fill_rates=fill_rates,
        detected_issues=issues,
        total_rows=total,
    )


# =============================================================================
# RISK TIER CALCULATION
# =============================================================================

def score_to_risk_tier(score: float) -> RiskTier:
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

        flagged.append(FlaggedFixedAsset(
            entry=e,
            test_name="Fully Depreciated Assets",
            test_key="fully_depreciated",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Fully depreciated: {e.asset_id or e.description or 'unknown'}"
                  f" cost=${cost:,.2f}, accum depr=${accum:,.2f}, NBV=${nbv:,.2f}",
            confidence=0.85,
            details={"cost": cost, "accumulated_depreciation": accum, "nbv": nbv},
        ))

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

        flagged.append(FlaggedFixedAsset(
            entry=e,
            test_name="Missing Required Fields",
            test_key="missing_fields",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Missing fields: {', '.join(missing)}"
                  f" — {e.asset_id or e.description or f'row {e.row_number}'}",
            confidence=0.90,
            details={"missing_fields": missing, "missing_count": len(missing)},
        ))

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

        flagged.append(FlaggedFixedAsset(
            entry=e,
            test_name="Negative Values",
            test_key="negative_values",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Negative values: {'; '.join(issues_found)}"
                  f" — {e.asset_id or e.description or f'row {e.row_number}'}",
            confidence=0.95,
            details={"cost": e.cost, "accumulated_depreciation": e.accumulated_depreciation},
        ))

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
        if excess <= cost * 0.01:
            continue

        excess_pct = excess / cost
        severity = Severity.HIGH if excess_pct > 0.10 else Severity.MEDIUM

        flagged.append(FlaggedFixedAsset(
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
        ))

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

        flagged.append(FlaggedFixedAsset(
            entry=e,
            test_name="Useful Life Outliers",
            test_key="useful_life_outliers",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Useful life {life:.1f} years {issue_type}"
                  f" — {e.asset_id or e.description or f'row {e.row_number}'}",
            confidence=0.80,
            details={"useful_life": life, "min_threshold": config.useful_life_min_years,
                     "max_threshold": config.useful_life_max_years},
        ))

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

        if z > 5:
            severity = Severity.HIGH
        elif z > 4:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        flagged.append(FlaggedFixedAsset(
            entry=e,
            test_name="Cost Z-Score Outliers",
            test_key="cost_zscore_outliers",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Outlier cost: ${abs(e.cost):,.2f} (z-score: {z:.1f}, mean: ${mean:,.2f})"
                  f" — {e.asset_id or e.description or f'row {e.row_number}'}",
            confidence=min(0.60 + z * 0.05, 0.95),
            details={"z_score": round(z, 2), "mean": round(mean, 2), "stdev": round(stdev, 2)},
        ))

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


def test_age_concentration(
    entries: list[FixedAssetEntry],
    config: FixedAssetTestingConfig,
) -> FATestResult:
    """FA-07: Asset Age Concentration.

    Flags if >50% of total asset cost is concentrated in a single
    acquisition year, indicating potential bulk capitalization risk.
    """
    dated = [(e, parse_date(e.acquisition_date)) for e in entries]
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

    total_cost = sum(abs(e.cost) for e, _ in dated_entries)
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
    year_costs: dict[int, float] = {}
    year_entries: dict[int, list[FixedAssetEntry]] = {}
    for e, d in dated_entries:
        yr = d.year
        year_costs[yr] = year_costs.get(yr, 0) + abs(e.cost)
        year_entries.setdefault(yr, []).append(e)

    flagged: list[FlaggedFixedAsset] = []
    for yr, yr_cost in year_costs.items():
        pct = yr_cost / total_cost
        if pct <= config.age_concentration_threshold_pct:
            continue

        severity = Severity.HIGH if pct > 0.70 else Severity.MEDIUM

        for e in year_entries[yr]:
            flagged.append(FlaggedFixedAsset(
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
            ))

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
        if key == (0.0, "", ""):
            continue  # Skip blank entries
        groups.setdefault(key, []).append(e)

    flagged: list[FlaggedFixedAsset] = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        cost, desc, acq_date = key
        severity = Severity.HIGH if abs(cost) > 50000 else Severity.MEDIUM

        for e in group:
            flagged.append(FlaggedFixedAsset(
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
            ))

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
            flagged.append(FlaggedFixedAsset(
                entry=e,
                test_name="Residual Value Anomalies",
                test_key="residual_value_anomalies",
                test_tier=TestTier.ADVANCED,
                severity=Severity.HIGH,
                issue=f"Negative residual value: ${e.residual_value:,.2f}"
                      f" — {e.asset_id or e.description or f'row {e.row_number}'}",
                confidence=0.95,
                details={"residual_value": e.residual_value, "cost": cost},
            ))
            continue

        if e.residual_value == 0:
            continue

        residual_pct = e.residual_value / cost
        if residual_pct <= config.residual_max_pct:
            continue

        severity = Severity.HIGH if residual_pct > 0.50 else Severity.MEDIUM

        flagged.append(FlaggedFixedAsset(
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
        ))

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


# =============================================================================
# TEST BATTERY + SCORING
# =============================================================================

def run_fa_test_battery(
    entries: list[FixedAssetEntry],
    config: Optional[FixedAssetTestingConfig] = None,
) -> list[FATestResult]:
    """Run all 9 fixed asset tests."""
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
        # Tier 3 — Advanced
        test_duplicate_assets(entries, config),
        test_residual_value_anomalies(entries, config),
    ]


def calculate_fa_composite_score(
    test_results: list[FATestResult],
    total_entries: int,
) -> FACompositeScore:
    """Calculate composite risk score from fixed asset test results."""
    if total_entries == 0:
        return FACompositeScore(
            score=0.0,
            risk_tier=RiskTier.LOW,
            tests_run=len(test_results),
            total_entries=0,
            total_flagged=0,
            flag_rate=0.0,
        )

    entry_test_counts: dict[int, int] = {}
    all_flagged_rows: set[int] = set()
    flags_by_severity: dict[str, int] = {"high": 0, "medium": 0, "low": 0}

    for tr in test_results:
        for fp in tr.flagged_entries:
            row = fp.entry.row_number
            entry_test_counts[row] = entry_test_counts.get(row, 0) + 1
            all_flagged_rows.add(row)
            flags_by_severity[fp.severity.value] = flags_by_severity.get(fp.severity.value, 0) + 1

    weighted_sum = 0.0
    for tr in test_results:
        weight = SEVERITY_WEIGHTS.get(tr.severity, 1.0)
        weighted_sum += tr.flag_rate * weight

    max_possible = sum(SEVERITY_WEIGHTS.get(tr.severity, 1.0) for tr in test_results)
    base_score = (weighted_sum / max_possible) * 100 if max_possible > 0 else 0.0

    multi_flag_count = sum(1 for c in entry_test_counts.values() if c >= 3)
    multi_flag_ratio = multi_flag_count / max(total_entries, 1)
    multiplier = 1.0 + (multi_flag_ratio * 0.25)

    score = min(base_score * multiplier, 100.0)

    top_findings: list[str] = []
    for tr in sorted(test_results, key=lambda t: t.flag_rate, reverse=True):
        if tr.entries_flagged > 0:
            top_findings.append(
                f"{tr.test_name}: {tr.entries_flagged} entries flagged ({tr.flag_rate:.1%})"
            )

    total_flagged = len(all_flagged_rows)
    flag_rate = total_flagged / max(total_entries, 1)

    return FACompositeScore(
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
    if config is None:
        config = FixedAssetTestingConfig()

    # 1. Detect columns
    detection = detect_fa_columns(column_names)

    # Apply manual overrides
    if column_mapping:
        for attr in ("asset_id_column", "description_column", "cost_column",
                     "accumulated_depreciation_column", "acquisition_date_column",
                     "useful_life_column", "depreciation_method_column",
                     "residual_value_column", "location_column", "category_column",
                     "net_book_value_column"):
            if attr in column_mapping:
                setattr(detection, attr, column_mapping[attr])
        detection.overall_confidence = 1.0

    # 2. Parse entries
    entries = parse_fa_entries(rows, detection)

    # 3. Assess data quality
    data_quality = assess_fa_data_quality(entries, detection)

    # 4. Run test battery
    test_results = run_fa_test_battery(entries, config)

    # 5. Calculate composite score
    composite = calculate_fa_composite_score(test_results, len(entries))

    return FATestingResult(
        composite_score=composite,
        test_results=test_results,
        data_quality=data_quality,
        column_detection=detection,
    )
