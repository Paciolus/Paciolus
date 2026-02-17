"""
Inventory Testing Engine — Sprint 117

Automated inventory register testing addressing IAS 2/ASC 330 inventory
assertions. Parses inventory registers (CSV/Excel), detects columns,
runs 9 tests across structural, statistical, and advanced tiers.

ZERO-STORAGE COMPLIANCE:
- All files processed in-memory only
- Test results are ephemeral (computed on demand)
- No raw inventory data is stored

Audit Standards References:
- IAS 2: Inventories
- ASC 330: Inventory
- ISA 501: Audit Evidence — Specific Considerations for Selected Items
- ISA 540: Auditing Accounting Estimates
- ISA 500: Audit Evidence

This engine documents automated inventory anomaly indicators — it does NOT
constitute an NRV adequacy opinion or obsolescence determination.
"""

import math
import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from shared.column_detector import ColumnFieldConfig, detect_columns
from shared.data_quality import FieldQualityConfig
from shared.data_quality import assess_data_quality as _shared_assess_dq
from shared.parsing_helpers import parse_date, safe_float, safe_str
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
class InventoryTestingConfig:
    """Configurable thresholds for all inventory tests."""
    # IN-01: Missing required fields
    missing_fields_enabled: bool = True

    # IN-02: Negative quantities or costs
    negative_values_enabled: bool = True

    # IN-03: Extended value mismatch
    value_mismatch_enabled: bool = True
    value_mismatch_tolerance_pct: float = 0.01  # 1% tolerance

    # IN-04: Unit cost z-score outliers
    cost_zscore_threshold: float = 2.5
    cost_zscore_min_entries: int = 10

    # IN-05: Quantity z-score outliers
    qty_zscore_threshold: float = 2.5
    qty_zscore_min_entries: int = 10

    # IN-06: Slow-moving inventory
    slow_moving_days: int = 180

    # IN-07: Category concentration
    category_concentration_threshold_pct: float = 0.50

    # IN-08: Duplicate items
    duplicate_enabled: bool = True

    # IN-09: Zero-value items
    zero_value_enabled: bool = True


# =============================================================================
# INVENTORY COLUMN DETECTION
# =============================================================================

INV_ITEM_ID_PATTERNS = [
    (r"^item\s*id$", 1.0, True),
    (r"^item\s*number$", 0.98, True),
    (r"^item\s*no$", 0.95, True),
    (r"^item\s*#$", 0.95, True),
    (r"^item\s*code$", 0.90, True),
    (r"^sku$", 0.95, True),
    (r"^sku\s*number$", 0.95, True),
    (r"^product\s*id$", 0.90, True),
    (r"^product\s*code$", 0.85, True),
    (r"^part\s*number$", 0.85, True),
    (r"^part\s*no$", 0.85, True),
    (r"^stock\s*code$", 0.80, True),
    (r"^material\s*number$", 0.80, True),
    (r"item.?id", 0.70, False),
    (r"item.?num", 0.65, False),
    (r"sku", 0.60, False),
    (r"part.?num", 0.55, False),
]

INV_DESCRIPTION_PATTERNS = [
    (r"^description$", 1.0, True),
    (r"^item\s*description$", 0.98, True),
    (r"^item\s*name$", 0.95, True),
    (r"^product\s*name$", 0.90, True),
    (r"^product\s*description$", 0.95, True),
    (r"^name$", 0.70, True),
    (r"^material\s*description$", 0.85, True),
    (r"description", 0.60, False),
]

INV_QUANTITY_PATTERNS = [
    (r"^quantity$", 1.0, True),
    (r"^qty$", 0.95, True),
    (r"^quantity\s*on\s*hand$", 1.0, True),
    (r"^qty\s*on\s*hand$", 0.95, True),
    (r"^on\s*hand$", 0.80, True),
    (r"^stock\s*qty$", 0.85, True),
    (r"^stock\s*quantity$", 0.90, True),
    (r"^units$", 0.70, True),
    (r"^count$", 0.65, True),
    (r"^balance\s*qty$", 0.80, True),
    (r"quantity", 0.55, False),
    (r"^qty", 0.50, False),
]

