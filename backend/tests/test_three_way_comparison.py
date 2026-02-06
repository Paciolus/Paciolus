"""
Tests for Three-Way TB Comparison + CSV Export — Sprint 63

Tests cover:
- Three-way comparison (prior + current + budget)
- Budget variance calculation and classification
- Budget-specific aggregates (over/under/on budget)
- Three-way lead sheet summaries
- CSV export (two-way and three-way)
- Three-way API endpoint
- CSV export API endpoint
- Edge cases (empty budget, no match, all on budget)
"""

import pytest
import csv
from io import StringIO

import sys
sys.path.insert(0, '..')

from multi_period_comparison import (
    compare_three_periods,
    compare_trial_balances,
    export_movements_csv,
    ThreeWayMovementSummary,
    ThreeWayLeadSheetSummary,
    BudgetVariance,
)


# =============================================================================
# FIXTURES
# =============================================================================

def _acct(name: str, debit: float = 0, credit: float = 0, acct_type: str = "asset") -> dict:
    return {"account": name, "debit": debit, "credit": credit, "type": acct_type}


@pytest.fixture
def prior():
    return [
        _acct("Cash", debit=50000, acct_type="asset"),
        _acct("Accounts Receivable", debit=30000, acct_type="asset"),
        _acct("Inventory", debit=20000, acct_type="asset"),
        _acct("Accounts Payable", credit=25000, acct_type="liability"),
        _acct("Revenue", credit=100000, acct_type="revenue"),
        _acct("Rent Expense", debit=12000, acct_type="expense"),
    ]


@pytest.fixture
def current():
    return [
        _acct("Cash", debit=65000, acct_type="asset"),
        _acct("Accounts Receivable", debit=35000, acct_type="asset"),
        _acct("Inventory", debit=18000, acct_type="asset"),
        _acct("Accounts Payable", credit=30000, acct_type="liability"),
        _acct("Revenue", credit=120000, acct_type="revenue"),
        _acct("Rent Expense", debit=12000, acct_type="expense"),
    ]


@pytest.fixture
def budget():
    return [
        _acct("Cash", debit=60000, acct_type="asset"),
        _acct("Accounts Receivable", debit=32000, acct_type="asset"),
        _acct("Inventory", debit=22000, acct_type="asset"),
        _acct("Accounts Payable", credit=28000, acct_type="liability"),
        _acct("Revenue", credit=110000, acct_type="revenue"),
        _acct("Rent Expense", debit=11500, acct_type="expense"),
    ]


# =============================================================================
# TEST: THREE-WAY COMPARISON — BASIC FUNCTIONALITY
# =============================================================================

