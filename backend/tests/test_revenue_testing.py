"""
Tests for Revenue Testing Engine — Sprint 104

Covers: column detection, parsing, helpers, data quality,
5 tier 1 tests, 4 tier 2 tests, 3 tier 3 tests,
scoring, battery, full pipeline, serialization, API.

~95 tests across 20 test classes.
"""

from datetime import date

from revenue_testing_engine import (
    BENFORD_EXPECTED,
    FlaggedRevenue,
    RevenueColumnDetection,
    RevenueCompositeScore,
    RevenueEntry,
    RevenueTestingConfig,
    RevenueTestingResult,
    RevenueTestResult,
    _is_contra_revenue,
    _is_manual_entry,
    assess_revenue_data_quality,
    calculate_revenue_composite_score,
    detect_revenue_columns,
    parse_revenue_entries,
    run_revenue_test_battery,
    run_revenue_testing,
    score_to_risk_tier,
)
from revenue_testing_engine import (
    test_benford_law as run_benford_test,
)
from revenue_testing_engine import (
    test_concentration_risk as run_concentration_test,
)
from revenue_testing_engine import (
    test_contra_revenue_anomalies as run_contra_test,
)
from revenue_testing_engine import (
    test_cutoff_risk as run_cutoff_test,
)
from revenue_testing_engine import (
    test_duplicate_entries as run_duplicate_test,
)
from revenue_testing_engine import (
    test_large_manual_entries as run_large_manual_test,
)
from revenue_testing_engine import (
    test_revenue_trend_variance as run_trend_variance_test,
)
from revenue_testing_engine import (
    test_round_revenue_amounts as run_round_amounts_test,
)
from revenue_testing_engine import (
    test_sign_anomalies as run_sign_anomalies_test,
)
from revenue_testing_engine import (
    test_unclassified_entries as run_unclassified_test,
)
from revenue_testing_engine import (
    test_year_end_concentration as run_year_end_test,
)
from revenue_testing_engine import (
    test_zscore_outliers as run_zscore_test,
)
from shared.column_detector import match_column as _match_column

# Aliased imports to avoid pytest collection of test_* functions
from shared.parsing_helpers import parse_date, safe_float, safe_str
from shared.testing_enums import RiskTier, Severity, TestTier

# =============================================================================
# FIXTURE HELPERS
# =============================================================================

def make_entries(rows: list[dict], columns: list[str] | None = None) -> list[RevenueEntry]:
    """Parse rows into RevenueEntry objects using auto-detection."""
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    detection = detect_revenue_columns(columns)
    return parse_revenue_entries(rows, detection)


def sample_revenue_rows() -> list[dict]:
    """4 clean revenue entries for baseline tests."""
    return [
        {
            "Entry Date": "2025-01-15",
            "Amount": -5000.50,
            "Account Name": "Product Revenue",
            "Account Number": "4000",
            "Description": "Monthly subscription",
            "Entry Type": "auto",
            "Reference": "REF-001",
            "Posted By": "system",
        },
        {
            "Entry Date": "2025-02-10",
            "Amount": -12500.00,
            "Account Name": "Service Revenue",
            "Account Number": "4100",
            "Description": "Consulting engagement Q1",
            "Entry Type": "auto",
            "Reference": "REF-002",
            "Posted By": "system",
        },
        {
            "Entry Date": "2025-03-20",
            "Amount": -8750.25,
            "Account Name": "Product Revenue",
            "Account Number": "4000",
            "Description": "Annual license",
            "Entry Type": "auto",
            "Reference": "REF-003",
            "Posted By": "jsmith",
        },
        {
            "Entry Date": "2025-04-05",
            "Amount": -3200.00,
            "Account Name": "Other Revenue",
            "Account Number": "4200",
            "Description": "Interest income",
            "Entry Type": "auto",
            "Reference": "REF-004",
            "Posted By": "system",
        },
    ]


def make_many_entries(n: int = 100, base_amount: float = 1000.0) -> list[RevenueEntry]:
    """Generate n revenue entries with varying amounts for statistical tests."""
    import random
    random.seed(42)
    entries = []
    for i in range(n):
        entries.append(RevenueEntry(
            date=f"2025-{((i % 12) + 1):02d}-{((i % 28) + 1):02d}",
            amount=-(base_amount + random.gauss(0, base_amount * 0.3)),
            account_name=f"Revenue Account {i % 5}",
            account_number=f"4{i % 5}00",
            description=f"Transaction {i}",
            entry_type="auto" if i % 4 != 0 else "manual",
            reference=f"REF-{i:04d}",
            posted_by="system" if i % 3 != 0 else "user1",
            row_number=i + 1,
        ))
    return entries


# =============================================================================
# COLUMN DETECTION TESTS
# =============================================================================

class TestColumnDetection:
    """Tests for detect_revenue_columns."""

    def test_standard_column_names(self):
        cols = ["Entry Date", "Amount", "Account Name", "Account Number",
                "Description", "Entry Type", "Reference", "Posted By"]
        result = detect_revenue_columns(cols)
        assert result.date_column == "Entry Date"
        assert result.amount_column == "Amount"
        assert result.account_name_column == "Account Name"
        assert result.account_number_column == "Account Number"
        assert result.description_column == "Description"
        assert result.entry_type_column == "Entry Type"
        assert result.reference_column == "Reference"
        assert result.posted_by_column == "Posted By"
        assert result.overall_confidence >= 0.80

    def test_alternative_column_names(self):
        cols = ["Posting Date", "Revenue Amount", "GL Account Name", "GL Code",
                "Memo", "Source Type", "Document Number", "Entered By"]
        result = detect_revenue_columns(cols)
        assert result.date_column == "Posting Date"
        assert result.amount_column == "Revenue Amount"
        assert result.account_name_column == "GL Account Name"
        assert result.account_number_column == "GL Code"

    def test_minimal_columns_detected(self):
        cols = ["Date", "Amount", "Account"]
        result = detect_revenue_columns(cols)
        assert result.date_column == "Date"
        assert result.amount_column == "Amount"
        assert result.account_name_column == "Account"

    def test_missing_required_columns(self):
        cols = ["Category", "Notes", "Status"]
        result = detect_revenue_columns(cols)
        assert result.overall_confidence < 0.70
        assert result.requires_mapping
        assert len(result.detection_notes) > 0

    def test_no_double_assignment(self):
        """Greedy assignment: one physical column maps to one type."""
        cols = ["Account Number", "Account Name", "Amount"]
        result = detect_revenue_columns(cols)
        detected = [result.account_number_column, result.account_name_column, result.amount_column]
        non_none = [d for d in detected if d is not None]
        assert len(non_none) == len(set(non_none)), "Columns should not be double-assigned"

    def test_to_dict(self):
        cols = ["Entry Date", "Amount", "Account Name"]
        result = detect_revenue_columns(cols)
        d = result.to_dict()
        assert "date_column" in d
        assert "amount_column" in d
        assert "requires_mapping" in d
        assert "overall_confidence" in d
        assert isinstance(d["all_columns"], list)


