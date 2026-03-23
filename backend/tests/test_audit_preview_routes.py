"""
Tests for the audit preview route (POST /audit/preview-pdf).

Sprint 570 / DEC F-001: Integration tests covering auth requirements,
file validation, quality gate, and error handling for PDF preview.
"""

from dataclasses import dataclass, field
from unittest.mock import MagicMock, patch

import httpx
import pytest


def _auth_headers(token="test-token"):
    return {
        "authorization": f"Bearer {token}",
        "x-csrf-token": "test-csrf",
    }


@dataclass
class _FakeMetadata:
    page_count: int = 1
    tables_found: int = 1
    extraction_confidence: float = 0.85
    header_confidence: float = 0.9
    numeric_density: float = 0.7
    row_consistency: float = 0.95
    remediation_hints: list = field(default_factory=list)


@dataclass
class _FakeExtractResult:
    column_names: list = field(default_factory=lambda: ["Account", "Debit", "Credit"])
    rows: list = field(default_factory=lambda: [["1000 Cash", "10000", "0"]])
    metadata: _FakeMetadata = field(default_factory=_FakeMetadata)


class TestPreviewAuth:
    """Auth gate tests for POST /audit/preview-pdf."""

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/preview-pdf",
                files={"file": ("test.pdf", b"%PDF-fake", "application/pdf")},
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
                    "/audit/preview-pdf",
                    files={"file": ("test.pdf", b"%PDF-fake", "application/pdf")},
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 403


@pytest.mark.usefixtures("bypass_csrf")
class TestPreviewSuccess:
    """Success-path tests for POST /audit/preview-pdf."""

    @pytest.mark.asyncio
    async def test_successful_preview(self, db_session):
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

        with (
            patch("auth.decode_access_token") as mock_decode,
            patch("shared.pdf_parser.extract_pdf_tables") as mock_extract,
            patch("shared.preflight_cache.preflight_cache") as mock_cache,
            patch("shared.pdf_parser.CONFIDENCE_THRESHOLD", 0.6),
            patch("shared.pdf_parser.PREVIEW_PAGE_LIMIT", 3),
        ):
            mock_decode.return_value = MagicMock(user_id=user.id, email=user.email, tier="solo", pwd_at=None)
            mock_extract.return_value = _FakeExtractResult()
            mock_cache.put.return_value = "token-abc-123"

            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/preview-pdf",
                    files={"file": ("test.pdf", b"%PDF-fake", "application/pdf")},
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["passes_quality_gate"] is True
        assert data["preflight_token"] == "token-abc-123"
        assert data["page_count"] == 1
        assert data["tables_found"] == 1
        assert len(data["column_names"]) == 3
        assert len(data["sample_rows"]) == 1

    @pytest.mark.asyncio
    async def test_low_confidence_fails_quality_gate(self, db_session):
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

        low_conf = _FakeExtractResult()
        low_conf.metadata.extraction_confidence = 0.3

        with (
            patch("auth.decode_access_token") as mock_decode,
            patch("shared.pdf_parser.extract_pdf_tables", return_value=low_conf),
            patch("shared.preflight_cache.preflight_cache") as mock_cache,
            patch("shared.pdf_parser.CONFIDENCE_THRESHOLD", 0.6),
            patch("shared.pdf_parser.PREVIEW_PAGE_LIMIT", 3),
        ):
            mock_decode.return_value = MagicMock(user_id=user.id, email=user.email, tier="solo", pwd_at=None)
            mock_cache.put.return_value = "token-xyz"

            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/preview-pdf",
                    files={"file": ("low.pdf", b"%PDF-fake", "application/pdf")},
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        assert response.json()["passes_quality_gate"] is False


@pytest.mark.usefixtures("bypass_csrf")
class TestPreviewErrors:
    """Error-handling tests for POST /audit/preview-pdf."""

    @pytest.mark.asyncio
    async def test_parse_error_returns_400(self, db_session):
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

        with (
            patch("auth.decode_access_token") as mock_decode,
            patch(
                "shared.pdf_parser.extract_pdf_tables",
                side_effect=ValueError("No tables found"),
            ),
            patch("shared.pdf_parser.CONFIDENCE_THRESHOLD", 0.6),
            patch("shared.pdf_parser.PREVIEW_PAGE_LIMIT", 3),
        ):
            mock_decode.return_value = MagicMock(user_id=user.id, email=user.email, tier="solo", pwd_at=None)
            app.dependency_overrides[get_db] = lambda: db_session

            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/audit/preview-pdf",
                    files={"file": ("bad.pdf", b"not-a-pdf", "application/pdf")},
                    headers=_auth_headers(),
                )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 400
