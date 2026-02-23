"""
Tests for POST /audit/compare-periods API Endpoint.

Sprint 61: Multi-Period Trial Balance Comparison API Integration Tests

Tests cover:
- Authentication and authorization (require_verified_user)
- Basic comparison success and response structure
- Movement type classification (all 6 types)
- Lead sheet grouping in API response
- Significant movement detection
- New and closed account detection
- Period label passthrough
- Empty period edge cases
- Materiality threshold classification
- Dormant account detection
- Debit/credit total calculation
- Sign change detection
- Movement summary cards data completeness
"""

# Import from parent directory
import sys
from unittest.mock import MagicMock

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_verified_user
from main import app

# =============================================================================
# TEST CLIENT SETUP
# =============================================================================


@pytest.fixture
def mock_user():
    """Create a mock verified user for authenticated endpoints."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.is_verified = True
    return user


@pytest.fixture
def override_auth(mock_user):
    """Override authentication for protected endpoints."""
    app.dependency_overrides[require_verified_user] = lambda: mock_user
    yield
    app.dependency_overrides.clear()


def _make_account(name: str, debit: float = 0, credit: float = 0, acct_type: str = "asset") -> dict:
    """Helper to create account dicts for API requests."""
    return {"account": name, "debit": debit, "credit": credit, "type": acct_type}


@pytest.fixture
def simple_prior():
    """Simple prior period trial balance."""
    return [
        _make_account("Cash", debit=50000, acct_type="asset"),
        _make_account("Accounts Receivable", debit=30000, acct_type="asset"),
        _make_account("Inventory", debit=20000, acct_type="asset"),
        _make_account("Accounts Payable", credit=25000, acct_type="liability"),
        _make_account("Revenue", credit=100000, acct_type="revenue"),
        _make_account("Rent Expense", debit=12000, acct_type="expense"),
    ]


@pytest.fixture
def simple_current():
    """Simple current period trial balance with changes."""
    return [
        _make_account("Cash", debit=65000, acct_type="asset"),
        _make_account("Accounts Receivable", debit=35000, acct_type="asset"),
        _make_account("Inventory", debit=18000, acct_type="asset"),
        _make_account("Accounts Payable", credit=30000, acct_type="liability"),
        _make_account("Revenue", credit=120000, acct_type="revenue"),
        _make_account("Rent Expense", debit=12000, acct_type="expense"),
    ]


def _build_payload(prior, current, prior_label="FY2024", current_label="FY2025", materiality_threshold=0.0):
    """Build a standard compare-periods request payload."""
    return {
        "prior_accounts": prior,
        "current_accounts": current,
        "prior_label": prior_label,
        "current_label": current_label,
        "materiality_threshold": materiality_threshold,
    }


# =============================================================================
# TEST: AUTHENTICATION & AUTHORIZATION
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestComparePeriodEndpoint:
    """Tests for POST /audit/compare-periods endpoint."""

    @pytest.mark.asyncio
    async def test_compare_requires_auth(self):
        """Test that endpoint returns 401 without authentication token."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            payload = _build_payload(
                [_make_account("Cash", debit=50000)],
                [_make_account("Cash", debit=65000)],
            )
            response = await client.post("/audit/compare-periods", json=payload)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_compare_requires_verified_user(self):
        """Test that endpoint requires a verified user (not just any authenticated user).

        This is tested implicitly via the dependency override — without the override,
        the dependency rejects unverified users. We verify 401 without override above.
        With override providing a mock verified user, the request succeeds (tested below).
        """
        # Without the override, the endpoint should reject the request
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            payload = _build_payload(
                [_make_account("Cash", debit=50000)],
                [_make_account("Cash", debit=65000)],
            )
            # Sending a fake/invalid token should not pass require_verified_user
            response = await client.post(
                "/audit/compare-periods", json=payload, headers={"Authorization": "Bearer invalid_token_for_unverified"}
            )
            assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_compare_basic_success(self, mock_user, simple_prior, simple_current):
        """Test that a valid request returns 200 with expected structure."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = _build_payload(simple_prior, simple_current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                # Verify top-level structure
                assert "all_movements" in data
                assert "lead_sheet_summaries" in data
                assert "significant_movements" in data
                assert "movements_by_type" in data
                assert "movements_by_significance" in data
                assert "total_accounts" in data
                assert "prior_label" in data
                assert "current_label" in data
                assert "new_accounts" in data
                assert "closed_accounts" in data
                assert "dormant_accounts" in data
                assert "prior_total_debits" in data
                assert "prior_total_credits" in data
                assert "current_total_debits" in data
                assert "current_total_credits" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_returns_movement_types(self, mock_user):
        """Test that response contains all 6 movement types in movements_by_type."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                # Construct accounts that trigger all 6 movement types:
                # 1. new_account: "New Equipment" in current only
                # 2. closed_account: "Old Reserve" in prior only
                # 3. sign_change: "Retained Earnings" flips debit->credit
                # 4. increase: "Cash" goes up
                # 5. decrease: "Inventory" goes down
                # 6. unchanged: "Rent Expense" same in both
                prior = [
                    _make_account("Cash", debit=50000, acct_type="asset"),
                    _make_account("Inventory", debit=20000, acct_type="asset"),
                    _make_account("Rent Expense", debit=12000, acct_type="expense"),
                    _make_account("Old Reserve", debit=5000, acct_type="asset"),
                    _make_account("Retained Earnings", debit=10000, acct_type="equity"),
                ]
                current = [
                    _make_account("Cash", debit=65000, acct_type="asset"),
                    _make_account("Inventory", debit=15000, acct_type="asset"),
                    _make_account("Rent Expense", debit=12000, acct_type="expense"),
                    _make_account("New Equipment", debit=75000, acct_type="asset"),
                    _make_account("Retained Earnings", credit=5000, acct_type="equity"),
                ]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                expected_types = ["new_account", "closed_account", "sign_change", "increase", "decrease", "unchanged"]
                for mt in expected_types:
                    assert mt in data["movements_by_type"], f"Missing movement type: {mt}"

                # Verify specific counts
                assert data["movements_by_type"]["new_account"] == 1
                assert data["movements_by_type"]["closed_account"] == 1
                assert data["movements_by_type"]["sign_change"] == 1
                assert data["movements_by_type"]["increase"] == 1
                assert data["movements_by_type"]["decrease"] == 1
                assert data["movements_by_type"]["unchanged"] == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_returns_lead_sheet_grouping(self, mock_user, simple_prior, simple_current):
        """Test that lead_sheet_summaries are present and properly structured."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = _build_payload(simple_prior, simple_current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert isinstance(data["lead_sheet_summaries"], list)
                assert len(data["lead_sheet_summaries"]) > 0

                # Verify structure of each lead sheet summary
                for ls in data["lead_sheet_summaries"]:
                    assert "lead_sheet" in ls
                    assert "lead_sheet_name" in ls
                    assert "lead_sheet_category" in ls
                    assert "prior_total" in ls
                    assert "current_total" in ls
                    assert "net_change" in ls
                    assert "account_count" in ls
                    assert "movements" in ls
                    assert ls["account_count"] > 0
                    assert len(ls["movements"]) > 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_returns_significant_movements(self, mock_user, simple_prior, simple_current):
        """Test that significant_movements list is populated with high-impact changes."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = _build_payload(simple_prior, simple_current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert isinstance(data["significant_movements"], list)
                # Cash +15000 and Revenue +20000 are > $10K threshold = significant
                assert len(data["significant_movements"]) > 0

                # Verify significant movements are sorted by absolute change descending
                if len(data["significant_movements"]) >= 2:
                    for i in range(len(data["significant_movements"]) - 1):
                        assert abs(data["significant_movements"][i]["change_amount"]) >= abs(
                            data["significant_movements"][i + 1]["change_amount"]
                        )

                # Verify each significant movement has expected fields
                for mov in data["significant_movements"]:
                    assert "account_name" in mov
                    assert "change_amount" in mov
                    assert "movement_type" in mov
                    assert "significance" in mov
                    assert mov["significance"] in ("material", "significant")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_new_accounts_detected(self, mock_user, simple_prior):
        """Test that accounts in current but not in prior are flagged as new."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                current = list(simple_prior)
                current.append(_make_account("New Equipment", debit=75000, acct_type="asset"))
                current.append(_make_account("Prepaid Insurance", debit=6000, acct_type="asset"))

                payload = _build_payload(simple_prior, current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert "New Equipment" in data["new_accounts"]
                assert "Prepaid Insurance" in data["new_accounts"]
                assert data["movements_by_type"]["new_account"] == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_closed_accounts_detected(self, mock_user, simple_current):
        """Test that accounts in prior but not in current are flagged as closed."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = list(simple_current)
                prior.append(_make_account("Old Reserve Fund", debit=8000, acct_type="asset"))
                prior.append(_make_account("Discontinued Product Line", credit=15000, acct_type="revenue"))

                payload = _build_payload(prior, simple_current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert "Old Reserve Fund" in data["closed_accounts"]
                assert "Discontinued Product Line" in data["closed_accounts"]
                assert data["movements_by_type"]["closed_account"] == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_labels_in_response(self, mock_user):
        """Test that prior_label and current_label are returned in response."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [_make_account("Cash", debit=100)]
                current = [_make_account("Cash", debit=200)]

                payload = _build_payload(
                    prior,
                    current,
                    prior_label="Q4 2024",
                    current_label="Q1 2025",
                )
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert data["prior_label"] == "Q4 2024"
                assert data["current_label"] == "Q1 2025"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_empty_prior(self, mock_user):
        """Test that all accounts are new when prior is empty."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                current = [
                    _make_account("Cash", debit=50000, acct_type="asset"),
                    _make_account("Revenue", credit=100000, acct_type="revenue"),
                    _make_account("Inventory", debit=20000, acct_type="asset"),
                ]

                payload = _build_payload([], current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert data["total_accounts"] == 3
                assert data["movements_by_type"]["new_account"] == 3
                assert len(data["new_accounts"]) == 3
                # No closed accounts
                assert len(data["closed_accounts"]) == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_empty_current(self, mock_user):
        """Test that all accounts are closed when current is empty."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [
                    _make_account("Cash", debit=50000, acct_type="asset"),
                    _make_account("Revenue", credit=100000, acct_type="revenue"),
                ]

                payload = _build_payload(prior, [])
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert data["total_accounts"] == 2
                assert data["movements_by_type"]["closed_account"] == 2
                assert len(data["closed_accounts"]) == 2
                # No new accounts
                assert len(data["new_accounts"]) == 0
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_with_materiality_threshold(self, mock_user):
        """Test that materiality_threshold affects significance classification."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [
                    _make_account("Cash", debit=50000, acct_type="asset"),
                    _make_account("Revenue", credit=100000, acct_type="revenue"),
                ]
                current = [
                    _make_account("Cash", debit=90000, acct_type="asset"),  # +40000 -> material if threshold=25000
                    _make_account(
                        "Revenue", credit=112000, acct_type="revenue"
                    ),  # +12000 -> significant but not material
                ]

                payload = _build_payload(
                    prior,
                    current,
                    materiality_threshold=25000.0,
                )
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                # Should have at least one material item (Cash +40K > 25K threshold)
                assert data["movements_by_significance"].get("material", 0) >= 1

                # Find the Cash movement and verify it is material
                cash_movement = None
                for mov in data["all_movements"]:
                    if mov["account_name"] == "Cash":
                        cash_movement = mov
                        break

                assert cash_movement is not None
                assert cash_movement["significance"] == "material"
                assert cash_movement["change_amount"] == 40000
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_dormant_accounts(self, mock_user):
        """Test that zero-balance unchanged accounts are flagged as dormant."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [
                    _make_account("Dormant Fund", debit=0, credit=0, acct_type="asset"),
                    _make_account("Cash", debit=50000, acct_type="asset"),
                ]
                current = [
                    _make_account("Dormant Fund", debit=0, credit=0, acct_type="asset"),
                    _make_account("Cash", debit=55000, acct_type="asset"),
                ]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert "Dormant Fund" in data["dormant_accounts"]

                # Find the dormant movement and verify the flag
                dormant_mov = None
                for mov in data["all_movements"]:
                    if mov["account_name"] == "Dormant Fund":
                        dormant_mov = mov
                        break

                assert dormant_mov is not None
                assert dormant_mov["is_dormant"] is True
                assert dormant_mov["movement_type"] == "unchanged"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_totals_calculated(self, mock_user, simple_prior, simple_current):
        """Test that debit and credit totals are correctly calculated for both periods."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = _build_payload(simple_prior, simple_current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                # Prior: Cash 50K + AR 30K + Inv 20K + Rent 12K = 112K debits
                # Prior: AP 25K + Revenue 100K = 125K credits
                assert data["prior_total_debits"] == 112000
                assert data["prior_total_credits"] == 125000

                # Current: Cash 65K + AR 35K + Inv 18K + Rent 12K = 130K debits
                # Current: AP 30K + Revenue 120K = 150K credits
                assert data["current_total_debits"] == 130000
                assert data["current_total_credits"] == 150000
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_sign_change_detected(self, mock_user):
        """Test that an account flipping from debit to credit is detected as sign_change."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [
                    _make_account("Retained Earnings", debit=10000, acct_type="equity"),
                ]
                current = [
                    _make_account("Retained Earnings", credit=5000, acct_type="equity"),
                ]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert data["movements_by_type"]["sign_change"] == 1

                mov = data["all_movements"][0]
                assert mov["movement_type"] == "sign_change"
                assert mov["prior_balance"] == 10000  # debit - credit = 10000 - 0
                assert mov["current_balance"] == -5000  # debit - credit = 0 - 5000
                assert mov["change_amount"] == -15000
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_compare_movement_summary_cards_data(self, mock_user, simple_prior, simple_current):
        """Test that movements_by_type dict has all 6 movement type keys."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = _build_payload(simple_prior, simple_current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                expected_keys = ["new_account", "closed_account", "sign_change", "increase", "decrease", "unchanged"]
                for key in expected_keys:
                    assert key in data["movements_by_type"], f"Missing key '{key}' in movements_by_type"
                    assert isinstance(data["movements_by_type"][key], int)

                # Verify total accounts equals sum of movement types
                total_from_types = sum(data["movements_by_type"].values())
                assert total_from_types == data["total_accounts"]
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# TEST: MOVEMENT DETAIL STRUCTURE
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestMovementDetailStructure:
    """Tests verifying individual movement objects have correct structure."""

    @pytest.mark.asyncio
    async def test_movement_has_all_fields(self, mock_user):
        """Test that each movement in all_movements has expected fields."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [_make_account("Cash", debit=50000, acct_type="asset")]
                current = [_make_account("Cash", debit=65000, acct_type="asset")]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert len(data["all_movements"]) == 1
                mov = data["all_movements"][0]

                expected_fields = [
                    "account_name",
                    "account_type",
                    "prior_balance",
                    "current_balance",
                    "change_amount",
                    "change_percent",
                    "movement_type",
                    "significance",
                    "lead_sheet",
                    "lead_sheet_name",
                    "lead_sheet_category",
                    "is_dormant",
                ]
                for field in expected_fields:
                    assert field in mov, f"Missing field '{field}' in movement object"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_movement_change_percent_calculated(self, mock_user):
        """Test that change_percent is correctly calculated."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [_make_account("Cash", debit=50000, acct_type="asset")]
                current = [_make_account("Cash", debit=65000, acct_type="asset")]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)
                data = response.json()

                mov = data["all_movements"][0]
                # Change: 15000 / 50000 = 30%
                assert mov["change_percent"] == 30.0
                assert mov["change_amount"] == 15000
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_new_account_has_null_percent(self, mock_user):
        """Test that new accounts have None/null change_percent (no prior to compare)."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = []
                current = [_make_account("New Account", debit=10000, acct_type="asset")]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)
                data = response.json()

                mov = data["all_movements"][0]
                assert mov["movement_type"] == "new_account"
                assert mov["change_percent"] is None
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# TEST: LEAD SHEET INTEGRATION
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestLeadSheetIntegration:
    """Tests for lead sheet grouping in API response."""

    @pytest.mark.asyncio
    async def test_cash_assigned_to_lead_sheet_a(self, mock_user):
        """Test that Cash accounts are grouped under lead sheet A."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [_make_account("Cash", debit=50000, acct_type="asset")]
                current = [_make_account("Cash", debit=60000, acct_type="asset")]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)
                data = response.json()

                mov = data["all_movements"][0]
                assert mov["lead_sheet"] == "A"
                assert "Cash" in mov["lead_sheet_name"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_lead_sheet_summary_net_change(self, mock_user):
        """Test that lead sheet summary calculates correct net_change."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [
                    _make_account("Cash", debit=50000, acct_type="asset"),
                    _make_account("Petty Cash", debit=1000, acct_type="asset"),
                ]
                current = [
                    _make_account("Cash", debit=60000, acct_type="asset"),
                    _make_account("Petty Cash", debit=1500, acct_type="asset"),
                ]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)
                data = response.json()

                # Both should be in lead sheet A
                ls_a = [s for s in data["lead_sheet_summaries"] if s["lead_sheet"] == "A"]
                assert len(ls_a) == 1
                assert ls_a[0]["account_count"] == 2
                assert ls_a[0]["prior_total"] == 51000
                assert ls_a[0]["current_total"] == 61500
                assert ls_a[0]["net_change"] == 10500
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# TEST: ZERO-STORAGE COMPLIANCE
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestZeroStorageCompliance:
    """Tests verifying Zero-Storage compliance for compare-periods endpoint."""

    @pytest.mark.asyncio
    async def test_response_contains_no_user_data(self, mock_user, simple_prior, simple_current):
        """Test that response does not leak user identifiers."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = _build_payload(simple_prior, simple_current)
                response = await client.post("/audit/compare-periods", json=payload)
                data = response.json()

                # Response should not contain user identifiers
                response_str = str(data)
                assert "test@example.com" not in response_str
                assert '"user_id"' not in response_str
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_comparison_is_ephemeral(self, mock_user):
        """Test that two identical requests produce identical results (no stored state)."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [_make_account("Cash", debit=50000, acct_type="asset")]
                current = [_make_account("Cash", debit=65000, acct_type="asset")]

                payload = _build_payload(prior, current)

                response1 = await client.post("/audit/compare-periods", json=payload)
                response2 = await client.post("/audit/compare-periods", json=payload)

                data1 = response1.json()
                data2 = response2.json()

                # Identical inputs should produce identical outputs
                assert data1["all_movements"][0]["change_amount"] == data2["all_movements"][0]["change_amount"]
                assert data1["total_accounts"] == data2["total_accounts"]
                assert data1["movements_by_type"] == data2["movements_by_type"]
        finally:
            app.dependency_overrides.clear()


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestEdgeCases:
    """Edge cases and boundary conditions for the API endpoint."""

    @pytest.mark.asyncio
    async def test_both_periods_empty(self, mock_user):
        """Test comparison with both empty periods returns valid empty result."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = _build_payload([], [])
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert data["total_accounts"] == 0
                assert len(data["all_movements"]) == 0
                assert len(data["lead_sheet_summaries"]) == 0
                assert len(data["significant_movements"]) == 0
                assert all(v == 0 for v in data["movements_by_type"].values())
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_default_labels_used(self, mock_user):
        """Test that default labels are used when not provided."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                payload = {
                    "prior_accounts": [_make_account("Cash", debit=100)],
                    "current_accounts": [_make_account("Cash", debit=200)],
                }
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()

                assert data["prior_label"] == "Prior Period"
                assert data["current_label"] == "Current Period"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_large_trial_balance_performance(self, mock_user):
        """Test that endpoint handles 200+ accounts without error."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
                timeout=30.0,
            ) as client:
                prior = [_make_account(f"Account {i}", debit=i * 100) for i in range(200)]
                current = [_make_account(f"Account {i}", debit=i * 110) for i in range(200)]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)

                assert response.status_code == 200
                data = response.json()
                assert data["total_accounts"] == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_significance_tiers_in_response(self, mock_user):
        """Test that movements_by_significance contains all tier keys."""
        app.dependency_overrides[require_verified_user] = lambda: mock_user

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                prior = [
                    _make_account("Cash", debit=50000, acct_type="asset"),
                    _make_account("Petty Cash", debit=100, acct_type="asset"),
                ]
                current = [
                    _make_account("Cash", debit=65000, acct_type="asset"),  # Significant (>$10K)
                    _make_account("Petty Cash", debit=105, acct_type="asset"),  # Minor
                ]

                payload = _build_payload(prior, current)
                response = await client.post("/audit/compare-periods", json=payload)
                data = response.json()

                expected_tiers = ["material", "significant", "minor"]
                for tier in expected_tiers:
                    assert tier in data["movements_by_significance"], (
                        f"Missing tier '{tier}' in movements_by_significance"
                    )
                    assert isinstance(data["movements_by_significance"][tier], int)
        finally:
            app.dependency_overrides.clear()
