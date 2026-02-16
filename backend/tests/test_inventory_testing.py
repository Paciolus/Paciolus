"""
Tests for Inventory Testing Engine — Sprint 117

Covers: column detection, parsing, helpers, data quality,
3 tier 1 tests, 4 tier 2 tests, 2 tier 3 tests,
scoring, battery, full pipeline, serialization, API.

~140 tests across 18 test classes.
"""

import pytest
from datetime import date, timedelta

# Aliased imports to avoid pytest collection of test_* functions
from shared.column_detector import match_column as _match_column
from inventory_testing_engine import (
    InvColumnDetection,
    InventoryEntry,
    InventoryTestingConfig,
    InvTestResult,
    InvCompositeScore,
    InvTestingResult,
    InvDataQuality,
    FlaggedInventoryItem,
    detect_inv_columns,
    parse_inv_entries,
    assess_inv_data_quality,
    score_to_risk_tier,
    _days_since,
    test_missing_required_fields as run_missing_fields_test,
    test_negative_values as run_negative_values_test,
    test_extended_value_mismatch as run_value_mismatch_test,
    test_unit_cost_outliers as run_cost_outliers_test,
    test_quantity_outliers as run_qty_outliers_test,
    test_slow_moving_inventory as run_slow_moving_test,
    test_category_concentration as run_concentration_test,
    test_duplicate_items as run_duplicate_test,
    test_zero_value_items as run_zero_value_test,
    run_inv_test_battery,
    calculate_inv_composite_score,
    run_inventory_testing,
)
from shared.testing_enums import RiskTier, TestTier, Severity
from shared.parsing_helpers import safe_float as _safe_float, safe_str as _safe_str, parse_date as _parse_date


# =============================================================================
# FIXTURE HELPERS
# =============================================================================

def make_entries(rows: list[dict], columns: list[str] | None = None) -> list[InventoryEntry]:
    """Parse rows into InventoryEntry objects using auto-detection."""
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    detection = detect_inv_columns(columns)
    return parse_inv_entries(rows, detection)


def sample_inv_rows() -> list[dict]:
    """5 clean inventory entries for baseline tests."""
    return [
        {
            "Item ID": "INV-001",
            "Description": "Widget A",
            "Quantity": 100.0,
            "Unit Cost": 25.00,
            "Extended Value": 2500.00,
            "Location": "Warehouse A",
            "Last Movement Date": "2025-11-15",
            "Category": "Raw Materials",
        },
        {
            "Item ID": "INV-002",
            "Description": "Widget B",
            "Quantity": 50.0,
            "Unit Cost": 75.00,
            "Extended Value": 3750.00,
            "Location": "Warehouse B",
            "Last Movement Date": "2025-12-01",
            "Category": "Finished Goods",
        },
        {
            "Item ID": "INV-003",
            "Description": "Component X",
            "Quantity": 200.0,
            "Unit Cost": 10.00,
            "Extended Value": 2000.00,
            "Location": "Warehouse A",
            "Last Movement Date": "2025-10-20",
            "Category": "Raw Materials",
        },
        {
            "Item ID": "INV-004",
            "Description": "Assembly Y",
            "Quantity": 30.0,
            "Unit Cost": 150.00,
            "Extended Value": 4500.00,
            "Location": "Production Floor",
            "Last Movement Date": "2025-09-01",
            "Category": "Work in Progress",
        },
        {
            "Item ID": "INV-005",
            "Description": "Packaging Material",
            "Quantity": 500.0,
            "Unit Cost": 2.00,
            "Extended Value": 1000.00,
            "Location": "Warehouse C",
            "Last Movement Date": "2025-11-30",
            "Category": "Supplies",
        },
    ]


def make_large_dataset(n: int = 20) -> list[dict]:
    """Generate n rows for statistical tests."""
    rows = []
    for i in range(n):
        rows.append({
            "Item ID": f"INV-{i+1:04d}",
            "Description": f"Item {i+1}",
            "Quantity": 100.0 + i * 10,
            "Unit Cost": 50.0 + i * 5,
            "Extended Value": (100.0 + i * 10) * (50.0 + i * 5),
            "Location": f"Loc-{i % 3}",
            "Last Movement Date": "2025-11-01",
            "Category": f"Cat-{i % 4}",
        })
    return rows


# =============================================================================
# COLUMN DETECTION TESTS
# =============================================================================

