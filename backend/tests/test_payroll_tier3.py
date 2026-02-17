"""
Tests for Payroll & Employee Testing Engine — Tier 3 Advanced Tests,
Scoring Calibration, and API Route Registration.

Covers:
- PR-T9: Ghost Employee Indicators
- PR-T10: Duplicate Bank Accounts / Addresses
- PR-T11: Duplicate Tax IDs
- Scoring calibration (comparative assertions)
- API route registration

Split from test_payroll_testing.py.
"""

from datetime import date

import pytest

from payroll_testing_engine import (
    # Column detection
    PayrollColumnDetectionResult,
    # Data models
    PayrollEntry,
    # Config
    PayrollTestingConfig,
    # Enums
    _test_duplicate_bank_accounts,
    # Tier 1 Tests (used in scoring calibration)
    _test_duplicate_employee_ids,
    _test_duplicate_tax_ids,
    # Tier 3 Tests
    _test_ghost_employee_indicators,
    _test_missing_critical_fields,
    _test_round_salary_amounts,
    # Scoring
    calculate_payroll_composite_score,
)

# =============================================================================
# TestGhostEmployeeIndicators (PR-T9)
# =============================================================================

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
        """Multiple indicators -> HIGH severity."""
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


# =============================================================================
# TestDuplicateBankAccounts (PR-T10)
# =============================================================================

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


# =============================================================================
# TestDuplicateTaxIds (PR-T11)
# =============================================================================

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
