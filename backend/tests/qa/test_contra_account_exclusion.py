"""
Regression tests for contra account sign anomaly exclusion (NEW-009).

Verifies that standard contra accounts are NOT flagged as sign anomalies,
while genuinely anomalous accounts are still caught.
"""

import pytest

from classification_validator import (
    CONTRA_ACCOUNT_PATTERNS,
    _is_contra_account,
    check_sign_anomalies,
)


class TestContraAccountDetection:
    """Test the _is_contra_account helper."""

    @pytest.mark.parametrize(
        "name",
        [
            "Allowance for Doubtful Accounts",
            "1200 - Accumulated Depreciation - Equipment",
            "Accum Depr - Buildings",
            "Accum. Depr. - Vehicles",
            "Inventory Reserve",
            "Treasury Stock",
            "Sales Returns and Allowances",
            "4900 - Sales Discounts",
            "Bond Discount",
            "ACCUMULATED AMORTIZATION - Patents",
        ],
    )
    def test_recognizes_contra_accounts(self, name: str):
        assert _is_contra_account(name) is True

    @pytest.mark.parametrize(
        "name",
        [
            "1000 - Cash",
            "2000 - Accounts Payable",
            "4000 - Sales Revenue",
            "5000 - Cost of Goods Sold",
            "Depreciation Expense",
            "Bad Debt Expense",
        ],
    )
    def test_non_contra_accounts_not_matched(self, name: str):
        assert _is_contra_account(name) is False


class TestSignAnomalyContraExclusion:
    """Test that check_sign_anomalies skips contra accounts."""

    def test_contra_accounts_not_flagged(self):
        """Standard contra accounts should produce zero sign_anomaly findings."""
        accounts = {
            "Allowance for Doubtful Accounts": {"debit": 0.0, "credit": 5000.0},
            "Accumulated Depreciation - Equipment": {"debit": 0.0, "credit": 120000.0},
            "Inventory Reserve": {"debit": 0.0, "credit": 3000.0},
            "Treasury Stock": {"debit": 50000.0, "credit": 0.0},
            "Sales Returns and Discounts": {"debit": 8000.0, "credit": 0.0},
        }
        classifications = {
            "Allowance for Doubtful Accounts": "asset",
            "Accumulated Depreciation - Equipment": "asset",
            "Inventory Reserve": "asset",
            "Treasury Stock": "equity",
            "Sales Returns and Discounts": "revenue",
        }

        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 0

    def test_genuine_anomaly_still_flagged(self):
        """A real anomalous balance (not a contra) should still be flagged."""
        accounts = {
            "4000 - Sales Revenue": {"debit": 100000.0, "credit": 0.0},
        }
        classifications = {
            "4000 - Sales Revenue": "revenue",
        }

        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 1
        assert issues[0].issue_type.value == "sign_anomaly"

    def test_mixed_contra_and_genuine(self):
        """Contra accounts skipped, genuine anomalies caught."""
        accounts = {
            "Accumulated Depreciation": {"debit": 0.0, "credit": 50000.0},
            "1500 - Prepaid Insurance": {"debit": 0.0, "credit": 2000.0},
        }
        classifications = {
            "Accumulated Depreciation": "asset",
            "1500 - Prepaid Insurance": "asset",
        }

        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 1
        assert issues[0].account_name == "1500 - Prepaid Insurance"

    def test_case_insensitive_matching(self):
        """Contra detection should be case-insensitive."""
        accounts = {
            "ACCUMULATED DEPRECIATION - MACHINERY": {"debit": 0.0, "credit": 80000.0},
            "allowance for doubtful accounts": {"debit": 0.0, "credit": 10000.0},
        }
        classifications = {
            "ACCUMULATED DEPRECIATION - MACHINERY": "asset",
            "allowance for doubtful accounts": "asset",
        }

        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 0


def test_contra_patterns_not_empty():
    """Sanity check: the patterns tuple should have entries."""
    assert len(CONTRA_ACCOUNT_PATTERNS) >= 20