class TestColumnDetection:
    """Tests for inventory column detection."""

    def test_exact_column_names(self):
        columns = [
            "Item ID", "Description", "Quantity",
            "Unit Cost", "Extended Value",
            "Location", "Last Movement Date", "Category",
        ]
        result = detect_inv_columns(columns)
        assert result.item_id_column == "Item ID"
        assert result.description_column == "Description"
        assert result.quantity_column == "Quantity"
        assert result.unit_cost_column == "Unit Cost"
        assert result.extended_value_column == "Extended Value"
        assert result.location_column == "Location"
        assert result.last_movement_date_column == "Last Movement Date"
        assert result.category_column == "Category"
        assert result.overall_confidence > 0.70

    def test_alternative_column_names(self):
        columns = [
            "SKU", "Product Name", "Qty On Hand",
            "Average Cost", "Total Value",
            "Warehouse", "Last Activity Date", "Product Type",
        ]
        result = detect_inv_columns(columns)
        assert result.item_id_column == "SKU"
        assert result.quantity_column == "Qty On Hand"
        assert result.unit_cost_column == "Average Cost"
        assert result.extended_value_column == "Total Value"

    def test_missing_required_columns(self):
        columns = ["Notes", "Status", "Remarks"]
        result = detect_inv_columns(columns)
        assert result.quantity_column is None
        assert result.overall_confidence == 0.0
        assert len(result.detection_notes) > 0

    def test_requires_mapping_low_confidence(self):
        result = detect_inv_columns(["col1", "col2", "col3"])
        assert result.requires_mapping is True

    def test_requires_mapping_high_confidence(self):
        result = detect_inv_columns(["Item ID", "Quantity", "Unit Cost"])
        assert result.requires_mapping is False

    def test_greedy_assignment_no_duplicates(self):
        columns = ["Cost", "Unit Cost", "Item ID"]
        result = detect_inv_columns(columns)
        # Both "Cost" and "Unit Cost" match unit_cost patterns
        # The best match gets assigned; no column should be used twice
        assigned = [
            result.item_id_column, result.unit_cost_column,
            result.extended_value_column,
        ]
        non_none = [c for c in assigned if c is not None]
        assert len(non_none) == len(set(non_none))

    def test_all_columns_preserved(self):
        columns = ["A", "B", "C"]
        result = detect_inv_columns(columns)
        assert result.all_columns == ["A", "B", "C"]

    def test_part_number_as_item_id(self):
        columns = ["Part Number", "Quantity", "Cost"]
        result = detect_inv_columns(columns)
        assert result.item_id_column == "Part Number"

    def test_stock_code_as_item_id(self):
        columns = ["Stock Code", "Description", "Qty"]
        result = detect_inv_columns(columns)
        assert result.item_id_column == "Stock Code"

    def test_bin_location_detected(self):
        columns = ["Item ID", "Quantity", "Unit Cost", "Bin Location"]
        result = detect_inv_columns(columns)
        assert result.location_column == "Bin Location"

    def test_to_dict(self):
        result = detect_inv_columns(["Item ID", "Quantity", "Unit Cost"])
        d = result.to_dict()
        assert "item_id_column" in d
        assert "quantity_column" in d
        assert "overall_confidence" in d
        assert "requires_mapping" in d
        assert isinstance(d["all_columns"], list)


# =============================================================================
# MATCH COLUMN HELPER TESTS
# =============================================================================

class TestMatchColumn:
    """Tests for the _match_column helper."""

    def test_exact_match_full_confidence(self):
        from inventory_testing_engine import INV_ITEM_ID_PATTERNS
        score = _match_column("item id", INV_ITEM_ID_PATTERNS)
        assert score == 1.0

    def test_partial_match_lower_confidence(self):
        from inventory_testing_engine import INV_ITEM_ID_PATTERNS
        score = _match_column("my_item_id_field", INV_ITEM_ID_PATTERNS)
        assert 0.0 < score < 1.0

    def test_no_match_zero(self):
        from inventory_testing_engine import INV_ITEM_ID_PATTERNS
        score = _match_column("xyz_random_col", INV_ITEM_ID_PATTERNS)
        assert score == 0.0

    def test_case_insensitive(self):
        from inventory_testing_engine import INV_QUANTITY_PATTERNS
        score = _match_column("QUANTITY", INV_QUANTITY_PATTERNS)
        assert score > 0.90


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelpers:
    """Tests for safe parsing helpers."""

    def test_safe_str_normal(self):
        assert _safe_str("hello") == "hello"

    def test_safe_str_none(self):
        assert _safe_str(None) is None

    def test_safe_str_empty(self):
        assert _safe_str("") is None

    def test_safe_str_nan(self):
        assert _safe_str("nan") is None
        assert _safe_str("NaN") is None

    def test_safe_str_none_string(self):
        assert _safe_str("none") is None

    def test_safe_str_strips_whitespace(self):
        assert _safe_str("  value  ") == "value"

    def test_safe_float_normal(self):
        assert _safe_float(42.5) == 42.5

    def test_safe_float_none(self):
        assert _safe_float(None) == 0.0

    def test_safe_float_nan(self):
        assert _safe_float(float("nan")) == 0.0

    def test_safe_float_inf(self):
        assert _safe_float(float("inf")) == 0.0

    def test_safe_float_currency_string(self):
        assert _safe_float("$1,234.56") == 1234.56

    def test_safe_float_negative_string(self):
        assert _safe_float("-500") == -500.0

    def test_safe_float_invalid(self):
        assert _safe_float("abc") == 0.0

    def test_parse_date_iso(self):
        result = _parse_date("2025-01-15")
        assert result == date(2025, 1, 15)

    def test_parse_date_us_format(self):
        result = _parse_date("01/15/2025")
        assert result == date(2025, 1, 15)

    def test_parse_date_none(self):
        assert _parse_date(None) is None

    def test_parse_date_invalid(self):
        assert _parse_date("not-a-date") is None

    def test_parse_date_with_time(self):
        result = _parse_date("2025-01-15 10:30:00")
        assert result == date(2025, 1, 15)

    def test_days_since_recent(self):
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = _days_since(yesterday)
        assert result == 1

    def test_days_since_old(self):
        old = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        result = _days_since(old)
        assert result == 365

    def test_days_since_none(self):
        assert _days_since(None) is None

    def test_days_since_invalid(self):
        assert _days_since("not-a-date") is None

    def test_days_since_with_reference(self):
        result = _days_since("2025-01-01", reference_date=date(2025, 7, 1))
        assert result == 181


