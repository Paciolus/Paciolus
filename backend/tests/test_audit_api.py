"""
Tests for Audit API Endpoints — Sprint 244

Tests cover:
- POST /audit/trial-balance — file upload with valid CSV
- POST /audit/trial-balance — empty file
- POST /audit/flux — flux analysis
- 401 on missing auth
"""

import io
import sys

import httpx
import pytest

sys.path.insert(0, '..')

from auth import require_verified_user
from database import get_db
from main import app
from models import User, UserTier

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_user(db_session):
    """Create a real verified user in the test DB."""
    user = User(
        email="audit_api_test@example.com",
        name="Audit API Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies."""
    app.dependency_overrides[require_verified_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def valid_csv_bytes():
    """Generate a valid balanced CSV — non-round amounts to avoid rounding/concentration anomalies."""
    return b"""Account Name,Debit,Credit
Cash,3217.45,
Accounts Receivable,2891.33,
Inventory,1456.78,
Prepaid Insurance,987.22,
Equipment,4123.67,
Revenue,,8234.56
Cost of Goods Sold,1567.89,
Salaries Expense,2345.67,
Rent Expense,1234.55,
Utilities Expense,876.34,
Accounts Payable,,2345.89
Notes Payable,,3456.78
Retained Earnings,,4663.67
"""


@pytest.fixture
def empty_csv_bytes():
    """Generate an empty CSV file (headers only)."""
    return b"""Account Name,Debit,Credit
"""


# =============================================================================
# POST /audit/trial-balance
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestAuditTrialBalance:
    """Tests for POST /audit/trial-balance endpoint."""

    @pytest.mark.asyncio
    async def test_upload_valid_csv(self, override_auth, valid_csv_bytes):
        """POST /audit/trial-balance with valid CSV returns 200."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/audit/trial-balance",
                files={"file": ("test.csv", io.BytesIO(valid_csv_bytes), "text/csv")},
                data={"materiality_threshold": "0"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["row_count"] > 0
            assert data["total_debits"] > 0

    @pytest.mark.asyncio
    async def test_upload_empty_csv(self, override_auth, empty_csv_bytes):
        """POST /audit/trial-balance with empty CSV still succeeds with 0 rows."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/audit/trial-balance",
                files={"file": ("empty.csv", io.BytesIO(empty_csv_bytes), "text/csv")},
                data={"materiality_threshold": "0"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["row_count"] == 0

    @pytest.mark.asyncio
    async def test_401_without_auth(self, valid_csv_bytes):
        """POST /audit/trial-balance returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/audit/trial-balance",
                files={"file": ("test.csv", io.BytesIO(valid_csv_bytes), "text/csv")},
                data={"materiality_threshold": "0"},
            )
            assert response.status_code == 401


# =============================================================================
# POST /audit/flux
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestAuditFlux:
    """Tests for POST /audit/flux endpoint."""

    @pytest.mark.asyncio
    async def test_flux_analysis(self, override_auth, valid_csv_bytes):
        """POST /audit/flux with two valid CSV files returns comparison."""
        current_csv = b"""Account Name,Debit,Credit
Cash,12000,
Revenue,,12000
"""
        prior_csv = b"""Account Name,Debit,Credit
Cash,10000,
Revenue,,10000
"""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/audit/flux",
                files=[
                    ("current_file", ("current.csv", io.BytesIO(current_csv), "text/csv")),
                    ("prior_file", ("prior.csv", io.BytesIO(prior_csv), "text/csv")),
                ],
                data={"materiality_threshold": "100"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "flux" in data
            assert "items" in data["flux"]