# =============================================================================
# MATCH COLUMN TESTS
# =============================================================================

class TestMatchColumn:
    """Tests for _match_column helper."""

    def test_exact_match(self):
        from revenue_testing_engine import REVENUE_DATE_PATTERNS
        assert _match_column("entry date", REVENUE_DATE_PATTERNS) >= 0.95

    def test_partial_match(self):
        from revenue_testing_engine import REVENUE_AMOUNT_PATTERNS
        assert _match_column("total_amount_usd", REVENUE_AMOUNT_PATTERNS) > 0.0

    def test_no_match(self):
        from revenue_testing_engine import REVENUE_DATE_PATTERNS
        assert _match_column("foobar_xyz", REVENUE_DATE_PATTERNS) == 0.0


# =============================================================================
# HELPER TESTS
# =============================================================================

class TestHelpers:
    """Tests for safe_str, safe_float, parse_date, etc."""

    def testsafe_str_none(self):
        assert safe_str(None) is None

    def testsafe_str_empty(self):
        assert safe_str("") is None

    def testsafe_str_nan(self):
        assert safe_str("nan") is None
        assert safe_str("NaN") is None

    def testsafe_str_valid(self):
        assert safe_str("hello") == "hello"
        assert safe_str("  spaced  ") == "spaced"

    def testsafe_float_none(self):
        assert safe_float(None) == 0.0

    def testsafe_float_valid(self):
        assert safe_float(42.5) == 42.5
        assert safe_float("100.50") == 100.50

    def testsafe_float_currency_string(self):
        assert safe_float("$1,234.56") == 1234.56

    def testsafe_float_nan(self):
        assert safe_float(float("nan")) == 0.0

    def testsafe_float_inf(self):
        assert safe_float(float("inf")) == 0.0

    def testsafe_float_invalid(self):
        assert safe_float("not a number") == 0.0

    def testparse_date_iso(self):
        assert parse_date("2025-03-15") == date(2025, 3, 15)

    def testparse_date_us_format(self):
        assert parse_date("03/15/2025") == date(2025, 3, 15)

    def testparse_date_with_time(self):
        assert parse_date("2025-03-15 10:30:00") == date(2025, 3, 15)

    def testparse_date_none(self):
        assert parse_date(None) is None

    def testparse_date_invalid(self):
        assert parse_date("not a date") is None

    def test_is_manual_entry_true(self):
        assert _is_manual_entry("manual") is True
        assert _is_manual_entry("Manual Entry") is True
        assert _is_manual_entry("MAN") is True
        assert _is_manual_entry("user") is True

    def test_is_manual_entry_false(self):
        assert _is_manual_entry("auto") is False
        assert _is_manual_entry("system") is False
        assert _is_manual_entry(None) is False

    def test_is_contra_revenue_true(self):
        keywords = ["return", "refund", "allowance"]
        assert _is_contra_revenue("Customer return processed", None, keywords) is True
        assert _is_contra_revenue(None, "Sales Returns", keywords) is True

    def test_is_contra_revenue_false(self):
        keywords = ["return", "refund", "allowance"]
        assert _is_contra_revenue("Monthly subscription", "Product Revenue", keywords) is False
        assert _is_contra_revenue(None, None, keywords) is False


# =============================================================================
# PARSER TESTS
# =============================================================================

class TestParser:
    """Tests for parse_revenue_entries."""

    def test_basic_parsing(self):
        rows = sample_revenue_rows()
        entries = make_entries(rows)
        assert len(entries) == 4
        assert entries[0].amount == -5000.50
        assert entries[0].row_number == 1

    def test_missing_optional_fields(self):
        rows = [{"Entry Date": "2025-01-01", "Amount": -100, "Account Name": "Revenue"}]
        entries = make_entries(rows)
        assert len(entries) == 1
        assert entries[0].entry_type is None
        assert entries[0].posted_by is None

    def test_row_numbering(self):
        rows = sample_revenue_rows()
        entries = make_entries(rows)
        for i, e in enumerate(entries):
            assert e.row_number == i + 1


# =============================================================================
# DATA QUALITY TESTS
# =============================================================================

class TestDataQuality:
    """Tests for assess_revenue_data_quality."""

    def test_full_data_quality(self):
        rows = sample_revenue_rows()
        columns = list(rows[0].keys())
        detection = detect_revenue_columns(columns)
        entries = parse_revenue_entries(rows, detection)
        quality = assess_revenue_data_quality(entries, detection)
        assert quality.completeness_score > 80.0
        assert quality.total_rows == 4
        assert quality.field_fill_rates["date"] == 1.0
        assert quality.field_fill_rates["amount"] == 1.0

    def test_empty_data(self):
        detection = RevenueColumnDetection()
        quality = assess_revenue_data_quality([], detection)
        assert quality.completeness_score == 0.0
        assert quality.total_rows == 0

    def test_missing_fields_detected(self):
        rows = [{"Amount": -100}]
        columns = ["Amount"]
        detection = detect_revenue_columns(columns)
        entries = parse_revenue_entries(rows, detection)
        quality = assess_revenue_data_quality(entries, detection)
        assert quality.field_fill_rates.get("date", 0) < 1.0
        assert len(quality.detected_issues) > 0

    def test_to_dict(self):
        rows = sample_revenue_rows()
        columns = list(rows[0].keys())
        detection = detect_revenue_columns(columns)
        entries = parse_revenue_entries(rows, detection)
        quality = assess_revenue_data_quality(entries, detection)
        d = quality.to_dict()
        assert "completeness_score" in d
        assert "field_fill_rates" in d
        assert "detected_issues" in d


# =============================================================================
# TIER 1 — STRUCTURAL TESTS
# =============================================================================

