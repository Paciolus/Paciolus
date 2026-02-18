"""
Tests for Sprint 288: Cross-Tool Account Convergence Index.

Covers:
- Account extractors (per-tool)
- Convergence aggregation logic
- ToolRun flagged_accounts column storage
- Route registration
"""

import json

import pytest

from shared.account_extractors import (
    ACCOUNT_EXTRACTORS,
    extract_ap_accounts,
    extract_ar_aging_accounts,
    extract_je_accounts,
    extract_multi_period_accounts,
    extract_revenue_accounts,
    extract_tb_accounts,
)


# ---------------------------------------------------------------------------
# TestAccountExtractors
# ---------------------------------------------------------------------------


class TestExtractTbAccounts:
    """Extract from TB Diagnostics abnormal_balances."""

    def test_empty_result(self):
        assert extract_tb_accounts({}) == []

    def test_empty_abnormal_balances(self):
        assert extract_tb_accounts({"abnormal_balances": []}) == []

    def test_single_account(self):
        result = {"abnormal_balances": [{"account": "Cash", "amount": 100}]}
        assert extract_tb_accounts(result) == ["Cash"]

    def test_multiple_accounts_deduped_sorted(self):
        result = {
            "abnormal_balances": [
                {"account": "Rent Expense"},
                {"account": "Cash"},
                {"account": "Rent Expense"},
                {"account": "Accounts Receivable"},
            ]
        }
        assert extract_tb_accounts(result) == [
            "Accounts Receivable",
            "Cash",
            "Rent Expense",
        ]

    def test_missing_account_field(self):
        result = {"abnormal_balances": [{"issue": "something", "amount": 100}]}
        assert extract_tb_accounts(result) == []

    def test_blank_account_filtered(self):
        result = {"abnormal_balances": [{"account": ""}, {"account": "  "}, {"account": "Cash"}]}
        assert extract_tb_accounts(result) == ["Cash"]


class TestExtractMultiPeriodAccounts:
    """Extract from Multi-Period significant_movements."""

    def test_empty_result(self):
        assert extract_multi_period_accounts({}) == []

    def test_filters_by_significance(self):
        result = {
            "significant_movements": [
                {"account_name": "Cash", "significance": "material"},
                {"account_name": "Petty Cash", "significance": "minor"},
                {"account_name": "AR", "significance": "significant"},
            ]
        }
        accounts = extract_multi_period_accounts(result)
        assert accounts == ["AR", "Cash"]

    def test_uses_account_fallback(self):
        result = {
            "significant_movements": [
                {"account": "Cash", "significance": "material"},
            ]
        }
        assert extract_multi_period_accounts(result) == ["Cash"]

    def test_deduplication(self):
        result = {
            "significant_movements": [
                {"account_name": "Cash", "significance": "material"},
                {"account_name": "Cash", "significance": "significant"},
            ]
        }
        assert extract_multi_period_accounts(result) == ["Cash"]


class TestExtractJeAccounts:
    """Extract from JE Testing test_results."""

    def test_empty_result(self):
        assert extract_je_accounts({}) == []

    def test_single_flagged_entry(self):
        result = {
            "test_results": [
                {
                    "flagged_entries": [
                        {"entry": {"account": "Office Supplies"}}
                    ]
                }
            ]
        }
        assert extract_je_accounts(result) == ["Office Supplies"]

    def test_multiple_tests_deduped(self):
        result = {
            "test_results": [
                {
                    "flagged_entries": [
                        {"entry": {"account": "Cash"}},
                        {"entry": {"account": "Revenue"}},
                    ]
                },
                {
                    "flagged_entries": [
                        {"entry": {"account": "Cash"}},
                    ]
                },
            ]
        }
        assert extract_je_accounts(result) == ["Cash", "Revenue"]

    def test_missing_entry_key(self):
        result = {
            "test_results": [
                {"flagged_entries": [{"issue": "bad"}]}
            ]
        }
        assert extract_je_accounts(result) == []


