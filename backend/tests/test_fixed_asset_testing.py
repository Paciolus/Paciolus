"""
Tests for Fixed Asset Testing Engine — Sprint 114

Covers: column detection, parsing, helpers, data quality,
4 tier 1 tests, 3 tier 2 tests, 2 tier 3 tests,
scoring, battery, full pipeline, serialization, API.

~140 tests across 20 test classes.
"""

import pytest
from datetime import date

# Aliased imports to avoid pytest collection of test_* functions
from fixed_asset_testing_engine import (
    FAColumnType,
    FAColumnDetection,
    FixedAssetEntry,
    FixedAssetTestingConfig,
    FATestResult,
    FACompositeScore,
    FATestingResult,
    FADataQuality,
    FlaggedFixedAsset,
    detect_fa_columns,
    parse_fa_entries,
    assess_fa_data_quality,
    score_to_risk_tier,
    _safe_float_optional,
    _asset_age_years,
    _match_column,
    test_fully_depreciated_assets as run_fully_depreciated_test,
    test_missing_required_fields as run_missing_fields_test,
    test_negative_values as run_negative_values_test,
    test_over_depreciation as run_over_depreciation_test,
    test_useful_life_outliers as run_useful_life_test,
    test_cost_zscore_outliers as run_zscore_test,
    test_age_concentration as run_age_concentration_test,
    test_duplicate_assets as run_duplicate_test,
    test_residual_value_anomalies as run_residual_test,
    run_fa_test_battery,
    calculate_fa_composite_score,
    run_fixed_asset_testing,
)
from shared.testing_enums import RiskTier, TestTier, Severity
from shared.parsing_helpers import safe_float as _safe_float, safe_str as _safe_str, parse_date as _parse_date


# =============================================================================
# FIXTURE HELPERS
# =============================================================================

def make_entries(rows: list[dict], columns: list[str] | None = None) -> list[FixedAssetEntry]:
    """Parse rows into FixedAssetEntry objects using auto-detection."""
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    detection = detect_fa_columns(columns)
    return parse_fa_entries(rows, detection)


def sample_fa_rows() -> list[dict]:
    """5 clean fixed asset entries for baseline tests."""
    return [
        {
            "Asset ID": "FA-001",
            "Description": "Office Building",
            "Original Cost": 500000.00,
            "Accumulated Depreciation": 100000.00,
            "Acquisition Date": "2020-01-15",
            "Useful Life": 40.0,
            "Depreciation Method": "Straight-line",
            "Residual Value": 50000.00,
            "Location": "HQ",
            "Category": "Buildings",
        },
        {
            "Asset ID": "FA-002",
            "Description": "Delivery Truck",
            "Original Cost": 75000.00,
            "Accumulated Depreciation": 30000.00,
            "Acquisition Date": "2021-06-01",
            "Useful Life": 7.0,
            "Depreciation Method": "Straight-line",
            "Residual Value": 5000.00,
            "Location": "Warehouse",
            "Category": "Vehicles",
        },
        {
            "Asset ID": "FA-003",
            "Description": "Computer Equipment",
            "Original Cost": 15000.00,
            "Accumulated Depreciation": 10000.00,
            "Acquisition Date": "2022-03-10",
            "Useful Life": 3.0,
            "Depreciation Method": "Straight-line",
            "Residual Value": 0.00,
            "Location": "HQ",
            "Category": "IT Equipment",
        },
        {
            "Asset ID": "FA-004",
            "Description": "Manufacturing Machine",
            "Original Cost": 250000.00,
            "Accumulated Depreciation": 62500.00,
            "Acquisition Date": "2023-01-01",
            "Useful Life": 10.0,
            "Depreciation Method": "Straight-line",
            "Residual Value": 25000.00,
            "Location": "Plant A",
            "Category": "Machinery",
        },
        {
            "Asset ID": "FA-005",
            "Description": "Office Furniture",
            "Original Cost": 8000.00,
            "Accumulated Depreciation": 4000.00,
            "Acquisition Date": "2023-07-15",
            "Useful Life": 5.0,
            "Depreciation Method": "Straight-line",
            "Residual Value": 500.00,
            "Location": "HQ",
            "Category": "Furniture",
        },
    ]


# =============================================================================
# COLUMN DETECTION TESTS
# =============================================================================

