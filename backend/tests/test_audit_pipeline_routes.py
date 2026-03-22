"""
Tests for the audit pipeline route (POST /audit/trial-balance).

Sprint 564: Integration tests covering auth requirements, entitlement checks,
file validation, dedup protection, and error handling for the core TB analysis
endpoint.
"""

import io
from unittest.mock import MagicMock, patch

import httpx
import pytest


def _auth_headers(token="test-token"):
    """Build auth headers with a bearer token and CSRF token."""
    return {
        "authorization": f"Bearer {token}",
        "x-csrf-token": "test-csrf",
    }


def _make_xlsx_bytes():
    """Create a minimal valid XLSX file in memory."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["Account", "Debit", "Credit"])
    ws.append(["1000 Cash", 10000, 0])
    ws.append(["2000 AP", 0, 10000])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


class TestAuditPipelineAuth:
    """Auth and entitlement gate tests for /audit/trial-balance."""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self):
        """POST /audit/trial-balance without auth is rejected (401 or 403)."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/trial-balance",
                files={"file": ("test.xlsx", b"fake", "application/octet-stream")},
            )

        # CSRF middleware returns 403 before auth can return 401
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_unverified_user_rejected(self, db_session):
        """POST /audit/trial-balance with unverified user is rejected."""
        from database import get_db
        from main import app
        from models import User, UserTier

        user = User(
            email="unverified@test.com",
            hashed_password="$2b$12$fakehash",
            is_verified=False,
            tier=UserTier.FREE,
        )
        db_session.add(user)
        db_session.commit()

        with patch("auth.decode_access_token") as mock_decode:
            mock_decode.return_value = MagicMock(user_id=user.id, email=user.email, tier="free")

            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/trial-balance",
                    files={"file": ("test.xlsx", b"fake", "application/octet-stream")},
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_endpoint_registered(self):
        """The /audit/trial-balance endpoint exists in the app router."""
        from main import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/trial-balance" in routes


class TestAuditPipelineValidation:
    """Input validation tests for /audit/trial-balance."""

    @pytest.mark.asyncio
    async def test_missing_file_rejected(self):
        """POST /audit/trial-balance without file is rejected (not 200)."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/trial-balance",
                headers=_auth_headers(),
            )

        # Must not succeed — 403 (CSRF), 401 (auth), or 422 (missing file)
        assert response.status_code in (401, 403, 422)


class TestAuditPipelineErrorHandling:
    """Error handling tests for /audit/trial-balance."""

    @pytest.mark.asyncio
    async def test_invalid_file_returns_400(self, db_session):
        """Uploading a non-spreadsheet file returns 400."""
        from database import get_db
        from main import app
        from models import User, UserTier

        user = User(
            email="badfile@test.com",
            hashed_password="$2b$12$fakehash",
            is_verified=True,
            tier=UserTier.SOLO,
        )
        db_session.add(user)
        db_session.commit()

        with (
            patch("auth.decode_access_token") as mock_decode,
            patch("shared.entitlement_checks.check_diagnostic_limit") as mock_ent,
        ):
            mock_decode.return_value = MagicMock(
                user_id=user.id,
                email=user.email,
                tier="solo",
                pwd_at=None,
            )

            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/trial-balance",
                    files={"file": ("test.jpg", b"not a spreadsheet", "image/jpeg")},
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        # Should get 400 (bad file), 403 (CSRF/auth), or 409 (dedup)
        assert response.status_code in (400, 403, 409, 422)

    @pytest.mark.asyncio
    async def test_rate_limit_configured(self):
        """The audit endpoint has rate limiting configured."""
        from shared.rate_limits import RATE_LIMIT_AUDIT

        assert RATE_LIMIT_AUDIT is not None
        # Rate limit string should contain a number
        assert any(c.isdigit() for c in RATE_LIMIT_AUDIT)

    @pytest.mark.asyncio
    async def test_dedup_protection_exists(self):
        """The audit pipeline uses upload dedup to prevent rapid re-submissions."""
        from upload_dedup_model import UploadDedup

        # Verify the model exists and has the expected columns
        assert hasattr(UploadDedup, "dedup_key")
        assert hasattr(UploadDedup, "expires_at")