class TestExtractApAccounts:
    """Extract from AP Testing (gl_account field)."""

    def test_empty_result(self):
        assert extract_ap_accounts({}) == []

    def test_gl_account_extraction(self):
        result = {
            "test_results": [
                {
                    "flagged_entries": [
                        {"entry": {"gl_account": "6100 - Office Supplies"}},
                        {"entry": {"gl_account": "6200 - Travel"}},
                    ]
                }
            ]
        }
        assert extract_ap_accounts(result) == [
            "6100 - Office Supplies",
            "6200 - Travel",
        ]


class TestExtractRevenueAccounts:
    """Extract from Revenue Testing (account_name field)."""

    def test_empty_result(self):
        assert extract_revenue_accounts({}) == []

    def test_account_name_extraction(self):
        result = {
            "test_results": [
                {
                    "flagged_entries": [
                        {"entry": {"account_name": "Sales Revenue"}},
                        {"entry": {"account_name": "Service Revenue"}},
                    ]
                }
            ]
        }
        assert extract_revenue_accounts(result) == [
            "Sales Revenue",
            "Service Revenue",
        ]


class TestExtractArAgingAccounts:
    """Extract from AR Aging (account_name field)."""

    def test_empty_result(self):
        assert extract_ar_aging_accounts({}) == []

    def test_account_name_extraction(self):
        result = {
            "test_results": [
                {
                    "flagged_entries": [
                        {"entry": {"account_name": "AR - Trade"}},
                    ]
                }
            ]
        }
        assert extract_ar_aging_accounts(result) == ["AR - Trade"]


class TestAccountExtractorRegistry:
    """Verify ACCOUNT_EXTRACTORS registry."""

    def test_registry_has_expected_tools(self):
        expected = {
            "trial_balance",
            "multi_period",
            "journal_entry_testing",
            "ap_testing",
            "revenue_testing",
            "ar_aging",
        }
        assert set(ACCOUNT_EXTRACTORS.keys()) == expected

    def test_all_extractors_callable(self):
        for name, func in ACCOUNT_EXTRACTORS.items():
            assert callable(func), f"{name} extractor is not callable"
            # Should handle empty dicts without error
            assert isinstance(func({}), list)


# ---------------------------------------------------------------------------
# TestToolRunFlaggedAccounts — model column + to_dict
# ---------------------------------------------------------------------------


class TestToolRunFlaggedAccounts:
    """Test ToolRun.flagged_accounts column and to_dict parsing."""

    def test_toolrun_to_dict_with_flagged_accounts(self):
        from engagement_model import ToolName, ToolRun, ToolRunStatus

        run = ToolRun(
            id=1,
            engagement_id=10,
            tool_name=ToolName.TRIAL_BALANCE,
            run_number=1,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=json.dumps(["Cash", "Rent"]),
        )
        d = run.to_dict()
        assert d["flagged_accounts"] == ["Cash", "Rent"]

    def test_toolrun_to_dict_without_flagged_accounts(self):
        from engagement_model import ToolName, ToolRun, ToolRunStatus

        run = ToolRun(
            id=2,
            engagement_id=10,
            tool_name=ToolName.AP_TESTING,
            run_number=1,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=None,
        )
        d = run.to_dict()
        assert d["flagged_accounts"] == []


# ---------------------------------------------------------------------------
# TestConvergenceAggregation — EngagementManager.get_convergence_index
# ---------------------------------------------------------------------------


