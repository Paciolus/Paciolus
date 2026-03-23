"""
Tests for the audit flux route (POST /audit/flux).

Sprint 570 / DEC F-001: Integration tests covering auth requirements,
file validation, and success path for the period-over-period flux endpoint.
"""

import io
from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import httpx
import pytest


def _auth_headers(token="test-token"):
    return {
        "authorization": f"Bearer {token}",
        "x-csrf-token": "test-csrf",
    }


def _make_xlsx_bytes():
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


@dataclass
class _FakeFluxResult:
    items: list = field(default_factory=list)

    def to_dict(self):
        return {
            "items": self.items,
            "summary": {
                "total_items": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "new_accounts": 0,
                "removed_accounts": 0,
                "reclassification_count": 0,
                "threshold": 5000.0,
            },
        }


@dataclass
class _FakeReconResult:
    def to_dict(self):
        return {
            "scores": [],
            "stats": {"high": 0, "medium": 0, "low": 0},
        }


class TestFluxAuth:
    """Auth gate tests for POST /audit/flux."""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/flux",
                files={
                    "current_file": ("curr.xlsx", b"fake", "application/octet-stream"),
                    "prior_file": ("prior.xlsx", b"fake", "application/octet-stream"),
                },
            )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_unverified_user_rejected(self, db_session):
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
                    "/audit/flux",
                    files={
                        "current_file": ("curr.xlsx", b"fake", "application/octet-stream"),
                        "prior_file": ("prior.xlsx", b"fake", "application/octet-stream"),
                    },
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 403


@pytest.mark.usefixtures("bypass_csrf")
class TestFluxValidation:
    """Input validation tests for POST /audit/flux."""

    @pytest.mark.asyncio
    async def test_missing_prior_file_rejected(self, db_session):
        from database import get_db
        from main import app
        from models import User, UserTier

        user = User(
            email="verified@test.com",
            hashed_password="$2b$12$fakehash",
            is_verified=True,
            tier=UserTier.SOLO,
        )
        db_session.add(user)
        db_session.commit()

        with patch("auth.decode_access_token") as mock_decode:
            mock_decode.return_value = MagicMock(user_id=user.id, email=user.email, tier="solo", pwd_at=None)
            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/flux",
                    files={
                        "current_file": ("curr.xlsx", b"fake", "application/octet-stream"),
                    },
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_successful_flux_analysis(self, db_session):
        """Verified user with two valid files gets a 200 response."""
        from database import get_db
        from main import app
        from models import User, UserTier

        user = User(
            email="verified@test.com",
            hashed_password="$2b$12$fakehash",
            is_verified=True,
            tier=UserTier.SOLO,
        )
        db_session.add(user)
        db_session.commit()

        xlsx = _make_xlsx_bytes()

        with (
            patch("auth.decode_access_token") as mock_decode,
            patch("routes.audit_flux.run_flux_analysis") as mock_flux,
            patch("routes.audit_flux.resolve_materiality") as mock_mat,
            patch("routes.audit_flux.extract_flux_accounts", return_value=[]),
            patch("routes.audit_flux.maybe_record_tool_run"),
        ):
            mock_decode.return_value = MagicMock(user_id=user.id, email=user.email, tier="solo", pwd_at=None)
            mock_flux.return_value = (_FakeFluxResult(), _FakeReconResult())
            mock_mat.return_value = (5000.0, "form")

            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/flux",
                    files={
                        "current_file": ("curr.xlsx", xlsx, "application/octet-stream"),
                        "prior_file": ("prior.xlsx", xlsx, "application/octet-stream"),
                    },
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert "flux" in data
        assert "recon" in data

    @pytest.mark.asyncio
    async def test_flux_engine_error_returns_500(self, db_session):
        """Engine ValueError should return 500 with sanitized detail."""
        from database import get_db
        from main import app
        from models import User, UserTier

        user = User(
            email="verified@test.com",
            hashed_password="$2b$12$fakehash",
            is_verified=True,
            tier=UserTier.SOLO,
        )
        db_session.add(user)
        db_session.commit()

        async def _fake_validate(f):
            return b"fake-bytes"

        with (
            patch("auth.decode_access_token") as mock_decode,
            patch("routes.audit_flux.validate_file_size", side_effect=_fake_validate),
            patch("routes.audit_flux.run_flux_analysis", side_effect=ValueError("bad data")),
            patch("routes.audit_flux.resolve_materiality", return_value=(0.0, "default")),
            patch("routes.audit_flux.maybe_record_tool_run"),
        ):
            mock_decode.return_value = MagicMock(user_id=user.id, email=user.email, tier="solo", pwd_at=None)
            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/flux",
                    files={
                        "current_file": ("curr.xlsx", b"fake", "application/octet-stream"),
                        "prior_file": ("prior.xlsx", b"fake", "application/octet-stream"),
                    },
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 500
