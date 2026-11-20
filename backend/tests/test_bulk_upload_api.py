"""
Tests for Bulk Upload API Endpoints — Route-level integration tests.

Tests cover:
- POST /upload/bulk — start bulk upload (Enterprise only)
- GET /upload/bulk/{job_id}/status — poll job progress
- Entitlement enforcement (403 for non-Enterprise)
- Auth enforcement (401)

NOTE: AUDIT-08 fixed the arg-order mismatch — route now calls
check_bulk_upload_access(user, db) matching the function signature.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from tests.helpers.route_inventory import all_routes

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_verified_user
from database import get_db
from main import app
from models import User, UserTier

# Sprint 812: exercise these routes with the rate limiter ON (see conftest.limiter_enabled).
pytestmark = pytest.mark.usefixtures("limiter_enabled")

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def enterprise_user(db_session):
    """Create an Enterprise-tier verified user."""
    user = User(
        email="bulk_enterprise@example.com",
        name="Enterprise User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.ENTERPRISE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def solo_user(db_session):
    """Create a Solo-tier verified user (no bulk upload access)."""
    user = User(
        email="bulk_solo@example.com",
        name="Solo User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.SOLO,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_enterprise(db_session, enterprise_user):
    """Override auth for Enterprise user."""
    app.dependency_overrides[require_verified_user] = lambda: enterprise_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield enterprise_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_solo(db_session, solo_user):
    """Override auth for Solo user."""
    app.dependency_overrides[require_verified_user] = lambda: solo_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield solo_user
    app.dependency_overrides.clear()


# =============================================================================
# Route Registration
# =============================================================================


class TestBulkUploadRouteRegistration:
    """Verify bulk upload routes are registered."""

    def test_bulk_upload_route_exists(self):
        paths = [r.path for r in all_routes(app) if hasattr(r, "path")]
        assert "/upload/bulk" in paths

    def test_bulk_status_route_exists(self):
        paths = [r.path for r in all_routes(app) if hasattr(r, "path")]
        assert "/upload/bulk/{job_id}/status" in paths


# =============================================================================
# POST /upload/bulk
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestBulkUpload:
    """Tests for POST /upload/bulk."""

    @pytest.mark.asyncio
    async def test_bulk_upload_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/upload/bulk",
                files=[("files", ("test.csv", b"header\ndata", "text/csv"))],
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bulk_upload_is_not_available_even_for_enterprise(self, override_enterprise):
        """Sprint 888: bulk upload runs no analysis yet, so it refuses with 501 and stores no job."""
        from shared import bulk_job_store

        with patch.object(bulk_job_store, "put") as put:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/upload/bulk",
                    files=[("files", ("test.csv", b"header\ndata", "text/csv"))],
                )
        assert response.status_code == 501
        assert response.json()["detail"] == "Bulk upload is not available yet."
        put.assert_not_called()


# =============================================================================
# GET /upload/bulk/{job_id}/status
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestBulkUploadStatus:
    """Tests for GET /upload/bulk/{job_id}/status."""

    @pytest.mark.asyncio
    async def test_status_not_found(self, override_enterprise):
        """Non-existent job returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/upload/bulk/nonexistent-job-id/status")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_status_no_auth_returns_401(self):
        """GET without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/upload/bulk/some-job-id/status")
            assert response.status_code == 401
