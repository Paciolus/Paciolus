"""
Tests for Payroll & Employee Testing Engine — Tier 2 Statistical Tests.

Covers:
- PR-T6: Unusual Pay Amounts (z-score outliers by department)
- PR-T7: Pay Frequency Anomalies
- PR-T8: Benford's Law on Gross Pay

Split from test_payroll_testing.py.
"""

import pytest
from datetime import date, timedelta

from payroll_testing_engine import (
    # Config
    PayrollTestingConfig,
    # Data models
    PayrollEntry,
    # Tier 2 Tests
    _test_unusual_pay_amounts,
    _test_pay_frequency_anomalies,
    _test_benford_gross_pay,
    _get_first_digit,
)


# =============================================================================
# TestUnusualPayAmounts (PR-T6)
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


# =============================================================================
# TestPayFrequencyAnomalies (PR-T7)
# =============================================================================

class TestPayFrequencyAnomalies:
    """PR-T7: Pay Frequency Anomalies."""

    def test_regular_biweekly(self):
        """Regular biweekly payments should have no anomalies."""
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


# =============================================================================
# TestBenfordPayroll (PR-T8)
# =============================================================================

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
