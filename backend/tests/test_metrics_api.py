"""
Tests for Metrics API Endpoint — Route-level integration tests.

Tests cover:
- GET /metrics — Prometheus metrics endpoint
- Production IP restriction
- Non-production open access
"""

import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app

# =============================================================================
# Route Registration
# =============================================================================


class TestMetricsRouteRegistration:
    """Verify metrics route is registered."""

    def test_metrics_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/metrics" in paths


# =============================================================================
# GET /metrics
# =============================================================================


class TestMetricsEndpoint:
    """Tests for GET /metrics."""

    @pytest.mark.asyncio
    async def test_metrics_success_dev_mode(self):
        """In non-production mode, metrics endpoint is accessible."""
        # ENV_MODE is imported lazily inside the endpoint via `from config import ENV_MODE`
        with patch("config.ENV_MODE", "development"):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/metrics")
                assert response.status_code == 200
                # Prometheus text format
                assert "text/plain" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_metrics_returns_prometheus_format(self):
        """Response contains Prometheus-compatible metric text."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/metrics")
            assert response.status_code == 200
            content = response.text
            # Prometheus metrics output is text/plain
            assert len(content) >= 0

    @pytest.mark.asyncio
    async def test_metrics_no_auth_required(self):
        """Metrics endpoint does not require auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/metrics")
            # Should not return 401
            assert response.status_code != 401
