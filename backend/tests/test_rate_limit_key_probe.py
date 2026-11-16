"""Sprint 870 (#274): the rate-limit key-derivation probe.

The probe exists to answer one production question — what does the anonymous
rate-limit key look like behind Render's proxy — without logging a customer
address. These tests pin what it records, that public addresses are hashed,
that it is bounded, and that it can never fail a request.
"""

import logging

import pytest
from starlette.requests import Request

from security_middleware import hash_ip_address
from shared import rate_limits

PROXY = "10.201.4.17"
CLIENT = "8.8.4.4"  # globally routable: TEST-NET ranges are not, and would log raw


def _request(peer: str, headers: dict[str, str] | None = None) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/benchmarks/industries",
        "headers": raw,
        "client": (peer, 40000),
        "state": {},
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def _reset_probe(monkeypatch):
    monkeypatch.setattr(rate_limits, "_key_probe_count", 0)
    monkeypatch.setattr("config.TRUSTED_PROXY_IPS", frozenset())


def _probe_lines(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith("rate_limit_key_probe")]


def test_untrusted_proxy_peer_is_logged_raw_and_client_hashed(caplog):
    req = _request(PROXY, {"X-Forwarded-For": f"{CLIENT}, 10.9.8.7", "CF-Connecting-IP": CLIENT})
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        key = rate_limits._get_rate_limit_key(req)

    assert key == PROXY  # TRUSTED_PROXY_IPS empty -> the peer is the key
    [line] = _probe_lines(caplog)
    assert f"peer=private:{PROXY}" in line
    assert "peer_trusted=False" in line
    assert "trusted_proxies=0" in line
    assert f"key=private:{PROXY}" in line
    assert f"x-forwarded-for=[public:{hash_ip_address(CLIENT)},private:10.9.8.7]" in line
    assert f"cf-connecting-ip=[public:{hash_ip_address(CLIENT)}]" in line
    # The customer address itself never appears.
    assert CLIENT not in line


def test_trusted_proxy_resolves_client_and_logs_key_hashed(caplog, monkeypatch):
    monkeypatch.setattr("config.TRUSTED_PROXY_IPS", frozenset({"10.0.0.0/8"}))
    req = _request(PROXY, {"X-Forwarded-For": CLIENT})
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        key = rate_limits._get_rate_limit_key(req)

    assert key == CLIENT
    [line] = _probe_lines(caplog)
    assert "peer_trusted=True" in line
    assert "trusted_proxies=1" in line
    assert f"key=public:{hash_ip_address(CLIENT)}" in line
    assert CLIENT not in line


def test_cgnat_proxy_range_is_infrastructure(caplog):
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        rate_limits._get_rate_limit_key(_request("100.64.3.9"))
    [line] = _probe_lines(caplog)
    assert "peer=private:100.64.3.9" in line


def test_no_forwarding_headers_is_stated(caplog):
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        rate_limits._get_rate_limit_key(_request("127.0.0.1"))
    [line] = _probe_lines(caplog)
    assert line.endswith("no-forwarding-headers")


def test_invalid_header_entries_are_marked_not_echoed(caplog):
    req = _request(PROXY, {"X-Forwarded-For": "<script>, " + CLIENT})
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        rate_limits._get_rate_limit_key(req)
    [line] = _probe_lines(caplog)
    assert "x-forwarded-for=[invalid,public:" in line
    assert "<script>" not in line


def test_probe_is_bounded(caplog):
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        for _ in range(rate_limits._KEY_PROBE_LIMIT + 25):
            rate_limits._get_rate_limit_key(_request(PROXY))
    lines = _probe_lines(caplog)
    assert len(lines) == rate_limits._KEY_PROBE_LIMIT
    assert lines[-1].startswith(f"rate_limit_key_probe n={rate_limits._KEY_PROBE_LIMIT} ")


def test_authenticated_keys_are_not_probed(caplog):
    req = _request(PROXY)
    req.state.rate_limit_user_id = 42
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        assert rate_limits._get_rate_limit_key(req) == "user:42"
    assert _probe_lines(caplog) == []


def test_probe_failure_never_breaks_key_derivation(caplog, monkeypatch):
    def _boom(_value: str) -> str:
        raise RuntimeError("probe bug")

    monkeypatch.setattr(rate_limits, "_describe_ip", _boom)
    with caplog.at_level(logging.INFO, logger="shared.rate_limits"):
        assert rate_limits._get_rate_limit_key(_request(PROXY)) == PROXY
    assert _probe_lines(caplog) == []


def test_storage_health_reports_trusted_proxy_count(monkeypatch):
    from shared.rate_limits import get_storage_health

    assert get_storage_health()["trusted_proxies_configured"] == 0
    monkeypatch.setattr("config.TRUSTED_PROXY_IPS", frozenset({"10.0.0.0/8", "172.16.0.0/12"}))
    assert get_storage_health()["trusted_proxies_configured"] == 2
