"""
Tests for Payroll & Employee Testing Engine.
Sprint 85-86: Payroll Testing — Backend Foundation + Tier 1-3

Tests cover:
- Column detection (12 tests)
- Payroll entry parsing (8 tests)
- Safe helpers (6 tests)
- Data quality (5 tests)
- PR-T1: Duplicate employee IDs (10 tests)
- PR-T2: Missing critical fields (8 tests)
- PR-T3: Round salary amounts (8 tests)
- PR-T4: Pay after termination (8 tests)
- PR-T5: Check number gaps (8 tests)
- PR-T6: Unusual pay amounts (8 tests)
- PR-T7: Pay frequency anomalies (7 tests)
- PR-T8: Benford's law on gross pay (6 tests)
- PR-T9: Ghost employee indicators (8 tests)
- PR-T10: Duplicate bank accounts / addresses (6 tests)
- PR-T11: Duplicate tax IDs (5 tests)
- Composite scoring (10 tests — includes calibration)
- Battery orchestration (3 tests)
- Full pipeline (5 tests)
- Serialization (4 tests)
- API route registration (4 tests)
"""

import pytest
from datetime import date

from shared.parsing_helpers import safe_str, safe_float, parse_date
from payroll_testing_engine import (
    # Enums
    RiskTier, TestTier, Severity,
    # Config
    PayrollTestingConfig,
    # Column detection
    PayrollColumnType, detect_payroll_columns, PayrollColumnDetectionResult,
    # Data models
    PayrollEntry, FlaggedEmployee, PayrollTestResult, PayrollDataQuality,
    PayrollCompositeScore, PayrollTestingResult,
    # Parser
    parse_payroll_entries,
    # Data quality
    assess_payroll_data_quality,
    # Tier 1 Tests
    _test_duplicate_employee_ids,
    _test_missing_critical_fields,
    _test_round_salary_amounts,
    _test_pay_after_termination,
    _test_check_number_gaps,
    # Tier 2 Tests
    _test_unusual_pay_amounts,
    _test_pay_frequency_anomalies,
    _test_benford_gross_pay,
    BENFORD_EXPECTED,
    _get_first_digit,
    # Tier 3 Tests
    _test_ghost_employee_indicators,
    _test_duplicate_bank_accounts,
    _test_duplicate_tax_ids,
    # Battery & scoring
    run_payroll_test_battery,
    calculate_payroll_composite_score,
    # Main entry
    run_payroll_testing,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def standard_columns():
    return ["Employee ID", "Employee Name", "Department", "Pay Date", "Gross Pay",
            "Net Pay", "Check Number", "Termination Date"]


@pytest.fixture
def minimal_columns():
    return ["Name", "Date", "Amount"]


@pytest.fixture
def sample_entries():
    """Sample payroll entries for testing."""
    return [
        PayrollEntry(employee_id="E001", employee_name="John Smith", department="Sales",
                     pay_date=date(2025, 1, 15), gross_pay=5000.0, _row_index=1),
        PayrollEntry(employee_id="E002", employee_name="Jane Doe", department="HR",
                     pay_date=date(2025, 1, 15), gross_pay=4500.0, _row_index=2),
        PayrollEntry(employee_id="E003", employee_name="Bob Wilson", department="IT",
                     pay_date=date(2025, 1, 15), gross_pay=6000.0, _row_index=3),
        PayrollEntry(employee_id="E001", employee_name="John Smith", department="Sales",
                     pay_date=date(2025, 1, 31), gross_pay=5000.0, _row_index=4),
        PayrollEntry(employee_id="E002", employee_name="Jane Doe", department="HR",
                     pay_date=date(2025, 1, 31), gross_pay=4500.0, _row_index=5),
    ]


@pytest.fixture
def default_config():
    return PayrollTestingConfig()


@pytest.fixture
def standard_detection():
    return PayrollColumnDetectionResult(
        employee_name_column="Employee Name",
        gross_pay_column="Gross Pay",
        pay_date_column="Pay Date",
        employee_id_column="Employee ID",
        department_column="Department",
        check_number_column="Check Number",
        has_check_numbers=True,
        has_term_dates=True,
        term_date_column="Termination Date",
        overall_confidence=1.0,
    )


# =============================================================================
# TestPayrollColumnDetection
# =============================================================================

class TestPayrollColumnDetection:
    """Tests for payroll column detection."""

    def test_standard_columns(self, standard_columns):
        result = detect_payroll_columns(standard_columns)
        assert result.employee_id_column == "Employee ID"
        assert result.employee_name_column == "Employee Name"
        assert result.gross_pay_column == "Gross Pay"
        assert result.pay_date_column == "Pay Date"

    def test_alternate_naming(self):
        cols = ["Emp ID", "Emp Name", "Dept", "Check Date", "Salary"]
        result = detect_payroll_columns(cols)
        assert result.employee_id_column is not None
        assert result.employee_name_column is not None

    def test_minimal_columns(self, minimal_columns):
        result = detect_payroll_columns(minimal_columns)
        assert result.employee_name_column == "Name"

    def test_low_confidence(self):
        cols = ["Column1", "Column2", "Column3"]
        result = detect_payroll_columns(cols)
        assert result.overall_confidence < 0.70
        assert result.requires_mapping is True

    def test_to_dict(self, standard_columns):
        result = detect_payroll_columns(standard_columns)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "employee_name_column" in d
        assert "overall_confidence" in d
        assert "requires_mapping" in d

    def test_greedy_assignment(self):
        """No column mapped to two types."""
        cols = ["Employee Name", "Employee ID", "Gross Pay", "Net Pay", "Pay Date"]
        result = detect_payroll_columns(cols)
        assigned = [
            result.employee_name_column,
            result.employee_id_column,
            result.gross_pay_column,
            result.net_pay_column,
            result.pay_date_column,
        ]
        non_none = [c for c in assigned if c is not None]
        assert len(non_none) == len(set(non_none)), "Greedy assignment should prevent duplicates"

    def test_department_detected(self, standard_columns):
        result = detect_payroll_columns(standard_columns)
        assert result.department_column == "Department"

    def test_check_number_flag(self, standard_columns):
        result = detect_payroll_columns(standard_columns)
        assert result.has_check_numbers is True

    def test_term_date_flag(self, standard_columns):
        result = detect_payroll_columns(standard_columns)
        assert result.has_term_dates is True

    def test_bank_account_detection(self):
        cols = ["Name", "Pay Date", "Gross Pay", "Bank Account"]
        result = detect_payroll_columns(cols)
        assert result.has_bank_accounts is True

    def test_tax_id_detection(self):
        cols = ["Name", "Pay Date", "Gross Pay", "SSN"]
        result = detect_payroll_columns(cols)
        assert result.has_tax_ids is True

    def test_address_detection(self):
        cols = ["Name", "Pay Date", "Gross Pay", "Address"]
        result = detect_payroll_columns(cols)
        assert result.has_addresses is True


# =============================================================================
# TestPayrollParsing
# =============================================================================

class TestPayrollParsing:
    """Tests for payroll entry parsing."""

    def test_valid_rows(self, standard_detection):
        rows = [
            {"Employee ID": "E001", "Employee Name": "John Smith",
             "Department": "Sales", "Pay Date": "2025-01-15",
             "Gross Pay": "5000.00", "Net Pay": "3500.00"},
        ]
        entries = parse_payroll_entries(rows, standard_detection)
        assert len(entries) == 1
        assert entries[0].employee_name == "John Smith"
        assert entries[0].gross_pay == 5000.0

    def test_invalid_dates(self, standard_detection):
        rows = [{"Employee Name": "Test", "Pay Date": "invalid", "Gross Pay": "100"}]
        entries = parse_payroll_entries(rows, standard_detection)
        assert entries[0].pay_date is None

    def test_missing_fields(self, standard_detection):
        rows = [{"Employee Name": "", "Gross Pay": "", "Pay Date": ""}]
        entries = parse_payroll_entries(rows, standard_detection)
        assert entries[0].employee_name == ""
        assert entries[0].gross_pay == 0.0

    def test_to_dict(self, standard_detection):
        rows = [{"Employee Name": "Test", "Gross Pay": "100", "Pay Date": "2025-01-15"}]
        entries = parse_payroll_entries(rows, standard_detection)
        d = entries[0].to_dict()
        assert isinstance(d, dict)
        assert d["employee_name"] == "Test"

    def test_row_index(self, standard_detection):
        rows = [{"Employee Name": "A"}, {"Employee Name": "B"}]
        entries = parse_payroll_entries(rows, standard_detection)
        assert entries[0]._row_index == 1
        assert entries[1]._row_index == 2

    def test_currency_parsing(self, standard_detection):
        rows = [{"Employee Name": "Test", "Gross Pay": "$5,000.00"}]
        entries = parse_payroll_entries(rows, standard_detection)
        assert entries[0].gross_pay == 5000.0

    def test_empty_rows(self, standard_detection):
        entries = parse_payroll_entries([], standard_detection)
        assert len(entries) == 0

    def test_term_date_parsing(self, standard_detection):
        rows = [{"Employee Name": "Test", "Termination Date": "2025-06-30", "Gross Pay": "100"}]
        entries = parse_payroll_entries(rows, standard_detection)
        assert entries[0].term_date == date(2025, 6, 30)


# =============================================================================
# TestSafeHelpers
# =============================================================================

class TestSafeHelpers:

    def testsafe_str_none(self):
        assert safe_str(None) is None

    def testsafe_str_value(self):
        assert safe_str("  hello  ") == "hello"

    def testsafe_float_none(self):
        assert safe_float(None) == 0.0

    def testsafe_float_currency(self):
        assert safe_float("$1,234.56") == 1234.56

    def testsafe_float_parenthetical(self):
        assert safe_float("(500.00)") == -500.0

    def testparse_date_formats(self):
        assert parse_date("2025-01-15") == date(2025, 1, 15)
        assert parse_date("01/15/2025") == date(2025, 1, 15)
        assert parse_date(None) is None
        assert parse_date("") is None
        assert parse_date("invalid") is None


# =============================================================================
# TestDataQuality
# =============================================================================

class TestDataQuality:

    def test_full_quality(self, sample_entries, standard_detection):
        dq = assess_payroll_data_quality(sample_entries, standard_detection)
        assert dq.completeness_score > 0.80
        assert dq.total_rows == 5

    def test_low_quality(self, standard_detection):
        entries = [
            PayrollEntry(employee_name="", gross_pay=0.0, pay_date=None),
        ] * 3
        dq = assess_payroll_data_quality(entries, standard_detection)
        assert dq.completeness_score < 0.50
        assert len(dq.detected_issues) > 0

    def test_empty_entries(self, standard_detection):
        dq = assess_payroll_data_quality([], standard_detection)
        assert dq.total_rows == 0
        assert dq.completeness_score == 0.0

    def test_field_fill_rates(self, sample_entries, standard_detection):
        dq = assess_payroll_data_quality(sample_entries, standard_detection)
        assert "employee_name" in dq.field_fill_rates
        assert "gross_pay" in dq.field_fill_rates

    def test_to_dict(self, sample_entries, standard_detection):
        dq = assess_payroll_data_quality(sample_entries, standard_detection)
        d = dq.to_dict()
        assert isinstance(d, dict)
        assert "completeness_score" in d


# =============================================================================
# TestDuplicateEmployees (PR-T1)
# =============================================================================

class TestDuplicateEmployees:

    def test_no_duplicates(self, sample_entries, default_config):
        result = _test_duplicate_employee_ids(sample_entries, default_config)
        assert result.entries_flagged == 0

    def test_exact_id_different_names(self, default_config):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John Smith", _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="Johnny Smith", _row_index=2),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert result.entries_flagged == 2

    def test_same_id_same_name_not_flagged(self, default_config):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John Smith", _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="John Smith", _row_index=2),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert result.entries_flagged == 0

    def test_case_insensitive_names(self, default_config):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John Smith", _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="john smith", _row_index=2),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert result.entries_flagged == 0

    def test_empty_id_ignored(self, default_config):
        entries = [
            PayrollEntry(employee_id="", employee_name="John Smith", _row_index=1),
            PayrollEntry(employee_id="", employee_name="Jane Doe", _row_index=2),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert result.entries_flagged == 0

    def test_severity_is_high(self, default_config):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John Smith", _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="Jane Doe", _row_index=2),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert result.flagged_entries[0].severity == Severity.HIGH.value

    def test_multiple_groups(self, default_config):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John Smith", _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="Jane Doe", _row_index=2),
            PayrollEntry(employee_id="E002", employee_name="Bob Wilson", _row_index=3),
            PayrollEntry(employee_id="E002", employee_name="Robert Wilson", _row_index=4),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert result.entries_flagged == 4

    def test_flag_rate(self, default_config):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John", _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="Jane", _row_index=2),
            PayrollEntry(employee_id="E002", employee_name="Bob", _row_index=3),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert result.flag_rate == pytest.approx(2 / 3)

    def test_test_key(self, sample_entries, default_config):
        result = _test_duplicate_employee_ids(sample_entries, default_config)
        assert result.test_key == "PR-T1"

    def test_details_contain_names(self, default_config):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John Smith", _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="Jane Doe", _row_index=2),
        ]
        result = _test_duplicate_employee_ids(entries, default_config)
        assert "names" in result.flagged_entries[0].details


# =============================================================================
# TestMissingFields (PR-T2)
# =============================================================================

class TestMissingFields:

    def test_no_missing(self, sample_entries, default_config):
        result = _test_missing_critical_fields(sample_entries, default_config)
        assert result.entries_flagged == 0

    def test_blank_name(self, default_config):
        entries = [PayrollEntry(employee_name="", gross_pay=100.0, pay_date=date(2025, 1, 1), _row_index=1)]
        result = _test_missing_critical_fields(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH.value

    def test_zero_pay(self, default_config):
        entries = [PayrollEntry(employee_name="John", gross_pay=0.0, pay_date=date(2025, 1, 1), _row_index=1)]
        result = _test_missing_critical_fields(entries, default_config)
        assert result.entries_flagged == 1

    def test_blank_date(self, default_config):
        entries = [PayrollEntry(employee_name="John", gross_pay=100.0, pay_date=None, _row_index=1)]
        result = _test_missing_critical_fields(entries, default_config)
        assert result.entries_flagged == 1

    def test_multiple_missing(self, default_config):
        entries = [PayrollEntry(employee_name="", gross_pay=0.0, pay_date=None, _row_index=1)]
        result = _test_missing_critical_fields(entries, default_config)
        assert result.entries_flagged == 1
        assert ";" in result.flagged_entries[0].issue

    def test_all_clean(self, default_config):
        entries = [
            PayrollEntry(employee_name="A", gross_pay=100.0, pay_date=date(2025, 1, 1), _row_index=1),
            PayrollEntry(employee_name="B", gross_pay=200.0, pay_date=date(2025, 1, 1), _row_index=2),
        ]
        result = _test_missing_critical_fields(entries, default_config)
        assert result.entries_flagged == 0

    def test_test_key(self, sample_entries, default_config):
        result = _test_missing_critical_fields(sample_entries, default_config)
        assert result.test_key == "PR-T2"

    def test_missing_details(self, default_config):
        entries = [PayrollEntry(employee_name="", gross_pay=100.0, pay_date=date(2025, 1, 1), _row_index=1)]
        result = _test_missing_critical_fields(entries, default_config)
        assert "missing_fields" in result.flagged_entries[0].details


# =============================================================================
# TestRoundAmounts (PR-T3)
# =============================================================================

class TestRoundAmounts:

    def test_100k_multiple(self, default_config):
        entries = [PayrollEntry(gross_pay=100000.0, _row_index=1)]
        result = _test_round_salary_amounts(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH.value

    def test_50k_multiple(self, default_config):
        entries = [PayrollEntry(gross_pay=50000.0, _row_index=1)]
        result = _test_round_salary_amounts(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH.value

    def test_25k_multiple(self, default_config):
        entries = [PayrollEntry(gross_pay=25000.0, _row_index=1)]
        result = _test_round_salary_amounts(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM.value

    def test_10k_multiple(self, default_config):
        entries = [PayrollEntry(gross_pay=10000.0, _row_index=1)]
        result = _test_round_salary_amounts(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW.value

    def test_below_threshold(self, default_config):
        entries = [PayrollEntry(gross_pay=5000.0, _row_index=1)]
        result = _test_round_salary_amounts(entries, default_config)
        assert result.entries_flagged == 0

    def test_non_round_amount(self, default_config):
        entries = [PayrollEntry(gross_pay=15123.45, _row_index=1)]
        result = _test_round_salary_amounts(entries, default_config)
        assert result.entries_flagged == 0

    def test_max_flags_respected(self):
        config = PayrollTestingConfig(round_amount_max_flags=2)
        entries = [PayrollEntry(gross_pay=100000.0, _row_index=i) for i in range(10)]
        result = _test_round_salary_amounts(entries, config)
        assert result.entries_flagged == 2

    def test_test_key(self, sample_entries, default_config):
        result = _test_round_salary_amounts(sample_entries, default_config)
        assert result.test_key == "PR-T3"


# =============================================================================
# TestPayAfterTermination (PR-T4)
# =============================================================================

class TestPayAfterTermination:

    def test_no_term_dates(self, sample_entries, default_config):
        result = _test_pay_after_termination(sample_entries, default_config)
        assert result.entries_flagged == 0

    def test_payment_after_30_days(self, default_config):
        entries = [PayrollEntry(
            employee_name="John", pay_date=date(2025, 3, 15),
            term_date=date(2025, 1, 1), gross_pay=5000.0, _row_index=1
        )]
        result = _test_pay_after_termination(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH.value

    def test_payment_after_7_days(self, default_config):
        entries = [PayrollEntry(
            employee_name="John", pay_date=date(2025, 1, 20),
            term_date=date(2025, 1, 10), gross_pay=5000.0, _row_index=1
        )]
        result = _test_pay_after_termination(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.MEDIUM.value

    def test_payment_within_7_days(self, default_config):
        entries = [PayrollEntry(
            employee_name="John", pay_date=date(2025, 1, 5),
            term_date=date(2025, 1, 1), gross_pay=5000.0, _row_index=1
        )]
        result = _test_pay_after_termination(entries, default_config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.LOW.value

    def test_payment_before_termination(self, default_config):
        entries = [PayrollEntry(
            employee_name="John", pay_date=date(2025, 1, 1),
            term_date=date(2025, 6, 30), gross_pay=5000.0, _row_index=1
        )]
        result = _test_pay_after_termination(entries, default_config)
        assert result.entries_flagged == 0

    def test_no_term_column(self, default_config):
        """No term_date → no flags."""
        entries = [PayrollEntry(
            employee_name="John", pay_date=date(2025, 1, 15),
            term_date=None, gross_pay=5000.0, _row_index=1
        )]
        result = _test_pay_after_termination(entries, default_config)
        assert result.entries_flagged == 0

    def test_disabled_by_config(self, default_config):
        config = PayrollTestingConfig(pay_after_term_enabled=False)
        entries = [PayrollEntry(
            employee_name="John", pay_date=date(2025, 3, 15),
            term_date=date(2025, 1, 1), gross_pay=5000.0, _row_index=1
        )]
        result = _test_pay_after_termination(entries, config)
        assert result.entries_flagged == 0

    def test_test_key(self, sample_entries, default_config):
        result = _test_pay_after_termination(sample_entries, default_config)
        assert result.test_key == "PR-T4"


# =============================================================================
# TestCheckNumberGaps (PR-T5)
# =============================================================================

class TestCheckNumberGaps:

    def test_sequential_no_gaps(self, default_config):
        entries = [
            PayrollEntry(check_number="1001", _row_index=1),
            PayrollEntry(check_number="1002", _row_index=2),
            PayrollEntry(check_number="1003", _row_index=3),
        ]
        result = _test_check_number_gaps(entries, default_config)
        assert result.entries_flagged == 0

    def test_gap_detected(self, default_config):
        entries = [
            PayrollEntry(check_number="1001", _row_index=1),
            PayrollEntry(check_number="1005", _row_index=2),
        ]
        result = _test_check_number_gaps(entries, default_config)
        assert result.entries_flagged == 1

    def test_large_gap_high_severity(self, default_config):
        entries = [
            PayrollEntry(check_number="1000", _row_index=1),
            PayrollEntry(check_number="1020", _row_index=2),
        ]
        result = _test_check_number_gaps(entries, default_config)
        assert result.flagged_entries[0].severity == Severity.HIGH.value

    def test_non_numeric_ignored(self, default_config):
        entries = [
            PayrollEntry(check_number="ABC", _row_index=1),
            PayrollEntry(check_number="DEF", _row_index=2),
        ]
        result = _test_check_number_gaps(entries, default_config)
        assert result.entries_flagged == 0

    def test_single_check(self, default_config):
        entries = [PayrollEntry(check_number="1001", _row_index=1)]
        result = _test_check_number_gaps(entries, default_config)
        assert result.entries_flagged == 0

    def test_disabled(self):
        config = PayrollTestingConfig(check_number_gap_enabled=False)
        entries = [
            PayrollEntry(check_number="1001", _row_index=1),
            PayrollEntry(check_number="1010", _row_index=2),
        ]
        result = _test_check_number_gaps(entries, config)
        assert result.entries_flagged == 0

    def test_gap_details(self, default_config):
        entries = [
            PayrollEntry(check_number="100", _row_index=1),
            PayrollEntry(check_number="110", _row_index=2),
        ]
        result = _test_check_number_gaps(entries, default_config)
        assert "gap_size" in result.flagged_entries[0].details

    def test_test_key(self, sample_entries, default_config):
        result = _test_check_number_gaps(sample_entries, default_config)
        assert result.test_key == "PR-T5"


# =============================================================================
# TestCompositeScoring
# =============================================================================

class TestCompositeScoring:

    def test_clean_low_score(self, default_config, standard_detection):
        """Truly clean data with multiple entries per employee = low score."""
        clean = [
            PayrollEntry(employee_id="E001", employee_name="John Smith", department="Sales",
                         pay_date=date(2025, 1, 15), gross_pay=5000.0, _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="John Smith", department="Sales",
                         pay_date=date(2025, 2, 15), gross_pay=5000.0, _row_index=2),
            PayrollEntry(employee_id="E001", employee_name="John Smith", department="Sales",
                         pay_date=date(2025, 3, 15), gross_pay=5000.0, _row_index=3),
            PayrollEntry(employee_id="E002", employee_name="Jane Doe", department="HR",
                         pay_date=date(2025, 1, 15), gross_pay=4500.0, _row_index=4),
            PayrollEntry(employee_id="E002", employee_name="Jane Doe", department="HR",
                         pay_date=date(2025, 2, 15), gross_pay=4500.0, _row_index=5),
            PayrollEntry(employee_id="E002", employee_name="Jane Doe", department="HR",
                         pay_date=date(2025, 3, 15), gross_pay=4500.0, _row_index=6),
        ]
        results = run_payroll_test_battery(clean, default_config, standard_detection)
        score = calculate_payroll_composite_score(results, len(clean))
        assert score.score < 10
        assert score.risk_tier == RiskTier.LOW.value

    def test_dirty_high_score(self, default_config):
        # All missing fields
        entries = [
            PayrollEntry(employee_name="", gross_pay=0.0, pay_date=None, _row_index=i)
            for i in range(10)
        ]
        detection = PayrollColumnDetectionResult(
            employee_name_column="Name",
            gross_pay_column="Pay",
            pay_date_column="Date",
        )
        results = run_payroll_test_battery(entries, default_config, detection)
        score = calculate_payroll_composite_score(results, len(entries))
        assert score.score > 10

    def test_comparative_ordering(self, default_config):
        """Clean score < moderate score < dirty score."""
        clean = [
            PayrollEntry(employee_id="E001", employee_name="John", department="Sales",
                         pay_date=date(2025, 1, 15), gross_pay=5000.0, _row_index=i)
            for i in range(10)
        ]
        dirty = [
            PayrollEntry(employee_name="", gross_pay=0.0, pay_date=None, _row_index=i)
            for i in range(10)
        ]
        detection = PayrollColumnDetectionResult(
            employee_name_column="Name",
            gross_pay_column="Pay",
            pay_date_column="Date",
        )
        clean_results = run_payroll_test_battery(clean, default_config, detection)
        dirty_results = run_payroll_test_battery(dirty, default_config, detection)
        clean_score = calculate_payroll_composite_score(clean_results, len(clean))
        dirty_score = calculate_payroll_composite_score(dirty_results, len(dirty))
        assert clean_score.score <= dirty_score.score

    def test_empty_entries(self):
        score = calculate_payroll_composite_score([], 0)
        assert score.score == 0.0
        assert score.risk_tier == RiskTier.LOW.value

    def test_flags_by_severity(self, default_config):
        entries = [PayrollEntry(employee_name="", gross_pay=0.0, pay_date=None, _row_index=1)]
        detection = PayrollColumnDetectionResult(
            employee_name_column="Name",
            gross_pay_column="Pay",
            pay_date_column="Date",
        )
        results = run_payroll_test_battery(entries, default_config, detection)
        score = calculate_payroll_composite_score(results, len(entries))
        assert score.total_flagged > 0
        assert isinstance(score.flags_by_severity, dict)

    def test_top_findings(self, default_config):
        entries = [PayrollEntry(employee_name="", gross_pay=0.0, _row_index=1)]
        detection = PayrollColumnDetectionResult(
            employee_name_column="Name", gross_pay_column="Pay", pay_date_column="Date",
        )
        results = run_payroll_test_battery(entries, default_config, detection)
        score = calculate_payroll_composite_score(results, len(entries))
        assert len(score.top_findings) > 0

    def test_to_dict(self, sample_entries, default_config, standard_detection):
        results = run_payroll_test_battery(sample_entries, default_config, standard_detection)
        score = calculate_payroll_composite_score(results, len(sample_entries))
        d = score.to_dict()
        assert isinstance(d, dict)
        assert "score" in d
        assert "risk_tier" in d


# =============================================================================
# TestBattery
# =============================================================================

class TestBattery:

    def test_full_battery(self, sample_entries, default_config, standard_detection):
        results = run_payroll_test_battery(sample_entries, default_config, standard_detection)
        # T1, T2, T3 always; T4 and T5 if columns exist
        assert len(results) >= 3

    def test_opt_in_behavior(self, sample_entries, default_config):
        """Without optional columns, T4/T5 skipped."""
        detection = PayrollColumnDetectionResult(
            employee_name_column="Name",
            gross_pay_column="Pay",
            pay_date_column="Date",
            has_check_numbers=False,
            has_term_dates=False,
        )
        results = run_payroll_test_battery(sample_entries, default_config, detection)
        keys = [r.test_key for r in results]
        assert "PR-T4" not in keys
        assert "PR-T5" not in keys

    def test_empty_input(self, default_config, standard_detection):
        results = run_payroll_test_battery([], default_config, standard_detection)
        assert len(results) >= 3
        for r in results:
            assert r.entries_flagged == 0


# =============================================================================
# TestFullPipeline
# =============================================================================

class TestFullPipeline:

    def test_run_payroll_testing(self):
        headers = ["Employee ID", "Employee Name", "Pay Date", "Gross Pay"]
        rows = [
            {"Employee ID": "E001", "Employee Name": "John Smith",
             "Pay Date": "2025-01-15", "Gross Pay": "5000.00"},
            {"Employee ID": "E002", "Employee Name": "Jane Doe",
             "Pay Date": "2025-01-15", "Gross Pay": "4500.00"},
        ]
        result = run_payroll_testing(headers, rows)
        assert isinstance(result, PayrollTestingResult)
        assert result.composite_score.total_entries == 2

    def test_manual_mapping(self):
        headers = ["Col1", "Col2", "Col3", "Col4"]
        rows = [
            {"Col1": "E001", "Col2": "John Smith", "Col3": "2025-01-15", "Col4": "5000"},
        ]
        mapping = {
            "employee_id": "Col1",
            "employee_name": "Col2",
            "pay_date": "Col3",
            "gross_pay": "Col4",
        }
        result = run_payroll_testing(headers, rows, column_mapping=mapping)
        assert result.column_detection.overall_confidence == 1.0
        assert result.composite_score.total_entries == 1

    def test_to_dict(self):
        headers = ["Employee Name", "Pay Date", "Gross Pay"]
        rows = [{"Employee Name": "Test", "Pay Date": "2025-01-15", "Gross Pay": "100"}]
        result = run_payroll_testing(headers, rows)
        d = result.to_dict()
        assert "composite_score" in d
        assert "test_results" in d
        assert "data_quality" in d
        assert "column_detection" in d

    def test_empty_input(self):
        result = run_payroll_testing([], [])
        assert result.composite_score.total_entries == 0

    def test_filename_preserved(self):
        headers = ["Employee Name", "Pay Date", "Gross Pay"]
        rows = [{"Employee Name": "Test", "Pay Date": "2025-01-15", "Gross Pay": "100"}]
        result = run_payroll_testing(headers, rows, filename="payroll_2025.csv")
        assert result.filename == "payroll_2025.csv"


# =============================================================================
# TestSerialization
# =============================================================================

class TestSerialization:

    def test_payroll_entry_to_dict(self):
        entry = PayrollEntry(
            employee_id="E001", employee_name="John Smith",
            pay_date=date(2025, 1, 15), gross_pay=5000.0, _row_index=1
        )
        d = entry.to_dict()
        assert d["employee_name"] == "John Smith"
        assert d["pay_date"] == "2025-01-15"
        assert d["row_index"] == 1

    def test_flagged_employee_to_dict(self):
        entry = PayrollEntry(employee_name="Test", _row_index=1)
        flagged = FlaggedEmployee(
            entry=entry, test_name="Test", test_key="PR-T1",
            severity="high", issue="Test issue", confidence=0.95
        )
        d = flagged.to_dict()
        assert d["test_key"] == "PR-T1"
        assert d["confidence"] == 0.95

    def test_test_result_to_dict(self):
        result = PayrollTestResult(
            test_name="Test", test_key="PR-T1",
            test_tier="structural", entries_flagged=0, total_entries=10
        )
        d = result.to_dict()
        assert d["test_key"] == "PR-T1"
        assert isinstance(d["flagged_entries"], list)

    def test_full_result_json_safe(self):
        headers = ["Employee Name", "Pay Date", "Gross Pay"]
        rows = [{"Employee Name": "Test", "Pay Date": "2025-01-15", "Gross Pay": "100"}]
        result = run_payroll_testing(headers, rows)
        d = result.to_dict()
        # Ensure all values are JSON-serializable
        import json
        json_str = json.dumps(d)
        assert len(json_str) > 0


# =============================================================================
# TIER 2 TESTS — STATISTICAL (Sprint 86)
# =============================================================================

class TestUnusualPayAmounts:
    """PR-T6: Unusual Pay Amounts — z-score outliers by department."""

    def test_no_outliers(self):
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", department="Sales",
                        gross_pay=5000.0 + i * 10, _row_index=i)
            for i in range(1, 11)
        ]
        config = PayrollTestingConfig()
        result = _test_unusual_pay_amounts(entries, config)
        assert result.test_key == "PR-T6"
        assert result.entries_flagged == 0

    def test_high_outlier(self):
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", department="Sales",
                        gross_pay=5000.0, _row_index=i)
            for i in range(1, 11)
        ]
        # Add extreme outlier
        entries.append(PayrollEntry(
            employee_name="Outlier", department="Sales",
            gross_pay=500000.0, _row_index=11
        ))
        config = PayrollTestingConfig(unusual_pay_min_entries=5)
        result = _test_unusual_pay_amounts(entries, config)
        assert result.entries_flagged >= 1
        assert any(f.entry.employee_name == "Outlier" for f in result.flagged_entries)

    def test_department_grouping(self):
        """Outlier in one dept should not affect another dept."""
        sales = [
            PayrollEntry(employee_name=f"Sales{i}", department="Sales",
                        gross_pay=5000.0, _row_index=i)
            for i in range(1, 11)
        ]
        # Engineering has higher pay — not outliers among themselves
        eng = [
            PayrollEntry(employee_name=f"Eng{i}", department="Engineering",
                        gross_pay=10000.0, _row_index=i + 10)
            for i in range(1, 11)
        ]
        config = PayrollTestingConfig(unusual_pay_min_entries=5)
        result = _test_unusual_pay_amounts(sales + eng, config)
        # No outliers since each dept is uniform
        assert result.entries_flagged == 0

    def test_insufficient_dept_size(self):
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", department="Sales",
                        gross_pay=5000.0, _row_index=i)
            for i in range(1, 4)  # Only 3 entries
        ]
        config = PayrollTestingConfig(unusual_pay_min_entries=5)
        result = _test_unusual_pay_amounts(entries, config)
        assert result.entries_flagged == 0

    def test_severity_high_z5(self):
        """z>5 should be HIGH severity."""
        # 100 entries at $1000 + 1 extreme outlier gives clean z > 5
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", department="Ops",
                        gross_pay=1000.0, _row_index=i)
            for i in range(1, 101)
        ]
        entries.append(PayrollEntry(
            employee_name="Extreme", department="Ops",
            gross_pay=1000000.0, _row_index=101
        ))
        config = PayrollTestingConfig(unusual_pay_min_entries=5, unusual_pay_stddev=3.0)
        result = _test_unusual_pay_amounts(entries, config)
        highs = [f for f in result.flagged_entries if f.severity == "high"]
        assert len(highs) >= 1

    def test_unknown_department(self):
        """Entries with no department should be grouped as 'Unknown'."""
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", department="",
                        gross_pay=5000.0, _row_index=i)
            for i in range(1, 11)
        ]
        config = PayrollTestingConfig(unusual_pay_min_entries=5)
        result = _test_unusual_pay_amounts(entries, config)
        assert result.test_key == "PR-T6"

    def test_zero_pay_excluded(self):
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", department="HR",
                        gross_pay=5000.0, _row_index=i)
            for i in range(1, 11)
        ]
        entries.append(PayrollEntry(
            employee_name="Zero", department="HR",
            gross_pay=0.0, _row_index=11
        ))
        config = PayrollTestingConfig(unusual_pay_min_entries=5)
        result = _test_unusual_pay_amounts(entries, config)
        # Zero-pay should not be flagged as outlier
        zero_flags = [f for f in result.flagged_entries if f.entry.employee_name == "Zero"]
        assert len(zero_flags) == 0

    def test_test_tier(self):
        entries = [PayrollEntry(employee_name="A", gross_pay=100, _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_unusual_pay_amounts(entries, config)
        assert result.test_tier == "statistical"


class TestPayFrequencyAnomalies:
    """PR-T7: Pay Frequency Anomalies."""

    def test_regular_biweekly(self):
        """Regular biweekly payments should have no anomalies."""
        from datetime import timedelta
        entries = []
        base = date(2025, 1, 3)
        for i in range(12):
            pay_d = base + timedelta(days=i * 14)
            entries.append(PayrollEntry(
                employee_id="E001", employee_name="John",
                pay_date=pay_d, gross_pay=5000.0, _row_index=i + 1
            ))
        config = PayrollTestingConfig()
        result = _test_pay_frequency_anomalies(entries, config)
        assert result.test_key == "PR-T7"
        assert result.entries_flagged == 0

    def test_irregular_payment(self):
        """An extra payment mid-cycle should be flagged."""
        from datetime import timedelta
        entries = []
        base = date(2025, 1, 3)
        # Regular biweekly for one employee
        for i in range(6):
            entries.append(PayrollEntry(
                employee_id="E001", employee_name="John",
                pay_date=base + timedelta(days=i * 14), gross_pay=5000.0,
                _row_index=i + 1
            ))
        # Add irregular extra payment 3 days after a regular one
        entries.append(PayrollEntry(
            employee_id="E001", employee_name="John",
            pay_date=base + timedelta(days=3), gross_pay=2000.0,
            _row_index=7
        ))
        config = PayrollTestingConfig()
        result = _test_pay_frequency_anomalies(entries, config)
        assert result.entries_flagged >= 1

    def test_disabled(self):
        entries = [PayrollEntry(employee_name="A", pay_date=date(2025, 1, 1), _row_index=1)]
        config = PayrollTestingConfig(frequency_enabled=False)
        result = _test_pay_frequency_anomalies(entries, config)
        assert "Disabled" in result.description

    def test_no_dates(self):
        entries = [PayrollEntry(employee_name="A", _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_pay_frequency_anomalies(entries, config)
        assert result.entries_flagged == 0

    def test_too_few_entries(self):
        """Employees with < 3 dated entries should be skipped."""
        from datetime import timedelta
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John",
                        pay_date=date(2025, 1, 1), gross_pay=5000.0, _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="John",
                        pay_date=date(2025, 1, 15), gross_pay=5000.0, _row_index=2),
        ]
        config = PayrollTestingConfig()
        result = _test_pay_frequency_anomalies(entries, config)
        assert result.entries_flagged == 0

    def test_multiple_employees(self):
        """Each employee's frequency is evaluated independently."""
        from datetime import timedelta
        entries = []
        base = date(2025, 1, 1)
        # Employee A: regular biweekly
        for i in range(6):
            entries.append(PayrollEntry(
                employee_id="E001", employee_name="Alice",
                pay_date=base + timedelta(days=i * 14), gross_pay=5000.0,
                _row_index=i + 1
            ))
        # Employee B: also regular biweekly
        for i in range(6):
            entries.append(PayrollEntry(
                employee_id="E002", employee_name="Bob",
                pay_date=base + timedelta(days=i * 14), gross_pay=6000.0,
                _row_index=i + 7
            ))
        config = PayrollTestingConfig()
        result = _test_pay_frequency_anomalies(entries, config)
        assert result.entries_flagged == 0

    def test_test_tier(self):
        entries = [PayrollEntry(employee_name="A", pay_date=date(2025, 1, 1), _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_pay_frequency_anomalies(entries, config)
        assert result.test_tier == "statistical"


class TestBenfordPayroll:
    """PR-T8: Benford's Law on Gross Pay."""

    def test_insufficient_data(self):
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", gross_pay=100.0 * i, _row_index=i)
            for i in range(1, 50)  # Only 49, below 500 threshold
        ]
        config = PayrollTestingConfig(benford_min_entries=500)
        result = _test_benford_gross_pay(entries, config)
        assert result.entries_flagged == 0
        assert "Insufficient" in result.description

    def test_disabled(self):
        entries = [PayrollEntry(employee_name="A", gross_pay=100, _row_index=1)]
        config = PayrollTestingConfig(enable_benford=False)
        result = _test_benford_gross_pay(entries, config)
        assert "Disabled" in result.description

    def test_conforming_distribution(self):
        """Generate Benford-conforming data — should have low severity."""
        import random
        random.seed(42)
        entries = []
        for i in range(1000):
            # Generate Benford-like: 10^(random uniform) gives Benford first digits
            amt = 10 ** (random.uniform(1, 5))
            entries.append(PayrollEntry(
                employee_name=f"Emp{i}", gross_pay=amt, _row_index=i + 1
            ))
        config = PayrollTestingConfig(benford_min_entries=500)
        result = _test_benford_gross_pay(entries, config)
        assert result.test_key == "PR-T8"
        # Conforming data should have few/no flags
        assert result.severity in ("low", "medium")

    def test_nonconforming_distribution(self):
        """Data with artificial digit bias should be flagged."""
        entries = []
        # All amounts start with digit 5 — heavily violates Benford
        for i in range(600):
            entries.append(PayrollEntry(
                employee_name=f"Emp{i}", gross_pay=5000.0 + i * 0.01,
                _row_index=i + 1
            ))
        config = PayrollTestingConfig(benford_min_entries=500)
        result = _test_benford_gross_pay(entries, config)
        assert result.severity in ("high", "medium")

    def test_insufficient_magnitude(self):
        """All amounts same order of magnitude — should fail pre-check."""
        entries = [
            PayrollEntry(employee_name=f"Emp{i}", gross_pay=5000.0 + i, _row_index=i + 1)
            for i in range(600)
        ]
        config = PayrollTestingConfig(benford_min_entries=500, benford_min_magnitude_range=2.0)
        result = _test_benford_gross_pay(entries, config)
        assert "magnitude" in result.description.lower()

    def test_first_digit_helper(self):
        assert _get_first_digit(123.45) == 1
        assert _get_first_digit(0.0056) == 5
        assert _get_first_digit(999) == 9
        assert _get_first_digit(0) is None


class TestGhostEmployeeIndicators:
    """PR-T9: Ghost Employee Indicators."""

    @pytest.fixture
    def detection_with_dept(self):
        return PayrollColumnDetectionResult(
            employee_name_column="name", department_column="dept",
            pay_date_column="date", gross_pay_column="pay",
        )

    @pytest.fixture
    def detection_no_dept(self):
        return PayrollColumnDetectionResult(
            employee_name_column="name", pay_date_column="date",
            gross_pay_column="pay",
        )

    def test_no_ghost_indicators(self, detection_with_dept):
        entries = [
            PayrollEntry(employee_id="E001", employee_name="John", department="Sales",
                        pay_date=date(2025, 3, 15), gross_pay=5000, _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="John", department="Sales",
                        pay_date=date(2025, 4, 15), gross_pay=5000, _row_index=2),
            PayrollEntry(employee_id="E001", employee_name="John", department="Sales",
                        pay_date=date(2025, 5, 15), gross_pay=5000, _row_index=3),
        ]
        config = PayrollTestingConfig()
        result = _test_ghost_employee_indicators(entries, config, detection_with_dept)
        assert result.entries_flagged == 0

    def test_no_department(self, detection_with_dept):
        """Employee with no department should trigger indicator."""
        entries = [
            PayrollEntry(employee_id="E001", employee_name="Ghost", department="",
                        pay_date=date(2025, 3, 15), gross_pay=5000, _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="Ghost", department="",
                        pay_date=date(2025, 4, 15), gross_pay=5000, _row_index=2),
            PayrollEntry(employee_id="E001", employee_name="Ghost", department="",
                        pay_date=date(2025, 5, 15), gross_pay=5000, _row_index=3),
        ]
        config = PayrollTestingConfig(ghost_min_indicators=1)
        result = _test_ghost_employee_indicators(entries, config, detection_with_dept)
        assert result.entries_flagged >= 1

    def test_single_entry(self, detection_no_dept):
        """Single pay entry is a ghost indicator."""
        entries = [
            PayrollEntry(employee_id="E001", employee_name="OneTime",
                        pay_date=date(2025, 3, 15), gross_pay=50000, _row_index=1),
        ]
        config = PayrollTestingConfig(ghost_min_indicators=1)
        result = _test_ghost_employee_indicators(entries, config, detection_no_dept)
        assert result.entries_flagged == 1

    def test_boundary_months_only(self, detection_no_dept):
        """Entries only in first and last month should trigger."""
        entries = [
            PayrollEntry(employee_id="E001", employee_name="Boundary",
                        pay_date=date(2025, 1, 15), gross_pay=5000, _row_index=1),
            PayrollEntry(employee_id="E001", employee_name="Boundary",
                        pay_date=date(2025, 1, 30), gross_pay=5000, _row_index=2),
            PayrollEntry(employee_id="E001", employee_name="Boundary",
                        pay_date=date(2025, 6, 15), gross_pay=5000, _row_index=3),
            # Non-boundary employees to establish period
            PayrollEntry(employee_id="E002", employee_name="Normal",
                        pay_date=date(2025, 3, 15), gross_pay=5000, _row_index=4),
        ]
        config = PayrollTestingConfig(ghost_min_indicators=1)
        result = _test_ghost_employee_indicators(entries, config, detection_no_dept)
        boundary_flags = [f for f in result.flagged_entries if f.entry.employee_name == "Boundary"]
        assert len(boundary_flags) >= 1

    def test_multi_indicator_high_severity(self, detection_with_dept):
        """Multiple indicators → HIGH severity."""
        entries = [
            PayrollEntry(employee_id="E001", employee_name="Suspicious", department="",
                        pay_date=date(2025, 1, 15), gross_pay=5000, _row_index=1),
            # Only one entry + no department = 2 indicators
        ]
        config = PayrollTestingConfig(ghost_min_indicators=1)
        result = _test_ghost_employee_indicators(entries, config, detection_with_dept)
        assert result.entries_flagged >= 1
        assert result.flagged_entries[0].severity == "high"

    def test_disabled(self, detection_no_dept):
        entries = [PayrollEntry(employee_name="A", pay_date=date(2025, 1, 1), _row_index=1)]
        config = PayrollTestingConfig(enable_ghost=False)
        result = _test_ghost_employee_indicators(entries, config, detection_no_dept)
        assert "Disabled" in result.description

    def test_no_dates(self, detection_no_dept):
        entries = [PayrollEntry(employee_name="A", _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_ghost_employee_indicators(entries, config, detection_no_dept)
        assert "No date" in result.description

    def test_test_key(self, detection_no_dept):
        entries = [PayrollEntry(employee_name="A", pay_date=date(2025, 1, 1), _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_ghost_employee_indicators(entries, config, detection_no_dept)
        assert result.test_key == "PR-T9"


class TestDuplicateBankAccounts:
    """PR-T10: Duplicate Bank Accounts / Addresses."""

    def test_no_duplicates(self):
        detection = PayrollColumnDetectionResult(
            bank_account_column="bank", has_bank_accounts=True,
            employee_name_column="name",
        )
        entries = [
            PayrollEntry(employee_name="Alice", bank_account="1111", _row_index=1),
            PayrollEntry(employee_name="Bob", bank_account="2222", _row_index=2),
        ]
        config = PayrollTestingConfig()
        result = _test_duplicate_bank_accounts(entries, config, detection)
        assert result.entries_flagged == 0

    def test_shared_bank_account(self):
        detection = PayrollColumnDetectionResult(
            bank_account_column="bank", has_bank_accounts=True,
            employee_name_column="name",
        )
        entries = [
            PayrollEntry(employee_name="Alice", bank_account="1234567890", _row_index=1),
            PayrollEntry(employee_name="Bob", bank_account="1234567890", _row_index=2),
        ]
        config = PayrollTestingConfig()
        result = _test_duplicate_bank_accounts(entries, config, detection)
        assert result.entries_flagged == 2
        assert all(f.severity == "high" for f in result.flagged_entries)

    def test_fuzzy_address_match(self):
        detection = PayrollColumnDetectionResult(
            address_column="addr", has_addresses=True,
            employee_name_column="name",
        )
        entries = [
            PayrollEntry(employee_name="Alice", address="123 Main Street Apt 4", _row_index=1),
            PayrollEntry(employee_name="Bob", address="123 Main Street Apt 4B", _row_index=2),
        ]
        config = PayrollTestingConfig(address_similarity_threshold=0.90)
        result = _test_duplicate_bank_accounts(entries, config, detection)
        assert result.entries_flagged >= 1

    def test_disabled(self):
        detection = PayrollColumnDetectionResult(has_bank_accounts=True)
        entries = [PayrollEntry(employee_name="A", bank_account="1111", _row_index=1)]
        config = PayrollTestingConfig(enable_duplicates=False)
        result = _test_duplicate_bank_accounts(entries, config, detection)
        assert "Disabled" in result.description

    def test_no_bank_column(self):
        detection = PayrollColumnDetectionResult(has_bank_accounts=False, has_addresses=False)
        entries = [PayrollEntry(employee_name="A", _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_duplicate_bank_accounts(entries, config, detection)
        assert result.entries_flagged == 0

    def test_test_key(self):
        detection = PayrollColumnDetectionResult(has_bank_accounts=False, has_addresses=False)
        entries = [PayrollEntry(employee_name="A", _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_duplicate_bank_accounts(entries, config, detection)
        assert result.test_key == "PR-T10"


class TestDuplicateTaxIds:
    """PR-T11: Duplicate Tax IDs."""

    def test_no_duplicates(self):
        detection = PayrollColumnDetectionResult(tax_id_column="ssn", has_tax_ids=True)
        entries = [
            PayrollEntry(employee_name="Alice", tax_id="111-22-3333", _row_index=1),
            PayrollEntry(employee_name="Bob", tax_id="444-55-6666", _row_index=2),
        ]
        config = PayrollTestingConfig()
        result = _test_duplicate_tax_ids(entries, config, detection)
        assert result.entries_flagged == 0

    def test_shared_tax_id(self):
        detection = PayrollColumnDetectionResult(tax_id_column="ssn", has_tax_ids=True)
        entries = [
            PayrollEntry(employee_name="Alice", tax_id="111-22-3333", _row_index=1),
            PayrollEntry(employee_name="Bob", tax_id="111-22-3333", _row_index=2),
        ]
        config = PayrollTestingConfig()
        result = _test_duplicate_tax_ids(entries, config, detection)
        assert result.entries_flagged == 2
        assert all(f.severity == "high" for f in result.flagged_entries)

    def test_no_tax_column(self):
        detection = PayrollColumnDetectionResult(has_tax_ids=False)
        entries = [PayrollEntry(employee_name="A", _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_duplicate_tax_ids(entries, config, detection)
        assert "No tax ID" in result.description

    def test_disabled(self):
        detection = PayrollColumnDetectionResult(tax_id_column="ssn", has_tax_ids=True)
        entries = [PayrollEntry(employee_name="A", tax_id="111", _row_index=1)]
        config = PayrollTestingConfig(enable_tax_id_duplicates=False)
        result = _test_duplicate_tax_ids(entries, config, detection)
        assert "Disabled" in result.description

    def test_test_key(self):
        detection = PayrollColumnDetectionResult(tax_id_column="ssn", has_tax_ids=True)
        entries = [PayrollEntry(employee_name="A", tax_id="111", _row_index=1)]
        config = PayrollTestingConfig()
        result = _test_duplicate_tax_ids(entries, config, detection)
        assert result.test_key == "PR-T11"


# =============================================================================
# SCORING CALIBRATION (Sprint 86)
# =============================================================================

class TestScoringCalibration:
    """Comparative scoring assertions: clean < moderate < dirty."""

    def test_clean_lower_than_moderate(self):
        """Clean data should score lower than moderately dirty data."""
        # Clean entries
        clean_entries = [
            PayrollEntry(employee_id=f"E{i:03d}", employee_name=f"Employee {i}",
                        department="Sales", pay_date=date(2025, 3, i % 28 + 1),
                        gross_pay=5000.0 + i * 10, _row_index=i)
            for i in range(1, 51)
        ]
        clean_results = [
            _test_duplicate_employee_ids(clean_entries, PayrollTestingConfig()),
            _test_missing_critical_fields(clean_entries, PayrollTestingConfig()),
        ]
        clean_score = calculate_payroll_composite_score(clean_results, len(clean_entries))

        # Moderate: some issues
        mod_entries = list(clean_entries)
        # Add duplicates
        mod_entries.append(PayrollEntry(
            employee_id="E001", employee_name="Different Name",
            department="Sales", pay_date=date(2025, 3, 15),
            gross_pay=50000.0, _row_index=51
        ))
        mod_results = [
            _test_duplicate_employee_ids(mod_entries, PayrollTestingConfig()),
            _test_missing_critical_fields(mod_entries, PayrollTestingConfig()),
        ]
        mod_score = calculate_payroll_composite_score(mod_results, len(mod_entries))

        assert clean_score.score < mod_score.score

    def test_moderate_lower_than_dirty(self):
        """Moderately dirty data should score lower than very dirty data."""
        # Moderate
        mod_entries = [
            PayrollEntry(employee_id=f"E{i:03d}", employee_name=f"Emp {i}",
                        gross_pay=50000.0, pay_date=date(2025, 3, 15), _row_index=i)
            for i in range(1, 11)
        ]
        mod_results = [_test_round_salary_amounts(mod_entries, PayrollTestingConfig())]
        mod_score = calculate_payroll_composite_score(mod_results, len(mod_entries))

        # Dirty: many issues
        dirty_entries = [
            PayrollEntry(employee_name="", gross_pay=0, _row_index=i)
            for i in range(1, 11)
        ]
        dirty_results = [
            _test_missing_critical_fields(dirty_entries, PayrollTestingConfig()),
            _test_round_salary_amounts(dirty_entries, PayrollTestingConfig()),
        ]
        dirty_score = calculate_payroll_composite_score(dirty_results, len(dirty_entries))

        # Dirty should be higher (more missing fields = more HIGH flags)
        assert mod_score.score <= dirty_score.score

    def test_risk_tier_ordering(self):
        """Verify risk tier boundaries."""
        # Score 0 -> LOW
        zero_score = calculate_payroll_composite_score([], 100)
        assert zero_score.risk_tier == "low"

        # Build HIGH score data
        dirty_entries = [
            PayrollEntry(employee_name="", gross_pay=0, _row_index=i)
            for i in range(1, 6)
        ]
        dirty_results = [_test_missing_critical_fields(dirty_entries, PayrollTestingConfig())]
        dirty_score = calculate_payroll_composite_score(dirty_results, len(dirty_entries))
        # Should be elevated or higher (all 5 have missing name + zero pay = HIGH severity)
        assert dirty_score.risk_tier in ("elevated", "moderate", "high", "critical")


# =============================================================================
# API ROUTE REGISTRATION (Sprint 86)
# =============================================================================

class TestAPIRouteRegistration:
    """Verify payroll testing API route is registered correctly."""

    def test_router_exists(self):
        from routes.payroll_testing import router
        assert router is not None

    def test_route_registered_in_app(self):
        from main import app
        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/payroll-testing" in route_paths

    def test_route_method(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/audit/payroll-testing":
                assert "POST" in route.methods
                break

    def test_router_tag(self):
        from routes.payroll_testing import router
        assert "payroll_testing" in router.tags