INV_UNIT_COST_PATTERNS = [
    (r"^unit\s*cost$", 1.0, True),
    (r"^cost\s*per\s*unit$", 0.98, True),
    (r"^unit\s*price$", 0.90, True),
    (r"^average\s*cost$", 0.90, True),
    (r"^avg\s*cost$", 0.85, True),
    (r"^standard\s*cost$", 0.85, True),
    (r"^cost$", 0.75, True),
    (r"^price$", 0.60, True),
    (r"^weighted\s*average\s*cost$", 0.90, True),
    (r"unit.?cost", 0.70, False),
    (r"cost.?per", 0.65, False),
    (r"avg.?cost", 0.60, False),
]

INV_EXTENDED_VALUE_PATTERNS = [
    (r"^extended\s*value$", 1.0, True),
    (r"^extended\s*amount$", 0.98, True),
    (r"^total\s*value$", 0.95, True),
    (r"^total\s*cost$", 0.90, True),
    (r"^inventory\s*value$", 0.95, True),
    (r"^value$", 0.70, True),
    (r"^amount$", 0.65, True),
    (r"^line\s*total$", 0.80, True),
    (r"^extended$", 0.75, True),
    (r"^net\s*value$", 0.80, True),
    (r"^book\s*value$", 0.75, True),
    (r"extended.?val", 0.70, False),
    (r"total.?val", 0.60, False),
    (r"inventory.?val", 0.65, False),
]

INV_LOCATION_PATTERNS = [
    (r"^location$", 1.0, True),
    (r"^warehouse$", 0.95, True),
    (r"^warehouse\s*location$", 0.98, True),
    (r"^site$", 0.80, True),
    (r"^bin$", 0.70, True),
    (r"^bin\s*location$", 0.85, True),
    (r"^storage\s*location$", 0.90, True),
    (r"^store$", 0.70, True),
    (r"^plant$", 0.75, True),
    (r"location", 0.55, False),
    (r"warehouse", 0.50, False),
]

INV_LAST_MOVEMENT_PATTERNS = [
    (r"^last\s*movement\s*date$", 1.0, True),
    (r"^last\s*activity\s*date$", 0.95, True),
    (r"^last\s*transaction\s*date$", 0.95, True),
    (r"^last\s*receipt\s*date$", 0.85, True),
    (r"^last\s*issue\s*date$", 0.85, True),
    (r"^last\s*used\s*date$", 0.80, True),
    (r"^last\s*moved$", 0.85, True),
    (r"^last\s*sold\s*date$", 0.80, True),
    (r"^last\s*shipment\s*date$", 0.80, True),
    (r"last.?movement", 0.70, False),
    (r"last.?activity", 0.65, False),
    (r"last.?transaction", 0.60, False),
]

INV_CATEGORY_PATTERNS = [
    (r"^category$", 0.90, True),
    (r"^item\s*category$", 1.0, True),
    (r"^product\s*category$", 0.95, True),
    (r"^item\s*type$", 0.85, True),
    (r"^product\s*type$", 0.85, True),
    (r"^class$", 0.70, True),
    (r"^group$", 0.60, True),
    (r"^material\s*group$", 0.80, True),
    (r"^inventory\s*type$", 0.85, True),
    (r"category", 0.55, False),
    (r"item.?type", 0.50, False),
]

# Shared column detector configs (replaces InvColumnType + _INV_COLUMN_PATTERNS)
INV_COLUMN_CONFIGS: list[ColumnFieldConfig] = [
    ColumnFieldConfig("quantity_column", INV_QUANTITY_PATTERNS, required=True,
                      missing_note="Could not identify a Quantity column", priority=10),
    ColumnFieldConfig("unit_cost_column", INV_UNIT_COST_PATTERNS, priority=15),
    ColumnFieldConfig("extended_value_column", INV_EXTENDED_VALUE_PATTERNS, priority=20),
    ColumnFieldConfig("item_id_column", INV_ITEM_ID_PATTERNS, priority=25),
    ColumnFieldConfig("description_column", INV_DESCRIPTION_PATTERNS, priority=30),
    ColumnFieldConfig("location_column", INV_LOCATION_PATTERNS, priority=40),
    ColumnFieldConfig("last_movement_date_column", INV_LAST_MOVEMENT_PATTERNS, priority=45),
    ColumnFieldConfig("category_column", INV_CATEGORY_PATTERNS, priority=50),
]


