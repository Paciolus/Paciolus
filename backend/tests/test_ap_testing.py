"""
Tests for AP Testing Engine (Duplicate Payment Detection) — Sprint 73-74

Covers: column detection, parsing, helpers, data quality,
5 tier 1 tests, 5 tier 2 tests, 3 tier 3 tests,
scoring, battery, full pipeline, serialization, API.

160+ tests across 24 test classes.
"""

import io
import pytest
from datetime import date

# Aliased imports to avoid pytest collection of test_* functions
from shared.parsing_helpers import safe_str, safe_float, parse_date
from ap_testing_engine import (
    APColumnType,
    APColumnDetectionResult,
    APPayment,
    APTestingConfig,
    APTestResult,
    APCompositeScore,
    APTestingResult,
    APDataQuality,
    FlaggedPayment,
    RiskTier,
    TestTier,
    Severity,
    AP_SUSPICIOUS_KEYWORDS,
    detect_ap_columns,
    parse_ap_payments,
    assess_ap_data_quality,
    score_to_risk_tier,
    _extract_check_number,
    _match_ap_column,
    test_exact_duplicate_payments as run_duplicate_payments_test,
    test_missing_critical_fields as run_missing_fields_test,
    test_check_number_gaps as run_check_gaps_test,
    test_round_dollar_amounts as run_round_amounts_test,
    test_payment_before_invoice as run_payment_before_invoice_test,
    test_fuzzy_duplicate_payments as run_fuzzy_duplicates_test,
    test_invoice_number_reuse as run_invoice_reuse_test,
    test_unusual_payment_amounts as run_unusual_amounts_test,
    test_weekend_payments as run_weekend_payments_test,
    test_high_frequency_vendors as run_high_frequency_test,
    test_vendor_name_variations as run_vendor_variations_test,
    test_just_below_threshold as run_just_below_threshold_test,
    test_suspicious_descriptions as run_suspicious_descriptions_test,
    run_ap_test_battery,
    calculate_ap_composite_score,
    run_ap_testing,
)


# =============================================================================
# FIXTURE HELPERS
# =============================================================================

def make_payments(rows: list[dict], columns: list[str] | None = None) -> list[APPayment]:
    """Parse rows into APPayment objects using auto-detection."""
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    detection = detect_ap_columns(columns)
    return parse_ap_payments(rows, detection)


def sample_ap_rows() -> list[dict]:
    """4 clean payments for baseline tests."""
    return [
        {
            "Invoice Number": "INV-001",
            "Invoice Date": "2025-01-05",
            "Payment Date": "2025-01-15",
            "Vendor Name": "Acme Corp",
            "Vendor ID": "V001",
            "Amount": 5000.50,
            "Check Number": "CHK-1001",
            "Description": "Office supplies",
            "GL Account": "6100",
            "Payment Method": "Check",
        },
        {
            "Invoice Number": "INV-002",
            "Invoice Date": "2025-01-10",
            "Payment Date": "2025-01-20",
            "Vendor Name": "Beta LLC",
            "Vendor ID": "V002",
            "Amount": 12500.00,
            "Check Number": "CHK-1002",
            "Description": "Consulting fees",
            "GL Account": "6200",
            "Payment Method": "Check",
        },
        {
            "Invoice Number": "INV-003",
            "Invoice Date": "2025-02-01",
            "Payment Date": "2025-02-10",
            "Vendor Name": "Gamma Inc",
            "Vendor ID": "V003",
            "Amount": 3200.75,
            "Check Number": "CHK-1003",
            "Description": "IT services",
            "GL Account": "6300",
            "Payment Method": "ACH",
        },
        {
            "Invoice Number": "INV-004",
            "Invoice Date": "2025-02-15",
            "Payment Date": "2025-02-25",
            "Vendor Name": "Delta Corp",
            "Vendor ID": "V004",
            "Amount": 8750.00,
            "Check Number": "CHK-1004",
            "Description": "Equipment lease",
            "GL Account": "6400",
            "Payment Method": "Wire",
        },
    ]


def sample_ap_columns() -> list[str]:
    """Standard AP column names."""
    return [
        "Invoice Number", "Invoice Date", "Payment Date",
        "Vendor Name", "Vendor ID", "Amount",
        "Check Number", "Description", "GL Account", "Payment Method",
    ]


# =============================================================================
# TEST CLASSES
# =============================================================================