class TestColumnDetection:
    """Tests for fixed asset column detection."""

    def test_exact_column_names(self):
        columns = [
            "Asset ID", "Description", "Original Cost",
            "Accumulated Depreciation", "Acquisition Date",
            "Useful Life", "Depreciation Method", "Residual Value",
            "Location", "Category",
        ]
        result = detect_fa_columns(columns)
        assert result.asset_id_column == "Asset ID"
        assert result.description_column == "Description"
        assert result.cost_column == "Original Cost"
        assert result.accumulated_depreciation_column == "Accumulated Depreciation"
        assert result.acquisition_date_column == "Acquisition Date"
        assert result.useful_life_column == "Useful Life"
        assert result.depreciation_method_column == "Depreciation Method"
        assert result.residual_value_column == "Residual Value"
        assert result.location_column == "Location"
        assert result.overall_confidence > 0.70

    def test_alternative_column_names(self):
        columns = [
            "Tag Number", "Asset Name", "Cost",
            "Accum Depr", "Date Acquired",
            "Life Years", "Depr Method", "Salvage Value",
            "Site", "Asset Class",
        ]
        result = detect_fa_columns(columns)
        assert result.asset_id_column == "Tag Number"
        assert result.cost_column == "Cost"
        assert result.accumulated_depreciation_column == "Accum Depr"
        assert result.acquisition_date_column == "Date Acquired"

    def test_missing_required_columns(self):
        columns = ["Notes", "Status", "Remarks"]
        result = detect_fa_columns(columns)
        assert result.cost_column is None
        assert result.overall_confidence == 0.0
        assert len(result.detection_notes) > 0

    def test_requires_mapping_low_confidence(self):
        result = detect_fa_columns(["col1", "col2", "col3"])
        assert result.requires_mapping is True

    def test_requires_mapping_high_confidence(self):
        result = detect_fa_columns(["Asset ID", "Original Cost", "Description"])
        assert result.requires_mapping is False

    def test_nbv_column_detection(self):
        columns = ["Asset ID", "Cost", "Net Book Value", "Description"]
        result = detect_fa_columns(columns)
        assert result.net_book_value_column == "Net Book Value"
        assert result.cost_column == "Cost"

    def test_carrying_value_detected_as_nbv(self):
        columns = ["Asset ID", "Cost", "Carrying Amount"]
        result = detect_fa_columns(columns)
        assert result.net_book_value_column == "Carrying Amount"

    def test_greedy_assignment_no_duplicates(self):
        columns = ["Cost", "Original Cost", "Asset ID"]
        result = detect_fa_columns(columns)
        # Both match "cost" but only the best match gets assigned
        assigned = [result.cost_column, result.accumulated_depreciation_column,
                    result.net_book_value_column]
        assigned_set = set(c for c in assigned if c is not None)
        assert len(assigned_set) == len([c for c in assigned if c is not None])

    def test_all_columns_preserved(self):
        columns = ["A", "B", "C"]
        result = detect_fa_columns(columns)
        assert result.all_columns == ["A", "B", "C"]

    def test_to_dict(self):
        result = detect_fa_columns(["Asset ID", "Cost", "Description"])
        d = result.to_dict()
        assert "asset_id_column" in d
        assert "cost_column" in d
        assert "overall_confidence" in d
        assert "requires_mapping" in d
        assert "all_columns" in d


class TestMatchColumn:
    """Tests for the _match_column helper."""

    def test_exact_match(self):
        from fixed_asset_testing_engine import FA_ASSET_ID_PATTERNS
        conf = _match_column("Asset ID", FA_ASSET_ID_PATTERNS)
        assert conf == 1.0

    def test_partial_match(self):
        from fixed_asset_testing_engine import FA_COST_PATTERNS
        conf = _match_column("Total Cost Amount", FA_COST_PATTERNS)
        assert conf > 0.0  # "cost" substring match

    def test_no_match(self):
        from fixed_asset_testing_engine import FA_ASSET_ID_PATTERNS
        conf = _match_column("xyz_random", FA_ASSET_ID_PATTERNS)
        assert conf == 0.0

    def test_case_insensitive(self):
        from fixed_asset_testing_engine import FA_ASSET_ID_PATTERNS
        conf = _match_column("ASSET ID", FA_ASSET_ID_PATTERNS)
        assert conf == 1.0


# =============================================================================
# HELPER TESTS
# =============================================================================

