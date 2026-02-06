"""
Tests for Journal Entry Testing Engine - Sprint 64

Covers:
- GL column detection (standard, dual-date, single-amount, edge cases)
- GL entry parsing
- Data quality scoring
- Multi-currency detection
- T1: Unbalanced Entries
- T2: Missing Fields
- T3: Duplicate Entries
- T4: Round Dollar Amounts
- T5: Unusual Amounts
- Composite scoring
- Full pipeline (run_je_testing)
- Serialization (to_dict)
"""

import pytest
from je_testing_engine import (
    # Column detection
    detect_gl_columns,
    GLColumnDetectionResult,
    GLColumnType,
    # Parsing
    parse_gl_entries,
    JournalEntry,
    # Data quality
    assess_data_quality,
    GLDataQuality,
    # Multi-currency
    detect_multi_currency,
    MultiCurrencyWarning,
    # Config
    JETestingConfig,
    # Tests — aliased to avoid pytest collection
    test_unbalanced_entries as run_unbalanced_test,
    test_missing_fields as run_missing_fields_test,
    test_duplicate_entries as run_duplicate_test,
    test_round_amounts as run_round_amounts_test,
    test_unusual_amounts as run_unusual_amounts_test,
    # Battery & scoring
    run_test_battery,
    calculate_composite_score,
    score_to_risk_tier,
    # Main entry point
    run_je_testing,
    # Enums & types
    RiskTier,
    TestTier,
    Severity,
    TestResult,
    FlaggedEntry,
    CompositeScore,
    JETestingResult,
    # Helpers
    _safe_str,
    _safe_float,
)


# =============================================================================
# FIXTURES
# =============================================================================

def make_entries(rows: list[dict], columns: list[str] | None = None) -> list[JournalEntry]:
    """Helper to create JournalEntry list from row dicts."""
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    detection = detect_gl_columns(columns)
    return parse_gl_entries(rows, detection)


def sample_gl_rows() -> list[dict]:
    """Standard GL rows for testing."""
    return [
        {"Entry ID": "JE001", "Date": "2025-01-15", "Account": "Cash", "Debit": 1000, "Credit": 0, "Description": "Payment received", "Posted By": "jsmith", "Reference": "INV-001"},
        {"Entry ID": "JE001", "Date": "2025-01-15", "Account": "Accounts Receivable", "Debit": 0, "Credit": 1000, "Description": "Payment received", "Posted By": "jsmith", "Reference": "INV-001"},
        {"Entry ID": "JE002", "Date": "2025-01-20", "Account": "Office Supplies", "Debit": 250, "Credit": 0, "Description": "Office supplies purchase", "Posted By": "jdoe", "Reference": "PO-100"},
        {"Entry ID": "JE002", "Date": "2025-01-20", "Account": "Accounts Payable", "Debit": 0, "Credit": 250, "Description": "Office supplies purchase", "Posted By": "jdoe", "Reference": "PO-100"},
    ]


def sample_gl_columns() -> list[str]:
    return ["Entry ID", "Date", "Account", "Debit", "Credit", "Description", "Posted By", "Reference"]


# =============================================================================
# GL COLUMN DETECTION
# =============================================================================