class TestLargeManualEntries:
    """RT-01: Large manual revenue entries."""

    def test_manual_large_flagged(self):
        entries = [
            RevenueEntry(amount=-60000, entry_type="manual", row_number=1, account_name="Revenue"),
        ]
        config = RevenueTestingConfig(large_entry_threshold=50000)
        result = run_large_manual_test(entries, config)
        assert result.entries_flagged == 1
        assert result.test_key == "large_manual_entries"

    def test_auto_entries_not_flagged(self):
        entries = [
            RevenueEntry(amount=-60000, entry_type="auto", row_number=1, account_name="Revenue"),
        ]
        config = RevenueTestingConfig(large_entry_threshold=50000)
        result = run_large_manual_test(entries, config)
        assert result.entries_flagged == 0

    def test_unknown_source_flagged_low(self):
        """Entries with no entry_type above threshold flagged as LOW."""
        entries = [
            RevenueEntry(amount=-60000, entry_type=None, row_number=1, account_name="Revenue"),
        ]
        config = RevenueTestingConfig(large_entry_threshold=50000)
        result = run_large_manual_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_below_threshold_not_flagged(self):
        entries = [
            RevenueEntry(amount=-10000, entry_type="manual", row_number=1),
        ]
        config = RevenueTestingConfig(large_entry_threshold=50000)
        result = run_large_manual_test(entries, config)
        assert result.entries_flagged == 0

    def test_very_large_manual_high_severity(self):
        entries = [
            RevenueEntry(amount=-150000, entry_type="manual", row_number=1),
        ]
        config = RevenueTestingConfig(large_entry_threshold=50000)
        result = run_large_manual_test(entries, config)
        assert result.flagged_entries[0].severity == Severity.HIGH


class TestYearEndConcentration:
    """RT-02: Year-end revenue concentration."""

    def test_concentration_flagged(self):
        entries = [
            RevenueEntry(date="2025-01-15", amount=-100, row_number=1),
            RevenueEntry(date="2025-12-28", amount=-900, row_number=2),
            RevenueEntry(date="2025-12-29", amount=-500, row_number=3),
        ]
        config = RevenueTestingConfig(year_end_days=7, year_end_concentration_pct=0.20)
        result = run_year_end_test(entries, config)
        # 1400/1500 = 93% of revenue is in last 7 days
        assert result.entries_flagged >= 1

    def test_even_distribution_not_flagged(self):
        """When revenue is spread evenly, last 7 days should be <20%."""
        entries = [
            RevenueEntry(date="2025-01-15", amount=-500, row_number=1),
            RevenueEntry(date="2025-04-15", amount=-500, row_number=2),
            RevenueEntry(date="2025-07-15", amount=-500, row_number=3),
            RevenueEntry(date="2025-10-15", amount=-500, row_number=4),
            RevenueEntry(date="2025-12-31", amount=-100, row_number=5),
        ]
        config = RevenueTestingConfig(year_end_days=7, year_end_concentration_pct=0.20)
        result = run_year_end_test(entries, config)
        # 100/2100 = 4.8% in last 7 days — well under 20%
        assert result.entries_flagged == 0

    def test_insufficient_dated_entries(self):
        entries = [RevenueEntry(amount=-100, row_number=1)]
        config = RevenueTestingConfig()
        result = run_year_end_test(entries, config)
        assert result.entries_flagged == 0


class TestRoundRevenueAmounts:
    """RT-03: Round amount revenue entries."""

    def test_round_100k_flagged(self):
        entries = [
            RevenueEntry(amount=-100000, row_number=1, account_name="Revenue"),
        ]
        config = RevenueTestingConfig(round_amount_threshold=10000)
        result = run_round_amounts_test(entries, config)
        assert result.entries_flagged == 1

    def test_below_threshold_not_flagged(self):
        entries = [
            RevenueEntry(amount=-5000, row_number=1),
        ]
        config = RevenueTestingConfig(round_amount_threshold=10000)
        result = run_round_amounts_test(entries, config)
        assert result.entries_flagged == 0

    def test_non_round_not_flagged(self):
        entries = [
            RevenueEntry(amount=-15432.67, row_number=1),
        ]
        config = RevenueTestingConfig(round_amount_threshold=10000)
        result = run_round_amounts_test(entries, config)
        assert result.entries_flagged == 0

    def test_max_flags_respected(self):
        entries = [
            RevenueEntry(amount=-50000, row_number=i) for i in range(1, 60)
        ]
        config = RevenueTestingConfig(round_amount_threshold=10000, round_amount_max_flags=10)
        result = run_round_amounts_test(entries, config)
        assert result.entries_flagged <= 10


class TestSignAnomalies:
    """RT-04: Revenue sign anomalies."""

    def test_debit_in_revenue_flagged(self):
        """Positive amounts in revenue accounts are anomalous."""
        entries = [
            RevenueEntry(amount=5000, row_number=1, account_name="Product Revenue"),
        ]
        config = RevenueTestingConfig()
        result = run_sign_anomalies_test(entries, config)
        assert result.entries_flagged == 1

    def test_credit_not_flagged(self):
        """Negative amounts (credits) are normal for revenue."""
        entries = [
            RevenueEntry(amount=-5000, row_number=1, account_name="Product Revenue"),
        ]
        result = run_sign_anomalies_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0

    def test_contra_revenue_excluded(self):
        """Debit entries clearly labeled as returns/refunds are excluded."""
        entries = [
            RevenueEntry(amount=5000, row_number=1, description="Customer return"),
        ]
        config = RevenueTestingConfig()
        result = run_sign_anomalies_test(entries, config)
        assert result.entries_flagged == 0

    def test_disabled(self):
        entries = [
            RevenueEntry(amount=5000, row_number=1, account_name="Revenue"),
        ]
        config = RevenueTestingConfig(sign_anomaly_enabled=False)
        result = run_sign_anomalies_test(entries, config)
        assert result.entries_flagged == 0

    def test_severity_tiers(self):
        entries = [
            RevenueEntry(amount=60000, row_number=1, account_name="Revenue"),   # HIGH
            RevenueEntry(amount=20000, row_number=2, account_name="Revenue"),   # MEDIUM
            RevenueEntry(amount=500, row_number=3, account_name="Revenue"),     # LOW
        ]
        result = run_sign_anomalies_test(entries, RevenueTestingConfig())
        severities = [f.severity for f in result.flagged_entries]
        assert Severity.HIGH in severities
        assert Severity.MEDIUM in severities
        assert Severity.LOW in severities