class TestHelpers:
    """Tests for helper functions."""

    def test_safe_str_normal(self):
        assert _safe_str("hello") == "hello"

    def test_safe_str_none(self):
        assert _safe_str(None) is None

    def test_safe_str_nan(self):
        assert _safe_str("nan") is None

    def test_safe_str_empty(self):
        assert _safe_str("  ") is None

    def test_safe_float_normal(self):
        assert _safe_float("1234.56") == 1234.56

    def test_safe_float_none(self):
        assert _safe_float(None) == 0.0

    def test_safe_float_currency(self):
        assert _safe_float("$1,234.56") == 1234.56

    def test_safe_float_nan(self):
        assert _safe_float(float("nan")) == 0.0

    def test_safe_float_invalid(self):
        assert _safe_float("abc") == 0.0

    def test_safe_float_optional_normal(self):
        assert _safe_float_optional("5.0") == 5.0

    def test_safe_float_optional_none(self):
        assert _safe_float_optional(None) is None

    def test_safe_float_optional_nan(self):
        assert _safe_float_optional("nan") is None

    def test_safe_float_optional_empty(self):
        assert _safe_float_optional("") is None

    def test_parse_date_ymd(self):
        assert _parse_date("2025-01-15") == date(2025, 1, 15)

    def test_parse_date_mdy(self):
        assert _parse_date("01/15/2025") == date(2025, 1, 15)

    def test_parse_date_none(self):
        assert _parse_date(None) is None

    def test_parse_date_invalid(self):
        assert _parse_date("not a date") is None

    def test_asset_age_years(self):
        age = _asset_age_years("2020-01-01", reference_date=date(2025, 1, 1))
        assert age is not None
        assert abs(age - 5.0) < 0.1

    def test_asset_age_years_none(self):
        assert _asset_age_years(None) is None

    def test_asset_age_years_invalid(self):
        assert _asset_age_years("bad date") is None


# =============================================================================
# PARSER TESTS
# =============================================================================

class TestParser:
    """Tests for FA entry parser."""

    def test_parse_basic_rows(self):
        rows = sample_fa_rows()
        columns = list(rows[0].keys())
        detection = detect_fa_columns(columns)
        entries = parse_fa_entries(rows, detection)
        assert len(entries) == 5
        assert entries[0].asset_id == "FA-001"
        assert entries[0].cost == 500000.00
        assert entries[0].accumulated_depreciation == 100000.00
        assert entries[0].row_number == 1

    def test_parse_empty(self):
        detection = FAColumnDetection()
        entries = parse_fa_entries([], detection)
        assert entries == []

    def test_row_numbering(self):
        rows = sample_fa_rows()[:2]
        detection = detect_fa_columns(list(rows[0].keys()))
        entries = parse_fa_entries(rows, detection)
        assert entries[0].row_number == 1
        assert entries[1].row_number == 2


# =============================================================================
# DATA QUALITY TESTS
# =============================================================================

class TestDataQuality:
    """Tests for FA data quality assessment."""

    def test_full_quality_data(self):
        entries = make_entries(sample_fa_rows())
        detection = detect_fa_columns(list(sample_fa_rows()[0].keys()))
        quality = assess_fa_data_quality(entries, detection)
        assert quality.completeness_score > 80.0
        assert quality.total_rows == 5

    def test_empty_data(self):
        quality = assess_fa_data_quality([], FAColumnDetection())
        assert quality.completeness_score == 0.0
        assert quality.total_rows == 0

    def test_missing_cost_lowers_score(self):
        rows = [{"Asset ID": "A1", "Original Cost": 0, "Description": "Test"}]
        entries = make_entries(rows)
        detection = detect_fa_columns(list(rows[0].keys()))
        quality = assess_fa_data_quality(entries, detection)
        assert quality.field_fill_rates.get("cost", 0) < 1.0

    def test_fill_rates_reported(self):
        entries = make_entries(sample_fa_rows())
        detection = detect_fa_columns(list(sample_fa_rows()[0].keys()))
        quality = assess_fa_data_quality(entries, detection)
        assert "identifier" in quality.field_fill_rates
        assert "cost" in quality.field_fill_rates

    def test_to_dict(self):
        entries = make_entries(sample_fa_rows())
        detection = detect_fa_columns(list(sample_fa_rows()[0].keys()))
        quality = assess_fa_data_quality(entries, detection)
        d = quality.to_dict()
        assert "completeness_score" in d
        assert "field_fill_rates" in d
        assert "total_rows" in d


# =============================================================================
# RISK TIER TESTS
# =============================================================================

class TestRiskTier:
    """Tests for score_to_risk_tier."""

    def test_low(self):
        assert score_to_risk_tier(5) == RiskTier.LOW

    def test_elevated(self):
        assert score_to_risk_tier(15) == RiskTier.ELEVATED

    def test_moderate(self):
        assert score_to_risk_tier(30) == RiskTier.MODERATE

    def test_high(self):
        assert score_to_risk_tier(60) == RiskTier.HIGH

    def test_critical(self):
        assert score_to_risk_tier(80) == RiskTier.CRITICAL

    def test_boundary_low(self):
        assert score_to_risk_tier(0) == RiskTier.LOW

    def test_boundary_elevated(self):
        assert score_to_risk_tier(10) == RiskTier.ELEVATED

    def test_boundary_moderate(self):
        assert score_to_risk_tier(25) == RiskTier.MODERATE