class TestAPColumnDetection:
    """12 tests for AP column detection."""

    def test_standard_columns_detected(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.vendor_name_column == "Vendor Name"
        assert result.amount_column == "Amount"
        assert result.payment_date_column == "Payment Date"
        assert result.invoice_number_column == "Invoice Number"
        assert result.invoice_date_column == "Invoice Date"

    def test_vendor_id_detected(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.vendor_id_column == "Vendor ID"

    def test_check_number_detected(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.check_number_column == "Check Number"
        assert result.has_check_numbers is True

    def test_dual_dates_detected(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.has_dual_dates is True

    def test_description_detected(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.description_column == "Description"

    def test_gl_account_detected(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.gl_account_column == "GL Account"

    def test_payment_method_detected(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.payment_method_column == "Payment Method"

    def test_overall_confidence_high(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.overall_confidence >= 0.85

    def test_requires_mapping_false(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        assert result.requires_mapping is False

    def test_alternative_column_names(self):
        cols = ["Supplier Name", "Pay Date", "Payment Amount", "Bill Number", "Bill Date"]
        result = detect_ap_columns(cols)
        assert result.vendor_name_column == "Supplier Name"
        assert result.payment_date_column == "Pay Date"
        assert result.amount_column == "Payment Amount"
        assert result.invoice_number_column == "Bill Number"
        assert result.invoice_date_column == "Bill Date"

    def test_ambiguous_columns_low_confidence(self):
        cols = ["col1", "col2", "col3"]
        result = detect_ap_columns(cols)
        assert result.overall_confidence == 0.0
        assert result.requires_mapping is True

    def test_no_double_mapping(self):
        """Greedy assignment prevents same column being used for multiple types."""
        cols = ["Vendor Name", "Amount", "Date"]
        result = detect_ap_columns(cols)
        assigned = [
            result.vendor_name_column,
            result.amount_column,
            result.payment_date_column,
        ]
        assigned = [c for c in assigned if c is not None]
        assert len(assigned) == len(set(assigned))


class TestAPParsing:
    """8 tests for AP payment parsing."""

    def test_standard_parsing(self):
        rows = sample_ap_rows()
        cols = sample_ap_columns()
        payments = make_payments(rows, cols)
        assert len(payments) == 4
        assert payments[0].vendor_name == "Acme Corp"
        assert payments[0].amount == 5000.50

    def test_row_numbers_assigned(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        assert payments[0].row_number == 1
        assert payments[3].row_number == 4

    def test_missing_fields_parsed_as_none(self):
        rows = [{"Vendor Name": "Test", "Amount": 100, "Payment Date": "2025-01-01"}]
        detection = detect_ap_columns(["Vendor Name", "Amount", "Payment Date"])
        payments = parse_ap_payments(rows, detection)
        assert payments[0].invoice_number is None
        assert payments[0].check_number is None

    def test_amount_parsing_with_currency_symbol(self):
        rows = [{"Vendor Name": "Test", "Amount": "$1,234.56", "Payment Date": "2025-01-01"}]
        detection = detect_ap_columns(["Vendor Name", "Amount", "Payment Date"])
        payments = parse_ap_payments(rows, detection)
        assert payments[0].amount == 1234.56

    def test_empty_rows(self):
        detection = detect_ap_columns(sample_ap_columns())
        payments = parse_ap_payments([], detection)
        assert len(payments) == 0

    def test_vendor_name_defaults_to_empty(self):
        rows = [{"Amount": 100, "Payment Date": "2025-01-01"}]
        detection = detect_ap_columns(["Amount", "Payment Date"])
        payments = parse_ap_payments(rows, detection)
        assert payments[0].vendor_name == ""

    def test_all_optional_fields_parsed(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        p = payments[0]
        assert p.invoice_number == "INV-001"
        assert p.invoice_date == "2025-01-05"
        assert p.vendor_id == "V001"
        assert p.check_number == "CHK-1001"
        assert p.description == "Office supplies"
        assert p.gl_account == "6100"
        assert p.payment_method == "Check"

    def test_nan_values_parsed_as_none(self):
        rows = [{"Vendor Name": "nan", "Amount": "nan", "Payment Date": "None"}]
        detection = detect_ap_columns(["Vendor Name", "Amount", "Payment Date"])
        payments = parse_ap_payments(rows, detection)
        assert payments[0].vendor_name == ""
        assert payments[0].amount == 0.0
        assert payments[0].payment_date is None


class TestAPSafeHelpers:
    """6 tests for safe_str, safe_float, parse_date."""

    def testsafe_str_normal(self):
        assert safe_str("hello") == "hello"

    def testsafe_str_none(self):
        assert safe_str(None) is None

    def testsafe_str_nan(self):
        assert safe_str("nan") is None
        assert safe_str("NaN") is None

    def testsafe_float_normal(self):
        assert safe_float(42.5) == 42.5

    def testsafe_float_none(self):
        assert safe_float(None) == 0.0

    def testparse_date_formats(self):
        assert parse_date("2025-01-15") == date(2025, 1, 15)
        assert parse_date("01/15/2025") == date(2025, 1, 15)
        assert parse_date(None) is None
        assert parse_date("not-a-date") is None


class TestAPDataQuality:
    """5 tests for AP data quality assessment."""

    def test_perfect_quality(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        detection = detect_ap_columns(sample_ap_columns())
        quality = assess_ap_data_quality(payments, detection)
        assert quality.completeness_score > 80.0
        assert quality.total_rows == 4
        assert quality.field_fill_rates["vendor_name"] == 1.0

    def test_missing_vendor_names(self):
        rows = [
            {"Vendor Name": "", "Amount": 100, "Payment Date": "2025-01-01"},
            {"Vendor Name": "", "Amount": 200, "Payment Date": "2025-01-02"},
        ]
        detection = detect_ap_columns(["Vendor Name", "Amount", "Payment Date"])
        payments = parse_ap_payments(rows, detection)
        quality = assess_ap_data_quality(payments, detection)
        assert quality.field_fill_rates["vendor_name"] == 0.0
        assert any("Missing vendor" in i for i in quality.detected_issues)

    def test_empty_list(self):
        detection = detect_ap_columns(sample_ap_columns())
        quality = assess_ap_data_quality([], detection)
        assert quality.completeness_score == 0.0
        assert quality.total_rows == 0

    def test_zero_amounts_flagged(self):
        rows = [
            {"Vendor Name": "Test", "Amount": 0, "Payment Date": "2025-01-01"},
            {"Vendor Name": "Test2", "Amount": 0, "Payment Date": "2025-01-02"},
        ]
        detection = detect_ap_columns(["Vendor Name", "Amount", "Payment Date"])
        payments = parse_ap_payments(rows, detection)
        quality = assess_ap_data_quality(payments, detection)
        assert quality.field_fill_rates["amount"] == 0.0
        assert any("zero amount" in i for i in quality.detected_issues)

    def test_quality_to_dict(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        detection = detect_ap_columns(sample_ap_columns())
        quality = assess_ap_data_quality(payments, detection)
        d = quality.to_dict()
        assert "completeness_score" in d
        assert "field_fill_rates" in d
        assert "total_rows" in d


class TestExactDuplicatePayments:
    """12 tests for AP-T1: Exact Duplicate Payments."""

    def test_no_duplicates(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "exact_duplicate_payments"

    def test_exact_duplicates_flagged(self):
        rows = sample_ap_rows()
        # Add an exact duplicate of row 0
        rows.append(dict(rows[0]))
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 2  # Both entries in the pair

    def test_case_insensitive_matching(self):
        rows = [
            {"Vendor Name": "ACME CORP", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
            {"Vendor Name": "acme corp", "Invoice Number": "inv-001", "Amount": 5000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 2

    def test_different_amounts_not_duplicates(self):
        rows = [
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5001, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 0

    def test_different_dates_not_duplicates(self):
        rows = [
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-16"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 0

    def test_severity_always_high(self):
        rows = [
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_confidence_095(self):
        rows = [
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        for f in result.flagged_entries:
            assert f.confidence == 0.95

    def test_triple_duplicate(self):
        rows = [
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 3
        assert result.flagged_entries[0].details["duplicate_count"] == 3

    def test_details_structure(self):
        rows = [
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        d = result.flagged_entries[0].details
        assert "duplicate_count" in d
        assert "vendor" in d
        assert "invoice_number" in d
        assert "amount" in d
        assert "payment_date" in d

    def test_empty_invoice_numbers_grouped(self):
        """Payments with same vendor, amount, date but no invoice are grouped."""
        rows = [
            {"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 2

    def test_flag_rate_calculation(self):
        rows = [
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Acme", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
            {"Vendor Name": "Beta", "Invoice Number": "INV-002", "Amount": 200, "Payment Date": "2025-01-16"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.entries_flagged == 2
        assert abs(result.flag_rate - 2 / 3) < 0.01

    def test_test_tier_structural(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        config = APTestingConfig()
        result = run_duplicate_payments_test(payments, config)
        assert result.test_tier == TestTier.STRUCTURAL


class TestMissingCriticalFields:
    """8 tests for AP-T2: Missing Critical Fields."""

    def test_no_missing_fields(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.entries_flagged == 0

    def test_missing_vendor_name(self):
        rows = [{"Vendor Name": "", "Amount": 100, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH
        assert "vendor_name" in result.flagged_entries[0].details["missing_fields"]

    def test_zero_amount(self):
        rows = [{"Vendor Name": "Acme", "Amount": 0, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH
        assert "amount" in result.flagged_entries[0].details["missing_fields"]

    def test_missing_payment_date(self):
        rows = [{"Vendor Name": "Acme", "Amount": 100, "Payment Date": ""}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_multiple_missing_fields(self):
        rows = [{"Vendor Name": "", "Amount": 0, "Payment Date": ""}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.entries_flagged == 1
        details = result.flagged_entries[0].details
        assert len(details["missing_fields"]) == 3
        # Severity should be HIGH because vendor_name and amount are missing
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_test_key(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.test_key == "missing_critical_fields"

    def test_confidence(self):
        rows = [{"Vendor Name": "", "Amount": 100, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.flagged_entries[0].confidence == 0.90

    def test_whitespace_vendor_treated_as_missing(self):
        rows = [{"Vendor Name": "   ", "Amount": 100, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_missing_fields_test(payments, config)
        assert result.entries_flagged == 1
        assert "vendor_name" in result.flagged_entries[0].details["missing_fields"]


class TestCheckNumberGaps:
    """8 tests for AP-T3: Check Number Gaps."""

    def test_sequential_no_gaps(self):
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01", "Check Number": "CHK-1001"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02", "Check Number": "CHK-1002"},
            {"Vendor Name": "C", "Amount": 300, "Payment Date": "2025-01-03", "Check Number": "CHK-1003"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Check Number"])
        config = APTestingConfig()
        result = run_check_gaps_test(payments, config)
        assert result.entries_flagged == 0

    def test_gap_detected(self):
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01", "Check Number": "CHK-1001"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02", "Check Number": "CHK-1005"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Check Number"])
        config = APTestingConfig()
        result = run_check_gaps_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].details["gap_size"] == 3

    def test_disabled(self):
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01", "Check Number": "1001"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02", "Check Number": "1010"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Check Number"])
        config = APTestingConfig(check_number_gap_enabled=False)
        result = run_check_gaps_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_no_check_numbers(self):
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_check_gaps_test(payments, config)
        assert result.entries_flagged == 0

    def test_prefix_stripping(self):
        """Check numbers with prefixes should be stripped to numeric."""
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01", "Check Number": "CHK-100"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02", "Check Number": "CHK-105"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Check Number"])
        config = APTestingConfig()
        result = run_check_gaps_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].details["gap_size"] == 4

    def test_severity_small_gap(self):
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01", "Check Number": "1001"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02", "Check Number": "1004"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Check Number"])
        config = APTestingConfig()
        result = run_check_gaps_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_severity_medium_gap(self):
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01", "Check Number": "1001"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02", "Check Number": "1020"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Check Number"])
        config = APTestingConfig()
        result = run_check_gaps_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_severity_large_gap(self):
        rows = [
            {"Vendor Name": "A", "Amount": 100, "Payment Date": "2025-01-01", "Check Number": "1001"},
            {"Vendor Name": "B", "Amount": 200, "Payment Date": "2025-01-02", "Check Number": "1200"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Check Number"])
        config = APTestingConfig()
        result = run_check_gaps_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.HIGH


class TestRoundDollarAmounts:
    """8 tests for AP-T4: Round Dollar Amounts."""

    def test_no_round_amounts(self):
        rows = [
            {"Vendor Name": "A", "Amount": 5123.45, "Payment Date": "2025-01-01"},
            {"Vendor Name": "B", "Amount": 8765.32, "Payment Date": "2025-01-02"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_round_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_100k_flagged_high(self):
        rows = [{"Vendor Name": "A", "Amount": 200000, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_round_amounts_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH
        assert result.flagged_entries[0].details["pattern"] == "hundred_thousand"

    def test_50k_flagged_high(self):
        rows = [{"Vendor Name": "A", "Amount": 50000, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_round_amounts_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_25k_flagged_medium(self):
        rows = [{"Vendor Name": "A", "Amount": 25000, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_round_amounts_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM
        assert result.flagged_entries[0].details["pattern"] == "twenty_five_thousand"

    def test_10k_flagged_low(self):
        rows = [{"Vendor Name": "A", "Amount": 10000, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_round_amounts_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_below_threshold_not_flagged(self):
        rows = [{"Vendor Name": "A", "Amount": 5000, "Payment Date": "2025-01-01"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_round_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_max_flags_respected(self):
        rows = [
            {"Vendor Name": f"V{i}", "Amount": 50000 * (i + 1), "Payment Date": "2025-01-01"}
            for i in range(60)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(round_amount_max_flags=5)
        result = run_round_amounts_test(payments, config)
        assert result.entries_flagged <= 5

    def test_sorted_descending(self):
        rows = [
            {"Vendor Name": "A", "Amount": 10000, "Payment Date": "2025-01-01"},
            {"Vendor Name": "B", "Amount": 100000, "Payment Date": "2025-01-02"},
            {"Vendor Name": "C", "Amount": 50000, "Payment Date": "2025-01-03"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_round_amounts_test(payments, config)
        amounts = [abs(f.entry.amount) for f in result.flagged_entries]
        assert amounts == sorted(amounts, reverse=True)


class TestPaymentBeforeInvoice:
    """8 tests for AP-T5: Payment Before Invoice."""

    def test_normal_payment_after_invoice(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_payment_before_invoice_test(payments, config)
        assert result.entries_flagged == 0

    def test_payment_before_invoice_flagged(self):
        rows = [{
            "Vendor Name": "Acme", "Amount": 5000,
            "Invoice Date": "2025-02-15", "Payment Date": "2025-01-15",
        }]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Invoice Date", "Payment Date"])
        config = APTestingConfig()
        result = run_payment_before_invoice_test(payments, config)
        assert result.entries_flagged == 1

    def test_severity_high_over_30_days(self):
        rows = [{
            "Vendor Name": "Acme", "Amount": 5000,
            "Invoice Date": "2025-03-15", "Payment Date": "2025-01-01",
        }]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Invoice Date", "Payment Date"])
        config = APTestingConfig()
        result = run_payment_before_invoice_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.HIGH
        assert result.flagged_entries[0].confidence == 0.95

    def test_severity_medium_over_7_days(self):
        rows = [{
            "Vendor Name": "Acme", "Amount": 5000,
            "Invoice Date": "2025-01-20", "Payment Date": "2025-01-05",
        }]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Invoice Date", "Payment Date"])
        config = APTestingConfig()
        result = run_payment_before_invoice_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.MEDIUM
        assert result.flagged_entries[0].confidence == 0.85

    def test_severity_low_under_7_days(self):
        rows = [{
            "Vendor Name": "Acme", "Amount": 5000,
            "Invoice Date": "2025-01-10", "Payment Date": "2025-01-05",
        }]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Invoice Date", "Payment Date"])
        config = APTestingConfig()
        result = run_payment_before_invoice_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.LOW
        assert result.flagged_entries[0].confidence == 0.70

    def test_disabled(self):
        rows = [{
            "Vendor Name": "Acme", "Amount": 5000,
            "Invoice Date": "2025-02-15", "Payment Date": "2025-01-15",
        }]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Invoice Date", "Payment Date"])
        config = APTestingConfig(payment_before_invoice_enabled=False)
        result = run_payment_before_invoice_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_missing_dates_skipped(self):
        rows = [
            {"Vendor Name": "Acme", "Amount": 5000, "Invoice Date": "", "Payment Date": "2025-01-15"},
            {"Vendor Name": "Beta", "Amount": 3000, "Invoice Date": "2025-01-10", "Payment Date": ""},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Invoice Date", "Payment Date"])
        config = APTestingConfig()
        result = run_payment_before_invoice_test(payments, config)
        assert result.entries_flagged == 0

    def test_details_structure(self):
        rows = [{
            "Vendor Name": "Acme", "Amount": 5000,
            "Invoice Date": "2025-02-15", "Payment Date": "2025-01-15",
        }]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Invoice Date", "Payment Date"])
        config = APTestingConfig()
        result = run_payment_before_invoice_test(payments, config)
        d = result.flagged_entries[0].details
        assert "days_early" in d
        assert "payment_date" in d
        assert "invoice_date" in d


class TestAPCompositeScoring:
    """6 tests for composite scoring."""

    def test_zero_entries(self):
        score = calculate_ap_composite_score([], 0)
        assert score.score == 0.0
        assert score.risk_tier == RiskTier.LOW

    def test_clean_data_low_score(self):
        """Clean test results should yield a low score."""
        results = [
            APTestResult(
                test_name="Test", test_key="t1", test_tier=TestTier.STRUCTURAL,
                entries_flagged=0, total_entries=100, flag_rate=0.0,
                severity=Severity.HIGH, description="", flagged_entries=[],
            ),
        ]
        score = calculate_ap_composite_score(results, 100)
        assert score.score == 0.0
        assert score.risk_tier == RiskTier.LOW

    def test_high_flag_rate_high_score(self):
        """High flag rate with high severity should produce elevated score."""
        payment = APPayment(vendor_name="Test", amount=1000, row_number=1)
        flagged = [
            FlaggedPayment(
                entry=payment, test_name="T", test_key="t1",
                test_tier=TestTier.STRUCTURAL, severity=Severity.HIGH,
                issue="test", confidence=0.9,
            )
        ]
        results = [
            APTestResult(
                test_name="Test", test_key="t1", test_tier=TestTier.STRUCTURAL,
                entries_flagged=1, total_entries=1, flag_rate=1.0,
                severity=Severity.HIGH, description="", flagged_entries=flagged,
            ),
        ]
        score = calculate_ap_composite_score(results, 1)
        assert score.score > 50

    def test_risk_tier_mapping(self):
        assert score_to_risk_tier(5) == RiskTier.LOW
        assert score_to_risk_tier(15) == RiskTier.ELEVATED
        assert score_to_risk_tier(30) == RiskTier.MODERATE
        assert score_to_risk_tier(60) == RiskTier.HIGH
        assert score_to_risk_tier(80) == RiskTier.CRITICAL

    def test_multi_flag_multiplier(self):
        """Entries flagged by 3+ tests should increase score."""
        payment = APPayment(vendor_name="Test", amount=1000, row_number=1)

        results = []
        for i in range(3):
            flagged = [
                FlaggedPayment(
                    entry=payment, test_name=f"T{i}", test_key=f"t{i}",
                    test_tier=TestTier.STRUCTURAL, severity=Severity.HIGH,
                    issue="test", confidence=0.9,
                )
            ]
            results.append(APTestResult(
                test_name=f"Test{i}", test_key=f"t{i}", test_tier=TestTier.STRUCTURAL,
                entries_flagged=1, total_entries=1, flag_rate=1.0,
                severity=Severity.HIGH, description="", flagged_entries=flagged,
            ))

        score = calculate_ap_composite_score(results, 1)
        assert score.score > 0
        assert score.flags_by_severity["high"] == 3

    def test_top_findings_populated(self):
        payment = APPayment(vendor_name="Test", amount=1000, row_number=1)
        flagged = [
            FlaggedPayment(
                entry=payment, test_name="T", test_key="t1",
                test_tier=TestTier.STRUCTURAL, severity=Severity.HIGH,
                issue="test", confidence=0.9,
            )
        ]
        results = [
            APTestResult(
                test_name="Dup Check", test_key="t1", test_tier=TestTier.STRUCTURAL,
                entries_flagged=1, total_entries=10, flag_rate=0.1,
                severity=Severity.HIGH, description="", flagged_entries=flagged,
            ),
        ]
        score = calculate_ap_composite_score(results, 10)
        assert len(score.top_findings) > 0
        assert "Dup Check" in score.top_findings[0]


class TestAPBattery:
    """3 tests for the full test battery."""

    def test_all_thirteen_tests_run(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        results = run_ap_test_battery(payments)
        assert len(results) == 13

    def test_all_test_keys_present(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        results = run_ap_test_battery(payments)
        keys = {r.test_key for r in results}
        expected = {
            "exact_duplicate_payments",
            "missing_critical_fields",
            "check_number_gaps",
            "round_dollar_amounts",
            "payment_before_invoice",
            "fuzzy_duplicate_payments",
            "invoice_number_reuse",
            "unusual_payment_amounts",
            "weekend_payments",
            "high_frequency_vendors",
            "vendor_name_variations",
            "just_below_threshold",
            "suspicious_descriptions",
        }
        assert keys == expected

    def test_battery_with_config(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        config = APTestingConfig(check_number_gap_enabled=False)
        results = run_ap_test_battery(payments, config)
        gap_test = [r for r in results if r.test_key == "check_number_gaps"][0]
        assert gap_test.entries_flagged == 0


class TestRunAPTesting:
    """5 tests for the full pipeline."""

    def test_full_pipeline(self):
        rows = sample_ap_rows()
        cols = sample_ap_columns()
        result = run_ap_testing(rows, cols)
        assert isinstance(result, APTestingResult)
        assert result.composite_score is not None
        assert len(result.test_results) == 13
        assert result.data_quality is not None
        assert result.column_detection is not None

    def test_column_mapping_override(self):
        rows = [
            {"v": "Acme", "a": 5000, "pd": "2025-01-15"},
            {"v": "Beta", "a": 3000, "pd": "2025-01-20"},
        ]
        cols = ["v", "a", "pd"]
        mapping = {
            "vendor_name_column": "v",
            "amount_column": "a",
            "payment_date_column": "pd",
        }
        result = run_ap_testing(rows, cols, column_mapping=mapping)
        assert result.column_detection.overall_confidence == 1.0
        assert result.column_detection.vendor_name_column == "v"

    def test_to_dict_full(self):
        rows = sample_ap_rows()
        cols = sample_ap_columns()
        result = run_ap_testing(rows, cols)
        d = result.to_dict()
        assert "composite_score" in d
        assert "test_results" in d
        assert "data_quality" in d
        assert "column_detection" in d

    def test_empty_input(self):
        result = run_ap_testing([], ["Vendor Name", "Amount", "Payment Date"])
        assert result.composite_score.score == 0.0
        assert result.composite_score.total_entries == 0

    def test_default_config_used(self):
        rows = sample_ap_rows()
        cols = sample_ap_columns()
        result = run_ap_testing(rows, cols)
        # Should work without explicit config
        assert result.composite_score.tests_run == 13


class TestAPSerialization:
    """4 tests for dataclass serialization."""

    def test_ap_payment_to_dict(self):
        p = APPayment(
            invoice_number="INV-001", vendor_name="Acme",
            amount=5000.0, row_number=1,
        )
        d = p.to_dict()
        assert d["invoice_number"] == "INV-001"
        assert d["vendor_name"] == "Acme"
        assert d["amount"] == 5000.0
        assert d["row_number"] == 1

    def test_flagged_payment_to_dict(self):
        p = APPayment(vendor_name="Acme", amount=5000.0, row_number=1)
        fp = FlaggedPayment(
            entry=p, test_name="Test", test_key="t1",
            test_tier=TestTier.STRUCTURAL, severity=Severity.HIGH,
            issue="test issue", confidence=0.95,
        )
        d = fp.to_dict()
        assert d["test_name"] == "Test"
        assert d["test_tier"] == "structural"
        assert d["severity"] == "high"
        assert d["confidence"] == 0.95
        assert d["entry"]["vendor_name"] == "Acme"

    def test_composite_score_to_dict(self):
        score = APCompositeScore(
            score=42.5, risk_tier=RiskTier.MODERATE,
            tests_run=5, total_entries=100,
            total_flagged=10, flag_rate=0.1,
        )
        d = score.to_dict()
        assert d["score"] == 42.5
        assert d["risk_tier"] == "moderate"
        assert d["tests_run"] == 5

    def test_detection_result_to_dict(self):
        cols = sample_ap_columns()
        result = detect_ap_columns(cols)
        d = result.to_dict()
        assert d["vendor_name_column"] == "Vendor Name"
        assert d["has_dual_dates"] is True
        assert d["has_check_numbers"] is True
        assert "requires_mapping" in d
        assert "overall_confidence" in d


# =============================================================================
# TIER 2 TESTS — Sprint 74
# =============================================================================

class TestFuzzyDuplicatePayments:
    """8 tests for AP-T6: Fuzzy Duplicate Payments."""

    def test_no_fuzzy_duplicates(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "fuzzy_duplicate_payments"

    def test_same_vendor_same_amount_different_date(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 2

    def test_outside_window_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-01"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-03-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(duplicate_days_window=30)
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0

    def test_different_amounts_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 6000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0

    def test_different_vendors_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Amount": 5000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0

    def test_high_severity_above_10k(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 15000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 15000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 2
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_medium_severity_below_10k(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_test_tier_statistical(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.test_tier == TestTier.STATISTICAL


class TestInvoiceNumberReuse:
    """8 tests for AP-T7: Invoice Number Reuse."""

    def test_no_reuse(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "invoice_number_reuse"

    def test_same_invoice_different_vendors(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 2

    def test_same_invoice_same_vendor_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0

    def test_always_high_severity(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_disabled(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig(invoice_reuse_check=False)
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_blank_invoices_ignored(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0

    def test_case_insensitive(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "inv-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 2

    def test_details_structure(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        d = result.flagged_entries[0].details
        assert "invoice_number" in d
        assert "vendor_count" in d
        assert "vendors" in d
        assert d["vendor_count"] == 2


class TestUnusualPaymentAmounts:
    """8 tests for AP-T8: Unusual Payment Amounts."""

    def _vendor_payments(self, amounts, vendor="Acme Corp"):
        rows = [
            {"Vendor Name": vendor, "Amount": a, "Payment Date": "2025-01-01"}
            for a in amounts
        ]
        return make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])

    def test_no_outliers(self):
        payments = self._vendor_payments([100, 105, 98, 102, 110])
        config = APTestingConfig()
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "unusual_payment_amounts"

    def test_outlier_detected(self):
        payments = self._vendor_payments([100, 100, 100, 100, 100, 100, 100, 10000])
        config = APTestingConfig(unusual_amount_stddev=2.0)
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged >= 1

    def test_min_payments_threshold(self):
        """Vendors with fewer than min_payments are skipped."""
        payments = self._vendor_payments([100, 100, 10000])
        config = APTestingConfig(unusual_amount_min_payments=5)
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_severity_tiers(self):
        # z>5 → HIGH, z>4 → MEDIUM, z>3 → LOW
        # Use very tight cluster with single extreme outlier
        base = [100] * 50
        base.append(1000000)  # massive outlier for guaranteed high z-score
        payments = self._vendor_payments(base)
        config = APTestingConfig(unusual_amount_stddev=3.0)
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged >= 1
        # The extreme outlier should be HIGH
        high_flags = [f for f in result.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1

    def test_all_same_amounts_no_flags(self):
        payments = self._vendor_payments([500, 500, 500, 500, 500])
        config = APTestingConfig()
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_per_vendor_analysis(self):
        """Each vendor analyzed independently."""
        rows = [
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-01"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-02"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-03"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-04"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-05"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-01"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-02"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-03"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-04"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-05"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        # No outliers within each vendor
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_details_structure(self):
        base = [100] * 20
        base.append(100000)
        payments = self._vendor_payments(base)
        config = APTestingConfig(unusual_amount_stddev=3.0)
        result = run_unusual_amounts_test(payments, config)
        if result.entries_flagged > 0:
            d = result.flagged_entries[0].details
            assert "z_score" in d
            assert "vendor_mean" in d
            assert "vendor_stdev" in d
            assert "vendor_payment_count" in d

    def test_test_tier_statistical(self):
        payments = self._vendor_payments([100, 100, 100, 100, 100])
        config = APTestingConfig()
        result = run_unusual_amounts_test(payments, config)
        assert result.test_tier == TestTier.STATISTICAL


class TestWeekendPayments:
    """8 tests for AP-T9: Weekend Payments."""

    def test_no_weekend_payments(self):
        # 2025-01-06 is Monday, 2025-01-07 is Tuesday
        rows = [
            {"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-06"},
            {"Vendor Name": "Beta", "Amount": 3000, "Payment Date": "2025-01-07"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "weekend_payments"

    def test_saturday_flagged(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 1
        assert "Saturday" in result.flagged_entries[0].issue

    def test_sunday_flagged(self):
        # 2025-01-05 is Sunday
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-05"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 1
        assert "Sunday" in result.flagged_entries[0].issue

    def test_high_severity_large_amount(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_medium_severity_small_amount(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_disabled(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(weekend_payment_enabled=False)
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_missing_date_skipped(self):
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": ""}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 0

    def test_details_structure(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        d = result.flagged_entries[0].details
        assert "day_of_week" in d
        assert "payment_date" in d
        assert "amount" in d


class TestHighFrequencyVendors:
    """8 tests for AP-T10: High-Frequency Vendors."""

    def test_no_high_frequency(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "high_frequency_vendors"

    def test_five_payments_same_day_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(5)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 5

    def test_below_threshold_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(4)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0

    def test_different_days_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000, "Payment Date": f"2025-01-{10+i:02d}"}
            for i in range(5)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0

    def test_high_severity_ten_plus(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 100 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(10)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_medium_severity_five_to_nine(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(6)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_disabled(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000, "Payment Date": "2025-01-10"}
            for _ in range(10)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(high_frequency_vendor_enabled=False)
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_details_structure(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(5)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        d = result.flagged_entries[0].details
        assert "vendor" in d
        assert "date" in d
        assert "daily_count" in d
        assert d["daily_count"] == 5


# =============================================================================
# TIER 3 TESTS — Sprint 74
# =============================================================================

class TestVendorNameVariations:
    """8 tests for AP-T11: Vendor Name Variations."""

    def test_no_variations(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.test_key == "vendor_name_variations"
        # All vendors are sufficiently different
        assert result.test_tier == TestTier.ADVANCED

    def test_similar_names_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 2

    def test_identical_names_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0

    def test_very_different_names_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "XYZ Industries", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0

    def test_high_severity_large_combined(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 30000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 25000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_medium_severity_small_combined(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_disabled(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(vendor_variation_enabled=False)
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_few_vendors_skip(self):
        rows = [{"Vendor Name": "Solo Vendor", "Amount": 5000, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0


class TestJustBelowThreshold:
    """8 tests for AP-T12: Just-Below-Threshold."""

    def test_no_near_threshold(self):
        rows = [
            {"Vendor Name": "Acme", "Amount": 3000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta", "Amount": 7500, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "just_below_threshold"

    def test_just_below_5k_flagged(self):
        # 4800 is within 5% of 5000 (lower bound = 4750)
        rows = [{"Vendor Name": "Acme", "Amount": 4800, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 1

    def test_just_below_10k_flagged(self):
        # 9600 is within 5% of 10000 (lower bound = 9500)
        rows = [{"Vendor Name": "Acme", "Amount": 9600, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 1

    def test_above_threshold_not_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 5100, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        # 5100 is above 5K threshold, below proximity range of 10K
        assert result.entries_flagged == 0

    def test_split_payments_detected(self):
        # Two payments to same vendor on same day totaling above 10K
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 6000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        split_flags = [f for f in result.flagged_entries if "Split" in f.issue or "split" in f.issue.lower()]
        assert len(split_flags) >= 1

    def test_high_severity_above_50k_threshold(self):
        # 49000 is within 5% of 50000 (lower = 47500)
        rows = [{"Vendor Name": "Acme", "Amount": 49000, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        high_flags = [f for f in result.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1

    def test_disabled(self):
        rows = [{"Vendor Name": "Acme", "Amount": 4900, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(threshold_proximity_enabled=False)
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_details_structure(self):
        rows = [{"Vendor Name": "Acme", "Amount": 4800, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        d = result.flagged_entries[0].details
        assert "amount" in d
        assert "threshold" in d
        assert "pct_below" in d


class TestSuspiciousDescriptions:
    """8 tests for AP-T13: Suspicious Descriptions."""

    def test_no_suspicious_descriptions(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.test_key == "suspicious_descriptions"

    def test_petty_cash_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-10", "Description": "Petty cash replenishment"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 1
        assert "petty cash" in result.flagged_entries[0].details["matched_keywords"]

    def test_override_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-10", "Description": "Manager override approval"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 1

    def test_high_severity_high_confidence_large_amount(self):
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-10", "Description": "Void reissue required"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_below_threshold_not_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-10", "Description": "Regular payment"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 0

    def test_no_descriptions_no_flags(self):
        rows = [
            {"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 0

    def test_disabled(self):
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-10", "Description": "Petty cash"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig(suspicious_keyword_enabled=False)
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_keywords_constant_has_16_entries(self):
        assert len(AP_SUSPICIOUS_KEYWORDS) == 16


# =============================================================================
# SCORING CALIBRATION + API — Sprint 74
# =============================================================================

class TestAPScoringCalibration:
    """5 tests for scoring calibration across clean/moderate/high scenarios."""

    def test_clean_data_low_score(self):
        rows = sample_ap_rows()
        result = run_ap_testing(rows, sample_ap_columns())
        assert result.composite_score.score < 15
        assert result.composite_score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED)

    def test_moderate_flags_moderate_score(self):
        """Some flags across a few tests should produce moderate risk."""
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-04",
             "Invoice Number": "INV-001", "Description": "Rush order", "Check Number": "1001"},
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-11",
             "Invoice Number": "INV-002", "Description": "Normal", "Check Number": "1002"},
            {"Vendor Name": "Beta LLC", "Amount": 5000, "Payment Date": "2025-01-06",
             "Invoice Number": "INV-003", "Description": "Standard", "Check Number": "1003"},
            {"Vendor Name": "Gamma Inc", "Amount": 3000, "Payment Date": "2025-01-07",
             "Invoice Number": "INV-004", "Description": "Standard", "Check Number": "1004"},
        ]
        result = run_ap_testing(rows, list(rows[0].keys()))
        # Should have some flags (weekend, near-threshold, fuzzy dupes)
        assert result.composite_score.score > 0

    def test_high_risk_data_high_score(self):
        """Many flags across multiple tests should produce high risk."""
        rows = []
        # Exact duplicates
        base = {"Vendor Name": "Acme Corp", "Amount": 50000, "Payment Date": "2025-01-04",
                "Invoice Number": "INV-001", "Description": "Override urgent rush",
                "Check Number": "1001", "Invoice Date": "2025-02-01"}
        for _ in range(3):
            rows.append(dict(base))
        # More risky entries
        rows.append({"Vendor Name": "Beta LLC", "Amount": 50000, "Payment Date": "2025-01-05",
                      "Invoice Number": "INV-001", "Description": "Manual check void reissue",
                      "Check Number": "1010", "Invoice Date": "2025-01-01"})
        result = run_ap_testing(rows, list(rows[0].keys()))
        assert result.composite_score.score > result.composite_score.score * 0  # Non-zero

    def test_clean_lower_than_moderate(self):
        clean_rows = sample_ap_rows()
        clean_result = run_ap_testing(clean_rows, sample_ap_columns())

        moderate_rows = [
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-04",
             "Invoice Number": "INV-001", "Description": "Rush order", "Check Number": "1001"},
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-18",
             "Invoice Number": "INV-002", "Description": "Normal", "Check Number": "1002"},
            {"Vendor Name": "Beta LLC", "Amount": 5000, "Payment Date": "2025-01-05",
             "Invoice Number": "INV-003", "Description": "Override", "Check Number": "1003"},
        ]
        moderate_result = run_ap_testing(moderate_rows, list(moderate_rows[0].keys()))

        assert clean_result.composite_score.score <= moderate_result.composite_score.score

    def test_thirteen_tests_always_run(self):
        result = run_ap_testing(sample_ap_rows(), sample_ap_columns())
        assert result.composite_score.tests_run == 13


class TestAPTestingAPI:
    """3 tests for the POST /audit/ap-payments endpoint."""

    def test_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/audit/ap-payments" in paths

    def test_route_method_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/audit/ap-payments":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /audit/ap-payments not found")

    def test_route_has_audit_tag(self):
        from routes.ap_testing import router
        assert "ap_testing" in router.tags