class TestConvergenceAggregation:
    """Test convergence index aggregation logic.

    Uses in-memory SQLite via conftest.py fixtures.
    """

    @pytest.fixture()
    def setup_engagement(self, db_session):
        """Create a user, client, and engagement for testing."""
        from datetime import UTC, datetime

        from engagement_manager import EngagementManager
        from models import Client, User

        user = User(
            email="convergence@test.com",
            hashed_password="hashed",
            name="Test User",
        )
        db_session.add(user)
        db_session.flush()

        client = Client(
            user_id=user.id,
            name="Test Client",
        )
        db_session.add(client)
        db_session.flush()

        manager = EngagementManager(db_session)
        engagement = manager.create_engagement(
            user_id=user.id,
            client_id=client.id,
            period_start=datetime(2025, 1, 1, tzinfo=UTC),
            period_end=datetime(2025, 12, 31, tzinfo=UTC),
        )

        return manager, engagement, user

    def test_no_runs_returns_empty(self, setup_engagement):
        manager, engagement, _ = setup_engagement
        result = manager.get_convergence_index(engagement.id)
        assert result == []

    def test_single_tool_single_account(self, setup_engagement):
        from engagement_model import ToolName, ToolRunStatus

        manager, engagement, _ = setup_engagement
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Cash"],
        )

        result = manager.get_convergence_index(engagement.id)
        assert len(result) == 1
        assert result[0]["account"] == "Cash"
        assert result[0]["convergence_count"] == 1
        assert result[0]["tools_flagging_it"] == ["trial_balance"]

    def test_multi_tool_convergence(self, setup_engagement):
        from engagement_model import ToolName, ToolRunStatus

        manager, engagement, _ = setup_engagement
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Cash", "Rent Expense"],
        )
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.JOURNAL_ENTRY_TESTING,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Cash", "Office Supplies"],
        )
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.REVENUE_TESTING,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Cash", "Sales Revenue"],
        )

        result = manager.get_convergence_index(engagement.id)

        # Cash should be first with count=3
        assert result[0]["account"] == "Cash"
        assert result[0]["convergence_count"] == 3
        assert set(result[0]["tools_flagging_it"]) == {
            "trial_balance",
            "journal_entry_testing",
            "revenue_testing",
        }

        # Others have count=1, sorted alphabetically
        names = [r["account"] for r in result if r["convergence_count"] == 1]
        assert names == ["Office Supplies", "Rent Expense", "Sales Revenue"]

    def test_latest_run_only(self, setup_engagement):
        """Only the latest completed run per tool should be used."""
        from engagement_model import ToolName, ToolRunStatus

        manager, engagement, _ = setup_engagement

        # First run: flagging Cash
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Cash"],
        )

        # Second run (latest): flagging Rent only
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Rent Expense"],
        )

        result = manager.get_convergence_index(engagement.id)
        accounts = [r["account"] for r in result]
        assert "Rent Expense" in accounts
        assert "Cash" not in accounts  # From older run

    def test_failed_run_excluded(self, setup_engagement):
        """Failed runs should be excluded from convergence."""
        from engagement_model import ToolName, ToolRunStatus

        manager, engagement, _ = setup_engagement
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.FAILED,
            flagged_accounts=["Cash"],
        )

        result = manager.get_convergence_index(engagement.id)
        assert result == []

    def test_null_flagged_accounts_excluded(self, setup_engagement):
        """Runs without flagged_accounts should be excluded."""
        from engagement_model import ToolName, ToolRunStatus

        manager, engagement, _ = setup_engagement
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.BANK_RECONCILIATION,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=None,
        )

        result = manager.get_convergence_index(engagement.id)
        assert result == []

    def test_sort_order(self, setup_engagement):
        """Results sorted by convergence_count desc, then account name asc."""
        from engagement_model import ToolName, ToolRunStatus

        manager, engagement, _ = setup_engagement
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.TRIAL_BALANCE,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Zebra Account", "Alpha Account"],
        )
        manager.record_tool_run(
            engagement_id=engagement.id,
            tool_name=ToolName.JOURNAL_ENTRY_TESTING,
            status=ToolRunStatus.COMPLETED,
            flagged_accounts=["Zebra Account"],
        )

        result = manager.get_convergence_index(engagement.id)
        assert len(result) == 2
        assert result[0]["account"] == "Zebra Account"
        assert result[0]["convergence_count"] == 2
        assert result[1]["account"] == "Alpha Account"
        assert result[1]["convergence_count"] == 1


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


class TestConvergenceRouteRegistration:
    """Verify convergence endpoints are registered."""

    def test_convergence_get_endpoint_registered(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/convergence" in paths

    def test_convergence_csv_export_endpoint_registered(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/export/convergence-csv" in paths