@dataclass
class InvColumnDetection:
    """Result of inventory column detection."""
    item_id_column: Optional[str] = None
    description_column: Optional[str] = None
    quantity_column: Optional[str] = None
    unit_cost_column: Optional[str] = None
    extended_value_column: Optional[str] = None
    location_column: Optional[str] = None
    last_movement_date_column: Optional[str] = None
    category_column: Optional[str] = None

    overall_confidence: float = 0.0
    all_columns: list[str] = field(default_factory=list)
    detection_notes: list[str] = field(default_factory=list)

    @property
    def requires_mapping(self) -> bool:
        return self.overall_confidence < 0.70

    def to_dict(self) -> dict:
        return {
            "item_id_column": self.item_id_column,
            "description_column": self.description_column,
            "quantity_column": self.quantity_column,
            "unit_cost_column": self.unit_cost_column,
            "extended_value_column": self.extended_value_column,
            "location_column": self.location_column,
            "last_movement_date_column": self.last_movement_date_column,
            "category_column": self.category_column,
            "overall_confidence": round(self.overall_confidence, 2),
            "requires_mapping": self.requires_mapping,
            "all_columns": self.all_columns,
            "detection_notes": self.detection_notes,
        }


def detect_inv_columns(column_names: list[str]) -> InvColumnDetection:
    """Auto-detect inventory register columns using shared column detector."""
    detection = detect_columns(column_names, INV_COLUMN_CONFIGS)
    result = InvColumnDetection(all_columns=detection.all_columns)

    # Map shared detection results to inventory-specific fields
    field_names = [
        "item_id_column", "description_column", "quantity_column",
        "unit_cost_column", "extended_value_column", "location_column",
        "last_movement_date_column", "category_column",
    ]
    for field_name in field_names:
        col = detection.get_column(field_name)
        if col:
            setattr(result, field_name, col)

    notes = list(detection.detection_notes)

    # Confidence: quantity + (cost or value) + (item_id or description)
    required_confs: list[float] = [
        detection.get_confidence("quantity_column") if result.quantity_column else 0.0,
    ]

    # Need at least cost or value
    cost_conf = detection.get_confidence("unit_cost_column") if result.unit_cost_column else 0.0
    value_conf = detection.get_confidence("extended_value_column") if result.extended_value_column else 0.0
    if cost_conf > 0.0:
        required_confs.append(cost_conf)
    elif value_conf > 0.0:
        required_confs.append(value_conf)
    else:
        notes.append("Could not identify a Unit Cost or Extended Value column")
        required_confs.append(0.0)

    # Identifier: item_id or description
    id_conf = max(
        detection.get_confidence("item_id_column") if result.item_id_column else 0.0,
        detection.get_confidence("description_column") if result.description_column else 0.0,
    )
    if id_conf == 0.0:
        notes.append("Could not identify an Item ID or Description column")
    required_confs.append(id_conf)

    result.overall_confidence = min(required_confs) if required_confs else 0.0
    result.detection_notes = notes
    return result


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class InventoryEntry:
    """A single line from the inventory register."""
    item_id: Optional[str] = None
    description: Optional[str] = None
    quantity: float = 0.0
    unit_cost: float = 0.0
    extended_value: float = 0.0
    location: Optional[str] = None
    last_movement_date: Optional[str] = None
    category: Optional[str] = None
    row_number: int = 0

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "description": self.description,
            "quantity": self.quantity,
            "unit_cost": self.unit_cost,
            "extended_value": self.extended_value,
            "location": self.location,
            "last_movement_date": self.last_movement_date,
            "category": self.category,
            "row_number": self.row_number,
        }


@dataclass
class FlaggedInventoryItem:
    """An inventory entry flagged by a test."""
    entry: InventoryEntry
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
class InvTestResult:
    """Result of a single inventory test."""
    test_name: str
    test_key: str
    test_tier: TestTier
    entries_flagged: int
    total_entries: int
    flag_rate: float
    severity: Severity
    description: str
    flagged_entries: list[FlaggedInventoryItem] = field(default_factory=list)

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
class InvDataQuality:
    """Quality assessment of the inventory data."""
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
class InvCompositeScore:
    """Overall inventory testing composite score."""
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
class InvTestingResult:
    """Complete result of inventory testing."""
    composite_score: InvCompositeScore
    test_results: list[InvTestResult] = field(default_factory=list)
    data_quality: Optional[InvDataQuality] = None
    column_detection: Optional[InvColumnDetection] = None

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite_score.to_dict(),
            "test_results": [t.to_dict() for t in self.test_results],
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "column_detection": self.column_detection.to_dict() if self.column_detection else None,
        }


