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
