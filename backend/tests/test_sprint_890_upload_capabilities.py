"""Sprint 890 (CEO brief 15B, review ST-05): one source for upload limits and enabled formats.

``GET /upload/capabilities`` serves what the upload pipeline enforces; the frontend derives its
pickers, client-side checks, labels and too-large message from it. Its defaults file is the
backend's own response under default configuration, so the two cannot drift.
"""

import json
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from routes.upload_capabilities import upload_capabilities
from shared.file_formats import FileFormat, get_active_extensions_display
from shared.upload_pipeline import MAX_FILE_SIZE_BYTES, MAX_ROW_COUNT

FRONTEND_DEFAULTS = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "content" / "upload-capabilities.default.json"
)


def _extensions(caps) -> set[str]:
    return {e for f in caps.formats for e in f.extensions}


def test_limits_are_the_ones_the_pipeline_enforces():
    caps = upload_capabilities()
    assert caps.max_file_size_bytes == MAX_FILE_SIZE_BYTES == 100 * 1024 * 1024
    assert caps.max_file_size_mb == 100
    assert caps.max_rows == MAX_ROW_COUNT == 500_000
    assert caps.bulk_max_files == 5


def test_ods_is_off_by_default_and_docx_on():
    exts = _extensions(upload_capabilities())
    assert ".ods" not in exts
    assert ".docx" in exts
    assert exts == {".csv", ".xlsx", ".xls", ".tsv", ".txt", ".qbo", ".ofx", ".iif", ".pdf", ".docx"}


def test_a_format_disabled_by_configuration_disappears_everywhere():
    with patch("config.FORMAT_PDF_ENABLED", False):
        assert ".pdf" not in _extensions(upload_capabilities())
        assert "PDF" not in get_active_extensions_display()
    with patch("config.FORMAT_ODS_ENABLED", True):
        assert ".ods" in _extensions(upload_capabilities())
        assert "ODS" in get_active_extensions_display()


def test_error_message_no_longer_names_a_disabled_format():
    assert "ODS" not in get_active_extensions_display()
    assert FileFormat.ODS.value == "ods"


def test_frontend_defaults_are_the_backend_default_response():
    served = upload_capabilities().model_dump()
    assert json.loads(FRONTEND_DEFAULTS.read_text(encoding="utf-8")) == served, (
        "frontend/src/content/upload-capabilities.default.json drifted from upload_capabilities(); "
        "rewrite it from the backend response"
    )


@pytest.mark.asyncio
async def test_route_is_public_and_serves_the_values():
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/upload/capabilities")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["max_file_size_mb"] == 100
    assert isinstance(body["max_file_size_bytes"], int)
    assert {e for f in body["formats"] for e in f["extensions"]} == _extensions(upload_capabilities())
