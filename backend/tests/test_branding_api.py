"""
Tests for Branding API Endpoints — Route-level integration tests.

Tests cover:
- GET /branding/ — get branding config
- PUT /branding/ — update header/footer text
- POST /branding/logo — upload logo
- DELETE /branding/logo — remove logo
- Entitlement enforcement (403 for non-Enterprise)
- Auth enforcement (401)

NOTE: AUDIT-08 fixed the arg-order mismatch — route now calls
check_custom_branding_access(user, db) matching the function signature.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_current_user
from database import get_db
from main import app
from models import User, UserTier
from organization_model import Organization, OrganizationMember, OrgRole

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def enterprise_user_with_org(db_session):
    """Create an Enterprise user with an org for branding access."""
    user = User(
        email="branding_ent@example.com",
        name="Enterprise Brander",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.ENTERPRISE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="Branding Firm",
        slug="branding-firm",
        owner_user_id=user.id,
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER,
    )
    db_session.add(member)
    db_session.flush()

    user.organization_id = org.id
    db_session.flush()

    return user


@pytest.fixture
def solo_user(db_session):
    """Create a Solo-tier user (no branding access)."""
    user = User(
        email="branding_solo@example.com",
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
def override_enterprise(db_session, enterprise_user_with_org):
    """Override auth + db for Enterprise user."""
    app.dependency_overrides[require_current_user] = lambda: enterprise_user_with_org
    app.dependency_overrides[get_db] = lambda: db_session
    yield enterprise_user_with_org
    app.dependency_overrides.clear()


@pytest.fixture
def override_solo(db_session, solo_user):
    """Override auth + db for Solo user."""
    app.dependency_overrides[require_current_user] = lambda: solo_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield solo_user
    app.dependency_overrides.clear()


# =============================================================================
# Route Registration
# =============================================================================


class TestBrandingRouteRegistration:
    """Verify branding routes are registered."""

    def test_get_branding_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/branding/" in paths

    def test_logo_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/branding/logo" in paths


# =============================================================================
# GET /branding/
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestGetBranding:
    """Tests for GET /branding/."""

    @pytest.mark.asyncio
    async def test_get_branding_success(self, override_enterprise):
        """Enterprise user gets branding config."""
        with patch("routes.branding.check_custom_branding_access"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/branding/")
                assert response.status_code == 200
                data = response.json()
                assert "has_logo" in data
                assert "header_text" in data
                assert "footer_text" in data

    @pytest.mark.asyncio
    async def test_get_branding_forbidden_for_solo(self, override_solo):
        """Solo user gets 403 (entitlement check rejects)."""
        from fastapi import HTTPException

        def _raise_403(*args, **kwargs):
            raise HTTPException(status_code=403, detail="Custom branding not available.")

        with patch("routes.branding.check_custom_branding_access", side_effect=_raise_403):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/branding/")
                assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_branding_no_auth_returns_401(self):
        """No auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/branding/")
            assert response.status_code == 401


# =============================================================================
# PUT /branding/
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestUpdateBranding:
    """Tests for PUT /branding/."""

    @pytest.mark.asyncio
    async def test_update_branding_success(self, override_enterprise):
        """Enterprise user can update header/footer text."""
        with patch("routes.branding.check_custom_branding_access"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put(
                    "/branding/",
                    json={"header_text": "My Firm", "footer_text": "Confidential"},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["header_text"] == "My Firm"
                assert data["footer_text"] == "Confidential"

    @pytest.mark.asyncio
    async def test_update_branding_partial(self, override_enterprise):
        """Can update only header_text."""
        with patch("routes.branding.check_custom_branding_access"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put(
                    "/branding/",
                    json={"header_text": "Updated Header"},
                )
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_branding_forbidden_for_solo(self, override_solo):
        """Solo user gets 403."""
        from fastapi import HTTPException

        def _raise_403(*args, **kwargs):
            raise HTTPException(status_code=403, detail="Custom branding not available.")

        with patch("routes.branding.check_custom_branding_access", side_effect=_raise_403):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put(
                    "/branding/",
                    json={"header_text": "Nope"},
                )
                assert response.status_code == 403


# =============================================================================
# POST /branding/logo
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestUploadLogo:
    """Tests for POST /branding/logo."""

    @pytest.mark.asyncio
    async def test_upload_logo_invalid_content_type(self, override_enterprise):
        """Upload non-image file gets 400."""
        with patch("routes.branding.check_custom_branding_access"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/branding/logo",
                    files={"file": ("test.txt", b"not an image", "text/plain")},
                )
                assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_logo_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/branding/logo",
                files={"file": ("logo.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 100, "image/png")},
            )
            assert response.status_code == 401


# =============================================================================
# DELETE /branding/logo
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestDeleteLogo:
    """Tests for DELETE /branding/logo."""

    @pytest.mark.asyncio
    async def test_delete_logo_success(self, override_enterprise):
        """Enterprise user can delete logo."""
        with patch("routes.branding.check_custom_branding_access"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete("/branding/logo")
                assert response.status_code == 200
                data = response.json()
                assert "detail" in data

    @pytest.mark.asyncio
    async def test_delete_logo_forbidden_for_solo(self, override_solo):
        """Solo user gets 403."""
        from fastapi import HTTPException

        def _raise_403(*args, **kwargs):
            raise HTTPException(status_code=403, detail="Custom branding not available.")

        with patch("routes.branding.check_custom_branding_access", side_effect=_raise_403):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete("/branding/logo")
                assert response.status_code == 403