def _days_since(date_str: Optional[str], reference_date: Optional[date] = None) -> Optional[int]:
    """Calculate days since a given date."""
    d = parse_date(date_str)
    if d is None:
        return None
    ref = reference_date or date.today()
    delta = ref - d
    return delta.days


# =============================================================================
# PARSER
# =============================================================================

def parse_inv_entries(
    rows: list[dict],
    detection: InvColumnDetection,
) -> list[InventoryEntry]:
    """Parse raw rows into InventoryEntry objects using detected columns."""
    entries: list[InventoryEntry] = []
    for idx, row in enumerate(rows):
        entry = InventoryEntry(row_number=idx + 1)
        if detection.item_id_column:
            entry.item_id = safe_str(row.get(detection.item_id_column))
        if detection.description_column:
            entry.description = safe_str(row.get(detection.description_column))
        if detection.quantity_column:
            entry.quantity = safe_float(row.get(detection.quantity_column))
        if detection.unit_cost_column:
            entry.unit_cost = safe_float(row.get(detection.unit_cost_column))
        if detection.extended_value_column:
            entry.extended_value = safe_float(row.get(detection.extended_value_column))
        if detection.location_column:
            entry.location = safe_str(row.get(detection.location_column))
        if detection.last_movement_date_column:
            entry.last_movement_date = safe_str(row.get(detection.last_movement_date_column))
        if detection.category_column:
            entry.category = safe_str(row.get(detection.category_column))
        entries.append(entry)
    return entries


# =============================================================================
# DATA QUALITY
# =============================================================================

def assess_inv_data_quality(
    entries: list[InventoryEntry],
    detection: InvColumnDetection,
) -> InvDataQuality:
    """Assess quality and completeness of inventory data.

    Delegates to shared data quality engine (Sprint 152).
    """
    configs: list[FieldQualityConfig] = [
        FieldQualityConfig("identifier", lambda e: e.item_id or e.description, weight=0.25,
                           issue_threshold=0.90, issue_template="Missing identifier on {unfilled} entries"),
        FieldQualityConfig("quantity", lambda e: e.quantity != 0, weight=0.30,
                           issue_threshold=0.90, issue_template="{unfilled} entries have zero quantity"),
    ]

    if detection.unit_cost_column:
        configs.append(FieldQualityConfig("unit_cost", lambda e: e.unit_cost != 0))
    if detection.extended_value_column:
        configs.append(FieldQualityConfig("extended_value", lambda e: e.extended_value != 0))
    if detection.location_column:
        configs.append(FieldQualityConfig("location", lambda e: e.location))
    if detection.last_movement_date_column:
        configs.append(FieldQualityConfig("last_movement_date", lambda e: e.last_movement_date,
                                          issue_threshold=0.80,
                                          issue_template="Low movement date fill rate: {fill_pct}"))
    if detection.category_column:
        configs.append(FieldQualityConfig("category", lambda e: e.category))

    result = _shared_assess_dq(entries, configs, optional_weight_pool=0.45)

    return InvDataQuality(
        completeness_score=result.completeness_score,
        field_fill_rates=result.field_fill_rates,
        detected_issues=result.detected_issues,
        total_rows=result.total_rows,
    )


# score_to_risk_tier is imported from shared.testing_enums (Sprint 152)


# =============================================================================
# TIER 1 — STRUCTURAL TESTS
# =============================================================================

