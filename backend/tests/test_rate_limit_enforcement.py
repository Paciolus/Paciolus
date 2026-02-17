"""
Tests for Rate Limit Enforcement — verify actual HTTP 429 responses.

Complements test_rate_limit_coverage.py (which checks decorator wiring via
AST inspection) by making real HTTP requests and asserting that SlowAPI
actually returns 429 when limits are exceeded.

Each test re-enables the limiter (conftest disables it globally), resets
internal storage for deterministic state, then fires (limit + 1) requests.

Endpoints tested:
- POST /auth/login                   — RATE_LIMIT_AUTH   (5/minute)
- POST /settings/materiality/preview — RATE_LIMIT_WRITE  (30/minute)
- POST /audit/compare-periods        — RATE_LIMIT_AUDIT  (10/minute)
- POST /export/csv/movements         — RATE_LIMIT_EXPORT (20/minute)
"""

from unittest.mock import MagicMock

import httpx
import pytest

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from shared.rate_limits import limiter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def enable_rate_limiter():
    """Re-enable rate limiter for 429 enforcement tests.

    The global conftest._disable_rate_limiter (autouse) sets
    limiter.enabled = False for deterministic tests.  This fixture
    re-enables it and resets internal storage so each test starts
    from zero recorded hits.
    """
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.enabled = False
    limiter.reset()


@pytest.fixture()
def mock_current_user():
    """Mock user for require_current_user-protected endpoints."""
    user = MagicMock()
    user.id = 998
    user.email = "ratelimit-current@test.com"
    user.is_active = True
    user.is_verified = True
    user.settings = "{}"
    return user


@pytest.fixture()
def mock_verified_user():
    """Mock user for require_verified_user-protected endpoints."""
    user = MagicMock()
    user.id = 999
    user.email = "ratelimit-verified@test.com"
    user.is_active = True
    user.is_verified = True
    return user


@pytest.fixture()
def override_current_user(mock_current_user):
    """Override require_current_user for rate limit tests."""
    app.dependency_overrides[require_current_user] = lambda: mock_current_user
    yield
    app.dependency_overrides.pop(require_current_user, None)


@pytest.fixture()
def override_verified_user(mock_verified_user):
    """Override require_verified_user for rate limit tests."""
    app.dependency_overrides[require_verified_user] = lambda: mock_verified_user
    yield
    app.dependency_overrides.pop(require_verified_user, None)


