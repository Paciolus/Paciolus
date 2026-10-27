"""Sprint 852 (security review L6): share and invite tokens never reach the access log.

Gunicorn's own access log (``--access-logfile -``) is removed from the
Dockerfile, which leaves HttpMetricsMiddleware as the only access log. It
must therefore redact the bearer tokens that travel in URL paths.
"""

import logging
import secrets
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from http_metrics_middleware import HttpMetricsMiddleware, _normalize_path, _redact_path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(HttpMetricsMiddleware)

    @app.get("/export-sharing/{token}")
    async def _share(token: str):
        return {"ok": True}

    @app.post("/organization/invite/accept/{token}")
    async def _invite(token: str):
        return {"ok": True}

    return app


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/export-sharing/TOKEN", "/export-sharing/{token}"),
        ("/export-sharing/TOKEN/download", "/export-sharing/{token}/download"),
        ("/organization/invite/accept/TOKEN", "/organization/invite/accept/{token}"),
    ],
)
def test_urlsafe_tokens_are_redacted(path, expected):
    # The real token format, including the - and _ characters the old hex-only
    # pattern could not match.
    token = secrets.token_urlsafe(32)
    token = "-_" + token[2:]
    assert _redact_path(path.replace("TOKEN", token)) == expected
    assert _normalize_path(path.replace("TOKEN", token)) == expected


def test_non_secret_paths_are_untouched_by_redaction():
    assert _redact_path("/export-sharing/create") == "/export-sharing/create"
    assert _redact_path("/clients/42") == "/clients/42"


@pytest.mark.asyncio
async def test_access_log_line_never_contains_the_token(caplog):
    share_token = secrets.token_urlsafe(32)
    invite_token = secrets.token_urlsafe(32)
    transport = httpx.ASGITransport(app=_app())
    with caplog.at_level(logging.INFO, logger="paciolus.access"):
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get(f"/export-sharing/{share_token}")).status_code == 200
            assert (await client.post(f"/organization/invite/accept/{invite_token}")).status_code == 200

    access_lines = [r.getMessage() for r in caplog.records if r.name == "paciolus.access"]
    assert len(access_lines) == 2
    assert all(share_token not in line and invite_token not in line for line in access_lines)
    assert "GET /export-sharing/{token} 200" in access_lines[0]
    assert "POST /organization/invite/accept/{token} 200" in access_lines[1]


def test_gunicorn_access_log_is_disabled():
    """The gunicorn/uvicorn access log records raw paths; it must stay off."""
    dockerfile = (_BACKEND_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "--access-logfile" not in dockerfile