class TestUnclassifiedEntries:
    """RT-05: Unclassified revenue entries."""

    def test_missing_account_flagged(self):
        entries = [
            RevenueEntry(amount=-1000, row_number=1),  # no account
        ]
        result = run_unclassified_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 1

    def test_account_name_present_not_flagged(self):
        entries = [
            RevenueEntry(amount=-1000, row_number=1, account_name="Revenue"),
        ]
        result = run_unclassified_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0

    def test_account_number_present_not_flagged(self):
        entries = [
            RevenueEntry(amount=-1000, row_number=1, account_number="4000"),
        ]
        result = run_unclassified_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0

    def test_disabled(self):
        entries = [RevenueEntry(amount=-1000, row_number=1)]
        config = RevenueTestingConfig(unclassified_enabled=False)
        result = run_unclassified_test(entries, config)
        assert result.entries_flagged == 0


# =============================================================================
# TIER 2 — STATISTICAL TESTS
# =============================================================================

class TestZScoreOutliers:
    """RT-06: Z-score outlier detection."""

    def test_outlier_flagged(self):
        entries = make_many_entries(50, base_amount=1000)
        # Add extreme outlier
        entries.append(RevenueEntry(amount=-50000, row_number=51, account_name="Revenue"))
        config = RevenueTestingConfig(zscore_threshold=2.5, zscore_min_entries=10)
        result = run_zscore_test(entries, config)
        assert result.entries_flagged >= 1

    def test_insufficient_entries(self):
        entries = [RevenueEntry(amount=-100 * i, row_number=i) for i in range(1, 5)]
        config = RevenueTestingConfig(zscore_min_entries=10)
        result = run_zscore_test(entries, config)
        assert result.entries_flagged == 0

    def test_identical_amounts_no_variance(self):
        entries = [RevenueEntry(amount=-100, row_number=i) for i in range(1, 20)]
        config = RevenueTestingConfig(zscore_min_entries=10)
        result = run_zscore_test(entries, config)
        assert result.entries_flagged == 0

    def test_zero_amounts_skipped(self):
        entries = [RevenueEntry(amount=0, row_number=i) for i in range(1, 20)]
        config = RevenueTestingConfig(zscore_min_entries=10)
        result = run_zscore_test(entries, config)
        assert result.entries_flagged == 0


class TestRevenueTrendVariance:
    """RT-07: Revenue trend variance."""

    def test_large_increase_flagged(self):
        entries = [RevenueEntry(amount=-1000, row_number=i) for i in range(1, 11)]
        config = RevenueTestingConfig(
            prior_period_total=5000, trend_variance_pct=0.30
        )
        result = run_trend_variance_test(entries, config)
        # Current: 10,000, Prior: 5,000 → 100% increase
        assert result.entries_flagged == 1

    def test_within_threshold_not_flagged(self):
        entries = [RevenueEntry(amount=-1000, row_number=i) for i in range(1, 11)]
        config = RevenueTestingConfig(
            prior_period_total=9000, trend_variance_pct=0.30
        )
        result = run_trend_variance_test(entries, config)
        # Current: 10,000, Prior: 9,000 → 11.1% change
        assert result.entries_flagged == 0

    def test_no_prior_period_skipped(self):
        entries = [RevenueEntry(amount=-1000, row_number=1)]
        config = RevenueTestingConfig(prior_period_total=None)
        result = run_trend_variance_test(entries, config)
        assert result.entries_flagged == 0

    def test_very_large_variance_high_severity(self):
        entries = [RevenueEntry(amount=-1000, row_number=i) for i in range(1, 11)]
        config = RevenueTestingConfig(
            prior_period_total=2000, trend_variance_pct=0.30
        )
        result = run_trend_variance_test(entries, config)
        # 400% increase → HIGH severity
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH


class TestConcentrationRisk:
    """RT-08: Revenue concentration risk."""

    def test_single_account_majority_flagged(self):
        entries = [
            RevenueEntry(amount=-9000, account_name="Big Client", row_number=1),
            RevenueEntry(amount=-500, account_name="Small Client A", row_number=2),
            RevenueEntry(amount=-500, account_name="Small Client B", row_number=3),
        ]
        config = RevenueTestingConfig(concentration_threshold_pct=0.50)
        result = run_concentration_test(entries, config)
        assert result.entries_flagged >= 1

    def test_diversified_not_flagged(self):
        entries = [
            RevenueEntry(amount=-1000, account_name=f"Client {i}", row_number=i)
            for i in range(1, 11)
        ]
        config = RevenueTestingConfig(concentration_threshold_pct=0.50)
        result = run_concentration_test(entries, config)
        assert result.entries_flagged == 0

    def test_zero_revenue(self):
        entries = [RevenueEntry(amount=0, account_name="X", row_number=1)]
        result = run_concentration_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0


class TestCutoffRisk:
    """RT-09: Cut-off risk indicators."""

    def test_near_period_end_flagged(self):
        entries = [
            RevenueEntry(date="2025-01-15", amount=-1000, row_number=1),
            RevenueEntry(date="2025-12-30", amount=-5000, row_number=2),
            RevenueEntry(date="2025-12-31", amount=-3000, row_number=3),
        ]
        config = RevenueTestingConfig(
            cutoff_days=3,
            period_end="2025-12-31",
        )
        result = run_cutoff_test(entries, config)
        assert result.entries_flagged >= 1

    def test_near_period_start_flagged(self):
        entries = [
            RevenueEntry(date="2025-01-01", amount=-5000, row_number=1),
            RevenueEntry(date="2025-01-02", amount=-3000, row_number=2),
            RevenueEntry(date="2025-06-15", amount=-1000, row_number=3),
        ]
        config = RevenueTestingConfig(
            cutoff_days=3,
            period_start="2025-01-01",
        )
        result = run_cutoff_test(entries, config)
        assert result.entries_flagged >= 1

    def test_mid_period_not_flagged(self):
        entries = [
            RevenueEntry(date="2025-06-15", amount=-1000, row_number=1),
        ]
        config = RevenueTestingConfig(
            cutoff_days=3,
            period_start="2025-01-01",
            period_end="2025-12-31",
        )
        result = run_cutoff_test(entries, config)
        assert result.entries_flagged == 0

    def test_insufficient_dates(self):
        entries = [RevenueEntry(amount=-1000, row_number=1)]
        config = RevenueTestingConfig(cutoff_days=3)
        result = run_cutoff_test(entries, config)
        assert result.entries_flagged == 0


# =============================================================================
# TIER 3 — ADVANCED TESTS
# =============================================================================