# =============================================================================
# TIER 1 — STRUCTURAL TESTS
# =============================================================================

class TestFullyDepreciated:
    """FA-01: Fully Depreciated Assets."""

    def test_flags_fully_depreciated(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, accumulated_depreciation=100000, row_number=1,
        )]
        result = run_fully_depreciated_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert result.test_key == "fully_depreciated"

    def test_skips_not_fully_depreciated(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, accumulated_depreciation=50000, row_number=1,
        )]
        result = run_fully_depreciated_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_flags_over_depreciated(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=50000, accumulated_depreciation=55000, row_number=1,
        )]
        result = run_fully_depreciated_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1

    def test_skips_zero_cost(self):
        entries = [FixedAssetEntry(cost=0, accumulated_depreciation=0, row_number=1)]
        result = run_fully_depreciated_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_high_severity_large_cost(self):
        entries = [FixedAssetEntry(
            cost=200000, accumulated_depreciation=200000, row_number=1,
        )]
        result = run_fully_depreciated_test(entries, FixedAssetTestingConfig())
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_disabled(self):
        config = FixedAssetTestingConfig(fully_depreciated_enabled=False)
        entries = [FixedAssetEntry(cost=100000, accumulated_depreciation=100000, row_number=1)]
        result = run_fully_depreciated_test(entries, config)
        assert result.entries_flagged == 0


class TestMissingFields:
    """FA-02: Missing Required Fields."""

    def test_flags_no_identifier(self):
        entries = [FixedAssetEntry(
            cost=5000, acquisition_date="2025-01-01", row_number=1,
        )]
        result = run_missing_fields_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "identifier" in result.flagged_entries[0].issue

    def test_flags_zero_cost(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=0, acquisition_date="2025-01-01", row_number=1,
        )]
        result = run_missing_fields_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "cost" in result.flagged_entries[0].issue

    def test_flags_missing_date(self):
        entries = [FixedAssetEntry(asset_id="A1", cost=5000, row_number=1)]
        result = run_missing_fields_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "acquisition_date" in result.flagged_entries[0].issue

    def test_high_severity_multiple_missing(self):
        entries = [FixedAssetEntry(cost=0, row_number=1)]
        result = run_missing_fields_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_clean_entry_not_flagged(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=5000, acquisition_date="2025-01-01", row_number=1,
        )]
        result = run_missing_fields_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_description_as_identifier(self):
        entries = [FixedAssetEntry(
            description="Office Chair", cost=500, acquisition_date="2025-01-01", row_number=1,
        )]
        result = run_missing_fields_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_disabled(self):
        config = FixedAssetTestingConfig(missing_fields_enabled=False)
        entries = [FixedAssetEntry(cost=0, row_number=1)]
        result = run_missing_fields_test(entries, config)
        assert result.entries_flagged == 0


class TestNegativeValues:
    """FA-03: Negative Cost or Accumulated Depreciation."""

    def test_flags_negative_cost(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=-50000, accumulated_depreciation=10000, row_number=1,
        )]
        result = run_negative_values_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "negative cost" in result.flagged_entries[0].issue

    def test_flags_negative_accum_depr(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=50000, accumulated_depreciation=-5000, row_number=1,
        )]
        result = run_negative_values_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "negative accum depr" in result.flagged_entries[0].issue

    def test_flags_both_negative(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=-50000, accumulated_depreciation=-5000, row_number=1,
        )]
        result = run_negative_values_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "negative cost" in result.flagged_entries[0].issue
        assert "negative accum depr" in result.flagged_entries[0].issue

    def test_positive_values_not_flagged(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=50000, accumulated_depreciation=10000, row_number=1,
        )]
        result = run_negative_values_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_high_severity_large_negative(self):
        entries = [FixedAssetEntry(cost=-100000, row_number=1)]
        result = run_negative_values_test(entries, FixedAssetTestingConfig())
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_disabled(self):
        config = FixedAssetTestingConfig(negative_values_enabled=False)
        entries = [FixedAssetEntry(cost=-50000, row_number=1)]
        result = run_negative_values_test(entries, config)
        assert result.entries_flagged == 0


