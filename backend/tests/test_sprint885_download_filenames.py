"""Sprint 885 / 10E (review OUT-28): non-English file names download correctly.

``safe_download_filename`` keeps non-ASCII letters and the name went straight
into ``Content-Disposition``. HTTP headers are Latin-1, so a name derived
from "北京.csv" raised UnicodeEncodeError (a 500), and "Café" went out as
Latin-1 bytes a browser may misread. Every download now sends an ASCII
fallback ``filename="..."`` plus the standard ``filename*=UTF-8''...`` form,
built in one place for ordinary and shared downloads.

Checked through real HTTP responses.
"""

from __future__ import annotations

import base64
import re
from urllib.parse import unquote

import httpx
import pytest

from models import UserTier

NAMES = {
    "chinese": "北京",
    "cyrillic": "Москва Отчёт",
    "accented": "Café Société",
    "quoted": 'Client "Big" Co; x=1',
    "very_long": "Ledger" * 120,
}


def _parse(header: str) -> tuple[str | None, str | None]:
    """(ASCII fallback, decoded filename*) from a Content-Disposition value."""
    header.encode("ascii")  # must be pure ASCII
    fallback = re.search(r'filename="([^"]*)"', header)
    star = re.search(r"filename\*=UTF-8''([^;\s]+)", header)
    return (fallback.group(1) if fallback else None, unquote(star.group(1), encoding="utf-8") if star else None)


def _check(header: str, source: str) -> None:
    assert header.startswith("attachment;")
    fallback, full = _parse(header)
    assert fallback, header
    assert re.fullmatch(r"[A-Za-z0-9._-]+", fallback), fallback
    assert len(header) < 600, len(header)
    expected = "".join(c for c in source if c.isalnum())[:40]
    shown = "".join(c for c in (full or fallback) if c.isalnum())
    if any(ord(c) > 127 for c in source):
        assert full is not None, header
    assert expected in shown, (shown, expected)


_AUDIT = {
    "status": "balanced",
    "balanced": True,
    "total_debits": 100.0,
    "total_credits": 100.0,
    "difference": 0.0,
    "row_count": 1,
    "message": "ok",
    "abnormal_balances": [{"account": "Cash", "type": "asset", "issue": "x", "amount": 1.0, "materiality": "material"}],
    "has_risk_alerts": True,
    "materiality_threshold": 10.0,
    "material_count": 1,
    "immaterial_count": 0,
}


@pytest.mark.usefixtures("bypass_csrf")
class TestOrdinaryDownloads:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("label", list(NAMES))
    async def test_csv_download(self, override_auth_verified, label):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json={**_AUDIT, "filename": NAMES[label]})
        assert response.status_code == 200, response.text[:200]
        _check(response.headers["content-disposition"], NAMES[label])

    @pytest.mark.asyncio
    async def test_pdf_download(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/pdf", json={**_AUDIT, "filename": NAMES["chinese"]})
        assert response.status_code == 200, response.text[:200]
        _check(response.headers["content-disposition"], NAMES["chinese"])

    @pytest.mark.asyncio
    async def test_plain_ascii_name_keeps_its_form(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/anomalies", json={**_AUDIT, "filename": "Client_ABC"})
        header = response.headers["content-disposition"]
        assert re.fullmatch(r'attachment; filename="Client_ABC_Anomalies_\d{8}_\d{6}\.csv"', header), header


@pytest.fixture
def share_client(db_session, make_user):
    from auth import require_verified_user
    from database import get_db
    from main import app

    user = make_user(email="sprint885_share_names@example.com", tier=UserTier.PROFESSIONAL)
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("bypass_csrf")
class TestSharedDownloads:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("label", list(NAMES))
    async def test_shared_download(self, share_client, label):
        async with share_client as client:
            created = await client.post(
                "/export-sharing/create",
                json={
                    "tool_name": NAMES[label][:100],
                    "export_format": "pdf",
                    "export_data_b64": base64.b64encode(b"%PDF-1.4 test").decode(),
                },
            )
            assert created.status_code == 200, created.text
            response = await client.get(f"/export-sharing/{created.json()['share_token']}")
        assert response.status_code == 200, response.text[:200]
        _check(response.headers["content-disposition"], NAMES[label][:80])


class TestHeaderBuilder:
    def test_one_shared_builder(self):
        from shared.filenames import content_disposition

        fallback, full = _parse(content_disposition("北京_Diagnostic.csv"))
        assert fallback == "Diagnostic.csv"
        assert full == "北京_Diagnostic.csv"

    def test_accented_fallback_is_transliterated(self):
        from shared.filenames import content_disposition

        fallback, full = _parse(content_disposition("Café_Société.pdf"))
        assert fallback == "Cafe_Societe.pdf"
        assert full == "Café_Société.pdf"


def test_long_non_latin_name_keeps_the_header_short():
    from shared.filenames import content_disposition, safe_download_filename

    header = content_disposition(safe_download_filename("北" * 200, "Diagnostic", "pdf"))
    assert len(header) < 600
    _parse(header)
