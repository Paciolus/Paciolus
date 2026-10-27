"""Sprint 852 (security review L7, L8): export-share hygiene.

- L7: a passcode mismatch logs a hashed client IP, never the raw one.
- L8: CSV share bytes are client-supplied, so they are re-written through the
  server's formula escaping (SafeCsvWriter) before they are stored.
"""

import base64
import logging
import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from routes.export_sharing import _rewrite_csv_share
from security_middleware import hash_ip_address

pytestmark = [pytest.mark.usefixtures("limiter_enabled", "bypass_csrf"), pytest.mark.anyio]

_VALID_PDF_BYTES = b"%PDF-1.4 minimal test content"


async def _create_share(client: httpx.AsyncClient, export_format: str, data: bytes, **extra) -> str:
    resp = await client.post(
        "/export-sharing/create",
        json={
            "tool_name": "trial_balance",
            "export_format": export_format,
            "export_data_b64": base64.b64encode(data).decode(),
            **extra,
        },
    )
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
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")

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


class TestCsvShareIsReEscaped:
    async def test_formula_cells_are_escaped_on_the_server(self, _app_as):
        raw = (
            b'account,amount,memo\r\n=HYPERLINK("https://evil.example","Click"),100,@SUM(A1)\r\nCash,-1250.50,+cmd\r\n'
        )
        async with _app_as("l8_csv_escape@example.com") as client:
            token = await _create_share(client, "csv", raw)
            dl = await client.get(f"/export-sharing/{token}")
        assert dl.status_code == 200
        body = dl.content.decode("utf-8")
        assert "'=HYPERLINK" in body
        assert "'@SUM(A1)" in body
        assert "'+cmd" in body
        # A plain negative amount stays numeric, and no line starts with a formula.
        assert ",-1250.50," in body
        assert not any(line.startswith(("=", "+", "@")) for line in body.splitlines())

    def test_rewrite_is_idempotent_for_paciolus_exports(self):
        already_safe = "﻿account,amount\r\n'=Cash,-5\r\nRevenue,2000\r\n".encode()
        assert _rewrite_csv_share(already_safe) == already_safe

    def test_bom_is_preserved(self):
        out = _rewrite_csv_share("﻿a,b\r\n=1+1,2\r\n".encode())
        assert out.startswith(b"\xef\xbb\xbf")
        assert out.decode("utf-8-sig") == "a,b\r\n'=1+1,2\r\n"
