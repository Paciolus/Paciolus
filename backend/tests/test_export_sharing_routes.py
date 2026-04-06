"""
Export sharing route tests — BUG-03 regression tests.

BUG-03: Export sharing trusts client-supplied bytes and serves them on a public URL.
Tests that content-type validation and magic-byte checking are enforced.
"""

import base64
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier

# ---------------------------------------------------------------------------
# Test data: valid and invalid payloads by format
# ---------------------------------------------------------------------------

# Minimal valid PDF (just magic bytes + minimal structure)
VALID_PDF_BYTES = b"%PDF-1.4 minimal test content"

# Minimal valid XLSX (ZIP magic bytes — all xlsx files start with PK)
VALID_XLSX_BYTES = b"PK\x03\x04" + b"\x00" * 100

# Valid CSV content
VALID_CSV_BYTES = b"account,amount\nCash,1000\nRevenue,2000\n"

# Invalid: random binary that doesn't match any format
RANDOM_BINARY = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a" + b"\xff" * 100  # PNG magic bytes

# Invalid: executable-like bytes
EXE_BYTES = b"MZ" + b"\x00" * 200

# Invalid: binary masquerading as CSV
BINARY_AS_CSV = bytes(range(256)) * 4


class TestExportSharingMagicByteValidation:
    """BUG-03: Ensure magic-byte validation rejects arbitrary content."""

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_valid_pdf_accepted(self, db_session, make_user):
        """Legitimate PDF content should be accepted."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="share_pdf@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert "share_token" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_valid_xlsx_accepted(self, db_session, make_user):
        """Legitimate XLSX content should be accepted."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="share_xlsx@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "xlsx",
                        "export_data_b64": base64.b64encode(VALID_XLSX_BYTES).decode(),
                    },
                )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_valid_csv_accepted(self, db_session, make_user):
        """Legitimate CSV content should be accepted."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="share_csv@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "csv",
                        "export_data_b64": base64.b64encode(VALID_CSV_BYTES).decode(),
                    },
                )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_arbitrary_binary_as_pdf_rejected(self, db_session, make_user):
        """Random binary bytes claiming to be PDF must be rejected."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="share_bin_pdf@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(RANDOM_BINARY).decode(),
                    },
                )
            assert resp.status_code == 400
            assert "does not match" in resp.json()["detail"].lower() or "format" in resp.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_arbitrary_binary_as_xlsx_rejected(self, db_session, make_user):
        """Random binary bytes claiming to be XLSX must be rejected."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="share_bin_xlsx@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "xlsx",
                        "export_data_b64": base64.b64encode(EXE_BYTES).decode(),
                    },
                )
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_binary_as_csv_rejected(self, db_session, make_user):
        """Binary data masquerading as CSV must be rejected."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="share_bin_csv@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "csv",
                        "export_data_b64": base64.b64encode(BINARY_AS_CSV).decode(),
                    },
                )
            assert resp.status_code == 400
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_returns_correct_artifact(self, db_session, make_user):
        """After creating a share, the public download endpoint returns the right content."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="share_dl@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Create
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                # Download (public, no auth needed — clear overrides for realism)
                dl_resp = await client.get(f"/export-sharing/{token}")
                assert dl_resp.status_code == 200
                assert dl_resp.content == VALID_PDF_BYTES
                assert "application/pdf" in dl_resp.headers.get("content-type", "")
        finally:
            app.dependency_overrides.clear()


class TestExportSharingMagicByteUnit:
    """Unit tests for the _validate_export_magic_bytes function."""

    def test_valid_pdf_passes(self):
        from routes.export_sharing import _validate_export_magic_bytes

        _validate_export_magic_bytes(VALID_PDF_BYTES, "pdf")  # Should not raise

    def test_invalid_pdf_raises(self):
        from routes.export_sharing import _validate_export_magic_bytes

        with pytest.raises(Exception):
            _validate_export_magic_bytes(RANDOM_BINARY, "pdf")

    def test_valid_xlsx_passes(self):
        from routes.export_sharing import _validate_export_magic_bytes

        _validate_export_magic_bytes(VALID_XLSX_BYTES, "xlsx")

    def test_invalid_xlsx_raises(self):
        from routes.export_sharing import _validate_export_magic_bytes

        with pytest.raises(Exception):
            _validate_export_magic_bytes(b"NOT_A_ZIP" + b"\x00" * 100, "xlsx")

    def test_valid_csv_passes(self):
        from routes.export_sharing import _validate_export_magic_bytes

        _validate_export_magic_bytes(VALID_CSV_BYTES, "csv")

    def test_binary_csv_raises(self):
        from routes.export_sharing import _validate_export_magic_bytes

        with pytest.raises(Exception):
            _validate_export_magic_bytes(BINARY_AS_CSV, "csv")


# ---------------------------------------------------------------------------
# Sprint 593: Passcode Protection Tests
# ---------------------------------------------------------------------------


class TestExportSharingPasscode:
    """Sprint 593: Passcode protection for share links."""

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_create_share_with_passcode(self, db_session, make_user):
        """Creating a share with a passcode sets has_passcode=True."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="pass_create@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                        "passcode": "mySecret1",
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            assert data["has_passcode"] is True
            assert "share_token" in data
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_with_correct_passcode(self, db_session, make_user):
        """Download succeeds with the correct passcode."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="pass_correct@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                        "passcode": "secret123",
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                dl_resp = await client.get(f"/export-sharing/{token}?passcode=secret123")
                assert dl_resp.status_code == 200
                assert dl_resp.content == VALID_PDF_BYTES
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_with_wrong_passcode_returns_403(self, db_session, make_user):
        """Download returns 403 with an incorrect passcode."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="pass_wrong@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                        "passcode": "secret123",
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                dl_resp = await client.get(f"/export-sharing/{token}?passcode=wrongpass")
                assert dl_resp.status_code == 403
                assert "invalid passcode" in dl_resp.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_without_passcode_when_required_returns_403(self, db_session, make_user):
        """Download returns 403 when passcode is required but not provided."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="pass_missing@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                        "passcode": "secret123",
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                dl_resp = await client.get(f"/export-sharing/{token}")
                assert dl_resp.status_code == 403
                assert "requires a passcode" in dl_resp.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_without_passcode_when_none_set_succeeds(self, db_session, make_user):
        """Backward compat: shares without passcode download fine without one."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="pass_none@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                dl_resp = await client.get(f"/export-sharing/{token}")
                assert dl_resp.status_code == 200
                assert dl_resp.content == VALID_PDF_BYTES
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sprint 593: Single-Use Mode Tests
# ---------------------------------------------------------------------------


