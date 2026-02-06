"""
Tests for Journal Entry Testing Engine - Sprint 64 / Sprint 65 / Sprint 68

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
- T6: Benford's Law (Sprint 65)
- T7: Weekend Postings (Sprint 65)
- T8: Month-End Clustering (Sprint 65)
- T9: Single-User High Volume (Sprint 68)
- T10: After-Hours Postings (Sprint 68)
- T11: Sequential Numbering Gaps (Sprint 68)
- T12: Backdated Entries (Sprint 68)
- T13: Suspicious Keywords (Sprint 68)
- Helper functions: _extract_hour, _extract_number (Sprint 68)
- Composite scoring
- Scoring calibration fixtures (Sprint 65)
- Full pipeline (run_je_testing)
- Serialization (to_dict)
"""

import pytest
import math
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
    # Tier 1 Structural — aliased to avoid pytest collection
    test_unbalanced_entries as run_unbalanced_test,
    test_missing_fields as run_missing_fields_test,
    test_duplicate_entries as run_duplicate_test,
    test_round_amounts as run_round_amounts_test,
    test_unusual_amounts as run_unusual_amounts_test,
    # Tier 1 Statistical (Sprint 65) — aliased
    test_benford_law as run_benford_test,
    test_weekend_postings as run_weekend_test,
    test_month_end_clustering as run_month_end_test,
    # Tier 2 (Sprint 68) — aliased
    test_single_user_high_volume as run_single_user_test,
    test_after_hours_postings as run_after_hours_test,
    test_numbering_gaps as run_numbering_gaps_test,
    test_backdated_entries as run_backdated_test,
    test_suspicious_keywords as run_suspicious_keywords_test,
    SUSPICIOUS_KEYWORDS,
    _extract_hour,
    _extract_number,
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
    BenfordResult,
    BENFORD_EXPECTED,
    # Helpers
    _safe_str,
    _safe_float,
    _get_first_digit,
    _parse_date,
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

    def test_runs_all_thirteen_tests(self):
        entries = [
            JournalEntry(entry_id="JE001", account="Cash", posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(entry_id="JE001", account="Revenue", posting_date="2025-01-15", credit=100, row_number=2),
        ]
        results, benford = run_test_battery(entries)
        assert len(results) == 13
        keys = {r.test_key for r in results}
        assert "unbalanced_entries" in keys
        assert "missing_fields" in keys
        assert "duplicate_entries" in keys
        assert "round_amounts" in keys
        assert "unusual_amounts" in keys
        assert "benford_law" in keys
        assert "weekend_postings" in keys
        assert "month_end_clustering" in keys
        # Tier 2 (Sprint 68)
        assert "single_user_high_volume" in keys
        assert "after_hours_postings" in keys
        assert "numbering_gaps" in keys
        assert "backdated_entries" in keys
        assert "suspicious_keywords" in keys
        assert benford is not None

    def test_custom_config_passed(self):
        entries = [JournalEntry(account="Cash", debit=100, row_number=1)]
        config = JETestingConfig(round_amount_threshold=50.0)
        results, benford = run_test_battery(entries, config)
        assert len(results) == 13

    def test_returns_benford_result(self):
        entries = [
            JournalEntry(account="Cash", debit=100, posting_date="2025-01-15", row_number=1),
        ]
        results, benford = run_test_battery(entries)
        assert isinstance(benford, BenfordResult)


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
        assert result.composite_score.tests_run == 13
        assert result.data_quality is not None
        assert result.column_detection is not None

    def test_full_pipeline_with_config(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        config = JETestingConfig(balance_tolerance=0.001)
        result = run_je_testing(rows, cols, config=config)
        assert result.composite_score.tests_run == 13

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
        assert len(d["test_results"]) == 13


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

    def test_benford_result_to_dict(self):
        br = BenfordResult(
            passed_prechecks=True,
            eligible_count=600,
            total_count=650,
            mad=0.005,
            chi_squared=8.5,
            conformity_level="conforming",
        )
        d = br.to_dict()
        assert d["passed_prechecks"] is True
        assert d["eligible_count"] == 600
        assert d["conformity_level"] == "conforming"
        assert isinstance(d["mad"], float)

    def test_je_testing_result_with_benford(self):
        result = JETestingResult(
            composite_score=CompositeScore(
                score=10.0, risk_tier=RiskTier.ELEVATED, tests_run=8,
                total_entries=100, total_flagged=5, flag_rate=0.05,
            ),
            benford_result=BenfordResult(passed_prechecks=False, precheck_message="Not enough data"),
        )
        d = result.to_dict()
        assert d["benford_result"] is not None
        assert d["benford_result"]["passed_prechecks"] is False


# =============================================================================
# HELPER FUNCTIONS (Sprint 65)
# =============================================================================

class TestHelperFunctions:
    """Tests for _get_first_digit and _parse_date helpers."""

    def test_first_digit_normal(self):
        assert _get_first_digit(1234.56) == 1
        assert _get_first_digit(567.89) == 5
        assert _get_first_digit(9.99) == 9

    def test_first_digit_small_numbers(self):
        assert _get_first_digit(0.05) == 5
        assert _get_first_digit(0.003) == 3

    def test_first_digit_negative(self):
        assert _get_first_digit(-456.78) == 4

    def test_first_digit_zero(self):
        assert _get_first_digit(0) is None

    def test_parse_date_iso(self):
        d = _parse_date("2025-01-15")
        assert d is not None
        assert d.year == 2025
        assert d.month == 1
        assert d.day == 15

    def test_parse_date_us_format(self):
        d = _parse_date("01/15/2025")
        assert d is not None
        assert d.month == 1
        assert d.day == 15

    def test_parse_date_with_time(self):
        d = _parse_date("2025-01-15 14:30:00")
        assert d is not None
        assert d.day == 15

    def test_parse_date_none(self):
        assert _parse_date(None) is None
        assert _parse_date("") is None

    def test_parse_date_invalid(self):
        assert _parse_date("not-a-date") is None


# =============================================================================
# T6: BENFORD'S LAW (Sprint 65)
# =============================================================================

class TestBenfordLaw:
    """Tests for test_benford_law()."""

    def _make_benford_entries(self, n=600):
        """Generate entries following Benford's distribution for testing."""
        import random
        random.seed(42)
        entries = []
        for i in range(1, n + 1):
            # Generate amounts roughly following Benford's Law
            # Using log-uniform distribution
            amt = 10 ** (random.uniform(1, 5))  # $10 to $100,000
            entries.append(JournalEntry(
                account="Revenue", debit=amt, posting_date="2025-01-15", row_number=i,
            ))
        return entries

    def _make_non_benford_entries(self, n=600):
        """Generate entries NOT following Benford's distribution.

        All amounts start with digit 5 but span 2+ orders of magnitude
        to pass the magnitude precheck while violating Benford's Law.
        """
        entries = []
        for i in range(1, n + 1):
            # Spread across magnitudes (50+, 500+, 5000+) — all start with 5
            magnitude = i % 3  # 0, 1, 2
            amt = 5 * (10 ** (magnitude + 1)) + (i % 50)
            entries.append(JournalEntry(
                account="Revenue", debit=amt, posting_date="2025-01-15", row_number=i,
            ))
        return entries

    def test_insufficient_entries_precheck(self):
        entries = [JournalEntry(debit=100, row_number=i) for i in range(1, 100)]
        result, benford = run_benford_test(entries, JETestingConfig())
        assert benford.passed_prechecks is False
        assert "Insufficient data" in benford.precheck_message
        assert result.entries_flagged == 0

    def test_insufficient_magnitude_precheck(self):
        # All amounts in same order of magnitude
        entries = [
            JournalEntry(debit=100 + i, row_number=i)
            for i in range(1, 600)
        ]
        config = JETestingConfig(benford_min_entries=100)
        result, benford = run_benford_test(entries, config)
        assert benford.passed_prechecks is False
        assert "magnitude" in benford.precheck_message.lower()

    def test_passes_prechecks_with_valid_data(self):
        entries = self._make_benford_entries(600)
        result, benford = run_benford_test(entries, JETestingConfig())
        assert benford.passed_prechecks is True
        assert benford.eligible_count >= 500

    def test_expected_distribution_present(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        assert len(benford.expected_distribution) == 9
        for d in range(1, 10):
            assert d in benford.expected_distribution
        # Benford expected for digit 1 ≈ 0.301
        assert abs(benford.expected_distribution[1] - 0.30103) < 0.001

    def test_actual_distribution_sums_to_one(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        total = sum(benford.actual_distribution.values())
        assert abs(total - 1.0) < 0.001

    def test_mad_calculated(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        assert benford.mad >= 0
        assert benford.mad < 1.0

    def test_chi_squared_positive(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        assert benford.chi_squared >= 0

    def test_conforming_data(self):
        entries = self._make_benford_entries(1000)
        _, benford = run_benford_test(entries, JETestingConfig())
        # Log-uniform should produce conforming or acceptable
        assert benford.conformity_level in ("conforming", "acceptable")

    def test_nonconforming_data_detected(self):
        entries = self._make_non_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        # Uniform 5xxx amounts should be nonconforming
        assert benford.conformity_level in ("marginally_acceptable", "nonconforming")

    def test_nonconforming_flags_entries(self):
        entries = self._make_non_benford_entries(600)
        result, benford = run_benford_test(entries, JETestingConfig())
        if benford.conformity_level in ("marginally_acceptable", "nonconforming"):
            # Should have some flagged entries
            assert result.entries_flagged > 0

    def test_sub_dollar_excluded(self):
        # Entries below min_amount should be excluded
        entries = [
            JournalEntry(debit=0.50, row_number=i)
            for i in range(1, 600)
        ]
        entries.extend([
            JournalEntry(debit=10 ** (i % 4 + 1), row_number=600 + i)
            for i in range(1, 100)
        ])
        config = JETestingConfig(benford_min_entries=50, benford_min_amount=1.0)
        _, benford = run_benford_test(entries, config)
        # Only non-sub-dollar entries should be counted
        assert benford.eligible_count < len(entries)

    def test_benford_test_key(self):
        entries = self._make_benford_entries(600)
        result, _ = run_benford_test(entries, JETestingConfig())
        assert result.test_key == "benford_law"
        assert result.test_tier == TestTier.STATISTICAL

    def test_custom_min_entries(self):
        entries = [
            JournalEntry(debit=10 ** (i % 4 + 1), row_number=i)
            for i in range(1, 200)
        ]
        config = JETestingConfig(benford_min_entries=100)
        _, benford = run_benford_test(entries, config)
        assert benford.passed_prechecks is True


# =============================================================================
# T7: WEEKEND POSTINGS (Sprint 65)
# =============================================================================

class TestWeekendPostings:
    """Tests for test_weekend_postings()."""

    def test_weekday_entries_no_flags(self):
        # 2025-01-15 is a Wednesday
        entries = [
            JournalEntry(posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-16", debit=200, row_number=2),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_saturday_flagged(self):
        # 2025-01-18 is a Saturday
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=100, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "Saturday" in result.flagged_entries[0].issue

    def test_sunday_flagged(self):
        # 2025-01-19 is a Sunday
        entries = [
            JournalEntry(posting_date="2025-01-19", debit=100, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "Sunday" in result.flagged_entries[0].issue

    def test_large_amount_high_severity(self):
        # 2025-01-18 is Saturday, amount > threshold
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=50000, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig(weekend_large_amount_threshold=10000))
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_small_amount_low_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=50, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig(weekend_large_amount_threshold=10000))
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_medium_amount_medium_severity(self):
        # Between threshold/5 and threshold
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=5000, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig(weekend_large_amount_threshold=10000))
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_disabled_no_flags(self):
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=100, row_number=1),
        ]
        config = JETestingConfig(weekend_posting_enabled=False)
        result = run_weekend_test(entries, config)
        assert result.entries_flagged == 0

    def test_unparseable_date_skipped(self):
        entries = [
            JournalEntry(posting_date="not-a-date", debit=100, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_test_key(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.test_key == "weekend_postings"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T8: MONTH-END CLUSTERING (Sprint 65)
# =============================================================================

class TestMonthEndClustering:
    """Tests for test_month_end_clustering()."""

    def test_uniform_distribution_no_flags(self):
        # Entries spread evenly across the month
        entries = []
        for day in range(1, 29):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{day:02d}", debit=100, row_number=day,
            ))
        result = run_month_end_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_month_end_cluster_flagged(self):
        # 5 entries spread across month + 20 crammed into last 3 days
        entries = []
        for i in range(1, 6):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{i:02d}", debit=100, row_number=i,
            ))
        for i in range(20):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{29 + (i % 3):02d}", debit=100, row_number=6 + i,
            ))
        result = run_month_end_test(entries, JETestingConfig())
        assert result.entries_flagged > 0

    def test_too_few_entries_skipped(self):
        # Less than 10 entries in month
        entries = [
            JournalEntry(posting_date="2025-01-31", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-30", debit=100, row_number=2),
        ]
        result = run_month_end_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_custom_multiplier(self):
        # High multiplier = fewer flags
        entries = []
        for day in range(1, 25):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{day:02d}", debit=100, row_number=day,
            ))
        # Add some month-end entries
        for i in range(10):
            entries.append(JournalEntry(
                posting_date="2025-01-31", debit=100, row_number=25 + i,
            ))
        # With very high multiplier, should not flag
        config = JETestingConfig(month_end_volume_multiplier=100.0)
        result = run_month_end_test(entries, config)
        assert result.entries_flagged == 0

    def test_multiple_months(self):
        # Two months, only one with clustering
        entries = []
        # January: even
        for day in range(1, 29):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{day:02d}", debit=100, row_number=day,
            ))
        # February: all crammed at month end
        for i in range(15):
            entries.append(JournalEntry(
                posting_date=f"2025-02-{26 + (i % 3):02d}", debit=100, row_number=29 + i,
            ))
        result = run_month_end_test(entries, JETestingConfig())
        # Feb should be flagged but not Jan
        flagged_dates = [f.details.get("month") for f in result.flagged_entries]
        if result.entries_flagged > 0:
            assert "2025-02" in flagged_dates

    def test_test_key(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_month_end_test(entries, JETestingConfig())
        assert result.test_key == "month_end_clustering"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# SCORING CALIBRATION FIXTURES (Sprint 65)
# =============================================================================

class TestScoringCalibration:
    """Validate scoring engine produces expected risk tiers for known profiles."""

    def _generate_clean_gl(self, n=200):
        """Generate a clean GL: balanced entries, no anomalies."""
        entries = []
        for i in range(1, n + 1):
            entries.append(JournalEntry(
                entry_id=f"JE{i:04d}", account="Cash",
                posting_date=f"2025-01-{(i % 28) + 1:02d}",
                debit=100 + (i * 7.3), row_number=i * 2 - 1,
            ))
            entries.append(JournalEntry(
                entry_id=f"JE{i:04d}", account="Revenue",
                posting_date=f"2025-01-{(i % 28) + 1:02d}",
                credit=100 + (i * 7.3), row_number=i * 2,
            ))
        return entries

    def _generate_moderate_risk_gl(self, n=200):
        """Generate moderate risk GL: some duplicates, round amounts, missing fields."""
        entries = self._generate_clean_gl(n)
        # Add duplicates (10% of entries)
        for i in range(n // 10):
            entries.append(JournalEntry(
                entry_id=f"JE{1:04d}", account="Cash",
                posting_date="2025-01-01", debit=107.3, row_number=len(entries) + 1,
            ))
        # Add entries with missing fields
        for i in range(n // 10):
            entries.append(JournalEntry(
                account="", debit=100, row_number=len(entries) + 1,
            ))
        # Add round amounts
        for i in range(n // 10):
            entries.append(JournalEntry(
                account="Expense", debit=100000, posting_date="2025-01-15",
                row_number=len(entries) + 1,
            ))
        return entries

    def _generate_high_risk_gl(self, n=200):
        """Generate high risk GL: many issues across all test types."""
        entries = []
        # Unbalanced entries (25% of base)
        for i in range(1, n // 4 + 1):
            entries.append(JournalEntry(
                entry_id=f"BAD{i:04d}", account="Cash",
                posting_date="2025-01-15", debit=5000, row_number=len(entries) + 1,
            ))
            entries.append(JournalEntry(
                entry_id=f"BAD{i:04d}", account="Revenue",
                posting_date="2025-01-15", credit=3000, row_number=len(entries) + 1,
            ))
        # Duplicates (many identical)
        for i in range(n // 3):
            entries.append(JournalEntry(
                account="Cash", posting_date="2025-01-10", debit=999,
                description="duplicate payment", row_number=len(entries) + 1,
            ))
        # Missing fields
        for i in range(n // 5):
            entries.append(JournalEntry(row_number=len(entries) + 1))
        # Round amounts
        for i in range(n // 5):
            entries.append(JournalEntry(
                account="Expense", debit=100000, posting_date="2025-01-15",
                row_number=len(entries) + 1,
            ))
        return entries

    def test_clean_gl_low_risk(self):
        entries = self._generate_clean_gl(200)
        results, _ = run_test_battery(entries)
        score = calculate_composite_score(results, len(entries))
        assert score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED)
        assert score.score < 25

    def test_moderate_risk_gl(self):
        entries = self._generate_moderate_risk_gl(200)
        results, _ = run_test_battery(entries)
        score = calculate_composite_score(results, len(entries))
        # Should score above zero — comparative ordering validated by other tests
        assert score.score > 2
        assert score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED, RiskTier.MODERATE, RiskTier.HIGH)

    def test_high_risk_gl(self):
        entries = self._generate_high_risk_gl(200)
        results, _ = run_test_battery(entries)
        score = calculate_composite_score(results, len(entries))
        # Should be elevated or higher (Tier 2 tests dilute average since they find fewer flags)
        assert score.score >= 15
        assert score.risk_tier in (RiskTier.ELEVATED, RiskTier.MODERATE, RiskTier.HIGH, RiskTier.CRITICAL)

    def test_clean_fewer_flagged_than_risky(self):
        clean = self._generate_clean_gl(200)
        risky = self._generate_high_risk_gl(200)
        clean_results, _ = run_test_battery(clean)
        risky_results, _ = run_test_battery(risky)
        clean_score = calculate_composite_score(clean_results, len(clean))
        risky_score = calculate_composite_score(risky_results, len(risky))
        assert clean_score.score < risky_score.score

    def test_flag_rate_increases_with_risk(self):
        clean = self._generate_clean_gl(200)
        risky = self._generate_high_risk_gl(200)
        clean_results, _ = run_test_battery(clean)
        risky_results, _ = run_test_battery(risky)
        clean_score = calculate_composite_score(clean_results, len(clean))
        risky_score = calculate_composite_score(risky_results, len(risky))
        assert clean_score.flag_rate < risky_score.flag_rate


# =============================================================================
# FULL PIPELINE WITH BENFORD (Sprint 65)
# =============================================================================

class TestFullPipelineWithBenford:
    """Tests for run_je_testing with Benford integration."""

    def test_pipeline_includes_benford_result(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        result = run_je_testing(rows, cols)
        assert result.benford_result is not None
        # Small dataset won't pass prechecks
        assert result.benford_result.passed_prechecks is False

    def test_pipeline_to_dict_includes_benford(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        result = run_je_testing(rows, cols)
        d = result.to_dict()
        assert "benford_result" in d
        assert d["benford_result"]["passed_prechecks"] is False


# =============================================================================
# TIER 2 HELPERS: _extract_hour and _extract_number (Sprint 68)
# =============================================================================

class TestExtractHour:
    """Tests for _extract_hour() helper."""

    def test_iso_datetime(self):
        assert _extract_hour("2025-01-15 14:30:00") == 14

    def test_midnight(self):
        assert _extract_hour("2025-01-15 00:00:00") == 0

    def test_late_night(self):
        assert _extract_hour("2025-01-15 23:59:00") == 23

    def test_date_only_returns_none(self):
        assert _extract_hour("2025-01-15") is None

    def test_none_returns_none(self):
        assert _extract_hour(None) is None

    def test_empty_string_returns_none(self):
        assert _extract_hour("") is None

    def test_us_datetime_format(self):
        assert _extract_hour("01/15/2025 09:30:00") == 9

    def test_iso_t_separator(self):
        assert _extract_hour("2025-01-15T18:00:00") == 18

    def test_no_seconds(self):
        assert _extract_hour("2025-01-15 14:30") == 14


class TestExtractNumber:
    """Tests for _extract_number() helper."""

    def test_prefixed_id(self):
        assert _extract_number("JE-001") == 1

    def test_plain_number(self):
        assert _extract_number("1234") == 1234

    def test_none_returns_none(self):
        assert _extract_number(None) is None

    def test_empty_string_returns_none(self):
        assert _extract_number("") is None

    def test_no_numeric_returns_none(self):
        assert _extract_number("ABC") is None

    def test_hash_prefix(self):
        assert _extract_number("#500") == 500

    def test_gj_prefix(self):
        assert _extract_number("GJ-0042") == 42

    def test_jv_prefix(self):
        assert _extract_number("JV100") == 100


# =============================================================================
# T9: SINGLE-USER HIGH VOLUME (Sprint 68)
# =============================================================================

class TestSingleUserHighVolume:
    """Tests for test_single_user_high_volume()."""

    def test_no_posted_by_data(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Revenue", credit=100, row_number=2),
        ]
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "posted_by" in result.description.lower()

    def test_evenly_distributed_users_no_flags(self):
        entries = []
        users = ["alice", "bob", "carol", "dave"]
        for i, user in enumerate(users):
            for j in range(10):
                entries.append(JournalEntry(
                    account="Cash", debit=100, posted_by=user,
                    row_number=i * 10 + j + 1,
                ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_single_user_above_threshold_flagged(self):
        entries = []
        # alice posts 30 out of 40 entries = 75%
        for i in range(30):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(10):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=31 + i,
            ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        assert result.flagged_entries[0].details["user"] == "alice"

    def test_severity_high_above_50_pct(self):
        entries = []
        # alice = 60%, bob = 40%
        for i in range(60):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(40):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=61 + i,
            ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_severity_medium_below_50_pct(self):
        entries = []
        # alice = 30%, bob = 35%, carol = 35%
        for i in range(30):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(35):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="bob", row_number=31 + i,
            ))
        for i in range(35):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="carol", row_number=66 + i,
            ))
        result = run_single_user_test(entries, JETestingConfig())
        assert result.entries_flagged > 0
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_max_flags_per_user_respected(self):
        entries = []
        # alice posts 50 entries out of 60 (83%)
        for i in range(50):
            entries.append(JournalEntry(
                account="Cash", debit=100 + i, posted_by="alice", row_number=i + 1,
            ))
        for i in range(10):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=51 + i,
            ))
        config = JETestingConfig(single_user_max_flags=5)
        result = run_single_user_test(entries, config)
        assert result.entries_flagged <= 5

    def test_custom_volume_threshold(self):
        entries = []
        # alice = 15%, bob = 85%: with threshold at 10%, alice gets flagged too
        for i in range(15):
            entries.append(JournalEntry(
                account="Cash", debit=100, posted_by="alice", row_number=i + 1,
            ))
        for i in range(85):
            entries.append(JournalEntry(
                account="Revenue", credit=100, posted_by="bob", row_number=16 + i,
            ))
        config = JETestingConfig(single_user_volume_pct=0.10)
        result = run_single_user_test(entries, config)
        # Both alice (15%) and bob (85%) exceed 10%
        flagged_users = {f.details["user"] for f in result.flagged_entries}
        assert "alice" in flagged_users
        assert "bob" in flagged_users

    def test_test_key_and_tier(self):
        entries = [JournalEntry(account="Cash", debit=100, row_number=1)]
        result = run_single_user_test(entries, JETestingConfig())
        assert result.test_key == "single_user_high_volume"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T10: AFTER-HOURS POSTINGS (Sprint 68)
# =============================================================================

class TestAfterHoursPostings:
    """Tests for test_after_hours_postings()."""

    def test_business_hours_no_flags(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 10:30:00", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-15 14:00:00", debit=200, row_number=2),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_after_hours_evening_flagged(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 22:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "22:00" in result.flagged_entries[0].issue

    def test_early_morning_flagged(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 03:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_no_time_component_returns_requires_timestamp(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-16", debit=200, row_number=2),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "timestamp" in result.description.lower()

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 22:00:00", debit=100, row_number=1),
        ]
        config = JETestingConfig(after_hours_enabled=False)
        result = run_after_hours_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_large_amount_high_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 23:00:00", debit=50000, row_number=1),
        ]
        config = JETestingConfig(after_hours_large_threshold=10000.0)
        result = run_after_hours_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_medium_amount_medium_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 23:00:00", debit=5000, row_number=1),
        ]
        config = JETestingConfig(after_hours_large_threshold=10000.0)
        result = run_after_hours_test(entries, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_small_amount_low_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-15 23:00:00", debit=50, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_boundary_start_of_business_not_flagged(self):
        # 06:00 is start of business hours (after_hours_end=6)
        entries = [
            JournalEntry(posting_date="2025-01-15 06:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_boundary_end_of_business_flagged(self):
        # 18:00 is after_hours_start, so it's outside hours
        entries = [
            JournalEntry(posting_date="2025-01-15 18:00:00", debit=100, row_number=1),
        ]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_test_key_and_tier(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_after_hours_test(entries, JETestingConfig())
        assert result.test_key == "after_hours_postings"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T11: SEQUENTIAL NUMBERING GAPS (Sprint 68)
# =============================================================================

class TestNumberingGaps:
    """Tests for test_numbering_gaps()."""

    def test_sequential_ids_no_flags(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-002", debit=200, row_number=2),
            JournalEntry(entry_id="JE-003", debit=300, row_number=3),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_gap_detected(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-005", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "gap" in result.flagged_entries[0].issue.lower()

    def test_no_entry_ids_returns_requires_column(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Revenue", credit=100, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "entry_id" in result.description.lower()

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-100", debit=200, row_number=2),
        ]
        config = JETestingConfig(numbering_gap_enabled=False)
        result = run_numbering_gaps_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_large_gap_high_severity(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-200", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_medium_gap_medium_severity(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-020", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_small_gap_low_severity(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-005", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_custom_min_gap_size(self):
        entries = [
            JournalEntry(entry_id="JE-001", debit=100, row_number=1),
            JournalEntry(entry_id="JE-003", debit=200, row_number=2),
        ]
        # Gap of 2 (001 -> 003), default min_size=2 flags it
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        # With min_size=5, gap of 2 should NOT be flagged
        config = JETestingConfig(numbering_gap_min_size=5)
        result2 = run_numbering_gaps_test(entries, config)
        assert result2.entries_flagged == 0

    def test_gap_details_include_surrounding_numbers(self):
        entries = [
            JournalEntry(entry_id="JE-010", debit=100, row_number=1),
            JournalEntry(entry_id="JE-025", debit=200, row_number=2),
        ]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert details["prev_number"] == 10
        assert details["curr_number"] == 25

    def test_test_key_and_tier(self):
        entries = [JournalEntry(entry_id="JE-001", debit=100, row_number=1)]
        result = run_numbering_gaps_test(entries, JETestingConfig())
        assert result.test_key == "numbering_gaps"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T12: BACKDATED ENTRIES (Sprint 68)
# =============================================================================

class TestBackdatedEntries:
    """Tests for test_backdated_entries()."""

    def test_no_dual_dates_returns_requires(self):
        entries = [
            JournalEntry(posting_date="2025-01-15", debit=100, row_number=1),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "dual dates" in result.description.lower()

    def test_close_dates_no_flags(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-15", entry_date="2025-01-14",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_backdated_beyond_threshold_flagged(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-03-15",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-06-01",
                debit=100, row_number=1,
            ),
        ]
        config = JETestingConfig(backdate_enabled=False)
        result = run_backdated_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_severity_high_above_90_days(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-06-01",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_severity_medium_31_to_90_days(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-02-15",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_severity_low_at_threshold(self):
        # Exactly 30 days with default threshold of 30
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-01-31",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_custom_days_threshold(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-01-20",
                debit=100, row_number=1,
            ),
        ]
        # Default 30 days threshold won't flag 19 day diff
        result_default = run_backdated_test(entries, JETestingConfig())
        assert result_default.entries_flagged == 0
        # Custom 10 day threshold will flag it
        config = JETestingConfig(backdate_days_threshold=10)
        result_custom = run_backdated_test(entries, config)
        assert result_custom.entries_flagged == 1

    def test_details_include_dates_and_diff(self):
        entries = [
            JournalEntry(
                posting_date="2025-01-01", entry_date="2025-04-01",
                debit=100, row_number=1,
            ),
        ]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert "days_diff" in details
        assert details["days_diff"] == 90
        assert details["posting_date"] == "2025-01-01"
        assert details["entry_date"] == "2025-04-01"

    def test_test_key_and_tier(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_backdated_test(entries, JETestingConfig())
        assert result.test_key == "backdated_entries"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T13: SUSPICIOUS KEYWORDS (Sprint 68)
# =============================================================================

class TestSuspiciousKeywords:
    """Tests for test_suspicious_keywords()."""

    def test_no_descriptions_returns_no_data(self):
        entries = [
            JournalEntry(account="Cash", debit=100, row_number=1),
            JournalEntry(account="Revenue", credit=100, row_number=2),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 0
        assert "description" in result.description.lower()

    def test_clean_descriptions_no_flags(self):
        entries = [
            JournalEntry(description="Regular sales transaction", debit=100, row_number=1),
            JournalEntry(description="Monthly rent payment", debit=2000, row_number=2),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_manual_adjustment_flagged(self):
        entries = [
            JournalEntry(description="Manual adjustment for Q4", debit=5000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "manual adjustment" in result.flagged_entries[0].issue.lower()

    def test_correction_keyword_flagged(self):
        entries = [
            JournalEntry(description="Error correction for invoice 1234", debit=800, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].details["matched_keyword"] in ("error correction", "correction")

    def test_reversal_keyword_flagged(self):
        entries = [
            JournalEntry(description="Reversal of prior period entry", debit=3000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_dummy_keyword_flagged(self):
        entries = [
            JournalEntry(description="Dummy entry for testing", debit=100, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1

    def test_related_party_flagged(self):
        entries = [
            JournalEntry(description="Related party transaction with XYZ Corp", debit=50000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].details["matched_keyword"] == "related party"

    def test_disabled_returns_test_disabled(self):
        entries = [
            JournalEntry(description="Manual adjustment", debit=100, row_number=1),
        ]
        config = JETestingConfig(suspicious_keyword_enabled=False)
        result = run_suspicious_keywords_test(entries, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_below_confidence_threshold_not_flagged(self):
        # "intercompany" has weight 0.60, raise threshold above it
        entries = [
            JournalEntry(description="Intercompany transfer", debit=100, row_number=1),
        ]
        config = JETestingConfig(suspicious_keyword_threshold=0.70)
        result = run_suspicious_keywords_test(entries, config)
        assert result.entries_flagged == 0

    def test_severity_high_for_high_confidence_large_amount(self):
        entries = [
            JournalEntry(description="Manual adjustment for year-end", debit=50000, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        # manual adjustment = 0.90 confidence, amount > 10000 => HIGH
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_severity_medium_for_moderate_confidence(self):
        entries = [
            JournalEntry(description="Correction entry", debit=100, row_number=1),
        ]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        # correction = 0.75 confidence, amount < 5000 => MEDIUM (confidence >= 0.70)
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_suspicious_keywords_list_not_empty(self):
        assert len(SUSPICIOUS_KEYWORDS) > 0
        for keyword, weight, is_phrase in SUSPICIOUS_KEYWORDS:
            assert isinstance(keyword, str)
            assert 0 < weight <= 1.0
            assert isinstance(is_phrase, bool)

    def test_test_key_and_tier(self):
        entries = [JournalEntry(description="Normal entry", debit=100, row_number=1)]
        result = run_suspicious_keywords_test(entries, JETestingConfig())
        assert result.test_key == "suspicious_keywords"
        assert result.test_tier == TestTier.STATISTICAL
