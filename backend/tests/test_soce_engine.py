"""Sprint 638 — Statement of Changes in Equity tests."""

from financial_statement_builder import (
    EquityActivity,
    FinancialStatementBuilder,
    StatementOfChangesInEquity,
)


def _grouping_with_equity(
    current_accounts: list[dict],
    include_income: bool = False,
) -> dict:
    """Build the minimum lead-sheet grouping dict the builder needs."""
    # Balance sheet: assets (A) offset by equity (K) so the books balance.
    total_equity = sum(-(a.get("net_balance", 0.0)) for a in current_accounts)
    summaries = [
        {"lead_sheet": "A", "net_balance": total_equity, "accounts": [{"name": "Cash", "net_balance": total_equity}]},
        {"lead_sheet": "K", "net_balance": -total_equity, "accounts": current_accounts},
    ]
    if include_income:
        # Credit-normal revenue lead sheet
        summaries.append({"lead_sheet": "L", "net_balance": -1000.0, "accounts": [{"name": "Revenue"}]})
        summaries.append({"lead_sheet": "M", "net_balance": 400.0, "accounts": [{"name": "COGS"}]})
        summaries.append({"lead_sheet": "N", "net_balance": 200.0, "accounts": [{"name": "Opex"}]})
    return {"summaries": summaries}


class TestSOCEBasics:
    def test_soce_produced_alongside_bs_is_cf(self):
        grouping = _grouping_with_equity(
            [
                {"name": "Common Stock", "net_balance": -1000.0},
                {"name": "Retained Earnings", "net_balance": -500.0},
            ]
        )
        stmts = FinancialStatementBuilder(grouping).build()
        assert stmts.statement_of_changes_in_equity is not None
        assert isinstance(stmts.statement_of_changes_in_equity, StatementOfChangesInEquity)

    def test_components_classified_by_keyword(self):
        grouping = _grouping_with_equity(
            [
                {"name": "Common Stock", "net_balance": -1000.0},
                {"name": "Additional Paid-In Capital", "net_balance": -500.0},
                {"name": "Retained Earnings", "net_balance": -300.0},
                {"name": "Treasury Stock", "net_balance": 200.0},
                {"name": "Accumulated Other Comprehensive Income", "net_balance": -100.0},
            ]
        )
        stmts = FinancialStatementBuilder(grouping).build()
        soce = stmts.statement_of_changes_in_equity
        component_types = {c.component_type for c in soce.components}
        assert {
            "common_stock",
            "additional_paid_in_capital",
            "retained_earnings",
            "treasury_stock",
            "aoci",
        }.issubset(component_types)

    def test_components_have_deterministic_order(self):
        grouping = _grouping_with_equity(
            [
                {"name": "Accumulated Other Comprehensive Income", "net_balance": -100.0},
                {"name": "Treasury Stock", "net_balance": 200.0},
                {"name": "Common Stock", "net_balance": -1000.0},
                {"name": "Retained Earnings", "net_balance": -300.0},
                {"name": "Additional Paid-In Capital", "net_balance": -500.0},
            ]
        )
        soce = FinancialStatementBuilder(grouping).build().statement_of_changes_in_equity
        types = [c.component_type for c in soce.components]
        assert types == [
            "common_stock",
            "additional_paid_in_capital",
            "retained_earnings",
            "treasury_stock",
            "aoci",
        ]


