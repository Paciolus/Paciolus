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

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_verified_user
from database import get_db
from main import app
from models import User, UserTier

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
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/upload/bulk" in paths

    def test_bulk_status_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
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
    async def test_bulk_upload_forbidden_for_solo(self, override_solo):
        """Solo user gets 403 (Enterprise only)."""
        from fastapi import HTTPException

        def _raise_403(*args, **kwargs):
            raise HTTPException(status_code=403, detail="Bulk upload not available.")

        with patch("routes.bulk_upload.check_bulk_upload_access", side_effect=_raise_403):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/upload/bulk",
                    files=[("files", ("test.csv", b"header\ndata", "text/csv"))],
                )
                assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_bulk_upload_too_many_files(self, override_enterprise):
        """More than 5 files returns 400."""
        with (
            patch("routes.bulk_upload.check_bulk_upload_access"),
            patch("routes.bulk_upload.check_upload_limit"),
            patch("routes.bulk_upload.validate_file_size", return_value=b"content"),
        ):
            files = [("files", (f"test{i}.csv", b"header\ndata", "text/csv")) for i in range(6)]
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/upload/bulk", files=files)
                assert response.status_code == 400


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