class TestBenfordLaw:
    """RT-10: Benford's Law analysis."""

    def test_benford_with_uniform_distribution(self):
        """Uniformly distributed first digits should deviate from Benford's."""
        import random
        random.seed(99)
        entries = []
        for i in range(200):
            # Create amounts with roughly uniform first digits
            first = random.randint(1, 9)
            amt = first * 1000 + random.randint(0, 999)
            entries.append(RevenueEntry(amount=-amt, row_number=i + 1))

        config = RevenueTestingConfig(benford_min_entries=50)
        result = run_benford_test(entries, config)
        # Uniform dist should fail Benford's
        assert result.entries_flagged >= 1

    def test_insufficient_entries(self):
        entries = [RevenueEntry(amount=-100 * i, row_number=i) for i in range(1, 20)]
        config = RevenueTestingConfig(benford_min_entries=50)
        result = run_benford_test(entries, config)
        assert result.entries_flagged == 0
        assert "Requires at least" in result.description

    def test_benford_expected_distribution(self):
        """Verify BENFORD_EXPECTED sums to ~1.0."""
        total = sum(BENFORD_EXPECTED.values())
        assert abs(total - 1.0) < 0.01


class TestDuplicateEntries:
    """RT-11: Duplicate revenue entry detection."""

    def test_exact_duplicates_flagged(self):
        entries = [
            RevenueEntry(amount=-5000, date="2025-03-15", account_name="revenue", row_number=1),
            RevenueEntry(amount=-5000, date="2025-03-15", account_name="Revenue", row_number=2),
        ]
        result = run_duplicate_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 2

    def test_different_amounts_not_flagged(self):
        entries = [
            RevenueEntry(amount=-5000, date="2025-03-15", account_name="Revenue", row_number=1),
            RevenueEntry(amount=-5001, date="2025-03-15", account_name="Revenue", row_number=2),
        ]
        result = run_duplicate_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0

    def test_different_dates_not_flagged(self):
        entries = [
            RevenueEntry(amount=-5000, date="2025-03-15", account_name="Revenue", row_number=1),
            RevenueEntry(amount=-5000, date="2025-03-16", account_name="Revenue", row_number=2),
        ]
        result = run_duplicate_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0

    def test_disabled(self):
        entries = [
            RevenueEntry(amount=-5000, date="2025-03-15", account_name="Revenue", row_number=1),
            RevenueEntry(amount=-5000, date="2025-03-15", account_name="Revenue", row_number=2),
        ]
        config = RevenueTestingConfig(duplicate_enabled=False)
        result = run_duplicate_test(entries, config)
        assert result.entries_flagged == 0

    def test_high_severity_for_large_amounts(self):
        entries = [
            RevenueEntry(amount=-50000, date="2025-03-15", account_name="Revenue", row_number=1),
            RevenueEntry(amount=-50000, date="2025-03-15", account_name="Revenue", row_number=2),
        ]
        result = run_duplicate_test(entries, RevenueTestingConfig())
        assert result.flagged_entries[0].severity == Severity.HIGH


class TestContraRevenueAnomalies:
    """RT-12: Contra-revenue anomalies."""

    def test_high_contra_ratio_flagged(self):
        entries = [
            RevenueEntry(amount=-10000, account_name="Product Revenue", row_number=1),
            RevenueEntry(amount=-3000, description="Customer return", row_number=2),
        ]
        config = RevenueTestingConfig(contra_threshold_pct=0.15)
        result = run_contra_test(entries, config)
        # 3000/10000 = 30% > 15% threshold
        assert result.entries_flagged >= 1

    def test_low_contra_ratio_not_flagged(self):
        entries = [
            RevenueEntry(amount=-100000, account_name="Product Revenue", row_number=1),
            RevenueEntry(amount=-500, description="Small refund", row_number=2),
        ]
        config = RevenueTestingConfig(contra_threshold_pct=0.15)
        result = run_contra_test(entries, config)
        # 500/100000 = 0.5% < 15%
        assert result.entries_flagged == 0

    def test_no_contra_entries(self):
        entries = [
            RevenueEntry(amount=-10000, account_name="Revenue", row_number=1),
        ]
        result = run_contra_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0

    def test_zero_gross_revenue(self):
        entries = [
            RevenueEntry(amount=-1000, description="Customer return", row_number=1),
        ]
        result = run_contra_test(entries, RevenueTestingConfig())
        assert result.entries_flagged == 0


# =============================================================================
# SCORING TESTS
# =============================================================================

class TestCompositeScoring:
    """Tests for calculate_revenue_composite_score."""

    def test_clean_data_low_score(self):
        results = [
            RevenueTestResult(
                test_name="Test 1", test_key="t1", test_tier=TestTier.STRUCTURAL,
                entries_flagged=0, total_entries=100, flag_rate=0.0,
                severity=Severity.LOW, description="Clean",
            ),
        ]
        score = calculate_revenue_composite_score(results, 100)
        assert score.score < 10
        assert score.risk_tier == RiskTier.LOW

    def test_high_flag_rate_high_score(self):
        flagged = [
            FlaggedRevenue(
                entry=RevenueEntry(amount=-1000, row_number=i),
                test_name="Test", test_key="t", test_tier=TestTier.STRUCTURAL,
                severity=Severity.HIGH, issue="Flagged",
            )
            for i in range(1, 51)
        ]
        results = [
            RevenueTestResult(
                test_name="Test 1", test_key="t1", test_tier=TestTier.STRUCTURAL,
                entries_flagged=50, total_entries=100, flag_rate=0.50,
                severity=Severity.HIGH, description="Many flags",
                flagged_entries=flagged,
            ),
        ]
        score = calculate_revenue_composite_score(results, 100)
        assert score.score > 10
        assert score.total_flagged == 50

    def test_zero_entries(self):
        score = calculate_revenue_composite_score([], 0)
        assert score.score == 0
        assert score.risk_tier == RiskTier.LOW

    def test_flags_by_severity(self):
        flagged = [
            FlaggedRevenue(
                entry=RevenueEntry(amount=-1000, row_number=1),
                test_name="T", test_key="t", test_tier=TestTier.STRUCTURAL,
                severity=Severity.HIGH, issue="High",
            ),
            FlaggedRevenue(
                entry=RevenueEntry(amount=-500, row_number=2),
                test_name="T", test_key="t", test_tier=TestTier.STRUCTURAL,
                severity=Severity.MEDIUM, issue="Med",
            ),
        ]
        results = [
            RevenueTestResult(
                test_name="T", test_key="t", test_tier=TestTier.STRUCTURAL,
                entries_flagged=2, total_entries=10, flag_rate=0.20,
                severity=Severity.HIGH, description="Mixed",
                flagged_entries=flagged,
            ),
        ]
        score = calculate_revenue_composite_score(results, 10)
        assert score.flags_by_severity["high"] == 1
        assert score.flags_by_severity["medium"] == 1

    def test_to_dict(self):
        score = RevenueCompositeScore(
            score=25.5, risk_tier=RiskTier.MODERATE,
            tests_run=12, total_entries=100,
            total_flagged=15, flag_rate=0.15,
        )
        d = score.to_dict()
        assert d["score"] == 25.5
        assert d["risk_tier"] == "moderate"
        assert d["tests_run"] == 12


