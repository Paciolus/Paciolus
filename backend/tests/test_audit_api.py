"""
Tests for Audit API Endpoints — Sprint 244 / Sprint LXIII-1

Tests cover:
- POST /audit/trial-balance — file upload with valid CSV
- POST /audit/trial-balance — empty file
- POST /audit/flux — flux analysis
- 401 on missing auth
- Diagnostic monthly limit enforcement (Sprint LXIII-1)
"""

import io
import sys
from datetime import UTC, datetime

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import ActivityLog, User, UserTier

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
        tier=UserTier.TEAM,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
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
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
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
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
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
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
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
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
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


# =============================================================================
# Diagnostic monthly limit enforcement (Sprint LXIII-1)
# =============================================================================


def _make_activity_log(user_id, db_session):
    """Insert one ActivityLog row for the given user_id in the current month."""
    log = ActivityLog(
        user_id=user_id,
        filename_hash="b" * 64,
        filename_display="test_limit.csv",
        timestamp=datetime.now(UTC),
        record_count=10,
        total_debits=1000.00,
        total_credits=1000.00,
        materiality_threshold=500.00,
        was_balanced=True,
    )
    db_session.add(log)
    db_session.flush()
    return log


@pytest.mark.usefixtures("bypass_csrf")
class TestDiagnosticLimitEnforcement:
    """Tests for monthly diagnostic limit on POST /audit/trial-balance (Sprint LXIII-1)."""

    def _setup_user_with_logs(self, db_session, tier, email, log_count):
        """Create a verified user of the given tier with log_count ActivityLog entries."""
        user = User(
            email=email,
            name="Limit Test User",
            hashed_password="$2b$12$fakehashvalue",
            tier=tier,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()
        for _ in range(log_count):
            _make_activity_log(user.id, db_session)
        return user

    def _override_deps(self, user, db_session):
        """Override require_current_user, require_verified_user, and get_db."""
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

    @pytest.mark.asyncio
    async def test_free_tier_at_limit_returns_403(self, db_session, valid_csv_bytes):
        """FREE tier user at monthly limit (10 runs) → 403 TIER_LIMIT_EXCEEDED."""
        user = self._setup_user_with_logs(db_session, UserTier.FREE, "free_limit_10@example.com", 10)
        self._override_deps(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/trial-balance",
                    files={"file": ("test.csv", io.BytesIO(valid_csv_bytes), "text/csv")},
                    data={"materiality_threshold": "0"},
                )
            assert response.status_code == 403
            detail = response.json()["detail"]
            assert detail["code"] == "TIER_LIMIT_EXCEEDED"
            assert detail["resource"] == "diagnostics"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_free_tier_under_limit_returns_200(self, db_session, valid_csv_bytes):
        """FREE tier user at limit-minus-1 (9 runs) → 200 still allowed."""
        user = self._setup_user_with_logs(db_session, UserTier.FREE, "free_limit_9@example.com", 9)
        self._override_deps(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/trial-balance",
                    files={"file": ("test.csv", io.BytesIO(valid_csv_bytes), "text/csv")},
                    data={"materiality_threshold": "0"},
                )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_solo_tier_at_limit_returns_403(self, db_session, valid_csv_bytes):
        """SOLO tier user at monthly limit (20 runs) → 403 TIER_LIMIT_EXCEEDED."""
        user = self._setup_user_with_logs(db_session, UserTier.SOLO, "solo_limit_20@example.com", 20)
        self._override_deps(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/trial-balance",
                    files={"file": ("test.csv", io.BytesIO(valid_csv_bytes), "text/csv")},
                    data={"materiality_threshold": "0"},
                )
            assert response.status_code == 403
            detail = response.json()["detail"]
            assert detail["code"] == "TIER_LIMIT_EXCEEDED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_team_tier_no_limit_enforced(self, db_session, valid_csv_bytes):
        """TEAM tier user with 100 ActivityLogs → 200 (unlimited)."""
        user = self._setup_user_with_logs(db_session, UserTier.TEAM, "team_nolimit@example.com", 100)
        self._override_deps(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/trial-balance",
                    files={"file": ("test.csv", io.BytesIO(valid_csv_bytes), "text/csv")},
                    data={"materiality_threshold": "0"},
                )
            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