class TestRollforward:
    def test_prior_period_sets_beginning_balance(self):
        current = [{"name": "Retained Earnings", "net_balance": -1500.0}]
        prior = {
            "summaries": [
                {
                    "lead_sheet": "K",
                    "net_balance": 1000.0,
                    "accounts": [{"name": "Retained Earnings", "net_balance": -1000.0}],
                },
            ]
        }
        current_grouping = _grouping_with_equity(current)
        stmts = FinancialStatementBuilder(current_grouping, prior_lead_sheet_grouping=prior).build()
        re = [c for c in stmts.statement_of_changes_in_equity.components if c.component_type == "retained_earnings"][0]
        assert re.beginning_balance == 1000.0
        assert re.ending_balance == 1500.0

    def test_net_income_flows_to_retained_earnings(self):
        grouping = _grouping_with_equity(
            [{"name": "Retained Earnings", "net_balance": -1400.0}],
            include_income=True,
        )
        stmts = FinancialStatementBuilder(grouping).build()
        re = [c for c in stmts.statement_of_changes_in_equity.components if c.component_type == "retained_earnings"][0]
        # L -1000 → revenue 1000, M 400 → COGS 400, N 200 → opex 200, net 400.
        assert re.net_income_allocation == stmts.net_income
        assert stmts.net_income == 400.0

    def test_explicit_activity_respected(self):
        current = [{"name": "Retained Earnings", "net_balance": -1400.0}]
        prior = {
            "summaries": [
                {
                    "lead_sheet": "K",
                    "net_balance": 1000.0,
                    "accounts": [{"name": "Retained Earnings", "net_balance": -1000.0}],
                },
            ]
        }
        activity = [
            EquityActivity(account="Retained Earnings", dividends=100.0),
        ]
        stmts = FinancialStatementBuilder(
            _grouping_with_equity(current, include_income=True),
            prior_lead_sheet_grouping=prior,
            equity_activity=activity,
        ).build()
        re = [c for c in stmts.statement_of_changes_in_equity.components if c.component_type == "retained_earnings"][0]
        assert re.dividends == 100.0

    def test_other_movement_catches_unexplained_residual(self):
        # Beginning 1,000; ending 1,400; net income 0; no activity → 400
        # unexplained drops to other_movement.
        current = [{"name": "Retained Earnings", "net_balance": -1400.0}]
        prior = {
            "summaries": [
                {
                    "lead_sheet": "K",
                    "net_balance": 1000.0,
                    "accounts": [{"name": "Retained Earnings", "net_balance": -1000.0}],
                },
            ]
        }
        stmts = FinancialStatementBuilder(
            _grouping_with_equity(current),
            prior_lead_sheet_grouping=prior,
        ).build()
        re = [c for c in stmts.statement_of_changes_in_equity.components if c.component_type == "retained_earnings"][0]
        assert re.other_movement == 400.0


class TestUnmappedAccounts:
    def test_unknown_equity_account_surfaces_in_unmapped_list(self):
        grouping = _grouping_with_equity(
            [
                {"name": "Mystery Equity Adjustment", "net_balance": -500.0},
            ]
        )
        soce = FinancialStatementBuilder(grouping).build().statement_of_changes_in_equity
        assert "Mystery Equity Adjustment" in soce.unmapped_accounts

    def test_known_accounts_are_not_in_unmapped(self):
        grouping = _grouping_with_equity(
            [
                {"name": "Common Stock", "net_balance": -1000.0},
                {"name": "Retained Earnings", "net_balance": -500.0},
            ]
        )
        soce = FinancialStatementBuilder(grouping).build().statement_of_changes_in_equity
        assert soce.unmapped_accounts == []


class TestSerialisation:
    def test_soce_in_to_dict_output(self):
        grouping = _grouping_with_equity(
            [
                {"name": "Common Stock", "net_balance": -1000.0},
                {"name": "Retained Earnings", "net_balance": -500.0},
            ]
        )
        stmts = FinancialStatementBuilder(grouping).build()
        d = stmts.to_dict()
        assert "statement_of_changes_in_equity" in d
        soce = d["statement_of_changes_in_equity"]
        assert "components" in soce
        assert "ending_total_equity" in soce
        assert "unmapped_accounts" in soce

    def test_soce_omitted_when_no_equity(self):
        # No K lead sheet → empty components list but object is still built.
        grouping = {"summaries": []}
        stmts = FinancialStatementBuilder(grouping).build()
        soce = stmts.statement_of_changes_in_equity
        assert soce is not None
        assert soce.components == []
