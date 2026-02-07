"""
Tests for Payroll & Employee Testing Engine.
Sprint 85: Payroll Testing — Backend Foundation + Tier 1

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
- Composite scoring (7 tests)
- Battery orchestration (3 tests)
- Full pipeline (5 tests)
- Serialization (4 tests)
"""

import pytest
from datetime import date

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
    # Tests
    _test_duplicate_employee_ids,
    _test_missing_critical_fields,
    _test_round_salary_amounts,
    _test_pay_after_termination,
    _test_check_number_gaps,
    # Battery & scoring
    run_payroll_test_battery,
    calculate_payroll_composite_score,
    # Main entry
    run_payroll_testing,
    # Helpers
    _safe_str, _safe_float, _parse_date,
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

    def test_safe_str_none(self):
        assert _safe_str(None) == ""

    def test_safe_str_value(self):
        assert _safe_str("  hello  ") == "hello"

    def test_safe_float_none(self):
        assert _safe_float(None) == 0.0

    def test_safe_float_currency(self):
        assert _safe_float("$1,234.56") == 1234.56

    def test_safe_float_parenthetical(self):
        assert _safe_float("(500.00)") == -500.0

    def test_parse_date_formats(self):
        assert _parse_date("2025-01-15") == date(2025, 1, 15)
        assert _parse_date("01/15/2025") == date(2025, 1, 15)
        assert _parse_date(None) is None
        assert _parse_date("") is None
        assert _parse_date("invalid") is None


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

    def test_clean_low_score(self, sample_entries, default_config, standard_detection):
        results = run_payroll_test_battery(sample_entries, default_config, standard_detection)
        score = calculate_payroll_composite_score(results, len(sample_entries))
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