class TestScoreToRiskTier:
    """Tests for score_to_risk_tier."""

    def test_low(self):
        assert score_to_risk_tier(5) == RiskTier.LOW

    def test_elevated(self):
        assert score_to_risk_tier(15) == RiskTier.ELEVATED

    def test_moderate(self):
        assert score_to_risk_tier(35) == RiskTier.MODERATE

    def test_high(self):
        assert score_to_risk_tier(60) == RiskTier.HIGH

    def test_critical(self):
        assert score_to_risk_tier(80) == RiskTier.CRITICAL

    def test_boundary_0(self):
        assert score_to_risk_tier(0) == RiskTier.LOW

    def test_boundary_10(self):
        assert score_to_risk_tier(10) == RiskTier.ELEVATED

    def test_boundary_25(self):
        assert score_to_risk_tier(25) == RiskTier.MODERATE


# =============================================================================
# BATTERY TESTS
# =============================================================================

class TestBattery:
    """Tests for run_revenue_test_battery."""

    def test_runs_all_16_tests(self):
        entries = make_many_entries(20)
        results = run_revenue_test_battery(entries)
        assert len(results) == 16  # 12 core + 4 contract (skipped without data)

    def test_all_test_keys_unique(self):
        entries = make_many_entries(20)
        results = run_revenue_test_battery(entries)
        keys = [r.test_key for r in results]
        assert len(keys) == len(set(keys))

    def test_test_tier_distribution(self):
        entries = make_many_entries(20)
        results = run_revenue_test_battery(entries)
        tiers = [r.test_tier for r in results]
        assert tiers.count(TestTier.STRUCTURAL) == 5
        assert tiers.count(TestTier.STATISTICAL) == 4
        assert tiers.count(TestTier.ADVANCED) == 3
        assert tiers.count(TestTier.CONTRACT) == 4

    def test_contract_tests_skipped_without_evidence(self):
        entries = make_many_entries(20)
        results = run_revenue_test_battery(entries)
        contract_results = [r for r in results if r.test_tier == TestTier.CONTRACT]
        assert len(contract_results) == 4
        assert all(r.skipped for r in contract_results)

    def test_default_config_used(self):
        entries = make_many_entries(20)
        results = run_revenue_test_battery(entries)
        assert len(results) == 16  # 12 core + 4 contract (skipped)


# =============================================================================
# FULL PIPELINE TESTS
# =============================================================================

class TestFullPipeline:
    """Tests for run_revenue_testing (main entry point)."""

    def test_basic_pipeline(self):
        rows = sample_revenue_rows()
        columns = list(rows[0].keys())
        result = run_revenue_testing(rows, columns)
        assert isinstance(result, RevenueTestingResult)
        assert result.composite_score is not None
        assert len(result.test_results) == 16  # 12 core + 4 contract
        assert result.data_quality is not None
        assert result.column_detection is not None
        assert result.contract_evidence is not None
        assert result.contract_evidence.level == "none"

    def test_pipeline_with_config(self):
        rows = sample_revenue_rows()
        columns = list(rows[0].keys())
        config = RevenueTestingConfig(large_entry_threshold=1000)
        result = run_revenue_testing(rows, columns, config=config)
        assert result.composite_score is not None

    def test_pipeline_with_column_mapping(self):
        rows = [{"col_a": "2025-01-01", "col_b": -5000, "col_c": "Revenue"}]
        columns = ["col_a", "col_b", "col_c"]
        mapping = {
            "date_column": "col_a",
            "amount_column": "col_b",
            "account_name_column": "col_c",
        }
        result = run_revenue_testing(rows, columns, column_mapping=mapping)
        assert result.column_detection.overall_confidence == 1.0

    def test_empty_data(self):
        result = run_revenue_testing([], [])
        assert result.composite_score.score == 0
        assert result.composite_score.total_entries == 0


# =============================================================================
# SERIALIZATION TESTS
# =============================================================================

