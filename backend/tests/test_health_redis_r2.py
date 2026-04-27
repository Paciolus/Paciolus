"""Sprint 730 — /health/redis and /health/r2 probe tests.

Covers the "not configured" happy paths (most environments) and the
unhealthy-on-failure paths via mocked clients. Does NOT spin up a real Redis
or R2 — tests are isolated via env-var manipulation and module-internal mocks.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import httpx
import pytest

sys.path.insert(0, "..")

from main import app

# ---------------------------------------------------------------------------
# /health/redis
# ---------------------------------------------------------------------------


class TestHealthRedis:
    @pytest.mark.asyncio
    async def test_returns_healthy_when_redis_url_unset(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/health/redis")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["details"]["redis"] == "not_configured"

    @pytest.mark.asyncio
    async def test_returns_healthy_on_successful_ping(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("REDIS_URL", "redis://fake-host:6379/0")

        fake_client = MagicMock()
        fake_client.ping.return_value = True

        with patch("redis.from_url", return_value=fake_client):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get("/health/redis")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["details"]["redis"] == "connected"
        assert data["latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_returns_503_on_connection_error(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("REDIS_URL", "redis://fake-host:6379/0")

        with patch("redis.from_url", side_effect=ConnectionError("refused")):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get("/health/redis")
        assert r.status_code == 503
        data = r.json()
        # FastAPI wraps the HTTPException detail under ``detail`` key.
        detail = data.get("detail", data)
        assert detail["status"] == "unhealthy"
        assert detail["details"]["redis"] == "ConnectionError"


# ---------------------------------------------------------------------------
# /health/r2
# ---------------------------------------------------------------------------


class TestHealthR2:
    @pytest.mark.asyncio
    async def test_returns_healthy_when_r2_not_configured(self):
        from shared import export_share_storage

        with patch.object(export_share_storage, "is_configured", return_value=False):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get("/health/r2")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["details"]["r2"] == "not_configured"

    @pytest.mark.asyncio
    async def test_returns_healthy_on_successful_head_bucket(self):
        from shared import export_share_storage

        fake_client = MagicMock()
        fake_client.head_bucket.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        with (
            patch.object(export_share_storage, "is_configured", return_value=True),
            patch.object(export_share_storage, "_get_client", return_value=fake_client),
            patch.object(export_share_storage, "_bucket_name", "paciolus-exports"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get("/health/r2")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert data["details"]["r2"] == "reachable"
        assert data["details"]["bucket"] == "paciolus-exports"

    @pytest.mark.asyncio
    async def test_returns_503_when_head_bucket_fails(self):
        from shared import export_share_storage

        fake_client = MagicMock()
        fake_client.head_bucket.side_effect = ConnectionError("R2 unreachable")

        with (
            patch.object(export_share_storage, "is_configured", return_value=True),
            patch.object(export_share_storage, "_get_client", return_value=fake_client),
            patch.object(export_share_storage, "_bucket_name", "paciolus-exports"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get("/health/r2")
        assert r.status_code == 503
        data = r.json()
        detail = data.get("detail", data)
        assert detail["status"] == "unhealthy"
        assert detail["details"]["r2"] == "ConnectionError"

    @pytest.mark.asyncio
    async def test_returns_unhealthy_when_client_init_returns_none(self):
        # ``is_configured`` says yes but the client lazy-init returned None
        # (a misconfiguration window). Probe should still report unhealthy
        # rather than 200 lying about reachability.
        from shared import export_share_storage

        with (
            patch.object(export_share_storage, "is_configured", return_value=True),
            patch.object(export_share_storage, "_get_client", return_value=None),
            patch.object(export_share_storage, "_bucket_name", "paciolus-exports"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                r = await client.get("/health/r2")
        assert r.status_code == 200  # 200 with details.status="unhealthy" — honest reporting
        data = r.json()
        assert data["status"] == "unhealthy"
        assert data["details"]["r2"] == "client_not_initialized"