class TestGLColumnDetection:
    """Tests for detect_gl_columns()."""

    def test_standard_columns(self):
        cols = ["Date", "Account", "Debit", "Credit", "Description", "Reference"]
        result = detect_gl_columns(cols)
        assert result.date_column == "Date"
        assert result.account_column == "Account"
        assert result.debit_column == "Debit"
        assert result.credit_column == "Credit"
        assert result.description_column == "Description"
        assert result.reference_column == "Reference"
        assert result.has_separate_debit_credit is True

    def test_dual_date_detection(self):
        cols = ["Entry Date", "Posting Date", "Account", "Debit", "Credit"]
        result = detect_gl_columns(cols)
        assert result.has_dual_dates is True
        assert result.entry_date_column == "Entry Date"
        assert result.posting_date_column == "Posting Date"
        assert result.date_column == "Posting Date"  # Primary = posting

    def test_single_amount_column(self):
        cols = ["Date", "Account", "Amount", "Description"]
        result = detect_gl_columns(cols)
        assert result.amount_column == "Amount"
        assert result.has_separate_debit_credit is False
        assert result.debit_column is None
        assert result.credit_column is None

    def test_entry_id_detection(self):
        cols = ["Entry ID", "Date", "Account", "Debit", "Credit"]
        result = detect_gl_columns(cols)
        assert result.entry_id_column == "Entry ID"

    def test_posted_by_detection(self):
        cols = ["Date", "Account", "Debit", "Credit", "Posted By"]
        result = detect_gl_columns(cols)
        assert result.posted_by_column == "Posted By"

    def test_source_detection(self):
        cols = ["Date", "Account", "Debit", "Credit", "Source Module"]
        result = detect_gl_columns(cols)
        assert result.source_column == "Source Module"

    def test_currency_detection(self):
        cols = ["Date", "Account", "Debit", "Credit", "Currency"]
        result = detect_gl_columns(cols)
        assert result.currency_column == "Currency"

    def test_overall_confidence_high(self):
        cols = ["Transaction Date", "Account Name", "Debit", "Credit"]
        result = detect_gl_columns(cols)
        assert result.overall_confidence >= 0.85

    def test_overall_confidence_low_missing_columns(self):
        cols = ["Col1", "Col2", "Col3"]
        result = detect_gl_columns(cols)
        assert result.overall_confidence < 0.50

    def test_requires_mapping_flag(self):
        cols = ["x", "y", "z"]
        result = detect_gl_columns(cols)
        assert result.requires_mapping is True

    def test_no_requires_mapping_for_standard(self):
        cols = ["Date", "Account", "Debit", "Credit"]
        result = detect_gl_columns(cols)
        assert result.requires_mapping is False

    def test_alternative_column_names(self):
        cols = ["Trans Date", "GL Account", "Dr", "Cr", "Memo", "Voucher Number", "Entered By"]
        result = detect_gl_columns(cols)
        assert result.date_column is not None
        assert result.account_column is not None
        assert result.debit_column is not None
        assert result.credit_column is not None
        assert result.description_column is not None
        assert result.reference_column is not None
        assert result.posted_by_column is not None

    def test_to_dict(self):
        cols = ["Date", "Account", "Debit", "Credit"]
        result = detect_gl_columns(cols)
        d = result.to_dict()
        assert "date_column" in d
        assert "account_column" in d
        assert "has_dual_dates" in d
        assert "overall_confidence" in d
        assert isinstance(d["overall_confidence"], float)


# =============================================================================
# GL ENTRY PARSING
# =============================================================================

