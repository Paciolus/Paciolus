"""Sprint 852 (security review L7, L8): export-share hygiene.

- L7: a passcode mismatch logs a hashed client IP, never the raw one.
- L8: CSV share bytes were client-supplied, so they were re-written through the
  server's formula escaping. Sprint 880 (OUT-03) replaced that: only files the
  server generated (and so already escaped by SafeCsvWriter) can be shared, so a
  client-made CSV is refused outright.
"""

import base64
import logging
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from security_middleware import hash_ip_address
from shared.export_provenance import sign_export

pytestmark = [pytest.mark.usefixtures("limiter_enabled", "bypass_csrf"), pytest.mark.anyio]

_VALID_PDF_BYTES = b"%PDF-1.4 minimal test content"


async def _post_share(client: httpx.AsyncClient, export_format: str, data: bytes, **extra) -> httpx.Response:
    return await client.post(
        "/export-sharing/create",
        json={
            "tool_name": "trial_balance",
            "export_format": export_format,
            "export_data_b64": base64.b64encode(data).decode(),
            **extra,
        },
    )


async def _create_share(client: httpx.AsyncClient, export_format: str, data: bytes, **extra) -> str:
    token = sign_export(user_id=client.user_id, export_format=export_format, data=data)  # type: ignore[attr-defined]
    resp = await _post_share(client, export_format, data, export_token=token, **extra)
    assert resp.status_code == 200, resp.text
    return resp.json()["share_token"]


@pytest.fixture
def _app_as(db_session, make_user):
    from auth import require_verified_user
    from database import get_db
    from main import app

    def _bind(email: str):
        user = make_user(email=email, tier=UserTier.PROFESSIONAL)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session
        client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
        client.user_id = user.id  # type: ignore[attr-defined]
        return client

    yield _bind
    app.dependency_overrides.clear()


class TestPasscodeMismatchLogsHashedIp:
    async def test_raw_ip_is_not_logged(self, _app_as, caplog):
        async with _app_as("l7_ip_hash@example.com") as client:
            token = await _create_share(client, "pdf", _VALID_PDF_BYTES, passcode="StrongP@ss1")
            with caplog.at_level(logging.INFO, logger="routes.export_sharing"):
                resp = await client.post(f"/export-sharing/{token}/download", json={"passcode": "WRONGpass2!"})
        assert resp.status_code == 403

        mismatch = [r.getMessage() for r in caplog.records if "passcode mismatch" in r.getMessage()]
        assert len(mismatch) == 1
        # httpx's ASGITransport presents the client as 127.0.0.1.
        assert "127.0.0.1" not in mismatch[0]
        assert hash_ip_address("127.0.0.1") in mismatch[0]


class TestClientMadeCsvIsRefused:
    async def test_a_csv_with_formula_cells_not_made_by_paciolus_is_refused(self, _app_as):
        raw = (
            b'account,amount,memo\r\n=HYPERLINK("https://evil.example","Click"),100,@SUM(A1)\r\nCash,-1250.50,+cmd\r\n'
        )
        async with _app_as("l8_csv_escape@example.com") as client:
            no_token = await _post_share(client, "csv", raw)
            forged = await _post_share(client, "csv", raw, export_token="not.a-token")
        assert no_token.status_code == 422
        assert forged.status_code == 400