class TestOverDepreciation:
    """FA-04: Depreciation Exceeds Cost."""

    def test_flags_excess_depreciation(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, accumulated_depreciation=120000, row_number=1,
        )]
        result = run_over_depreciation_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert result.test_key == "over_depreciation"

    def test_skips_equal_amounts(self):
        """FA-01 catches this; FA-04 only flags excess >1%."""
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, accumulated_depreciation=100000, row_number=1,
        )]
        result = run_over_depreciation_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_skips_rounding_difference(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, accumulated_depreciation=100500, row_number=1,
        )]
        result = run_over_depreciation_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_flags_meaningful_excess(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, accumulated_depreciation=115000, row_number=1,
        )]
        result = run_over_depreciation_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1

    def test_high_severity_large_excess(self):
        entries = [FixedAssetEntry(
            cost=100000, accumulated_depreciation=150000, row_number=1,
        )]
        result = run_over_depreciation_test(entries, FixedAssetTestingConfig())
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_skips_zero_cost(self):
        entries = [FixedAssetEntry(cost=0, accumulated_depreciation=5000, row_number=1)]
        result = run_over_depreciation_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_disabled(self):
        config = FixedAssetTestingConfig(over_depreciation_enabled=False)
        entries = [FixedAssetEntry(cost=100000, accumulated_depreciation=200000, row_number=1)]
        result = run_over_depreciation_test(entries, config)
        assert result.entries_flagged == 0


# =============================================================================
# TIER 2 — STATISTICAL TESTS
# =============================================================================

class TestUsefulLifeOutliers:
    """FA-05: Useful Life Outliers."""

    def test_flags_too_short(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=5000, useful_life=0.1, row_number=1,
        )]
        result = run_useful_life_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "below minimum" in result.flagged_entries[0].issue

    def test_flags_too_long(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=5000, useful_life=60.0, row_number=1,
        )]
        result = run_useful_life_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert "above maximum" in result.flagged_entries[0].issue

    def test_normal_life_not_flagged(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=5000, useful_life=10.0, row_number=1,
        )]
        result = run_useful_life_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_no_useful_life_data(self):
        entries = [FixedAssetEntry(asset_id="A1", cost=5000, row_number=1)]
        result = run_useful_life_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0
        assert "No useful life data" in result.description

    def test_boundary_min(self):
        entries = [FixedAssetEntry(useful_life=0.5, cost=1000, row_number=1)]
        result = run_useful_life_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0  # Exactly at minimum, not below

    def test_boundary_max(self):
        entries = [FixedAssetEntry(useful_life=50.0, cost=1000, row_number=1)]
        result = run_useful_life_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0  # Exactly at maximum, not above

    def test_high_severity_extreme(self):
        entries = [FixedAssetEntry(useful_life=200.0, cost=5000, row_number=1)]
        result = run_useful_life_test(entries, FixedAssetTestingConfig())
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_custom_thresholds(self):
        config = FixedAssetTestingConfig(useful_life_min_years=1.0, useful_life_max_years=30.0)
        entries = [FixedAssetEntry(useful_life=0.8, cost=5000, row_number=1)]
        result = run_useful_life_test(entries, config)
        assert result.entries_flagged == 1