@pytest.fixture()
def override_db(db_session):
    """Override get_db so login requests use the in-memory test database."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# AUTH Tier: POST /auth/login — 5/minute
# ---------------------------------------------------------------------------

class TestAuthTier429:
    """POST /auth/login is rate-limited at RATE_LIMIT_AUTH (5/minute).

    Login is CSRF-exempt (in CSRF_EXEMPT_PATHS), so bypass_csrf is not
    needed.  A non-existent email yields 401 without DB writes.
    """

    ENDPOINT = "/auth/login"
    LIMIT = 5  # RATE_LIMIT_AUTH = "5/minute"

    @pytest.mark.asyncio
    async def test_login_returns_429_after_limit_exceeded(
        self, enable_rate_limiter, override_db,
    ):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # First LIMIT requests should return 401 (invalid credentials)
            for i in range(self.LIMIT):
                r = await client.post(
                    self.ENDPOINT,
                    json={"email": "nobody@example.com", "password": "wrongpass"},
                )
                assert r.status_code == 401, (
                    f"Expected 401 on request {i + 1}/{self.LIMIT}, got {r.status_code}"
                )

            # The (LIMIT+1)th request should be rate-limited
            r = await client.post(
                self.ENDPOINT,
                json={"email": "nobody@example.com", "password": "wrongpass"},
            )
            assert r.status_code == 429


# ---------------------------------------------------------------------------
# WRITE Tier: POST /settings/materiality/preview — 30/minute
# ---------------------------------------------------------------------------

class TestWriteTier429:
    """POST /settings/materiality/preview is rate-limited at RATE_LIMIT_WRITE (30/minute).

    Materiality preview is a pure calculation (no DB writes), making it
    safe and fast for repeated requests.
    """

    ENDPOINT = "/settings/materiality/preview"
    LIMIT = 30  # RATE_LIMIT_WRITE = "30/minute"
    PAYLOAD = {
        "formula": {"type": "fixed", "value": 500.0},
        "total_revenue": 1_000_000,
        "total_assets": 2_000_000,
        "total_equity": 500_000,
    }

    @pytest.mark.asyncio
    async def test_materiality_preview_returns_429_after_limit_exceeded(
        self, enable_rate_limiter, bypass_csrf, override_current_user,
    ):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # First LIMIT requests should return 200 (successful calculation)
            for i in range(self.LIMIT):
                r = await client.post(
                    self.ENDPOINT,
                    json=self.PAYLOAD,
                    headers={"X-CSRF-Token": "test"},
                )
                assert r.status_code == 200, (
                    f"Expected 200 on request {i + 1}/{self.LIMIT}, got {r.status_code}"
                )

            # The (LIMIT+1)th request should be rate-limited
            r = await client.post(
                self.ENDPOINT,
                json=self.PAYLOAD,
                headers={"X-CSRF-Token": "test"},
            )
            assert r.status_code == 429


# ---------------------------------------------------------------------------
# AUDIT Tier: POST /audit/compare-periods — 10/minute
# ---------------------------------------------------------------------------

class TestAuditTier429:
    """POST /audit/compare-periods is rate-limited at RATE_LIMIT_AUDIT (10/minute).

    Minimal valid payload — one account each in prior and current periods.
    """

    ENDPOINT = "/audit/compare-periods"
    LIMIT = 10  # RATE_LIMIT_AUDIT = "10/minute"
    PAYLOAD = {
        "prior_accounts": [
            {"account": "Cash", "debit": 100, "credit": 0, "type": "asset"},
        ],
        "current_accounts": [
            {"account": "Cash", "debit": 200, "credit": 0, "type": "asset"},
        ],
    }

    @pytest.mark.asyncio
    async def test_compare_periods_returns_429_after_limit_exceeded(
        self, enable_rate_limiter, bypass_csrf, override_verified_user,
    ):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # First LIMIT requests should return 200 (successful comparison)
            for i in range(self.LIMIT):
                r = await client.post(
                    self.ENDPOINT,
                    json=self.PAYLOAD,
                    headers={"X-CSRF-Token": "test"},
                )
                assert r.status_code == 200, (
                    f"Expected 200 on request {i + 1}/{self.LIMIT}, got {r.status_code}"
                )

            # The (LIMIT+1)th request should be rate-limited
            r = await client.post(
                self.ENDPOINT,
                json=self.PAYLOAD,
                headers={"X-CSRF-Token": "test"},
            )
            assert r.status_code == 429


# ---------------------------------------------------------------------------
# EXPORT Tier: POST /export/csv/movements — 20/minute
# ---------------------------------------------------------------------------

class TestExportTier429:
    """POST /export/csv/movements is rate-limited at RATE_LIMIT_EXPORT (20/minute).

    Reuses the same minimal account payload as the AUDIT tier test.
    The endpoint runs a lightweight compare + CSV encode (no DB access).
    """

    ENDPOINT = "/export/csv/movements"
    LIMIT = 20  # RATE_LIMIT_EXPORT = "20/minute"
    PAYLOAD = {
        "prior_accounts": [
            {"account": "Cash", "debit": 100, "credit": 0, "type": "asset"},
        ],
        "current_accounts": [
            {"account": "Cash", "debit": 200, "credit": 0, "type": "asset"},
        ],
    }

    @pytest.mark.asyncio
    async def test_export_csv_movements_returns_429_after_limit_exceeded(
        self, enable_rate_limiter, bypass_csrf, override_verified_user,
    ):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            # First LIMIT requests should return 200 (successful CSV export)
            for i in range(self.LIMIT):
                r = await client.post(
                    self.ENDPOINT,
                    json=self.PAYLOAD,
                    headers={"X-CSRF-Token": "test"},
                )
                assert r.status_code == 200, (
                    f"Expected 200 on request {i + 1}/{self.LIMIT}, got {r.status_code}"
                )

            # The (LIMIT+1)th request should be rate-limited
            r = await client.post(
                self.ENDPOINT,
                json=self.PAYLOAD,
                headers={"X-CSRF-Token": "test"},
            )
            assert r.status_code == 429