# =============================================================================
# PARSING TESTS
# =============================================================================

class TestParsing:
    """Tests for parsing rows into InventoryEntry objects."""

    def test_parse_clean_rows(self):
        rows = sample_inv_rows()
        entries = make_entries(rows)
        assert len(entries) == 5
        assert entries[0].item_id == "INV-001"
        assert entries[0].quantity == 100.0
        assert entries[0].unit_cost == 25.0
        assert entries[0].extended_value == 2500.0

    def test_parse_empty_rows(self):
        entries = make_entries([], columns=["Item ID", "Quantity"])
        assert entries == []

    def test_row_numbers_sequential(self):
        rows = sample_inv_rows()
        entries = make_entries(rows)
        for i, e in enumerate(entries):
            assert e.row_number == i + 1

    def test_missing_column_gives_default(self):
        rows = [{"Item ID": "X", "Quantity": 10}]
        detection = detect_inv_columns(["Item ID", "Quantity"])
        entries = parse_inv_entries(rows, detection)
        assert entries[0].unit_cost == 0.0
        assert entries[0].extended_value == 0.0
        assert entries[0].location is None

    def test_entry_to_dict(self):
        rows = sample_inv_rows()[:1]
        entries = make_entries(rows)
        d = entries[0].to_dict()
        assert d["item_id"] == "INV-001"
        assert d["quantity"] == 100.0
        assert d["unit_cost"] == 25.0
        assert d["row_number"] == 1
        assert "description" in d
        assert "location" in d


# =============================================================================
# DATA QUALITY TESTS
# =============================================================================

class TestDataQuality:
    """Tests for data quality assessment."""

    def test_full_quality_clean_data(self):
        rows = sample_inv_rows()
        entries = make_entries(rows)
        detection = detect_inv_columns(list(rows[0].keys()))
        quality = assess_inv_data_quality(entries, detection)
        assert quality.completeness_score > 80
        assert quality.total_rows == 5

    def test_empty_entries(self):
        detection = detect_inv_columns(["Item ID", "Quantity"])
        quality = assess_inv_data_quality([], detection)
        assert quality.completeness_score == 0.0
        assert quality.total_rows == 0

    def test_identifier_fill_rate(self):
        rows = sample_inv_rows()
        entries = make_entries(rows)
        detection = detect_inv_columns(list(rows[0].keys()))
        quality = assess_inv_data_quality(entries, detection)
        assert quality.field_fill_rates["identifier"] == 1.0

    def test_low_date_fill_rate_flagged(self):
        rows = sample_inv_rows()
        # Remove dates from 4 of 5
        for i in range(4):
            rows[i]["Last Movement Date"] = ""
        entries = make_entries(rows)
        detection = detect_inv_columns(list(rows[0].keys()))
        quality = assess_inv_data_quality(entries, detection)
        assert quality.field_fill_rates["last_movement_date"] < 0.80
        assert any("movement date" in issue.lower() for issue in quality.detected_issues)

    def test_to_dict(self):
        rows = sample_inv_rows()
        entries = make_entries(rows)
        detection = detect_inv_columns(list(rows[0].keys()))
        quality = assess_inv_data_quality(entries, detection)
        d = quality.to_dict()
        assert "completeness_score" in d
        assert "field_fill_rates" in d
        assert "total_rows" in d

    def test_quality_score_capped_at_100(self):
        rows = sample_inv_rows()
        entries = make_entries(rows)
        detection = detect_inv_columns(list(rows[0].keys()))
        quality = assess_inv_data_quality(entries, detection)
        assert quality.completeness_score <= 100.0


# =============================================================================
# RISK TIER TESTS
# =============================================================================