class TestCostZScoreOutliers:
    """FA-06: Cost Z-Score Outliers."""

    def test_flags_outlier(self):
        entries = [
            FixedAssetEntry(cost=1000, row_number=i)
            for i in range(1, 21)
        ]
        entries.append(FixedAssetEntry(cost=500000, row_number=21))
        result = run_zscore_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged >= 1
        assert result.test_key == "cost_zscore_outliers"

    def test_uniform_costs_not_flagged(self):
        entries = [
            FixedAssetEntry(cost=10000 + i * 100, row_number=i)
            for i in range(1, 21)
        ]
        result = run_zscore_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_insufficient_entries(self):
        entries = [FixedAssetEntry(cost=1000, row_number=1)]
        result = run_zscore_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0
        assert "Requires at least" in result.description

    def test_identical_costs(self):
        entries = [FixedAssetEntry(cost=5000, row_number=i) for i in range(1, 15)]
        result = run_zscore_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0
        assert "identical" in result.description

    def test_high_severity_extreme_outlier(self):
        entries = [FixedAssetEntry(cost=1000, row_number=i) for i in range(1, 51)]
        entries.append(FixedAssetEntry(cost=10000000, row_number=51))
        result = run_zscore_test(entries, FixedAssetTestingConfig())
        high_flags = [f for f in result.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1

    def test_custom_threshold(self):
        config = FixedAssetTestingConfig(zscore_threshold=1.0)
        entries = [FixedAssetEntry(cost=1000, row_number=i) for i in range(1, 21)]
        entries.append(FixedAssetEntry(cost=5000, row_number=21))
        result = run_zscore_test(entries, config)
        assert result.entries_flagged >= 1


class TestAgeConcentration:
    """FA-07: Asset Age Concentration."""

    def test_flags_concentration(self):
        entries = [
            FixedAssetEntry(cost=100000, acquisition_date="2020-01-01", row_number=1),
            FixedAssetEntry(cost=100000, acquisition_date="2020-06-01", row_number=2),
            FixedAssetEntry(cost=100000, acquisition_date="2020-12-01", row_number=3),
            FixedAssetEntry(cost=10000, acquisition_date="2021-01-01", row_number=4),
            FixedAssetEntry(cost=10000, acquisition_date="2022-01-01", row_number=5),
        ]
        result = run_age_concentration_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged >= 1
        assert result.test_key == "age_concentration"

    def test_distributed_years_not_flagged(self):
        entries = [
            FixedAssetEntry(cost=50000, acquisition_date="2018-01-01", row_number=1),
            FixedAssetEntry(cost=50000, acquisition_date="2019-01-01", row_number=2),
            FixedAssetEntry(cost=50000, acquisition_date="2020-01-01", row_number=3),
            FixedAssetEntry(cost=50000, acquisition_date="2021-01-01", row_number=4),
            FixedAssetEntry(cost=50000, acquisition_date="2022-01-01", row_number=5),
        ]
        result = run_age_concentration_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_no_dates(self):
        entries = [FixedAssetEntry(cost=50000, row_number=1)]
        result = run_age_concentration_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0
        assert "No acquisition dates" in result.description

    def test_zero_cost(self):
        entries = [FixedAssetEntry(cost=0, acquisition_date="2020-01-01", row_number=1)]
        result = run_age_concentration_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_high_severity_extreme_concentration(self):
        entries = [
            FixedAssetEntry(cost=900000, acquisition_date="2020-01-01", row_number=1),
            FixedAssetEntry(cost=100000, acquisition_date="2021-01-01", row_number=2),
        ]
        result = run_age_concentration_test(entries, FixedAssetTestingConfig())
        high_flags = [f for f in result.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1

    def test_custom_threshold(self):
        config = FixedAssetTestingConfig(age_concentration_threshold_pct=0.30)
        entries = [
            FixedAssetEntry(cost=40000, acquisition_date="2020-01-01", row_number=1),
            FixedAssetEntry(cost=30000, acquisition_date="2021-01-01", row_number=2),
            FixedAssetEntry(cost=30000, acquisition_date="2022-01-01", row_number=3),
        ]
        result = run_age_concentration_test(entries, config)
        assert result.entries_flagged >= 1


# =============================================================================
# TIER 3 — ADVANCED TESTS
# =============================================================================

class TestDuplicateAssets:
    """FA-08: Duplicate Asset Detection."""

    def test_flags_duplicates(self):
        entries = [
            FixedAssetEntry(
                cost=25000, description="Laptop", acquisition_date="2024-01-01", row_number=1,
            ),
            FixedAssetEntry(
                cost=25000, description="Laptop", acquisition_date="2024-01-01", row_number=2,
            ),
        ]
        result = run_duplicate_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 2
        assert result.test_key == "duplicate_assets"

    def test_different_costs_not_flagged(self):
        entries = [
            FixedAssetEntry(cost=25000, description="Laptop", acquisition_date="2024-01-01", row_number=1),
            FixedAssetEntry(cost=30000, description="Laptop", acquisition_date="2024-01-01", row_number=2),
        ]
        result = run_duplicate_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_different_dates_not_flagged(self):
        entries = [
            FixedAssetEntry(cost=25000, description="Laptop", acquisition_date="2024-01-01", row_number=1),
            FixedAssetEntry(cost=25000, description="Laptop", acquisition_date="2024-06-01", row_number=2),
        ]
        result = run_duplicate_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_blank_entries_skipped(self):
        entries = [
            FixedAssetEntry(cost=0, description="", row_number=1),
            FixedAssetEntry(cost=0, description="", row_number=2),
        ]
        result = run_duplicate_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_high_severity_large_cost(self):
        entries = [
            FixedAssetEntry(cost=100000, description="Machine", acquisition_date="2024-01-01", row_number=1),
            FixedAssetEntry(cost=100000, description="Machine", acquisition_date="2024-01-01", row_number=2),
        ]
        result = run_duplicate_test(entries, FixedAssetTestingConfig())
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_triple_duplicate(self):
        entries = [
            FixedAssetEntry(cost=5000, description="Chair", acquisition_date="2024-01-01", row_number=i)
            for i in range(1, 4)
        ]
        result = run_duplicate_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 3
        assert "3 occurrences" in result.flagged_entries[0].issue

    def test_disabled(self):
        config = FixedAssetTestingConfig(duplicate_enabled=False)
        entries = [
            FixedAssetEntry(cost=5000, description="Chair", acquisition_date="2024-01-01", row_number=i)
            for i in range(1, 3)
        ]
        result = run_duplicate_test(entries, config)
        assert result.entries_flagged == 0


class TestResidualValueAnomalies:
    """FA-09: Residual Value Anomalies."""

    def test_flags_high_residual(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, residual_value=50000, row_number=1,
        )]
        result = run_residual_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert result.test_key == "residual_value_anomalies"

    def test_normal_residual_not_flagged(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, residual_value=10000, row_number=1,
        )]
        result = run_residual_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_flags_negative_residual(self):
        entries = [FixedAssetEntry(
            asset_id="A1", cost=100000, residual_value=-5000, row_number=1,
        )]
        result = run_residual_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_zero_residual_not_flagged(self):
        entries = [FixedAssetEntry(cost=100000, residual_value=0, row_number=1)]
        result = run_residual_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_zero_cost_skipped(self):
        entries = [FixedAssetEntry(cost=0, residual_value=5000, row_number=1)]
        result = run_residual_test(entries, FixedAssetTestingConfig())
        assert result.entries_flagged == 0

    def test_high_severity_extreme_residual(self):
        entries = [FixedAssetEntry(cost=100000, residual_value=60000, row_number=1)]
        result = run_residual_test(entries, FixedAssetTestingConfig())
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_custom_threshold(self):
        config = FixedAssetTestingConfig(residual_max_pct=0.10)
        entries = [FixedAssetEntry(cost=100000, residual_value=15000, row_number=1)]
        result = run_residual_test(entries, config)
        assert result.entries_flagged == 1

    def test_disabled(self):
        config = FixedAssetTestingConfig(residual_enabled=False)
        entries = [FixedAssetEntry(cost=100000, residual_value=50000, row_number=1)]
        result = run_residual_test(entries, config)
        assert result.entries_flagged == 0