class TestGLParsing:
    """Tests for parse_gl_entries()."""

    def test_parse_standard_rows(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        detection = detect_gl_columns(cols)
        entries = parse_gl_entries(rows, detection)
        assert len(entries) == 4
        assert entries[0].account == "Cash"
        assert entries[0].debit == 1000
        assert entries[0].credit == 0

    def test_parse_single_amount(self):
        rows = [
            {"Date": "2025-01-15", "Account": "Cash", "Amount": 1000},
            {"Date": "2025-01-15", "Account": "Revenue", "Amount": -1000},
        ]
        detection = detect_gl_columns(["Date", "Account", "Amount"])
        entries = parse_gl_entries(rows, detection)
        assert entries[0].debit == 1000
        assert entries[0].credit == 0
        assert entries[1].debit == 0
        assert entries[1].credit == 1000

    def test_parse_row_numbers(self):
        rows = sample_gl_rows()
        detection = detect_gl_columns(sample_gl_columns())
        entries = parse_gl_entries(rows, detection)
        assert entries[0].row_number == 1
        assert entries[3].row_number == 4

    def test_parse_dual_dates(self):
        rows = [
            {"Entry Date": "2025-01-10", "Posting Date": "2025-01-15", "Account": "Cash", "Debit": 100, "Credit": 0},
        ]
        detection = detect_gl_columns(["Entry Date", "Posting Date", "Account", "Debit", "Credit"])
        entries = parse_gl_entries(rows, detection)
        assert entries[0].entry_date == "2025-01-10"
        assert entries[0].posting_date == "2025-01-15"

    def test_net_amount_property(self):
        e = JournalEntry(debit=500, credit=0)
        assert e.net_amount == 500
        e2 = JournalEntry(debit=0, credit=300)
        assert e2.net_amount == -300

    def test_abs_amount_property(self):
        e = JournalEntry(debit=500, credit=0)
        assert e.abs_amount == 500
        e2 = JournalEntry(debit=0, credit=300)
        assert e2.abs_amount == 300

    def test_entry_to_dict(self):
        e = JournalEntry(entry_id="JE001", account="Cash", debit=100, credit=0, row_number=1)
        d = e.to_dict()
        assert d["entry_id"] == "JE001"
        assert d["account"] == "Cash"
        assert d["debit"] == 100
        assert d["row_number"] == 1


# =============================================================================
# SAFE HELPERS
# =============================================================================

class TestSafeHelpers:
    """Tests for _safe_str and _safe_float."""

    def test_safe_str_normal(self):
        assert _safe_str("hello") == "hello"

    def test_safe_str_none(self):
        assert _safe_str(None) is None

    def test_safe_str_nan(self):
        assert _safe_str("nan") is None
        assert _safe_str("NaN") is None

    def test_safe_str_empty(self):
        assert _safe_str("") is None
        assert _safe_str("  ") is None

    def test_safe_float_normal(self):
        assert _safe_float(123.45) == 123.45

    def test_safe_float_none(self):
        assert _safe_float(None) == 0.0

    def test_safe_float_string(self):
        assert _safe_float("123.45") == 123.45

    def test_safe_float_currency_string(self):
        assert _safe_float("$1,234.56") == 1234.56

    def test_safe_float_nan(self):
        assert _safe_float(float("nan")) == 0.0

    def test_safe_float_non_numeric(self):
        assert _safe_float("abc") == 0.0


# =============================================================================
# DATA QUALITY SCORING
# =============================================================================

class TestDataQuality:
    """Tests for assess_data_quality()."""

    def test_perfect_quality(self):
        entries = make_entries(sample_gl_rows(), sample_gl_columns())
        detection = detect_gl_columns(sample_gl_columns())
        quality = assess_data_quality(entries, detection)
        assert quality.completeness_score > 80
        assert quality.total_rows == 4
        assert quality.field_fill_rates["date"] == 1.0
        assert quality.field_fill_rates["account"] == 1.0

    def test_missing_descriptions(self):
        rows = [
            {"Date": "2025-01-15", "Account": "Cash", "Debit": 100, "Credit": 0, "Description": ""},
            {"Date": "2025-01-15", "Account": "Revenue", "Debit": 0, "Credit": 100, "Description": ""},
        ]
        cols = ["Date", "Account", "Debit", "Credit", "Description"]
        entries = make_entries(rows, cols)
        detection = detect_gl_columns(cols)
        quality = assess_data_quality(entries, detection)
        assert quality.field_fill_rates["description"] == 0.0
        assert any("description" in i.lower() for i in quality.detected_issues)

    def test_empty_entries(self):
        detection = detect_gl_columns(["Date", "Account", "Debit", "Credit"])
        quality = assess_data_quality([], detection)
        assert quality.completeness_score == 0.0
        assert quality.total_rows == 0

    def test_quality_to_dict(self):
        entries = make_entries(sample_gl_rows(), sample_gl_columns())
        detection = detect_gl_columns(sample_gl_columns())
        quality = assess_data_quality(entries, detection)
        d = quality.to_dict()
        assert "completeness_score" in d
        assert "field_fill_rates" in d
        assert "detected_issues" in d
        assert "total_rows" in d


# =============================================================================
# MULTI-CURRENCY DETECTION
# =============================================================================

class TestMultiCurrency:
    """Tests for detect_multi_currency()."""

    def test_single_currency_returns_none(self):
        entries = [
            JournalEntry(currency="USD"),
            JournalEntry(currency="USD"),
        ]
        assert detect_multi_currency(entries) is None

    def test_no_currency_returns_none(self):
        entries = [
            JournalEntry(),
            JournalEntry(),
        ]
        assert detect_multi_currency(entries) is None

    def test_multi_currency_detected(self):
        entries = [
            JournalEntry(currency="USD"),
            JournalEntry(currency="USD"),
            JournalEntry(currency="EUR"),
            JournalEntry(currency="GBP"),
        ]
        result = detect_multi_currency(entries)
        assert result is not None
        assert len(result.currencies_found) == 3
        assert result.primary_currency == "USD"
        assert "Multi-currency GL detected" in result.warning_message

    def test_multi_currency_counts(self):
        entries = [
            JournalEntry(currency="USD"),
            JournalEntry(currency="USD"),
            JournalEntry(currency="USD"),
            JournalEntry(currency="EUR"),
        ]
        result = detect_multi_currency(entries)
        assert result is not None
        assert result.entry_counts_by_currency["USD"] == 3
        assert result.entry_counts_by_currency["EUR"] == 1

    def test_multi_currency_to_dict(self):
        entries = [
            JournalEntry(currency="USD"),
            JournalEntry(currency="EUR"),
        ]
        result = detect_multi_currency(entries)
        assert result is not None
        d = result.to_dict()
        assert "currencies_found" in d
        assert "primary_currency" in d
        assert "warning_message" in d


# =============================================================================
# T1: UNBALANCED ENTRIES
# =============================================================================

class TestUnbalancedEntries:
    """Tests for test_unbalanced_entries()."""

    def test_balanced_entries_no_flags(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=1000, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=1000, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_unbalanced_entry_flagged(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=1000, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=500, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Both lines of the entry flagged
        assert result.flagged_entries[0].severity == Severity.MEDIUM  # diff=500, between 10-1000

    def test_rounding_tolerance(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=100.005, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=100.00, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig(balance_tolerance=0.01))
        assert result.entries_flagged == 0  # Within tolerance

    def test_multiple_groups(self):
        entries = [
            JournalEntry(entry_id="JE001", debit=100, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=100, row_number=2),
            JournalEntry(entry_id="JE002", debit=200, credit=0, row_number=3),
            JournalEntry(entry_id="JE002", debit=0, credit=150, row_number=4),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Only JE002 lines flagged

    def test_fallback_to_reference(self):
        entries = [
            JournalEntry(reference="REF001", debit=100, credit=0, row_number=1),
            JournalEntry(reference="REF001", debit=0, credit=50, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.entries_flagged == 2

    def test_severity_based_on_difference(self):
        # Small difference = low severity
        entries = [
            JournalEntry(entry_id="JE001", debit=100, credit=0, row_number=1),
            JournalEntry(entry_id="JE001", debit=0, credit=95, row_number=2),
        ]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_test_key(self):
        entries = [JournalEntry(entry_id="JE001", debit=100, credit=0, row_number=1)]
        result = run_unbalanced_test(entries, JETestingConfig())
        assert result.test_key == "unbalanced_entries"
        assert result.test_tier == TestTier.STRUCTURAL


# =============================================================================
# T2: MISSING FIELDS
# =============================================================================

class TestMissingFields:
    """Tests for test_missing_fields()."""

    def test_complete_entries_no_flags(self):
        entries = [
            JournalEntry(account="Cash", posting_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_missing_account_flagged(self):
        entries = [
            JournalEntry(account="", posting_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "account" in result.flagged_entries[0].issue

    def test_missing_date_flagged(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "date" in result.flagged_entries[0].issue

    def test_zero_amount_flagged(self):
        entries = [
            JournalEntry(account="Cash", posting_date="2025-01-15", debit=0, credit=0, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "amount" in result.flagged_entries[0].issue

    def test_entry_date_sufficient(self):
        entries = [
            JournalEntry(account="Cash", entry_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 0  # entry_date counts

    def test_multiple_missing_fields(self):
        entries = [
            JournalEntry(row_number=1),  # Missing everything
        ]
        result = run_missing_fields_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert "account" in details["missing_fields"]
        assert "date" in details["missing_fields"]
        assert "amount" in details["missing_fields"]


# =============================================================================
# T3: DUPLICATE ENTRIES
# =============================================================================

class TestDuplicateEntries:
    """Tests for test_duplicate_entries()."""

    def test_no_duplicates(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="A", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=200, description="B", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_exact_duplicates_flagged(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 2  # Both entries flagged

    def test_different_amounts_not_duplicate(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=101, description="Payment", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_three_duplicates(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Pay", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Pay", row_number=2),
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Pay", row_number=3),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 3
        assert result.flagged_entries[0].details["duplicate_count"] == 3

    def test_case_insensitive_matching(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", account="Cash", debit=100, description="Payment", row_number=1),
            JournalEntry(posting_date="2025-01-15", account="CASH", debit=100, description="payment", row_number=2),
        ]
        result = run_duplicate_test(entries, JETestingConfig())
        assert result.entries_flagged == 2


# =============================================================================
# T4: ROUND DOLLAR AMOUNTS
# =============================================================================

class TestRoundAmounts:
    """Tests for test_round_amounts()."""

    def test_no_round_amounts(self):
        entries = [
            JournalEntry(debit=1234.56, row_number=1),
            JournalEntry(debit=789.01, row_number=2),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_hundred_thousand_flagged(self):
        entries = [
            JournalEntry(debit=100000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_fifty_thousand_flagged(self):
        entries = [
            JournalEntry(debit=50000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_ten_thousand_flagged(self):
        entries = [
            JournalEntry(debit=10000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_below_threshold_not_flagged(self):
        entries = [
            JournalEntry(debit=5000, row_number=1),  # Below default 10K threshold
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_custom_threshold(self):
        entries = [
            JournalEntry(debit=5000, row_number=1),
        ]
        config = JETestingConfig(round_amount_threshold=1000.0)
        result = run_round_amounts_test(entries, config)
        # 5000 is not divisible by 10000/50000/100000, so still no flag
        assert result.entries_flagged == 0

    def test_max_flags_respected(self):
        entries = [JournalEntry(debit=100000, row_number=i) for i in range(1, 100)]
        config = JETestingConfig(round_amount_max_flags=5)
        result = run_round_amounts_test(entries, config)
        assert result.entries_flagged <= 5

    def test_credit_amount_detected(self):
        entries = [
            JournalEntry(credit=200000, row_number=1),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_sorted_by_amount_descending(self):
        entries = [
            JournalEntry(debit=10000, row_number=1),
            JournalEntry(debit=100000, row_number=2),
            JournalEntry(debit=50000, row_number=3),
        ]
        result = run_round_amounts_test(entries, JETestingConfig())
        amounts = [f.entry.abs_amount for f in result.flagged_entries]
        assert amounts == sorted(amounts, reverse=True)


# =============================================================================
# T5: UNUSUAL AMOUNTS
# =============================================================================

class TestUnusualAmounts:
    """Tests for test_unusual_amounts()."""

    def test_normal_amounts_no_flags(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 11)
        ]
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_outlier_flagged(self):
        # 29 normal entries + 1 huge outlier (need enough entries so stdev stays small)
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 30)
        ]
        entries.append(JournalEntry(account="Cash", debit=100000, row_number=30))
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].entry.debit == 100000

    def test_min_entries_threshold(self):
        # Only 3 entries, below min_entries of 5
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Cash", debit=100, row_number=2),
            JournalEntry(account="Cash", debit=100000, row_number=3),
        ]
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_custom_stddev_threshold(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 10)
        ]
        entries.append(JournalEntry(account="Cash", debit=500, row_number=10))
        # With strict threshold (1 stddev), should flag more
        config = JETestingConfig(unusual_amount_stddev=1.0, unusual_amount_min_entries=3)
        result = run_unusual_amounts_test(entries, config)
        assert result.entries_flagged >= 1

    def test_per_account_grouping(self):
        # Two accounts, outlier in one — use 25 normal Cash + 1 outlier
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 26)
        ]
        entries.append(JournalEntry(account="Cash", debit=100000, row_number=26))
        entries.extend([
            JournalEntry(account="Revenue", debit=50000, row_number=i)
            for i in range(27, 34)
        ])
        result = run_unusual_amounts_test(entries, JETestingConfig())
        # Only Cash outlier should be flagged (Revenue amounts are consistent)
        flagged_accounts = {f.entry.account for f in result.flagged_entries}
        assert "Cash" in flagged_accounts

    def test_z_score_in_details(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=i)
            for i in range(1, 30)
        ]
        entries.append(JournalEntry(account="Cash", debit=100000, row_number=30))
        result = run_unusual_amounts_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        assert "z_score" in result.flagged_entries[0].details

    def test_zero_amounts_excluded(self):
        entries = [
            JournalEntry(account="Cash", debit=0, credit=0, row_number=i)
            for i in range(1, 10)
        ]
        entries.append(JournalEntry(account="Cash", debit=100, row_number=10))
        result = run_unusual_amounts_test(entries, JETestingConfig())
        # Only 1 non-zero entry, below min_entries threshold
        assert result.entries_flagged == 0


# =============================================================================
# COMPOSITE SCORING
# =============================================================================

class TestCompositeScoring:
    """Tests for calculate_composite_score() and score_to_risk_tier()."""

    def test_zero_entries_score(self):
        score = calculate_composite_score([], 0)
        assert score.score == 0.0
        assert score.risk_tier == RiskTier.LOW

    def test_clean_data_low_score(self):
        # All tests return 0 flags
        results = [
            TestResult("T1", "t1", TestTier.STRUCTURAL, 0, 100, 0.0, Severity.HIGH, ""),
            TestResult("T2", "t2", TestTier.STRUCTURAL, 0, 100, 0.0, Severity.MEDIUM, ""),
        ]
        score = calculate_composite_score(results, 100)
        assert score.score == 0.0
        assert score.risk_tier == RiskTier.LOW
        assert score.total_flagged == 0

    def test_high_flag_rate_high_score(self):
        # All entries flagged on a high-severity test
        flagged = [
            FlaggedEntry(
                entry=JournalEntry(row_number=i),
                test_name="T1", test_key="t1", test_tier=TestTier.STRUCTURAL,
                severity=Severity.HIGH, issue="Unbalanced",
            ) for i in range(1, 101)
        ]
        results = [
            TestResult("T1", "t1", TestTier.STRUCTURAL, 100, 100, 1.0, Severity.HIGH, "", flagged),
        ]
        score = calculate_composite_score(results, 100)
        assert score.score >= 80  # Should be high/critical

    def test_risk_tier_mapping(self):
        assert score_to_risk_tier(5) == RiskTier.LOW
        assert score_to_risk_tier(15) == RiskTier.ELEVATED
        assert score_to_risk_tier(30) == RiskTier.MODERATE
        assert score_to_risk_tier(60) == RiskTier.HIGH
        assert score_to_risk_tier(80) == RiskTier.CRITICAL

    def test_flags_by_severity_counted(self):
        flagged_high = [
            FlaggedEntry(
                entry=JournalEntry(row_number=1),
                test_name="T1", test_key="t1", test_tier=TestTier.STRUCTURAL,
                severity=Severity.HIGH, issue="Issue",
            )
        ]
        flagged_low = [
            FlaggedEntry(
                entry=JournalEntry(row_number=2),
                test_name="T2", test_key="t2", test_tier=TestTier.STRUCTURAL,
                severity=Severity.LOW, issue="Issue",
            )
        ]
        results = [
            TestResult("T1", "t1", TestTier.STRUCTURAL, 1, 10, 0.1, Severity.HIGH, "", flagged_high),
            TestResult("T2", "t2", TestTier.STRUCTURAL, 1, 10, 0.1, Severity.LOW, "", flagged_low),
        ]
        score = calculate_composite_score(results, 10)
        assert score.flags_by_severity["high"] == 1
        assert score.flags_by_severity["low"] == 1

    def test_top_findings_generated(self):
        flagged = [
            FlaggedEntry(
                entry=JournalEntry(row_number=1),
                test_name="T1", test_key="t1", test_tier=TestTier.STRUCTURAL,
                severity=Severity.HIGH, issue="Issue",
            )
        ]
        results = [
            TestResult("Unbalanced", "t1", TestTier.STRUCTURAL, 1, 10, 0.1, Severity.HIGH, "", flagged),
        ]
        score = calculate_composite_score(results, 10)
        assert len(score.top_findings) > 0
        assert "Unbalanced" in score.top_findings[0]

    def test_composite_score_to_dict(self):
        score = CompositeScore(
            score=25.5, risk_tier=RiskTier.MODERATE, tests_run=5,
            total_entries=100, total_flagged=10, flag_rate=0.1,
        )
        d = score.to_dict()
        assert d["score"] == 25.5
        assert d["risk_tier"] == "moderate"
        assert d["tests_run"] == 5


# =============================================================================
# TEST BATTERY
# =============================================================================

class TestBattery:
    """Tests for run_test_battery()."""

    def test_runs_all_five_tests(self):
        entries = [
            JournalEntry(entry_id="JE001", account="Cash", posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(entry_id="JE001", account="Revenue", posting_date="2025-01-15", credit=100, row_number=2),
        ]
        results = run_test_battery(entries)
        assert len(results) == 5
        keys = {r.test_key for r in results}
        assert "unbalanced_entries" in keys
        assert "missing_fields" in keys
        assert "duplicate_entries" in keys
        assert "round_amounts" in keys
        assert "unusual_amounts" in keys

    def test_custom_config_passed(self):
        entries = [JournalEntry(account="Cash", debit=100, row_number=1)]
        config = JETestingConfig(round_amount_threshold=50.0)
        results = run_test_battery(entries, config)
        # Should use custom config
        assert len(results) == 5


# =============================================================================
# FULL PIPELINE
# =============================================================================

class TestRunJETesting:
    """Tests for run_je_testing() full pipeline."""

    def test_full_pipeline_clean_data(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        result = run_je_testing(rows, cols)
        assert isinstance(result, JETestingResult)
        assert result.composite_score is not None
        assert result.composite_score.tests_run == 5
        assert result.data_quality is not None
        assert result.column_detection is not None

    def test_full_pipeline_with_config(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        config = JETestingConfig(balance_tolerance=0.001)
        result = run_je_testing(rows, cols, config=config)
        assert result.composite_score.tests_run == 5

    def test_full_pipeline_with_column_mapping(self):
        rows = [
            {"d": "2025-01-15", "a": "Cash", "dr": 100, "cr": 0},
            {"d": "2025-01-15", "a": "Revenue", "dr": 0, "cr": 100},
        ]
        mapping = {
            "date_column": "d",
            "account_column": "a",
            "debit_column": "dr",
            "credit_column": "cr",
        }
        result = run_je_testing(rows, ["d", "a", "dr", "cr"], column_mapping=mapping)
        assert result.column_detection.overall_confidence == 1.0

    def test_full_pipeline_multi_currency(self):
        rows = [
            {"Date": "2025-01-15", "Account": "Cash", "Debit": 100, "Credit": 0, "Currency": "USD"},
            {"Date": "2025-01-15", "Account": "Revenue", "Debit": 0, "Credit": 100, "Currency": "EUR"},
        ]
        result = run_je_testing(rows, ["Date", "Account", "Debit", "Credit", "Currency"])
        assert result.multi_currency_warning is not None
        assert len(result.multi_currency_warning.currencies_found) == 2

    def test_full_pipeline_to_dict(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        result = run_je_testing(rows, cols)
        d = result.to_dict()
        assert "composite_score" in d
        assert "test_results" in d
        assert "data_quality" in d
        assert "column_detection" in d
        assert isinstance(d["test_results"], list)
        assert len(d["test_results"]) == 5


# =============================================================================
# SERIALIZATION
# =============================================================================

class TestSerialization:
    """Tests for to_dict() on all major types."""

    def test_test_result_to_dict(self):
        tr = TestResult(
            test_name="Test", test_key="test", test_tier=TestTier.STRUCTURAL,
            entries_flagged=5, total_entries=100, flag_rate=0.05,
            severity=Severity.MEDIUM, description="A test",
        )
        d = tr.to_dict()
        assert d["test_name"] == "Test"
        assert d["test_tier"] == "structural"
        assert d["severity"] == "medium"
        assert d["flag_rate"] == 0.05

    def test_flagged_entry_to_dict(self):
        fe = FlaggedEntry(
            entry=JournalEntry(account="Cash", debit=100, row_number=1),
            test_name="T1", test_key="t1", test_tier=TestTier.STRUCTURAL,
            severity=Severity.HIGH, issue="Bad entry",
        )
        d = fe.to_dict()
        assert d["entry"]["account"] == "Cash"
        assert d["severity"] == "high"
        assert d["test_tier"] == "structural"

    def test_risk_tier_enum_values(self):
        assert RiskTier.LOW.value == "low"
        assert RiskTier.CRITICAL.value == "critical"

    def test_je_testing_result_no_currency(self):
        result = JETestingResult(
            composite_score=CompositeScore(
                score=0.0, risk_tier=RiskTier.LOW, tests_run=0,
                total_entries=0, total_flagged=0, flag_rate=0.0,
            ),
        )
        d = result.to_dict()
        assert d["multi_currency_warning"] is None