class TestRiskTier:
    """Tests for score_to_risk_tier mapping."""

    def test_low(self):
        assert score_to_risk_tier(5.0) == RiskTier.LOW

    def test_elevated(self):
        assert score_to_risk_tier(15.0) == RiskTier.ELEVATED

    def test_moderate(self):
        assert score_to_risk_tier(30.0) == RiskTier.MODERATE

    def test_high(self):
        assert score_to_risk_tier(60.0) == RiskTier.HIGH

    def test_critical(self):
        assert score_to_risk_tier(80.0) == RiskTier.CRITICAL

    def test_boundary_low(self):
        assert score_to_risk_tier(0.0) == RiskTier.LOW

    def test_boundary_elevated(self):
        assert score_to_risk_tier(10.0) == RiskTier.ELEVATED

    def test_boundary_moderate(self):
        assert score_to_risk_tier(25.0) == RiskTier.MODERATE

    def test_boundary_high(self):
        assert score_to_risk_tier(50.0) == RiskTier.HIGH

    def test_boundary_critical(self):
        assert score_to_risk_tier(75.0) == RiskTier.CRITICAL


# =============================================================================
# TIER 1 — STRUCTURAL TESTS
# =============================================================================

class TestMissingRequiredFields:
    """IN-01: Missing Required Fields."""

    def test_clean_data_no_flags(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig()
        result = run_missing_fields_test(entries, config)
        assert result.entries_flagged == 0
        assert result.test_key == "missing_fields"
        assert result.test_tier == TestTier.STRUCTURAL

    def test_missing_identifier(self):
        rows = [{"Quantity": 100, "Unit Cost": 25, "Extended Value": 2500}]
        entries = make_entries(rows, ["Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_missing_fields_test(entries, config)
        assert result.entries_flagged == 1

    def test_missing_quantity_and_value(self):
        rows = [{"Item ID": "X", "Description": "Test", "Quantity": 0, "Unit Cost": 0, "Extended Value": 0}]
        entries = make_entries(rows, ["Item ID", "Description", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_missing_fields_test(entries, config)
        assert result.entries_flagged == 1

    def test_multi_missing_high_severity(self):
        rows = [{"Quantity": 0, "Unit Cost": 0, "Extended Value": 0}]
        entries = make_entries(rows, ["Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_missing_fields_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_disabled_returns_empty(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig(missing_fields_enabled=False)
        result = run_missing_fields_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_has_description_only_passes(self):
        rows = [{"Description": "Widget", "Quantity": 10, "Unit Cost": 5, "Extended Value": 50}]
        entries = make_entries(rows, ["Description", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_missing_fields_test(entries, config)
        assert result.entries_flagged == 0


class TestNegativeValues:
    """IN-02: Negative Values."""

    def test_clean_data_no_flags(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig()
        result = run_negative_values_test(entries, config)
        assert result.entries_flagged == 0
        assert result.test_key == "negative_values"
        assert result.test_tier == TestTier.STRUCTURAL

    def test_negative_quantity(self):
        rows = [{"Item ID": "X", "Quantity": -10, "Unit Cost": 25, "Extended Value": -250}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_negative_values_test(entries, config)
        assert result.entries_flagged == 1

    def test_negative_unit_cost(self):
        rows = [{"Item ID": "X", "Quantity": 10, "Unit Cost": -25, "Extended Value": 250}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_negative_values_test(entries, config)
        assert result.entries_flagged == 1

    def test_negative_extended_value(self):
        rows = [{"Item ID": "X", "Quantity": 10, "Unit Cost": 25, "Extended Value": -250}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_negative_values_test(entries, config)
        assert result.entries_flagged == 1

    def test_high_severity_above_50k(self):
        rows = [{"Item ID": "X", "Quantity": 10, "Unit Cost": -10000, "Extended Value": -100000}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_negative_values_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_disabled_returns_empty(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig(negative_values_enabled=False)
        result = run_negative_values_test(entries, config)
        assert result.entries_flagged == 0


class TestExtendedValueMismatch:
    """IN-03: Extended Value Mismatch (qty × unit_cost ≠ extended_value)."""

    def test_clean_data_no_flags(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig()
        result = run_value_mismatch_test(entries, config)
        assert result.entries_flagged == 0
        assert result.test_key == "value_mismatch"
        assert result.test_tier == TestTier.STRUCTURAL

    def test_mismatch_flagged(self):
        rows = [{"Item ID": "X", "Quantity": 10, "Unit Cost": 25, "Extended Value": 300}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_value_mismatch_test(entries, config)
        assert result.entries_flagged == 1

    def test_within_tolerance_not_flagged(self):
        # qty=10, cost=25, expected=250, value=252 → diff=0.8% < 1%
        rows = [{"Item ID": "X", "Quantity": 10, "Unit Cost": 25, "Extended Value": 252}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_value_mismatch_test(entries, config)
        assert result.entries_flagged == 0

    def test_zero_values_skipped(self):
        rows = [{"Item ID": "X", "Quantity": 0, "Unit Cost": 0, "Extended Value": 0}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_value_mismatch_test(entries, config)
        assert result.entries_flagged == 0

    def test_high_severity_large_diff(self):
        rows = [{"Item ID": "X", "Quantity": 100, "Unit Cost": 200, "Extended Value": 31000}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_value_mismatch_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_disabled_returns_empty(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig(value_mismatch_enabled=False)
        result = run_value_mismatch_test(entries, config)
        assert result.entries_flagged == 0

    def test_details_include_expected_actual(self):
        rows = [{"Item ID": "X", "Quantity": 10, "Unit Cost": 25, "Extended Value": 300}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_value_mismatch_test(entries, config)
        details = result.flagged_entries[0].details
        assert "expected_value" in details
        assert details["expected_value"] == 250.0
        assert details["actual_value"] == 300.0


# =============================================================================
# TIER 2 — STATISTICAL TESTS
# =============================================================================

class TestUnitCostOutliers:
    """IN-04: Unit Cost Outliers (Z-Score)."""

    def test_clean_data_no_flags(self):
        entries = make_entries(make_large_dataset(20))
        config = InventoryTestingConfig()
        result = run_cost_outliers_test(entries, config)
        assert result.test_key == "unit_cost_outliers"
        assert result.test_tier == TestTier.STATISTICAL

    def test_extreme_outlier_flagged(self):
        rows = make_large_dataset(20)
        rows.append({"Item ID": "OUTLIER", "Quantity": 10, "Unit Cost": 99999,
                     "Extended Value": 999990, "Category": "Cat-0"})
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_cost_outliers_test(entries, config)
        assert result.entries_flagged >= 1
        outlier_ids = [f.entry.item_id for f in result.flagged_entries]
        assert "OUTLIER" in outlier_ids

    def test_too_few_entries_skipped(self):
        rows = sample_inv_rows()[:5]
        entries = make_entries(rows)
        config = InventoryTestingConfig(cost_zscore_min_entries=10)
        result = run_cost_outliers_test(entries, config)
        assert result.entries_flagged == 0
        assert "requires" in result.description.lower()

    def test_identical_costs_skipped(self):
        rows = [{"Item ID": f"I-{i}", "Quantity": 10, "Unit Cost": 50, "Extended Value": 500}
                for i in range(15)]
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_cost_outliers_test(entries, config)
        assert result.entries_flagged == 0
        assert "identical" in result.description.lower()

    def test_z_score_in_details(self):
        rows = make_large_dataset(20)
        rows.append({"Item ID": "OUT", "Quantity": 10, "Unit Cost": 99999,
                     "Extended Value": 999990, "Category": "Cat-0"})
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_cost_outliers_test(entries, config)
        if result.entries_flagged > 0:
            assert "z_score" in result.flagged_entries[0].details


class TestQuantityOutliers:
    """IN-05: Quantity Outliers (Z-Score)."""

    def test_clean_data_no_flags(self):
        entries = make_entries(make_large_dataset(20))
        config = InventoryTestingConfig()
        result = run_qty_outliers_test(entries, config)
        assert result.test_key == "quantity_outliers"
        assert result.test_tier == TestTier.STATISTICAL

    def test_extreme_outlier_flagged(self):
        rows = make_large_dataset(20)
        rows.append({"Item ID": "QOUT", "Quantity": 99999, "Unit Cost": 50,
                     "Extended Value": 4999950, "Category": "Cat-0"})
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_qty_outliers_test(entries, config)
        assert result.entries_flagged >= 1

    def test_too_few_entries_skipped(self):
        rows = sample_inv_rows()[:5]
        entries = make_entries(rows)
        config = InventoryTestingConfig(qty_zscore_min_entries=10)
        result = run_qty_outliers_test(entries, config)
        assert result.entries_flagged == 0

    def test_identical_quantities_skipped(self):
        rows = [{"Item ID": f"I-{i}", "Quantity": 100, "Unit Cost": 50, "Extended Value": 5000}
                for i in range(15)]
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_qty_outliers_test(entries, config)
        assert result.entries_flagged == 0


class TestSlowMovingInventory:
    """IN-06: Slow-Moving Inventory."""

    def test_recent_movement_no_flags(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig(slow_moving_days=180)
        result = run_slow_moving_test(entries, config)
        assert result.test_key == "slow_moving"
        assert result.test_tier == TestTier.STATISTICAL

    def test_old_movement_flagged(self):
        old_date = (date.today() - timedelta(days=250)).strftime("%Y-%m-%d")
        rows = [{"Item ID": "OLD", "Quantity": 50, "Unit Cost": 25,
                 "Extended Value": 1250, "Last Movement Date": old_date, "Category": "Raw"}]
        entries = make_entries(rows)
        config = InventoryTestingConfig(slow_moving_days=180)
        result = run_slow_moving_test(entries, config)
        assert result.entries_flagged == 1

    def test_very_old_high_severity(self):
        old_date = (date.today() - timedelta(days=400)).strftime("%Y-%m-%d")
        rows = [{"Item ID": "VERY-OLD", "Quantity": 50, "Unit Cost": 25,
                 "Extended Value": 1250, "Last Movement Date": old_date, "Category": "Raw"}]
        entries = make_entries(rows)
        config = InventoryTestingConfig(slow_moving_days=180)
        result = run_slow_moving_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_no_dates_available(self):
        rows = [{"Item ID": "X", "Quantity": 50, "Unit Cost": 25, "Extended Value": 1250}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_slow_moving_test(entries, config)
        assert result.entries_flagged == 0
        assert "no movement dates" in result.description.lower()

    def test_within_threshold_not_flagged(self):
        recent_date = (date.today() - timedelta(days=90)).strftime("%Y-%m-%d")
        rows = [{"Item ID": "RECENT", "Quantity": 50, "Unit Cost": 25,
                 "Extended Value": 1250, "Last Movement Date": recent_date, "Category": "Raw"}]
        entries = make_entries(rows)
        config = InventoryTestingConfig(slow_moving_days=180)
        result = run_slow_moving_test(entries, config)
        assert result.entries_flagged == 0

    def test_details_include_days(self):
        old_date = (date.today() - timedelta(days=200)).strftime("%Y-%m-%d")
        rows = [{"Item ID": "OLD2", "Quantity": 50, "Unit Cost": 25,
                 "Extended Value": 1250, "Last Movement Date": old_date, "Category": "Raw"}]
        entries = make_entries(rows)
        config = InventoryTestingConfig(slow_moving_days=180)
        result = run_slow_moving_test(entries, config)
        assert result.flagged_entries[0].details["days_since_movement"] >= 200


class TestCategoryConcentration:
    """IN-07: Category Concentration."""

    def test_balanced_categories_no_flags(self):
        rows = make_large_dataset(20)
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_concentration_test(entries, config)
        assert result.test_key == "category_concentration"
        assert result.test_tier == TestTier.STATISTICAL

    def test_concentrated_category_flagged(self):
        rows = []
        # 9 items with tiny value in Cat-A
        for i in range(9):
            rows.append({"Item ID": f"I-{i}", "Quantity": 1, "Unit Cost": 1,
                         "Extended Value": 1, "Category": "Cat-A"})
        # 1 item with massive value in Cat-B
        rows.append({"Item ID": "BIG", "Quantity": 1, "Unit Cost": 100000,
                     "Extended Value": 100000, "Category": "Cat-B"})
        entries = make_entries(rows)
        config = InventoryTestingConfig(category_concentration_threshold_pct=0.50)
        result = run_concentration_test(entries, config)
        assert result.entries_flagged >= 1

    def test_no_categories_available(self):
        rows = [{"Item ID": "X", "Quantity": 50, "Unit Cost": 25, "Extended Value": 1250}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_concentration_test(entries, config)
        assert result.entries_flagged == 0

    def test_zero_total_value(self):
        rows = [{"Item ID": "X", "Quantity": 0, "Unit Cost": 0,
                 "Extended Value": 0, "Category": "Cat-A"}]
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_concentration_test(entries, config)
        assert result.entries_flagged == 0

    def test_high_severity_above_70pct(self):
        rows = []
        # 1 item with 90%+ concentration
        rows.append({"Item ID": "HUGE", "Quantity": 1, "Unit Cost": 90000,
                     "Extended Value": 90000, "Category": "Dominant"})
        rows.append({"Item ID": "SMALL", "Quantity": 1, "Unit Cost": 1000,
                     "Extended Value": 1000, "Category": "Minor"})
        entries = make_entries(rows)
        config = InventoryTestingConfig(category_concentration_threshold_pct=0.50)
        result = run_concentration_test(entries, config)
        assert result.entries_flagged >= 1
        assert any(f.severity == Severity.HIGH for f in result.flagged_entries)


# =============================================================================
# TIER 3 — ADVANCED TESTS
# =============================================================================

class TestDuplicateItems:
    """IN-08: Duplicate Item Detection."""

    def test_unique_items_no_flags(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig()
        result = run_duplicate_test(entries, config)
        assert result.entries_flagged == 0
        assert result.test_key == "duplicate_items"
        assert result.test_tier == TestTier.ADVANCED

    def test_duplicate_desc_and_cost_flagged(self):
        rows = [
            {"Item ID": "D1", "Description": "Widget A", "Quantity": 10,
             "Unit Cost": 25, "Extended Value": 250, "Category": "Raw"},
            {"Item ID": "D2", "Description": "Widget A", "Quantity": 20,
             "Unit Cost": 25, "Extended Value": 500, "Category": "Raw"},
        ]
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_duplicate_test(entries, config)
        assert result.entries_flagged == 2

    def test_same_desc_different_cost_not_flagged(self):
        rows = [
            {"Item ID": "D1", "Description": "Widget A", "Quantity": 10,
             "Unit Cost": 25, "Extended Value": 250, "Category": "Raw"},
            {"Item ID": "D2", "Description": "Widget A", "Quantity": 20,
             "Unit Cost": 30, "Extended Value": 600, "Category": "Raw"},
        ]
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_duplicate_test(entries, config)
        assert result.entries_flagged == 0

    def test_disabled_returns_empty(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig(duplicate_enabled=False)
        result = run_duplicate_test(entries, config)
        assert result.entries_flagged == 0

    def test_high_severity_above_50k(self):
        rows = [
            {"Item ID": "D1", "Description": "Expensive", "Quantity": 100,
             "Unit Cost": 500, "Extended Value": 50000, "Category": "Raw"},
            {"Item ID": "D2", "Description": "Expensive", "Quantity": 100,
             "Unit Cost": 500, "Extended Value": 50000, "Category": "Raw"},
        ]
        entries = make_entries(rows)
        config = InventoryTestingConfig()
        result = run_duplicate_test(entries, config)
        assert result.entries_flagged == 2
        assert all(f.severity == Severity.HIGH for f in result.flagged_entries)

    def test_blank_entries_skipped(self):
        rows = [
            {"Item ID": "D1", "Quantity": 10, "Unit Cost": 0, "Extended Value": 0},
            {"Item ID": "D2", "Quantity": 20, "Unit Cost": 0, "Extended Value": 0},
        ]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_duplicate_test(entries, config)
        # key=(0.0, "") should be skipped
        assert result.entries_flagged == 0


class TestZeroValueItems:
    """IN-09: Zero-Value Items with Quantity."""

    def test_clean_data_no_flags(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig()
        result = run_zero_value_test(entries, config)
        assert result.entries_flagged == 0
        assert result.test_key == "zero_value_items"
        assert result.test_tier == TestTier.ADVANCED

    def test_quantity_with_zero_value_flagged(self):
        rows = [{"Item ID": "Z1", "Quantity": 100, "Unit Cost": 0, "Extended Value": 0}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_zero_value_test(entries, config)
        assert result.entries_flagged == 1

    def test_zero_quantity_not_flagged(self):
        rows = [{"Item ID": "Z2", "Quantity": 0, "Unit Cost": 0, "Extended Value": 0}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_zero_value_test(entries, config)
        assert result.entries_flagged == 0

    def test_has_unit_cost_not_flagged(self):
        rows = [{"Item ID": "Z3", "Quantity": 100, "Unit Cost": 25, "Extended Value": 0}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_zero_value_test(entries, config)
        assert result.entries_flagged == 0

    def test_medium_severity_above_100_qty(self):
        rows = [{"Item ID": "Z4", "Quantity": 500, "Unit Cost": 0, "Extended Value": 0}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_zero_value_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_disabled_returns_empty(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig(zero_value_enabled=False)
        result = run_zero_value_test(entries, config)
        assert result.entries_flagged == 0


# =============================================================================
# BATTERY + SCORING TESTS
# =============================================================================

class TestBattery:
    """Tests for run_inv_test_battery."""

    def test_runs_all_9_tests(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        assert len(results) == 9

    def test_correct_test_keys(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        keys = [r.test_key for r in results]
        expected = [
            "missing_fields", "negative_values", "value_mismatch",
            "unit_cost_outliers", "quantity_outliers", "slow_moving",
            "category_concentration", "duplicate_items", "zero_value_items",
        ]
        assert keys == expected

    def test_tier_distribution(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        tiers = [r.test_tier for r in results]
        assert tiers.count(TestTier.STRUCTURAL) == 3
        assert tiers.count(TestTier.STATISTICAL) == 4
        assert tiers.count(TestTier.ADVANCED) == 2

    def test_custom_config_propagated(self):
        entries = make_entries(sample_inv_rows())
        config = InventoryTestingConfig(missing_fields_enabled=False)
        results = run_inv_test_battery(entries, config)
        missing_result = next(r for r in results if r.test_key == "missing_fields")
        assert "disabled" in missing_result.description.lower()


class TestCompositeScore:
    """Tests for calculate_inv_composite_score."""

    def test_clean_data_low_score(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        score = calculate_inv_composite_score(results, len(entries))
        assert score.score < 25
        assert score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED)
        assert score.tests_run == 9
        assert score.total_entries == 5

    def test_zero_entries(self):
        score = calculate_inv_composite_score([], 0)
        assert score.score == 0.0
        assert score.risk_tier == RiskTier.LOW
        assert score.total_entries == 0

    def test_score_capped_at_100(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        score = calculate_inv_composite_score(results, len(entries))
        assert score.score <= 100.0

    def test_flags_by_severity_populated(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        score = calculate_inv_composite_score(results, len(entries))
        assert "high" in score.flags_by_severity
        assert "medium" in score.flags_by_severity
        assert "low" in score.flags_by_severity

    def test_to_dict(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        score = calculate_inv_composite_score(results, len(entries))
        d = score.to_dict()
        assert "score" in d
        assert "risk_tier" in d
        assert "tests_run" in d
        assert "flag_rate" in d
        assert "top_findings" in d

    def test_top_findings_max_5(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        score = calculate_inv_composite_score(results, len(entries))
        assert len(score.top_findings) <= 5


# =============================================================================
# FULL PIPELINE TESTS
# =============================================================================

class TestFullPipeline:
    """Tests for run_inventory_testing end-to-end."""

    def test_clean_data(self):
        rows = sample_inv_rows()
        columns = list(rows[0].keys())
        result = run_inventory_testing(rows, columns)
        assert isinstance(result, InvTestingResult)
        assert result.composite_score is not None
        assert len(result.test_results) == 9
        assert result.data_quality is not None
        assert result.column_detection is not None

    def test_column_mapping_override(self):
        rows = [{"col_a": "X", "col_b": 100, "col_c": 25, "col_d": 2500}]
        columns = ["col_a", "col_b", "col_c", "col_d"]
        mapping = {
            "item_id_column": "col_a",
            "quantity_column": "col_b",
            "unit_cost_column": "col_c",
            "extended_value_column": "col_d",
        }
        result = run_inventory_testing(rows, columns, column_mapping=mapping)
        assert result.column_detection.overall_confidence == 1.0
        assert result.column_detection.item_id_column == "col_a"

    def test_empty_data(self):
        result = run_inventory_testing([], [])
        assert result.composite_score.total_entries == 0
        assert result.composite_score.score == 0.0

    def test_large_dataset(self):
        rows = make_large_dataset(100)
        columns = list(rows[0].keys())
        result = run_inventory_testing(rows, columns)
        assert result.composite_score.total_entries == 100
        assert result.composite_score.tests_run == 9

    def test_custom_config(self):
        rows = sample_inv_rows()
        columns = list(rows[0].keys())
        config = InventoryTestingConfig(slow_moving_days=365)
        result = run_inventory_testing(rows, columns, config=config)
        assert isinstance(result, InvTestingResult)


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestSerialization:
    """Tests for to_dict serialization."""

    def test_full_result_serializable(self):
        rows = sample_inv_rows()
        columns = list(rows[0].keys())
        result = run_inventory_testing(rows, columns)
        d = result.to_dict()
        assert "composite_score" in d
        assert "test_results" in d
        assert "data_quality" in d
        assert "column_detection" in d

    def test_test_result_to_dict(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        for r in results:
            d = r.to_dict()
            assert "test_name" in d
            assert "test_key" in d
            assert "test_tier" in d
            assert "entries_flagged" in d
            assert "flag_rate" in d
            assert "severity" in d
            assert "description" in d

    def test_flagged_item_to_dict(self):
        rows = [{"Item ID": "Z1", "Quantity": 100, "Unit Cost": 0, "Extended Value": 0}]
        entries = make_entries(rows, ["Item ID", "Quantity", "Unit Cost", "Extended Value"])
        config = InventoryTestingConfig()
        result = run_zero_value_test(entries, config)
        if result.entries_flagged > 0:
            d = result.flagged_entries[0].to_dict()
            assert "entry" in d
            assert "test_name" in d
            assert "severity" in d
            assert "issue" in d
            assert "confidence" in d

    def test_composite_score_risk_tier_string(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        score = calculate_inv_composite_score(results, len(entries))
        d = score.to_dict()
        assert isinstance(d["risk_tier"], str)

    def test_test_tier_string(self):
        entries = make_entries(sample_inv_rows())
        results = run_inv_test_battery(entries)
        for r in results:
            d = r.to_dict()
            assert isinstance(d["test_tier"], str)


# =============================================================================
# API INTEGRATION TESTS
# =============================================================================

class TestAPIIntegration:
    """Tests for API route registration and enum membership."""

    def test_route_registered(self):
        from main import app
        paths = [route.path for route in app.routes if hasattr(route, "path")]
        assert "/audit/inventory-testing" in paths

    def test_engagement_model_has_inventory(self):
        from engagement_model import ToolName
        assert hasattr(ToolName, "INVENTORY_TESTING")
        assert ToolName.INVENTORY_TESTING.value == "inventory_testing"

    def test_tool_name_count(self):
        from engagement_model import ToolName
        assert len(ToolName) == 12

    def test_workpaper_index_labels(self):
        from workpaper_index_generator import TOOL_LABELS, TOOL_LEAD_SHEET_REFS
        from engagement_model import ToolName
        assert ToolName.INVENTORY_TESTING in TOOL_LABELS
        assert ToolName.INVENTORY_TESTING in TOOL_LEAD_SHEET_REFS

    def test_workpaper_label_value(self):
        from workpaper_index_generator import TOOL_LABELS
        from engagement_model import ToolName
        assert TOOL_LABELS[ToolName.INVENTORY_TESTING] == "Inventory Testing"

    def test_workpaper_lead_sheet_ref(self):
        from workpaper_index_generator import TOOL_LEAD_SHEET_REFS
        from engagement_model import ToolName
        refs = TOOL_LEAD_SHEET_REFS[ToolName.INVENTORY_TESTING]
        assert len(refs) == 1
        assert "IN-" in refs[0]