class TestExportSharingSingleUse:
    """Sprint 593: Single-use share links auto-revoke after first download."""

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_create_single_use_share(self, db_session, make_user):
        """Creating a single-use share returns single_use=True."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="single_create@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                        "single_use": True,
                    },
                )
            assert resp.status_code == 200
            assert resp.json()["single_use"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_single_use_auto_revokes_after_download(self, db_session, make_user):
        """Single-use share: first download succeeds, second returns 404 (revoked)."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="single_revoke@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                        "single_use": True,
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                # First download succeeds
                dl1 = await client.get(f"/export-sharing/{token}")
                assert dl1.status_code == 200
                assert dl1.content == VALID_PDF_BYTES

                # Second download fails (revoked)
                dl2 = await client.get(f"/export-sharing/{token}")
                assert dl2.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_non_single_use_allows_multiple_downloads(self, db_session, make_user):
        """Regular shares allow multiple downloads."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="multi_dl@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                for _ in range(3):
                    dl = await client.get(f"/export-sharing/{token}")
                    assert dl.status_code == 200
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sprint 593: Security Headers Tests
# ---------------------------------------------------------------------------


class TestExportSharingSecurityHeaders:
    """Sprint 593: Download responses must include security headers."""

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_response_has_security_headers(self, db_session, make_user):
        """Download response includes Cache-Control: no-store and middleware security headers."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="headers@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                dl = await client.get(f"/export-sharing/{token}")
                assert dl.status_code == 200
                # Route-level: prevent caching of exported artifacts
                assert dl.headers.get("cache-control") == "no-store"
                # Middleware-level: standard security headers
                assert dl.headers.get("x-content-type-options") == "nosniff"
                assert dl.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sprint 593: Tier-Configurable TTL Tests
# ---------------------------------------------------------------------------


class TestExportSharingTierTTL:
    """Sprint 593: Share TTL depends on user tier."""

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_professional_share_expires_in_24h(self, db_session, make_user):
        """Professional tier shares expire in approximately 24 hours."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="ttl_pro@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            from datetime import datetime as dt

            created = dt.fromisoformat(data["created_at"])
            expires = dt.fromisoformat(data["expires_at"])
            diff_hours = (expires - created).total_seconds() / 3600
            assert 23.5 < diff_hours < 24.5, f"Expected ~24h TTL, got {diff_hours:.1f}h"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_enterprise_share_expires_in_48h(self, db_session, make_user):
        """Enterprise tier shares expire in approximately 48 hours."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="ttl_ent@example.com", tier=UserTier.ENTERPRISE)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
            assert resp.status_code == 200
            data = resp.json()
            from datetime import datetime as dt

            created = dt.fromisoformat(data["created_at"])
            expires = dt.fromisoformat(data["expires_at"])
            diff_hours = (expires - created).total_seconds() / 3600
            assert 47.5 < diff_hours < 48.5, f"Expected ~48h TTL, got {diff_hours:.1f}h"
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Sprint 593: Anomaly Logging Tests
# ---------------------------------------------------------------------------


class TestExportSharingAnomalyLogging:
    """Sprint 593: Warning log when access count exceeds threshold."""

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_high_access_count_triggers_warning_log(self, db_session, make_user, caplog):
        """After >10 downloads, a warning-level log is emitted."""
        from auth import require_verified_user
        from database import get_db
        from export_share_model import ExportShare
        from main import app

        user = make_user(email="anomaly@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                assert resp.status_code == 200
                token = resp.json()["share_token"]

                # Pre-set access_count to threshold to avoid 11 real requests
                import hashlib

                token_hash = hashlib.sha256(token.encode()).hexdigest()
                share = db_session.query(ExportShare).filter(ExportShare.share_token_hash == token_hash).first()
                share.access_count = 10
                db_session.commit()

                import logging

                with caplog.at_level(logging.WARNING, logger="routes.export_sharing"):
                    dl = await client.get(f"/export-sharing/{token}")
                    assert dl.status_code == 200

                assert any("anomaly" in r.message.lower() for r in caplog.records), (
                    "Expected anomaly warning log not found"
                )
        finally:
            app.dependency_overrides.clear()
