"""
Tests for Health & Waitlist API Endpoints — Sprint 244, updated Sprint 305

Tests cover:
- GET /health — returns 200 with status (shallow)
- GET /health?deep=true — returns 200 with DB status or 503
- GET /health/live — liveness probe (static, zero I/O)
- GET /health/ready — readiness probe (DB + pool stats)
- POST /waitlist — valid email submission
"""

import sys
from unittest.mock import MagicMock, patch

import httpx
import pytest
from sqlalchemy.exc import OperationalError

sys.path.insert(0, '..')

from main import app

# =============================================================================
# GET /health (shallow)
# =============================================================================

class TestHealthCheck:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_returns_healthy(self):
        """GET /health returns 200 with healthy status."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        """GET /health works without authentication."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_shallow_has_no_database_field(self):
        """GET /health (shallow) omits database field."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data.get("database") is None


# =============================================================================
# GET /health?deep=true (deep probe)
# =============================================================================

class TestHealthDeepProbe:
    """Tests for GET /health?deep=true — DB connectivity check."""

    @pytest.mark.asyncio
    async def test_deep_healthy_returns_200(self):
        """GET /health?deep=true returns 200 with database=connected when DB is up."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health", params={"deep": "true"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"
            assert "version" in data

    @pytest.mark.asyncio
    async def test_deep_db_down_returns_503(self):
        """GET /health?deep=true returns 503 when DB is unreachable."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = OSError("Connection refused")

        with patch("database.SessionLocal", return_value=mock_session):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health", params={"deep": "true"})
                assert response.status_code == 503
                data = response.json()
                detail = data["detail"]
                assert detail["status"] == "unhealthy"
                assert detail["database"] == "unreachable"


# =============================================================================
# GET /health/live (liveness probe)
# =============================================================================

class TestLivenessProbe:
    """Tests for GET /health/live — static liveness probe."""

    @pytest.mark.asyncio
    async def test_returns_200_healthy(self):
        """GET /health/live returns 200 with status=healthy."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        """GET /health/live works without authentication."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_dependencies_field(self):
        """GET /health/live response has no dependencies or database field."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/live")
            data = response.json()
            assert "dependencies" not in data
            assert "database" not in data

    @pytest.mark.asyncio
    async def test_healthy_even_when_db_down(self):
        """GET /health/live returns 200 even when DB is unreachable (zero I/O)."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = OSError("Connection refused")

        with patch("database.SessionLocal", return_value=mock_session):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health/live")
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"


# =============================================================================
# GET /health/ready (readiness probe)
# =============================================================================

class TestReadinessProbe:
    """Tests for GET /health/ready — DB connectivity + pool stats."""

    @pytest.mark.asyncio
    async def test_returns_200_with_db_status(self):
        """GET /health/ready returns 200 with database dependency when DB is up."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data
            db = data["dependencies"]["database"]
            assert db["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_db_latency_is_nonnegative(self):
        """GET /health/ready reports non-negative latency_ms."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            data = response.json()
            latency = data["dependencies"]["database"]["latency_ms"]
            assert isinstance(latency, (int, float))
            assert latency >= 0

    @pytest.mark.asyncio
    async def test_pool_details_present(self):
        """GET /health/ready includes pool_class in details."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            data = response.json()
            details = data["dependencies"]["database"]["details"]
            assert "pool_class" in details

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        """GET /health/ready works without authentication."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_db_unreachable_returns_503(self):
        """GET /health/ready returns 503 when DB raises OSError."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = OSError("Connection refused")

        with patch("database.SessionLocal", return_value=mock_session):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                detail = data["detail"]
                assert detail["status"] == "unhealthy"
                assert detail["dependencies"]["database"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_sqlalchemy_error_returns_503(self):
        """GET /health/ready returns 503 on SQLAlchemy errors."""
        mock_session = MagicMock()
        mock_session.execute.side_effect = OperationalError(
            "SELECT 1", {}, Exception("DB down")
        )

        with patch("database.SessionLocal", return_value=mock_session):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health/ready")
                assert response.status_code == 503
                data = response.json()
                detail = data["detail"]
                assert detail["status"] == "unhealthy"


# =============================================================================
# POST /waitlist
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestWaitlist:
    """Tests for POST /waitlist endpoint."""

    @pytest.mark.asyncio
    async def test_valid_email_submission(self, tmp_path, monkeypatch):
        """POST /waitlist with valid email returns 201."""
        # Override waitlist file to tmp_path to avoid side effects
        import routes.health as health_mod
        monkeypatch.setattr(health_mod, "WAITLIST_FILE", tmp_path / "waitlist.csv")

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/waitlist", json={
                "email": "waitlist_test@example.com",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_email_422(self):
        """POST /waitlist with invalid email returns 422."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/waitlist", json={
                "email": "not-an-email",
            })
            assert response.status_code == 422