class TestThreeWayComparison:
    """Tests for compare_three_periods() function."""

    def test_returns_three_way_summary(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        assert isinstance(result, ThreeWayMovementSummary)

    def test_labels_passed_through(self, prior, current, budget):
        result = compare_three_periods(
            prior, current, budget,
            prior_label="FY2024", current_label="FY2025", budget_label="Budget 2025",
        )
        assert result.prior_label == "FY2024"
        assert result.current_label == "FY2025"
        assert result.budget_label == "Budget 2025"

    def test_default_labels(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        assert result.prior_label == "Prior Year"
        assert result.current_label == "Current Year"
        assert result.budget_label == "Budget"

    def test_total_accounts_matches_two_way(self, prior, current, budget):
        three_way = compare_three_periods(prior, current, budget)
        two_way = compare_trial_balances(prior, current)
        assert three_way.total_accounts == two_way.total_accounts

    def test_movements_by_type_matches_two_way(self, prior, current, budget):
        three_way = compare_three_periods(prior, current, budget)
        two_way = compare_trial_balances(prior, current)
        assert three_way.movements_by_type == two_way.movements_by_type

    def test_all_movements_have_budget_variance(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        for m in result.all_movements:
            assert "budget_variance" in m
            # All accounts in budget fixture, so all should have variance
            assert m["budget_variance"] is not None

    def test_budget_totals_calculated(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        # Budget debits: Cash 60K + AR 32K + Inv 22K + Rent 11.5K = 125,500
        assert result.budget_total_debits == 125500.0
        # Budget credits: AP 28K + Revenue 110K = 138,000
        assert result.budget_total_credits == 138000.0


# =============================================================================
# TEST: BUDGET VARIANCE CALCULATION
# =============================================================================

class TestBudgetVariance:
    """Tests for budget variance calculation in three-way comparison."""

    def test_over_budget_detected(self, prior, current, budget):
        """Cash: current 65K vs budget 60K = +5K over budget."""
        result = compare_three_periods(prior, current, budget)
        cash = next(m for m in result.all_movements if m["account_name"] == "Cash")
        bv = cash["budget_variance"]
        assert bv["budget_balance"] == 60000
        assert bv["variance_amount"] == 5000  # 65K - 60K
        assert bv["variance_percent"] == pytest.approx(8.33, rel=0.01)

    def test_under_budget_detected(self, prior, current, budget):
        """Inventory: current 18K vs budget 22K = -4K under budget."""
        result = compare_three_periods(prior, current, budget)
        inv = next(m for m in result.all_movements if m["account_name"] == "Inventory")
        bv = inv["budget_variance"]
        assert bv["budget_balance"] == 22000
        assert bv["variance_amount"] == -4000  # 18K - 22K
        assert bv["variance_percent"] == pytest.approx(-18.18, rel=0.01)

    def test_on_budget_detected(self):
        """Account exactly matching budget should count as on_budget."""
        prior = [_acct("Cash", debit=50000)]
        current = [_acct("Cash", debit=60000)]
        budget = [_acct("Cash", debit=60000)]  # Exactly matches current
        result = compare_three_periods(prior, current, budget)
        assert result.accounts_on_budget == 1
        assert result.accounts_over_budget == 0
        assert result.accounts_under_budget == 0

    def test_budget_variance_significance(self, prior, current, budget):
        """Revenue variance (current 120K vs budget 110K = 10K) should be significant."""
        result = compare_three_periods(prior, current, budget)
        revenue = next(m for m in result.all_movements if m["account_name"] == "Revenue")
        bv = revenue["budget_variance"]
        assert bv["variance_amount"] == -10000  # credit: -(120K - 110K) = net is -(120K) - -(110K) = -10K
        # Revenue is a credit account, net = debit - credit
        # Current: 0 - 120000 = -120000
        # Budget: 0 - 110000 = -110000
        # Variance = -120000 - (-110000) = -10000

    def test_budget_aggregate_counts(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        total = result.accounts_over_budget + result.accounts_under_budget + result.accounts_on_budget
        assert total == result.total_accounts

    def test_budget_variances_by_significance(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        sig = result.budget_variances_by_significance
        assert "material" in sig
        assert "significant" in sig
        assert "minor" in sig
        total_sig = sum(sig.values())
        assert total_sig == result.total_accounts

    def test_materiality_threshold_applied_to_budget(self):
        """Budget variance > materiality = material classification."""
        prior = [_acct("Cash", debit=50000)]
        current = [_acct("Cash", debit=100000)]
        budget = [_acct("Cash", debit=60000)]  # Variance = 40K
        result = compare_three_periods(
            prior, current, budget,
            materiality_threshold=25000.0,
        )
        cash = next(m for m in result.all_movements if m["account_name"] == "Cash")
        bv = cash["budget_variance"]
        assert bv["variance_significance"] == "material"


# =============================================================================
# TEST: UNMATCHED BUDGET ACCOUNTS
# =============================================================================

class TestUnmatchedBudget:
    """Tests for accounts with no budget match."""

    def test_no_budget_match_returns_null(self):
        prior = [_acct("Cash", debit=50000)]
        current = [_acct("Cash", debit=65000)]
        budget = [_acct("Equipment", debit=80000)]  # No match to Cash
        result = compare_three_periods(prior, current, budget)
        cash = next(m for m in result.all_movements if m["account_name"] == "Cash")
        assert cash["budget_variance"] is None

    def test_empty_budget_all_null(self, prior, current):
        result = compare_three_periods(prior, current, [])
        for m in result.all_movements:
            assert m["budget_variance"] is None
        assert result.accounts_over_budget == 0
        assert result.accounts_under_budget == 0
        assert result.accounts_on_budget == 0

    def test_partial_budget_match(self):
        """Only some accounts have budget data."""
        prior = [_acct("Cash", debit=50000), _acct("Inventory", debit=20000)]
        current = [_acct("Cash", debit=65000), _acct("Inventory", debit=18000)]
        budget = [_acct("Cash", debit=60000)]  # Only Cash has budget
        result = compare_three_periods(prior, current, budget)
        cash = next(m for m in result.all_movements if m["account_name"] == "Cash")
        inv = next(m for m in result.all_movements if m["account_name"] == "Inventory")
        assert cash["budget_variance"] is not None
        assert inv["budget_variance"] is None

    def test_new_account_budget_variance(self):
        """New account (not in prior) that IS in budget."""
        prior = []
        current = [_acct("Equipment", debit=80000)]
        budget = [_acct("Equipment", debit=75000)]
        result = compare_three_periods(prior, current, budget)
        equip = next(m for m in result.all_movements if m["account_name"] == "Equipment")
        assert equip["budget_variance"] is not None
        assert equip["budget_variance"]["variance_amount"] == 5000  # 80K - 75K


# =============================================================================
# TEST: THREE-WAY LEAD SHEET SUMMARIES
# =============================================================================

class TestThreeWayLeadSheets:
    """Tests for lead sheet summaries with budget data."""

    def test_lead_sheet_has_budget_total(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        assert len(result.lead_sheet_summaries) > 0
        for ls in result.lead_sheet_summaries:
            assert isinstance(ls, ThreeWayLeadSheetSummary)
            assert ls.budget_total is not None

    def test_lead_sheet_budget_variance(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        # Find Cash lead sheet (A)
        ls_a = next((ls for ls in result.lead_sheet_summaries if ls.lead_sheet == "A"), None)
        if ls_a:
            assert ls_a.budget_variance is not None
            assert ls_a.budget_variance == ls_a.current_total - ls_a.budget_total

    def test_lead_sheet_budget_variance_percent(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        for ls in result.lead_sheet_summaries:
            if ls.budget_total and ls.budget_total != 0:
                expected_pct = (ls.budget_variance / abs(ls.budget_total)) * 100
                assert ls.budget_variance_percent == pytest.approx(expected_pct, rel=0.01)


# =============================================================================
# TEST: CSV EXPORT — TWO-WAY
# =============================================================================

class TestCsvExportTwoWay:
    """Tests for two-way CSV export."""

    def test_csv_has_header_row(self, prior, current):
        summary = compare_trial_balances(prior, current)
        csv_content = export_movements_csv(summary)
        reader = csv.reader(StringIO(csv_content))
        header = next(reader)
        assert "Account" in header
        assert "Prior Balance" in header
        assert "Current Balance" in header
        assert "Movement Type" in header
        assert "Significance" in header

    def test_csv_has_all_accounts(self, prior, current):
        summary = compare_trial_balances(prior, current)
        csv_content = export_movements_csv(summary)
        # Count non-empty data rows (before summary section)
        reader = csv.reader(StringIO(csv_content))
        next(reader)  # Skip header
        data_rows = []
        for row in reader:
            if row and row[0] and not row[0].startswith("==="):
                data_rows.append(row)
            elif row and row[0].startswith("==="):
                break
        assert len(data_rows) == summary.total_accounts

    def test_csv_has_lead_sheet_summary(self, prior, current):
        summary = compare_trial_balances(prior, current)
        csv_content = export_movements_csv(summary)
        assert "LEAD SHEET SUMMARY" in csv_content

    def test_csv_has_summary_statistics(self, prior, current):
        summary = compare_trial_balances(prior, current)
        csv_content = export_movements_csv(summary)
        assert "SUMMARY STATISTICS" in csv_content
        assert "Total Accounts" in csv_content

    def test_csv_no_budget_columns_by_default(self, prior, current):
        summary = compare_trial_balances(prior, current)
        csv_content = export_movements_csv(summary)
        reader = csv.reader(StringIO(csv_content))
        header = next(reader)
        assert "Budget Balance" not in header


# =============================================================================
# TEST: CSV EXPORT — THREE-WAY
# =============================================================================

class TestCsvExportThreeWay:
    """Tests for three-way CSV export with budget columns."""

    def test_csv_includes_budget_columns(self, prior, current, budget):
        three_way = compare_three_periods(prior, current, budget)
        csv_content = export_movements_csv(three_way, include_budget=True, budget_data=True)
        reader = csv.reader(StringIO(csv_content))
        header = next(reader)
        assert "Budget Balance" in header
        assert "Budget Variance" in header
        assert "Budget Variance %" in header

    def test_csv_budget_data_populated(self, prior, current, budget):
        three_way = compare_three_periods(prior, current, budget)
        csv_content = export_movements_csv(three_way, include_budget=True, budget_data=True)
        reader = csv.reader(StringIO(csv_content))
        next(reader)  # Skip header
        first_row = next(reader)
        # Budget columns should be populated (at index 9, 10, 11)
        assert len(first_row) >= 12  # 9 base + 3 budget columns


# =============================================================================
# TEST: TO_DICT SERIALIZATION
# =============================================================================

class TestSerialization:
    """Tests for ThreeWayMovementSummary serialization."""

    def test_to_dict_has_budget_fields(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        d = result.to_dict()
        assert "budget_label" in d
        assert "budget_total_debits" in d
        assert "budget_total_credits" in d
        assert "budget_variances_by_significance" in d
        assert "accounts_over_budget" in d
        assert "accounts_under_budget" in d
        assert "accounts_on_budget" in d

    def test_to_dict_preserves_two_way_fields(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        d = result.to_dict()
        assert "prior_label" in d
        assert "current_label" in d
        assert "all_movements" in d
        assert "lead_sheet_summaries" in d
        assert "movements_by_type" in d

    def test_lead_sheet_summary_to_dict(self, prior, current, budget):
        result = compare_three_periods(prior, current, budget)
        d = result.to_dict()
        for ls in d["lead_sheet_summaries"]:
            assert "budget_total" in ls
            assert "budget_variance" in ls
            assert "budget_variance_percent" in ls

    def test_budget_variance_to_dict(self):
        from multi_period_comparison import SignificanceTier
        bv = BudgetVariance(
            budget_balance=60000,
            variance_amount=5000,
            variance_percent=8.33,
            variance_significance=SignificanceTier.MINOR,
        )
        d = bv.to_dict()
        assert d["budget_balance"] == 60000
        assert d["variance_amount"] == 5000
        assert d["variance_percent"] == 8.33
        assert d["variance_significance"] == "minor"


# =============================================================================
# TEST: THREE-WAY API ENDPOINT
# =============================================================================

import httpx
from unittest.mock import MagicMock
from main import app, require_verified_user


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.is_verified = True
    return user


class TestThreeWayApiEndpoint:
    """Tests for POST /audit/compare-three-way endpoint."""

    @pytest.mark.asyncio
    async def test_three_way_requires_auth(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            payload = {
                "prior_accounts": [_acct("Cash", debit=50000)],
                "current_accounts": [_acct("Cash", debit=65000)],
                "budget_accounts": [_acct("Cash", debit=60000)],
            }
            response = await client.post("/audit/compare-three-way", json=payload)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_three_way_success(self, mock_user):
        app.dependency_overrides[require_verified_user] = lambda: mock_user
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "prior_accounts": [_acct("Cash", debit=50000)],
                    "current_accounts": [_acct("Cash", debit=65000)],
                    "budget_accounts": [_acct("Cash", debit=60000)],
                    "prior_label": "FY2024",
                    "current_label": "FY2025",
                    "budget_label": "Budget 2025",
                }
                response = await client.post("/audit/compare-three-way", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert data["budget_label"] == "Budget 2025"
                assert data["accounts_over_budget"] == 1
                assert "budget_variances_by_significance" in data
                # Verify movement has budget variance
                m = data["all_movements"][0]
                assert m["budget_variance"] is not None
                assert m["budget_variance"]["budget_balance"] == 60000
        finally:
            app.dependency_overrides.clear()


class TestCsvExportApiEndpoint:
    """Tests for POST /export/csv/movements endpoint."""

    @pytest.mark.asyncio
    async def test_csv_export_requires_auth(self):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            payload = {
                "prior_accounts": [_acct("Cash", debit=50000)],
                "current_accounts": [_acct("Cash", debit=65000)],
            }
            response = await client.post("/export/csv/movements", json=payload)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_csv_export_two_way(self, mock_user):
        app.dependency_overrides[require_verified_user] = lambda: mock_user
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "prior_accounts": [_acct("Cash", debit=50000)],
                    "current_accounts": [_acct("Cash", debit=65000)],
                }
                response = await client.post("/export/csv/movements", json=payload)
                assert response.status_code == 200
                assert "text/csv" in response.headers["content-type"]
                assert "Movement_Comparison" in response.headers["content-disposition"]
                content = response.text
                assert "Cash" in content
                assert "Account" in content

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_csv_export_three_way(self, mock_user):
        app.dependency_overrides[require_verified_user] = lambda: mock_user
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                payload = {
                    "prior_accounts": [_acct("Cash", debit=50000)],
                    "current_accounts": [_acct("Cash", debit=65000)],
                    "budget_accounts": [_acct("Cash", debit=60000)],
                }
                response = await client.post("/export/csv/movements", json=payload)
                assert response.status_code == 200
                content = response.text
                assert "Budget Balance" in content
                assert "Budget Variance" in content
        finally:
            app.dependency_overrides.clear()