def test_missing_required_fields(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-01: Missing Required Fields.

    Flags entries missing critical register fields (identifier, quantity, cost/value).
    """
    if not config.missing_fields_enabled:
        return InvTestResult(
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

    flagged: list[FlaggedInventoryItem] = []
    for e in entries:
        missing: list[str] = []
        if not e.item_id and not e.description:
            missing.append("identifier (item_id or description)")
        if e.quantity == 0 and e.extended_value == 0:
            missing.append("quantity")
        if e.unit_cost == 0 and e.extended_value == 0:
            missing.append("cost or value")

        if not missing:
            continue

        severity = Severity.HIGH if len(missing) >= 2 else Severity.MEDIUM

        flagged.append(FlaggedInventoryItem(
            entry=e,
            test_name="Missing Required Fields",
            test_key="missing_fields",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Missing fields: {', '.join(missing)}"
                  f" — {e.item_id or e.description or f'row {e.row_number}'}",
            confidence=0.90,
            details={"missing_fields": missing, "missing_count": len(missing)},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Missing Required Fields",
        test_key="missing_fields",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags inventory entries missing critical register fields.",
        flagged_entries=flagged,
    )


def test_negative_values(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-02: Negative Quantities or Costs.

    Flags items with negative quantity, unit cost, or extended value
    which may indicate data entry errors, returns, or adjustments.
    """
    if not config.negative_values_enabled:
        return InvTestResult(
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

    flagged: list[FlaggedInventoryItem] = []
    for e in entries:
        issues_found: list[str] = []
        if e.quantity < 0:
            issues_found.append(f"negative quantity={e.quantity:,.2f}")
        if e.unit_cost < 0:
            issues_found.append(f"negative unit cost=${e.unit_cost:,.2f}")
        if e.extended_value < 0:
            issues_found.append(f"negative value=${e.extended_value:,.2f}")

        if not issues_found:
            continue

        amt = max(abs(e.extended_value), abs(e.unit_cost * e.quantity))
        severity = Severity.HIGH if amt > 50000 else Severity.MEDIUM

        flagged.append(FlaggedInventoryItem(
            entry=e,
            test_name="Negative Values",
            test_key="negative_values",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Negative values: {'; '.join(issues_found)}"
                  f" — {e.item_id or e.description or f'row {e.row_number}'}",
            confidence=0.95,
            details={"quantity": e.quantity, "unit_cost": e.unit_cost, "extended_value": e.extended_value},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Negative Values",
        test_key="negative_values",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags items with negative quantity, unit cost, or extended value.",
        flagged_entries=flagged,
    )


def test_extended_value_mismatch(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-03: Extended Value Mismatch.

    Flags items where quantity × unit_cost differs from extended_value
    by more than the configured tolerance (default 1%).
    """
    if not config.value_mismatch_enabled:
        return InvTestResult(
            test_name="Extended Value Mismatch",
            test_key="value_mismatch",
            test_tier=TestTier.STRUCTURAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedInventoryItem] = []
    for e in entries:
        if e.unit_cost == 0 or e.quantity == 0 or e.extended_value == 0:
            continue

        expected = e.quantity * e.unit_cost
        if expected == 0:
            continue

        diff = abs(e.extended_value - expected)
        diff_pct = diff / abs(expected)

        if diff_pct <= config.value_mismatch_tolerance_pct:
            continue

        severity = Severity.HIGH if diff > 10000 else Severity.MEDIUM if diff > 1000 else Severity.LOW

        flagged.append(FlaggedInventoryItem(
            entry=e,
            test_name="Extended Value Mismatch",
            test_key="value_mismatch",
            test_tier=TestTier.STRUCTURAL,
            severity=severity,
            issue=f"Value mismatch: qty({e.quantity:,.2f}) × cost(${e.unit_cost:,.2f})"
                  f" = ${expected:,.2f}, but extended=${e.extended_value:,.2f}"
                  f" (diff ${diff:,.2f}, {diff_pct:.1%})"
                  f" — {e.item_id or e.description or f'row {e.row_number}'}",
            confidence=0.90,
            details={
                "expected_value": round(expected, 2),
                "actual_value": round(e.extended_value, 2),
                "difference": round(diff, 2),
                "difference_pct": round(diff_pct, 4),
            },
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Extended Value Mismatch",
        test_key="value_mismatch",
        test_tier=TestTier.STRUCTURAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags items where qty × unit cost differs from extended value by >{config.value_mismatch_tolerance_pct:.0%}.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 2 — STATISTICAL TESTS
# =============================================================================

def test_unit_cost_outliers(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-04: Unit Cost Outliers (Z-Score).

    Flags items with unit cost >2.5 standard deviations from the mean.
    """
    costs = [abs(e.unit_cost) for e in entries if e.unit_cost != 0]

    if len(costs) < config.cost_zscore_min_entries:
        return InvTestResult(
            test_name="Unit Cost Outliers",
            test_key="unit_cost_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description=f"Requires at least {config.cost_zscore_min_entries} entries for statistical analysis.",
            flagged_entries=[],
        )

    mean = statistics.mean(costs)
    stdev = statistics.stdev(costs)
    if stdev == 0:
        return InvTestResult(
            test_name="Unit Cost Outliers",
            test_key="unit_cost_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="All unit costs identical — no variance to analyze.",
            flagged_entries=[],
        )

    flagged: list[FlaggedInventoryItem] = []
    for e in entries:
        if e.unit_cost == 0:
            continue
        z = abs(abs(e.unit_cost) - mean) / stdev
        if z < config.cost_zscore_threshold:
            continue

        severity = zscore_to_severity(z)

        flagged.append(FlaggedInventoryItem(
            entry=e,
            test_name="Unit Cost Outliers",
            test_key="unit_cost_outliers",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Outlier unit cost: ${abs(e.unit_cost):,.2f} (z-score: {z:.1f}, mean: ${mean:,.2f})"
                  f" — {e.item_id or e.description or f'row {e.row_number}'}",
            confidence=min(0.60 + z * 0.05, 0.95),
            details={"z_score": round(z, 2), "mean": round(mean, 2), "stdev": round(stdev, 2)},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Unit Cost Outliers",
        test_key="unit_cost_outliers",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags items with unit cost >{config.cost_zscore_threshold} standard deviations from mean.",
        flagged_entries=flagged,
    )


def test_quantity_outliers(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-05: Quantity Outliers (Z-Score).

    Flags items with quantity >2.5 standard deviations from the mean.
    """
    qtys = [abs(e.quantity) for e in entries if e.quantity != 0]

    if len(qtys) < config.qty_zscore_min_entries:
        return InvTestResult(
            test_name="Quantity Outliers",
            test_key="quantity_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description=f"Requires at least {config.qty_zscore_min_entries} entries for statistical analysis.",
            flagged_entries=[],
        )

    mean = statistics.mean(qtys)
    stdev = statistics.stdev(qtys)
    if stdev == 0:
        return InvTestResult(
            test_name="Quantity Outliers",
            test_key="quantity_outliers",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="All quantities identical — no variance to analyze.",
            flagged_entries=[],
        )

    flagged: list[FlaggedInventoryItem] = []
    for e in entries:
        if e.quantity == 0:
            continue
        z = abs(abs(e.quantity) - mean) / stdev
        if z < config.qty_zscore_threshold:
            continue

        severity = zscore_to_severity(z)

        flagged.append(FlaggedInventoryItem(
            entry=e,
            test_name="Quantity Outliers",
            test_key="quantity_outliers",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"Outlier quantity: {abs(e.quantity):,.2f} (z-score: {z:.1f}, mean: {mean:,.2f})"
                  f" — {e.item_id or e.description or f'row {e.row_number}'}",
            confidence=min(0.60 + z * 0.05, 0.95),
            details={"z_score": round(z, 2), "mean": round(mean, 2), "stdev": round(stdev, 2)},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Quantity Outliers",
        test_key="quantity_outliers",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags items with quantity >{config.qty_zscore_threshold} standard deviations from mean.",
        flagged_entries=flagged,
    )


def test_slow_moving_inventory(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-06: Slow-Moving Inventory.

    Flags items where last movement date exceeds the threshold (default 180 days).
    Slow-moving inventory is an anomaly indicator for potential obsolescence risk.
    """
    entries_with_dates = [e for e in entries if e.last_movement_date]

    if not entries_with_dates:
        return InvTestResult(
            test_name="Slow-Moving Inventory",
            test_key="slow_moving",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="No movement dates available for slow-moving analysis.",
            flagged_entries=[],
        )

    flagged: list[FlaggedInventoryItem] = []
    for e in entries_with_dates:
        days = _days_since(e.last_movement_date)
        if days is None or days <= config.slow_moving_days:
            continue

        value = abs(e.extended_value) if e.extended_value != 0 else abs(e.quantity * e.unit_cost)
        if days > 365:
            severity = Severity.HIGH
        elif days > 270:
            severity = Severity.MEDIUM
        else:
            severity = Severity.LOW

        flagged.append(FlaggedInventoryItem(
            entry=e,
            test_name="Slow-Moving Inventory",
            test_key="slow_moving",
            test_tier=TestTier.STATISTICAL,
            severity=severity,
            issue=f"No movement for {days} days (threshold: {config.slow_moving_days})"
                  f", value=${value:,.2f}"
                  f" — {e.item_id or e.description or f'row {e.row_number}'}",
            confidence=0.80,
            details={"days_since_movement": days, "threshold_days": config.slow_moving_days, "value": round(value, 2)},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Slow-Moving Inventory",
        test_key="slow_moving",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags items with no movement for >{config.slow_moving_days} days — an obsolescence anomaly indicator.",
        flagged_entries=flagged,
    )


def test_category_concentration(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-07: Category Concentration.

    Flags if >50% of total inventory value is concentrated in a single category.
    """
    categorized = [(e, e.category) for e in entries if e.category]

    if not categorized:
        return InvTestResult(
            test_name="Category Concentration",
            test_key="category_concentration",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="No category data available for concentration analysis.",
            flagged_entries=[],
        )

    total_value = sum(
        abs(e.extended_value) if e.extended_value != 0 else abs(e.quantity * e.unit_cost)
        for e, _ in categorized
    )
    if total_value == 0:
        return InvTestResult(
            test_name="Category Concentration",
            test_key="category_concentration",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Zero total value — category concentration not applicable.",
            flagged_entries=[],
        )

    cat_values: dict[str, float] = {}
    cat_entries: dict[str, list[InventoryEntry]] = {}
    for e, cat in categorized:
        val = abs(e.extended_value) if e.extended_value != 0 else abs(e.quantity * e.unit_cost)
        cat_values[cat] = cat_values.get(cat, 0) + val
        cat_entries.setdefault(cat, []).append(e)

    flagged: list[FlaggedInventoryItem] = []
    for cat, cat_val in cat_values.items():
        pct = cat_val / total_value
        if pct <= config.category_concentration_threshold_pct:
            continue

        severity = Severity.HIGH if pct > 0.70 else Severity.MEDIUM

        for e in cat_entries[cat]:
            flagged.append(FlaggedInventoryItem(
                entry=e,
                test_name="Category Concentration",
                test_key="category_concentration",
                test_tier=TestTier.STATISTICAL,
                severity=severity,
                issue=f"Category '{cat}' represents {pct:.1%} of total inventory value"
                      f" (${cat_val:,.2f}/${total_value:,.2f})"
                      f" — {e.item_id or e.description or f'row {e.row_number}'}",
                confidence=0.75,
                details={
                    "category": cat,
                    "category_value": round(cat_val, 2),
                    "total_value": round(total_value, 2),
                    "concentration_pct": round(pct, 4),
                },
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Category Concentration",
        test_key="category_concentration",
        test_tier=TestTier.STATISTICAL,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description=f"Flags if >{config.category_concentration_threshold_pct:.0%} of value is in a single category.",
        flagged_entries=flagged,
    )


# =============================================================================
# TIER 3 — ADVANCED TESTS
# =============================================================================

def test_duplicate_items(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-08: Duplicate Item Detection.

    Flags items with identical description + unit cost,
    which may indicate double-counting or duplicate records.
    """
    if not config.duplicate_enabled:
        return InvTestResult(
            test_name="Duplicate Items",
            test_key="duplicate_items",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    groups: dict[tuple, list[InventoryEntry]] = {}
    for e in entries:
        desc = (e.description or "").lower().strip()
        key = (round(e.unit_cost, 2), desc)
        if key == (0.0, ""):
            continue
        groups.setdefault(key, []).append(e)

    flagged: list[FlaggedInventoryItem] = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        cost, desc = key
        value = math.fsum(abs(e.extended_value) if e.extended_value != 0 else abs(e.quantity * e.unit_cost) for e in group)
        severity = Severity.HIGH if value > 50000 else Severity.MEDIUM

        for e in group:
            flagged.append(FlaggedInventoryItem(
                entry=e,
                test_name="Duplicate Items",
                test_key="duplicate_items",
                test_tier=TestTier.ADVANCED,
                severity=severity,
                issue=f"Potential duplicate: '{desc}' @ ${abs(cost):,.2f}"
                      f" ({len(group)} occurrences, total value=${value:,.2f})",
                confidence=0.85,
                details={
                    "duplicate_count": len(group),
                    "unit_cost": cost,
                    "description": desc,
                    "group_total_value": round(value, 2),
                },
            ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Duplicate Items",
        test_key="duplicate_items",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.HIGH,
        description="Flags items with identical description and unit cost.",
        flagged_entries=flagged,
    )


def test_zero_value_items(
    entries: list[InventoryEntry],
    config: InventoryTestingConfig,
) -> InvTestResult:
    """IN-09: Zero-Value Items with Quantity.

    Flags items that have quantity on hand but zero extended value,
    which may indicate items written down to zero or pricing data issues.
    This is an anomaly indicator, not an NRV determination.
    """
    if not config.zero_value_enabled:
        return InvTestResult(
            test_name="Zero-Value Items",
            test_key="zero_value_items",
            test_tier=TestTier.ADVANCED,
            entries_flagged=0,
            total_entries=len(entries),
            flag_rate=0.0,
            severity=Severity.LOW,
            description="Test disabled.",
            flagged_entries=[],
        )

    flagged: list[FlaggedInventoryItem] = []
    for e in entries:
        if e.quantity == 0:
            continue

        has_value = (e.extended_value != 0) or (e.unit_cost != 0)
        if has_value:
            continue

        severity = Severity.MEDIUM if abs(e.quantity) > 100 else Severity.LOW

        flagged.append(FlaggedInventoryItem(
            entry=e,
            test_name="Zero-Value Items",
            test_key="zero_value_items",
            test_tier=TestTier.ADVANCED,
            severity=severity,
            issue=f"Quantity={e.quantity:,.2f} but zero value"
                  f" — {e.item_id or e.description or f'row {e.row_number}'}",
            confidence=0.80,
            details={"quantity": e.quantity, "unit_cost": e.unit_cost, "extended_value": e.extended_value},
        ))

    flag_rate = len(flagged) / max(len(entries), 1)
    return InvTestResult(
        test_name="Zero-Value Items",
        test_key="zero_value_items",
        test_tier=TestTier.ADVANCED,
        entries_flagged=len(flagged),
        total_entries=len(entries),
        flag_rate=flag_rate,
        severity=Severity.MEDIUM,
        description="Flags items with quantity on hand but zero value — a potential pricing anomaly indicator.",
        flagged_entries=flagged,
    )


# =============================================================================
# TEST BATTERY + SCORING
# =============================================================================

def run_inv_test_battery(
    entries: list[InventoryEntry],
    config: Optional[InventoryTestingConfig] = None,
) -> list[InvTestResult]:
    """Run all 9 inventory tests."""
    if config is None:
        config = InventoryTestingConfig()

    return [
        # Tier 1 — Structural
        test_missing_required_fields(entries, config),
        test_negative_values(entries, config),
        test_extended_value_mismatch(entries, config),
        # Tier 2 — Statistical
        test_unit_cost_outliers(entries, config),
        test_quantity_outliers(entries, config),
        test_slow_moving_inventory(entries, config),
        test_category_concentration(entries, config),
        # Tier 3 — Advanced
        test_duplicate_items(entries, config),
        test_zero_value_items(entries, config),
    ]


def calculate_inv_composite_score(
    test_results: list[InvTestResult],
    total_entries: int,
) -> InvCompositeScore:
    """Calculate composite risk score from inventory test results.

    Delegates to shared test aggregator (Sprint 152).
    """
    result = _shared_calc_cs(test_results, total_entries)

    return InvCompositeScore(
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

def run_inventory_testing(
    rows: list[dict],
    column_names: list[str],
    config: Optional[InventoryTestingConfig] = None,
    column_mapping: Optional[dict] = None,
) -> InvTestingResult:
    """Run the complete inventory testing pipeline.

    Args:
        rows: List of dicts (raw inventory register rows)
        column_names: List of column header names
        config: Optional testing configuration
        column_mapping: Optional manual column mapping override

    Returns:
        InvTestingResult with composite score, test results, data quality.
    """
    if config is None:
        config = InventoryTestingConfig()

    # 1. Detect columns
    detection = detect_inv_columns(column_names)

    # Apply manual overrides
    if column_mapping:
        for attr in ("item_id_column", "description_column", "quantity_column",
                     "unit_cost_column", "extended_value_column",
                     "location_column", "last_movement_date_column", "category_column"):
            if attr in column_mapping:
                setattr(detection, attr, column_mapping[attr])
        detection.overall_confidence = 1.0

    # 2. Parse entries
    entries = parse_inv_entries(rows, detection)

    # 3. Assess data quality
    data_quality = assess_inv_data_quality(entries, detection)

    # 4. Run test battery
    test_results = run_inv_test_battery(entries, config)

    # 5. Calculate composite score
    composite = calculate_inv_composite_score(test_results, len(entries))

    return InvTestingResult(
        composite_score=composite,
        test_results=test_results,
        data_quality=data_quality,
        column_detection=detection,
    )