class TestSerialization:
    """Tests for to_dict methods."""

    def test_revenue_entry_to_dict(self):
        e = RevenueEntry(
            date="2025-01-15", amount=-5000, account_name="Revenue",
            account_number="4000", row_number=1,
        )
        d = e.to_dict()
        assert d["date"] == "2025-01-15"
        assert d["amount"] == -5000
        assert d["account_name"] == "Revenue"
        assert d["row_number"] == 1

    def test_flagged_revenue_to_dict(self):
        f = FlaggedRevenue(
            entry=RevenueEntry(amount=-1000, row_number=1),
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
        r = RevenueTestResult(
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
        rows = sample_revenue_rows()
        columns = list(rows[0].keys())
        result = run_revenue_testing(rows, columns)
        d = result.to_dict()
        assert "composite_score" in d
        assert "test_results" in d
        assert "data_quality" in d
        assert "column_detection" in d
        assert isinstance(d["test_results"], list)
        assert len(d["test_results"]) == 16  # 12 core + 4 contract
        assert "contract_evidence" in d
        assert d["contract_evidence"]["level"] == "none"


# =============================================================================
# CONTRACT EVIDENCE LEVEL TESTS (Sprint 352)
# =============================================================================

class TestContractEvidenceLevel:
    """Tests for assess_contract_evidence()."""

    def test_full_evidence(self):
        from revenue_testing_engine import assess_contract_evidence
        det = RevenueColumnDetection(
            contract_id_column="Contract ID",
            performance_obligation_id_column="PO ID",
            recognition_method_column="Rec Method",
            contract_modification_column="Mod Type",
            allocation_basis_column="SSP Basis",
            obligation_satisfaction_date_column="Satisfaction Date",
        )
        ev = assess_contract_evidence(det)
        assert ev.level == "full"
        assert ev.confidence_modifier == 1.0
        assert len(ev.detected_fields) == 6

    def test_partial_evidence(self):
        from revenue_testing_engine import assess_contract_evidence
        det = RevenueColumnDetection(
            contract_id_column="Contract ID",
            performance_obligation_id_column="PO ID",
            obligation_satisfaction_date_column="Satisfaction Date",
        )
        ev = assess_contract_evidence(det)
        assert ev.level == "partial"
        assert ev.confidence_modifier == 0.70
        assert len(ev.detected_fields) == 3

    def test_minimal_evidence(self):
        from revenue_testing_engine import assess_contract_evidence
        det = RevenueColumnDetection(
            obligation_satisfaction_date_column="Satisfaction Date",
        )
        ev = assess_contract_evidence(det)
        assert ev.level == "minimal"
        assert ev.confidence_modifier == 0.50
        assert len(ev.detected_fields) == 1

    def test_no_evidence(self):
        from revenue_testing_engine import assess_contract_evidence
        det = RevenueColumnDetection()
        ev = assess_contract_evidence(det)
        assert ev.level == "none"
        assert ev.confidence_modifier == 0.0
        assert len(ev.detected_fields) == 0


# =============================================================================
# RT-13: RECOGNITION BEFORE SATISFACTION TESTS (Sprint 352)
# =============================================================================

class TestRecognitionBeforeSatisfaction:
    """Tests for test_recognition_before_satisfaction (RT-13)."""

    def _make_evidence(self, fields: list[str]) -> "ContractEvidenceLevel":
        from revenue_testing_engine import ContractEvidenceLevel
        return ContractEvidenceLevel(level="full", confidence_modifier=1.0, detected_fields=fields)

    def test_flags_high_premature(self):
        from revenue_testing_engine import test_recognition_before_satisfaction, ContractEvidenceLevel
        entries = [
            RevenueEntry(date="2025-01-01", amount=5000, obligation_satisfaction_date="2025-02-15", row_number=1),
        ]
        evidence = self._make_evidence(["contract_id", "obligation_satisfaction_date"])
        config = RevenueTestingConfig()
        result = test_recognition_before_satisfaction(entries, config, evidence)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH
        assert not result.skipped

    def test_flags_medium_small_gap(self):
        from revenue_testing_engine import test_recognition_before_satisfaction
        entries = [
            RevenueEntry(date="2025-01-10", amount=5000, obligation_satisfaction_date="2025-01-15", row_number=1),
        ]
        evidence = self._make_evidence(["contract_id", "obligation_satisfaction_date"])
        config = RevenueTestingConfig()
        result = test_recognition_before_satisfaction(entries, config, evidence)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_exempt_over_time(self):
        from revenue_testing_engine import test_recognition_before_satisfaction
        entries = [
            RevenueEntry(
                date="2025-01-01", amount=5000, obligation_satisfaction_date="2025-06-01",
                recognition_method="over-time", row_number=1,
            ),
        ]
        evidence = self._make_evidence(["contract_id", "obligation_satisfaction_date", "recognition_method"])
        config = RevenueTestingConfig()
        result = test_recognition_before_satisfaction(entries, config, evidence)
        assert result.entries_flagged == 0

    def test_same_day_ok(self):
        from revenue_testing_engine import test_recognition_before_satisfaction
        entries = [
            RevenueEntry(date="2025-03-15", amount=5000, obligation_satisfaction_date="2025-03-15", row_number=1),
        ]
        evidence = self._make_evidence(["contract_id", "obligation_satisfaction_date"])
        config = RevenueTestingConfig()
        result = test_recognition_before_satisfaction(entries, config, evidence)
        assert result.entries_flagged == 0

    def test_skipped_without_column(self):
        from revenue_testing_engine import test_recognition_before_satisfaction
        entries = [RevenueEntry(date="2025-01-01", amount=5000, row_number=1)]
        evidence = self._make_evidence(["contract_id"])  # No obligation_satisfaction_date
        config = RevenueTestingConfig()
        result = test_recognition_before_satisfaction(entries, config, evidence)
        assert result.skipped
        assert "not detected" in result.skip_reason


# =============================================================================
# RT-14: MISSING OBLIGATION LINKAGE TESTS (Sprint 352)
# =============================================================================

class TestMissingObligationLinkage:
    """Tests for test_missing_obligation_linkage (RT-14)."""

    def _make_evidence(self, fields: list[str]) -> "ContractEvidenceLevel":
        from revenue_testing_engine import ContractEvidenceLevel
        return ContractEvidenceLevel(level="partial", confidence_modifier=0.70, detected_fields=fields)

    def test_contract_without_po(self):
        from revenue_testing_engine import test_missing_obligation_linkage
        entries = [
            RevenueEntry(contract_id="C001", performance_obligation_id=None, amount=1000, row_number=1),
        ]
        evidence = self._make_evidence(["contract_id", "performance_obligation_id"])
        result = test_missing_obligation_linkage(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_po_without_contract(self):
        from revenue_testing_engine import test_missing_obligation_linkage
        entries = [
            RevenueEntry(contract_id=None, performance_obligation_id="PO-A", amount=1000, row_number=1),
        ]
        evidence = self._make_evidence(["contract_id", "performance_obligation_id"])
        result = test_missing_obligation_linkage(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_both_present_clean(self):
        from revenue_testing_engine import test_missing_obligation_linkage
        entries = [
            RevenueEntry(contract_id="C001", performance_obligation_id="PO-A", amount=1000, row_number=1),
        ]
        evidence = self._make_evidence(["contract_id", "performance_obligation_id"])
        result = test_missing_obligation_linkage(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 0

    def test_skipped_without_either_column(self):
        from revenue_testing_engine import test_missing_obligation_linkage
        entries = [RevenueEntry(amount=1000, row_number=1)]
        evidence = self._make_evidence(["recognition_method"])  # Neither contract_id nor PO
        result = test_missing_obligation_linkage(entries, RevenueTestingConfig(), evidence)
        assert result.skipped


# =============================================================================
# RT-15: MODIFICATION TREATMENT MISMATCH TESTS (Sprint 352)
# =============================================================================

class TestModificationTreatmentMismatch:
    """Tests for test_modification_treatment_mismatch (RT-15)."""

    def _make_evidence(self, fields: list[str]) -> "ContractEvidenceLevel":
        from revenue_testing_engine import ContractEvidenceLevel
        return ContractEvidenceLevel(level="partial", confidence_modifier=0.70, detected_fields=fields)

    def test_mixed_treatments_high(self):
        from revenue_testing_engine import test_modification_treatment_mismatch
        entries = [
            RevenueEntry(contract_id="C001", contract_modification="prospective", amount=1000, row_number=1),
            RevenueEntry(contract_id="C001", contract_modification="catch-up", amount=2000, row_number=2),
        ]
        evidence = self._make_evidence(["contract_id", "contract_modification"])
        result = test_modification_treatment_mismatch(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 2
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_consistent_ok(self):
        from revenue_testing_engine import test_modification_treatment_mismatch
        entries = [
            RevenueEntry(contract_id="C001", contract_modification="prospective", amount=1000, row_number=1),
            RevenueEntry(contract_id="C001", contract_modification="prospective", amount=2000, row_number=2),
        ]
        evidence = self._make_evidence(["contract_id", "contract_modification"])
        result = test_modification_treatment_mismatch(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 0

    def test_partial_tracking_medium(self):
        from revenue_testing_engine import test_modification_treatment_mismatch
        entries = [
            RevenueEntry(contract_id="C001", contract_modification="prospective", amount=1000, row_number=1),
            RevenueEntry(contract_id="C001", contract_modification=None, amount=2000, row_number=2),
        ]
        evidence = self._make_evidence(["contract_id", "contract_modification"])
        result = test_modification_treatment_mismatch(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 2
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_single_entry_contract_ok(self):
        from revenue_testing_engine import test_modification_treatment_mismatch
        entries = [
            RevenueEntry(contract_id="C001", contract_modification="prospective", amount=1000, row_number=1),
        ]
        evidence = self._make_evidence(["contract_id", "contract_modification"])
        result = test_modification_treatment_mismatch(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 0

    def test_skipped_without_columns(self):
        from revenue_testing_engine import test_modification_treatment_mismatch
        entries = [RevenueEntry(amount=1000, row_number=1)]
        evidence = self._make_evidence(["contract_id"])  # No contract_modification
        result = test_modification_treatment_mismatch(entries, RevenueTestingConfig(), evidence)
        assert result.skipped


# =============================================================================
# RT-16: ALLOCATION INCONSISTENCY TESTS (Sprint 352)
# =============================================================================

class TestAllocationInconsistency:
    """Tests for test_allocation_inconsistency (RT-16)."""

    def _make_evidence(self, fields: list[str]) -> "ContractEvidenceLevel":
        from revenue_testing_engine import ContractEvidenceLevel
        return ContractEvidenceLevel(level="partial", confidence_modifier=0.70, detected_fields=fields)

    def test_multiple_bases_high(self):
        from revenue_testing_engine import test_allocation_inconsistency
        entries = [
            RevenueEntry(contract_id="C001", allocation_basis="observable price", amount=1000, row_number=1),
            RevenueEntry(contract_id="C001", allocation_basis="residual approach", amount=2000, row_number=2),
        ]
        evidence = self._make_evidence(["contract_id", "allocation_basis"])
        result = test_allocation_inconsistency(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 2
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_consistent_ok(self):
        from revenue_testing_engine import test_allocation_inconsistency
        entries = [
            RevenueEntry(contract_id="C001", allocation_basis="observable price", amount=1000, row_number=1),
            RevenueEntry(contract_id="C001", allocation_basis="observable price", amount=2000, row_number=2),
        ]
        evidence = self._make_evidence(["contract_id", "allocation_basis"])
        result = test_allocation_inconsistency(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 0

    def test_sparse_low(self):
        from revenue_testing_engine import test_allocation_inconsistency
        entries = [
            RevenueEntry(contract_id="C001", allocation_basis="observable price", amount=1000, row_number=1),
            RevenueEntry(contract_id="C001", allocation_basis=None, amount=2000, row_number=2),
        ]
        evidence = self._make_evidence(["contract_id", "allocation_basis"])
        result = test_allocation_inconsistency(entries, RevenueTestingConfig(), evidence)
        assert result.entries_flagged == 2
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_skipped_without_columns(self):
        from revenue_testing_engine import test_allocation_inconsistency
        entries = [RevenueEntry(amount=1000, row_number=1)]
        evidence = self._make_evidence(["contract_id"])  # No allocation_basis
        result = test_allocation_inconsistency(entries, RevenueTestingConfig(), evidence)
        assert result.skipped


# =============================================================================
# BATTERY WITH CONTRACT TESTS (Sprint 352)
# =============================================================================

class TestBatteryWithContractTests:
    """Tests for battery integration with contract tests."""

    def test_16_results_with_evidence(self):
        from revenue_testing_engine import ContractEvidenceLevel
        entries = [
            RevenueEntry(
                date="2025-01-01", amount=5000, account_name="Sales",
                contract_id="C001", performance_obligation_id="PO-A",
                obligation_satisfaction_date="2025-02-01", row_number=1,
            ),
            RevenueEntry(
                date="2025-01-15", amount=3000, account_name="Sales",
                contract_id="C001", performance_obligation_id="PO-B",
                obligation_satisfaction_date="2025-01-10", row_number=2,
            ),
        ]
        evidence = ContractEvidenceLevel(
            level="partial", confidence_modifier=0.70,
            detected_fields=["contract_id", "performance_obligation_id", "obligation_satisfaction_date"],
        )
        results = run_revenue_test_battery(entries, evidence=evidence)
        assert len(results) == 16
        contract_results = [r for r in results if r.test_tier == TestTier.CONTRACT]
        assert len(contract_results) == 4
        # Some should be active (not skipped), some may be skipped due to missing columns
        active_contract = [r for r in contract_results if not r.skipped]
        assert len(active_contract) >= 2  # RT-13 and RT-14 should run

    def test_4_skipped_without_evidence(self):
        entries = make_many_entries(5)
        results = run_revenue_test_battery(entries)
        contract_results = [r for r in results if r.test_tier == TestTier.CONTRACT]
        assert len(contract_results) == 4
        assert all(r.skipped for r in contract_results)
        assert all("No contract data" in r.skip_reason for r in contract_results)


# =============================================================================
# API ROUTE TESTS
# =============================================================================

class TestRevenueTestingRoute:
    """Tests for route registration."""

    def test_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/revenue-testing" in paths

    def test_engagement_model_has_revenue(self):
        from engagement_model import ToolName
        assert hasattr(ToolName, "REVENUE_TESTING")
        assert ToolName.REVENUE_TESTING.value == "revenue_testing"