# =============================================================================
# BATTERY + SCORING TESTS
# =============================================================================

class TestBattery:
    """Tests for the full test battery."""

    def test_runs_all_9_tests(self):
        entries = make_entries(sample_fa_rows())
        results = run_fa_test_battery(entries)
        assert len(results) == 9

    def test_all_tiers_represented(self):
        entries = make_entries(sample_fa_rows())
        results = run_fa_test_battery(entries)
        tiers = set(r.test_tier for r in results)
        assert TestTier.STRUCTURAL in tiers
        assert TestTier.STATISTICAL in tiers
        assert TestTier.ADVANCED in tiers

    def test_default_config(self):
        entries = make_entries(sample_fa_rows())
        results = run_fa_test_battery(entries, config=None)
        assert len(results) == 9

    def test_all_test_keys_unique(self):
        entries = make_entries(sample_fa_rows())
        results = run_fa_test_battery(entries)
        keys = [r.test_key for r in results]
        assert len(keys) == len(set(keys))


class TestCompositeScoring:
    """Tests for composite score calculation."""

    def test_clean_data_low_score(self):
        entries = make_entries(sample_fa_rows())
        results = run_fa_test_battery(entries)
        score = calculate_fa_composite_score(results, len(entries))
        assert score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED)

    def test_zero_entries(self):
        score = calculate_fa_composite_score([], 0)
        assert score.score == 0.0
        assert score.risk_tier == RiskTier.LOW
        assert score.total_entries == 0

    def test_flags_by_severity_populated(self):
        entries = [
            FixedAssetEntry(cost=-50000, accumulated_depreciation=60000, row_number=1),
            FixedAssetEntry(cost=100000, accumulated_depreciation=200000, row_number=2),
        ]
        results = run_fa_test_battery(entries)
        score = calculate_fa_composite_score(results, len(entries))
        assert "high" in score.flags_by_severity or "medium" in score.flags_by_severity

    def test_top_findings_populated(self):
        entries = [
            FixedAssetEntry(cost=-50000, row_number=1),
            FixedAssetEntry(cost=100000, accumulated_depreciation=200000, row_number=2),
        ]
        results = run_fa_test_battery(entries)
        score = calculate_fa_composite_score(results, len(entries))
        assert len(score.top_findings) > 0

    def test_multi_flag_multiplier(self):
        """Entries flagged by 3+ tests get a score multiplier."""
        entries = [
            FixedAssetEntry(
                cost=-50000, accumulated_depreciation=-100000,
                useful_life=0.01, residual_value=-500,
                row_number=1,
            ),
        ]
        results = run_fa_test_battery(entries)
        score = calculate_fa_composite_score(results, len(entries))
        assert score.score > 0

    def test_to_dict(self):
        score = FACompositeScore(
            score=25.5, risk_tier=RiskTier.MODERATE,
            tests_run=9, total_entries=100,
            total_flagged=10, flag_rate=0.1,
        )
        d = score.to_dict()
        assert d["score"] == 25.5
        assert d["risk_tier"] == "moderate"
        assert d["tests_run"] == 9


