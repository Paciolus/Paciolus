"""Sprint 870 part B (#274): one client behind Cloudflare and Render shares one bucket.

Production returned zero 429s from 2026-10-01 to 2026-11-25. The part-A probe
showed why: every request arrives from one of Render's rotating internal
proxies (``10.x``), ``TRUSTED_PROXY_IPS`` was empty, so the anonymous key was
the proxy — a 75-request burst from one client was spread over about seven
buckets. The second ``X-Forwarded-For`` hop was a Cloudflare edge (all nine
logged hashes matched Cloudflare's published ranges).

The fix is the production value documented in ``docs/ops/ENVIRONMENT_VARIABLES.md``:
Render's internal range plus Cloudflare's. After it was set, the same burst
returned 60 × 200 then 429s. These tests pin that value against the observed
header shape, and the readiness guard that reports a missing value.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from starlette.requests import Request

from shared import rate_limits

DOC = Path(__file__).resolve().parents[2] / "docs" / "ops" / "ENVIRONMENT_VARIABLES.md"
CLIENT = "8.8.4.4"

# Observed on production 2026-11-25 (peer, Cloudflare edge): addresses from the
# same networks as the logged ones (peers are Render internal; the edges are in
# 162.158.0.0/15, 108.162.192.0/18 and 172.64.0.0/13).
HOPS = [
    ("10.29.199.206", "108.162.200.10"),
    ("10.25.65.174", "162.158.10.20"),
    ("10.28.145.177", "172.64.1.5"),
    ("10.31.190.228", "172.68.0.9"),
    ("10.29.234.203", "162.159.40.1"),
    ("10.29.5.2", "162.158.90.3"),
    ("10.31.107.142", "162.158.200.7"),
]


def _documented_value() -> frozenset[str]:
    text = DOC.read_text(encoding="utf-8")
    match = re.search(r"```\n(10\.0\.0\.0/8,[^\n`]+)\n```", text)
    assert match, "production TRUSTED_PROXY_IPS value not found in ENVIRONMENT_VARIABLES.md"
    return frozenset(part.strip() for part in match.group(1).split(","))


def _request(peer: str, xff: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/benchmarks/industries",
        "headers": [(b"x-forwarded-for", xff.encode()), (b"cf-connecting-ip", CLIENT.encode())],
        "client": (peer, 40000),
        "state": {},
    }
    return Request(scope)


@pytest.fixture
def production_trust(monkeypatch):
    monkeypatch.setattr(rate_limits, "_key_probe_count", rate_limits._KEY_PROBE_LIMIT)  # probe quiet
    monkeypatch.setattr("config.TRUSTED_PROXY_IPS", _documented_value())


def test_one_client_through_rotating_proxies_and_edges_has_one_key(production_trust):
    keys = {rate_limits._get_rate_limit_key(_request(peer, f"{CLIENT}, {edge}")) for peer, edge in HOPS}
    assert keys == {CLIENT}


def test_a_spoofed_forwarded_for_does_not_change_the_key(production_trust):
    peer, edge = HOPS[0]
    spoofed = rate_limits._get_rate_limit_key(_request(peer, f"1.2.3.4, 5.6.7.8, {CLIENT}, {edge}"))
    assert spoofed == CLIENT


def test_without_the_value_the_key_is_the_proxy_the_original_defect(monkeypatch):
    monkeypatch.setattr(rate_limits, "_key_probe_count", rate_limits._KEY_PROBE_LIMIT)
    monkeypatch.setattr("config.TRUSTED_PROXY_IPS", frozenset())
    keys = {rate_limits._get_rate_limit_key(_request(peer, f"{CLIENT}, {edge}")) for peer, edge in HOPS}
    assert len(keys) == len(HOPS)  # one client, seven buckets: no limit fires


def test_documented_value_trusts_render_internal_and_cloudflare():
    value = _documented_value()
    assert "10.0.0.0/8" in value
    for cloudflare in ("162.158.0.0/15", "108.162.192.0/18", "172.64.0.0/13", "2606:4700::/32"):
        assert cloudflare in value


class TestReadinessGuard:
    def test_production_without_trusted_proxies_is_unreliable(self, monkeypatch):
        monkeypatch.setattr("config.ENV_MODE", "production")
        monkeypatch.setattr("config.TRUSTED_PROXY_IPS", frozenset())
        assert rate_limits.get_storage_health()["client_key_unreliable"] is True

    def test_production_with_trusted_proxies_is_reliable(self, monkeypatch):
        monkeypatch.setattr("config.ENV_MODE", "production")
        monkeypatch.setattr("config.TRUSTED_PROXY_IPS", _documented_value())
        assert rate_limits.get_storage_health()["client_key_unreliable"] is False

    def test_development_is_never_flagged(self, monkeypatch):
        monkeypatch.setattr("config.ENV_MODE", "development")
        monkeypatch.setattr("config.TRUSTED_PROXY_IPS", frozenset())
        assert rate_limits.get_storage_health()["client_key_unreliable"] is False

    @pytest.mark.asyncio
    async def test_readiness_reports_degraded(self, monkeypatch):
        import httpx

        from main import app

        monkeypatch.setattr("config.ENV_MODE", "production")
        monkeypatch.setattr("config.TRUSTED_PROXY_IPS", frozenset())
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health/ready")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "degraded"
        assert body["dependencies"]["rate_limit_storage"]["details"]["client_key_unreliable"] is True
