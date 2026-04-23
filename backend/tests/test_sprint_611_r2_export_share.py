"""
Sprint 611: ExportShare Object Store Migration tests.

Pins the three new behaviours:
  1. ``shared.export_share_storage`` env-var-driven lazy init — off by
     default, on when all four ``R2_EXPORTS_*`` vars are set.
  2. Route: when R2 is configured, ``create_share`` uploads bytes to R2
     and the DB row stores ``object_key`` (not ``export_data``); download
     streams from R2; revoke deletes the R2 object.
  3. Cleanup scheduler: expired/revoked rows whose bytes live in R2
     trigger ``export_share_storage.delete`` before the DB DELETE.

R2 I/O is patched with an in-memory dict so tests run without network
access.  The inline-blob fallback path is already exercised by
``test_export_sharing_routes.py``.
"""

from __future__ import annotations

import base64
import hashlib
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from export_share_model import ExportShare
from models import UserTier
from shared import export_share_storage

VALID_PDF_BYTES = b"%PDF-1.4 sprint611 test content"


# ---------------------------------------------------------------------------
# Fake R2 — an in-memory bucket that matches the storage-module surface.
# ---------------------------------------------------------------------------


class _FakeR2:
    """Dict-backed stand-in for the boto3 S3 client against R2."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.upload_calls: list[tuple[str, int, str]] = []
        self.delete_calls: list[str] = []

    def upload(self, share_token_hash: str, data: bytes, content_type: str) -> str:
        key = f"shares/{share_token_hash}"
        self.objects[key] = data
        self.upload_calls.append((key, len(data), content_type))
        return key

    def download(self, object_key: str) -> bytes | None:
        return self.objects.get(object_key)

    def delete(self, object_key: str) -> bool:
        self.delete_calls.append(object_key)
        return self.objects.pop(object_key, None) is not None


@pytest.fixture
def fake_r2(monkeypatch: pytest.MonkeyPatch) -> _FakeR2:
    """Patch the storage module to behave as R2-configured with a fake bucket."""
    fake = _FakeR2()
    monkeypatch.setattr(export_share_storage, "is_configured", lambda: True)
    monkeypatch.setattr(export_share_storage, "upload", fake.upload)
    monkeypatch.setattr(export_share_storage, "download", fake.download)
    monkeypatch.setattr(export_share_storage, "delete", fake.delete)
    return fake


# ---------------------------------------------------------------------------
# Storage-module unit tests (real lazy-init path, no network)
# ---------------------------------------------------------------------------


class TestStorageModuleLazyInit:
    """The four ``R2_EXPORTS_*`` env vars drive ``is_configured()``."""

    def test_not_configured_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for var in (
            "R2_EXPORTS_BUCKET",
            "R2_EXPORTS_ENDPOINT",
            "R2_EXPORTS_ACCESS_KEY_ID",
            "R2_EXPORTS_SECRET_ACCESS_KEY",
        ):
            monkeypatch.delenv(var, raising=False)
        export_share_storage._reset_for_tests()
        assert export_share_storage.is_configured() is False

    def test_not_configured_with_partial_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R2_EXPORTS_BUCKET", "paciolus-exports")
        monkeypatch.setenv("R2_EXPORTS_ENDPOINT", "https://fake.r2.cloudflarestorage.com")
        # Missing access key + secret — must NOT be considered configured.
        monkeypatch.delenv("R2_EXPORTS_ACCESS_KEY_ID", raising=False)
        monkeypatch.delenv("R2_EXPORTS_SECRET_ACCESS_KEY", raising=False)
        export_share_storage._reset_for_tests()
        assert export_share_storage.is_configured() is False

    def test_download_returns_none_when_not_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for var in (
            "R2_EXPORTS_BUCKET",
            "R2_EXPORTS_ENDPOINT",
            "R2_EXPORTS_ACCESS_KEY_ID",
            "R2_EXPORTS_SECRET_ACCESS_KEY",
        ):
            monkeypatch.delenv(var, raising=False)
        export_share_storage._reset_for_tests()
        assert export_share_storage.download("shares/does-not-matter") is None

    def test_delete_returns_false_when_not_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for var in (
            "R2_EXPORTS_BUCKET",
            "R2_EXPORTS_ENDPOINT",
            "R2_EXPORTS_ACCESS_KEY_ID",
            "R2_EXPORTS_SECRET_ACCESS_KEY",
        ):
            monkeypatch.delenv(var, raising=False)
        export_share_storage._reset_for_tests()
        assert export_share_storage.delete("shares/does-not-matter") is False


# ---------------------------------------------------------------------------
# Route behaviour when R2 is configured
# ---------------------------------------------------------------------------


class TestCreateShareUsesR2:
    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_create_uploads_to_r2_and_omits_blob(
        self,
        db_session: Any,
        make_user: Any,
        fake_r2: _FakeR2,
    ) -> None:
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="sprint611_create@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
        finally:
            app.dependency_overrides.clear()

        assert resp.status_code == 200, resp.text
        token = resp.json()["share_token"]
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Exactly one R2 upload happened for this hash.
        assert len(fake_r2.upload_calls) == 1
        uploaded_key, size, ctype = fake_r2.upload_calls[0]
        assert uploaded_key == f"shares/{token_hash}"
        assert size == len(VALID_PDF_BYTES)
        assert ctype == "application/pdf"

        # DB row stores key; inline blob is NOT populated.
        share = db_session.query(ExportShare).filter_by(share_token_hash=token_hash).one()
        assert share.object_key == f"shares/{token_hash}"
        assert share.export_data is None

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_streams_from_r2(
        self,
        db_session: Any,
        make_user: Any,
        fake_r2: _FakeR2,
    ) -> None:
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="sprint611_dl@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                create = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                token = create.json()["share_token"]
                dl = await client.get(f"/export-sharing/{token}")
        finally:
            app.dependency_overrides.clear()

        assert dl.status_code == 200
        assert dl.content == VALID_PDF_BYTES
        assert dl.headers["content-type"].startswith("application/pdf")

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_download_returns_410_when_r2_object_missing(
        self,
        db_session: Any,
        make_user: Any,
        fake_r2: _FakeR2,
    ) -> None:
        """DB row with object_key but missing R2 object must 410, not empty body."""
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="sprint611_missing@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                create = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                token = create.json()["share_token"]

                # Simulate the bucket object vanishing out from under the row.
                fake_r2.objects.clear()

                dl = await client.get(f"/export-sharing/{token}")
        finally:
            app.dependency_overrides.clear()

        assert dl.status_code == 410

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_revoke_deletes_r2_object(
        self,
        db_session: Any,
        make_user: Any,
        fake_r2: _FakeR2,
    ) -> None:
        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="sprint611_revoke@example.com", tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                create = await client.post(
                    "/export-sharing/create",
                    json={
                        "tool_name": "trial_balance",
                        "export_format": "pdf",
                        "export_data_b64": base64.b64encode(VALID_PDF_BYTES).decode(),
                    },
                )
                token = create.json()["share_token"]
                revoke = await client.delete(f"/export-sharing/{token}")
        finally:
            app.dependency_overrides.clear()

        assert revoke.status_code == 200
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        assert f"shares/{token_hash}" in fake_r2.delete_calls
        assert fake_r2.objects == {}


# ---------------------------------------------------------------------------
# Cleanup scheduler — expired/revoked rows with object_key purge R2 too
# ---------------------------------------------------------------------------


class TestCleanupSchedulerPurgesR2:
    def test_expired_shares_trigger_r2_delete(
        self,
        db_session: Any,
        make_user: Any,
        fake_r2: _FakeR2,
    ) -> None:
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="sprint611_cleanup@example.com", tier=UserTier.PROFESSIONAL)

        # Two rows: one R2-backed, one inline-blob (simulates a pre-flip row).
        r2_hash = "a" * 64
        inline_hash = "b" * 64
        fake_r2.objects[f"shares/{r2_hash}"] = b"stored-in-r2"

        past = datetime.now(UTC) - timedelta(hours=1)
        db_session.add(
            ExportShare(
                user_id=user.id,
                share_token_hash=r2_hash,
                tool_name="trial_balance",
                export_format="pdf",
                export_data=None,
                object_key=f"shares/{r2_hash}",
                expires_at=past,
            )
        )
        db_session.add(
            ExportShare(
                user_id=user.id,
                share_token_hash=inline_hash,
                tool_name="trial_balance",
                export_format="pdf",
                export_data=b"stored-inline",
                object_key=None,
                expires_at=past,
            )
        )
        db_session.commit()

        deleted = purge_expired_export_shares(db_session)

        assert deleted == 2
        # R2 object gone; inline row was never in R2 so no delete call for it.
        assert fake_r2.delete_calls == [f"shares/{r2_hash}"]
        assert fake_r2.objects == {}
        # Both DB rows purged.
        assert db_session.query(ExportShare).count() == 0

    def test_revoked_share_with_r2_object_triggers_delete(
        self,
        db_session: Any,
        make_user: Any,
        fake_r2: _FakeR2,
    ) -> None:
        """Revoked (but not yet expired) rows also fire the R2 delete."""
        from cleanup_scheduler import purge_expired_export_shares

        user = make_user(email="sprint611_revoked_cleanup@example.com", tier=UserTier.PROFESSIONAL)

        token_hash = "c" * 64
        fake_r2.objects[f"shares/{token_hash}"] = b"bytes"

        future = datetime.now(UTC) + timedelta(hours=24)
        db_session.add(
            ExportShare(
                user_id=user.id,
                share_token_hash=token_hash,
                tool_name="trial_balance",
                export_format="pdf",
                export_data=None,
                object_key=f"shares/{token_hash}",
                expires_at=future,
                revoked_at=datetime.now(UTC),
            )
        )
        db_session.commit()

        deleted = purge_expired_export_shares(db_session)
        assert deleted == 1
        assert fake_r2.delete_calls == [f"shares/{token_hash}"]
        assert db_session.query(ExportShare).count() == 0

    def test_no_rows_no_r2_calls(
        self,
        db_session: Any,
        fake_r2: _FakeR2,
    ) -> None:
        from cleanup_scheduler import purge_expired_export_shares

        assert purge_expired_export_shares(db_session) == 0
        assert fake_r2.delete_calls == []