# =============================================================================
# FULL PIPELINE TESTS
# =============================================================================

class TestFullPipeline:
    """Tests for the complete run_fixed_asset_testing pipeline."""

    def test_clean_data(self):
        rows = sample_fa_rows()
        columns = list(rows[0].keys())
        result = run_fixed_asset_testing(rows, columns)
        assert result.composite_score is not None
        assert result.data_quality is not None
        assert result.column_detection is not None
        assert len(result.test_results) == 9

    def test_pipeline_with_column_mapping(self):
        rows = [{"col_a": "FA-001", "col_b": 50000, "col_c": "Machine"}]
        columns = ["col_a", "col_b", "col_c"]
        mapping = {
            "asset_id_column": "col_a",
            "cost_column": "col_b",
            "description_column": "col_c",
        }
        result = run_fixed_asset_testing(rows, columns, column_mapping=mapping)
        assert result.column_detection.overall_confidence == 1.0

    def test_empty_data(self):
        result = run_fixed_asset_testing([], [])
        assert result.composite_score.score == 0
        assert result.composite_score.total_entries == 0

    def test_problematic_data(self):
        rows = [
            {"Asset ID": "A1", "Cost": -50000, "Accumulated Depreciation": 60000,
             "Acquisition Date": "2020-01-01", "Useful Life": 200, "Residual Value": -1000},
        ]
        columns = list(rows[0].keys())
        result = run_fixed_asset_testing(rows, columns)
        assert result.composite_score.total_flagged > 0


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestSerialization:
    """Tests for to_dict methods."""

    def test_fixed_asset_entry_to_dict(self):
        e = FixedAssetEntry(
            asset_id="FA-001", description="Building", cost=500000,
            accumulated_depreciation=100000, row_number=1,
        )
        d = e.to_dict()
        assert d["asset_id"] == "FA-001"
        assert d["cost"] == 500000
        assert d["accumulated_depreciation"] == 100000
        assert d["row_number"] == 1

    def test_flagged_fixed_asset_to_dict(self):
        f = FlaggedFixedAsset(
            entry=FixedAssetEntry(cost=50000, row_number=1),
            test_name="Test", test_key="test_key",
            test_tier=TestTier.STRUCTURAL,
            severity=Severity.HIGH, issue="Issue",
        )
        d = f.to_dict()
        assert d["test_key"] == "test_key"
        assert d["severity"] == "high"
        assert d["test_tier"] == "structural"
        assert "entry" in d

    def test_test_result_to_dict(self):
        r = FATestResult(
            test_name="Test", test_key="test_key",
            test_tier=TestTier.STATISTICAL,
            entries_flagged=5, total_entries=100,
            flag_rate=0.05, severity=Severity.MEDIUM,
            description="Desc",
        )
        d = r.to_dict()
        assert d["test_key"] == "test_key"
        assert d["test_tier"] == "statistical"
        assert d["flag_rate"] == 0.05

    def test_full_result_to_dict(self):
        rows = sample_fa_rows()
        columns = list(rows[0].keys())
        result = run_fixed_asset_testing(rows, columns)
        d = result.to_dict()
        assert "composite_score" in d
        assert "test_results" in d
        assert "data_quality" in d
        assert "column_detection" in d
        assert isinstance(d["test_results"], list)
        assert len(d["test_results"]) == 9


# =============================================================================
# API ROUTE TESTS
# =============================================================================

class TestFixedAssetTestingRoute:
    """Tests for route registration."""

    def test_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/fixed-assets" in paths

    def test_engagement_model_has_fixed_assets(self):
        from engagement_model import ToolName
        assert hasattr(ToolName, "FIXED_ASSET_TESTING")
        assert ToolName.FIXED_ASSET_TESTING.value == "fixed_asset_testing"

    def test_tool_name_count(self):
        from engagement_model import ToolName
        assert len(ToolName) == 11

    def test_workpaper_index_labels(self):
        from workpaper_index_generator import TOOL_LABELS, TOOL_LEAD_SHEET_REFS
        from engagement_model import ToolName
        assert ToolName.FIXED_ASSET_TESTING in TOOL_LABELS
        assert ToolName.FIXED_ASSET_TESTING in TOOL_LEAD_SHEET_REFS
        assert TOOL_LABELS[ToolName.FIXED_ASSET_TESTING] == "Fixed Asset Testing"
        assert "FA-1" in TOOL_LEAD_SHEET_REFS[ToolName.FIXED_ASSET_TESTING][0]
