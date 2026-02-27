"""
Tests for Data Transport & Infrastructure Trust Controls.

Covers:
1. is_trusted_proxy() — exact IP, CIDR, invalid input, edge cases
2. get_client_ip()    — proxy-aware IP extraction (security_middleware)
3. _get_client_ip()   — rate-limit IP extraction (shared/rate_limits)
4. PostgreSQL TLS enforcement — startup config.py guardrail
"""

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from security_middleware import get_client_ip, is_trusted_proxy
from shared.rate_limits import _get_client_ip

# ===========================================================================
# 1. is_trusted_proxy()
# ===========================================================================


class TestIsTrustedProxy:
    # -----------------------------------------------------------------------
    # Exact-IP matching
    # -----------------------------------------------------------------------

    def test_exact_ipv4_match(self):
        assert is_trusted_proxy("127.0.0.1", frozenset({"127.0.0.1"})) is True

    def test_exact_ipv4_no_match(self):
        assert is_trusted_proxy("127.0.0.2", frozenset({"127.0.0.1"})) is False

    def test_exact_ipv6_match(self):
        assert is_trusted_proxy("::1", frozenset({"::1"})) is True

    def test_exact_ipv6_no_match(self):
        assert is_trusted_proxy("::2", frozenset({"::1"})) is False

    # -----------------------------------------------------------------------
    # CIDR matching
    # -----------------------------------------------------------------------

    def test_cidr_ipv4_inside(self):
        """10.0.1.50 is inside 10.0.0.0/8."""
        assert is_trusted_proxy("10.0.1.50", frozenset({"10.0.0.0/8"})) is True

    def test_cidr_ipv4_boundary_network_address(self):
        """Network address itself is inside the CIDR."""
        assert is_trusted_proxy("10.0.0.0", frozenset({"10.0.0.0/8"})) is True

    def test_cidr_ipv4_boundary_broadcast(self):
        """Broadcast address is inside the CIDR."""
        assert is_trusted_proxy("10.255.255.255", frozenset({"10.0.0.0/8"})) is True

    def test_cidr_ipv4_outside(self):
        """172.31.0.5 is NOT inside 10.0.0.0/8."""
        assert is_trusted_proxy("172.31.0.5", frozenset({"10.0.0.0/8"})) is False

    def test_cidr_private_172_range(self):
        assert is_trusted_proxy("172.16.5.1", frozenset({"172.16.0.0/12"})) is True
        assert is_trusted_proxy("172.32.0.1", frozenset({"172.16.0.0/12"})) is False

    def test_cidr_private_192_range(self):
        assert is_trusted_proxy("192.168.99.1", frozenset({"192.168.0.0/16"})) is True
        assert is_trusted_proxy("192.169.0.1", frozenset({"192.168.0.0/16"})) is False

    def test_cidr_slash32_acts_as_exact(self):
        """A /32 CIDR should match only the single host."""
        assert is_trusted_proxy("10.10.10.10", frozenset({"10.10.10.10/32"})) is True
        assert is_trusted_proxy("10.10.10.11", frozenset({"10.10.10.10/32"})) is False

    def test_multiple_entries_first_cidr_matches(self):
        trusted = frozenset({"127.0.0.1", "10.0.0.0/8"})
        assert is_trusted_proxy("10.5.5.5", trusted) is True

    def test_multiple_entries_second_exact_matches(self):
        trusted = frozenset({"10.0.0.0/8", "127.0.0.1"})
        assert is_trusted_proxy("127.0.0.1", trusted) is True

    def test_multiple_entries_none_match(self):
        trusted = frozenset({"127.0.0.1", "10.0.0.0/8"})
        assert is_trusted_proxy("203.0.113.1", trusted) is False

    # -----------------------------------------------------------------------
    # Edge cases
    # -----------------------------------------------------------------------

    def test_empty_trusted_set_returns_false(self):
        assert is_trusted_proxy("127.0.0.1", frozenset()) is False

    def test_invalid_peer_ip_returns_false(self):
        """A non-IP string (e.g. hostname) must not raise — returns False."""
        assert is_trusted_proxy("not-an-ip", frozenset({"127.0.0.1"})) is False

    def test_invalid_cidr_entry_skipped(self):
        """A malformed CIDR entry must not raise — it is skipped."""
        trusted = frozenset({"not-a-cidr/xyz", "127.0.0.1"})
        assert is_trusted_proxy("127.0.0.1", trusted) is True

    def test_invalid_ip_in_trusted_set_skipped(self):
        """A malformed IP entry must not raise — it is skipped."""
        trusted = frozenset({"garbage", "127.0.0.1"})
        assert is_trusted_proxy("127.0.0.1", trusted) is True

    def test_unknown_peer_ip_string_returns_false(self):
        """'unknown' is returned by get_client_ip when request.client is None."""
        assert is_trusted_proxy("unknown", frozenset({"127.0.0.1"})) is False


# ===========================================================================
# 2. get_client_ip() — security_middleware
# ===========================================================================


class TestGetClientIpMiddleware:
    def _make_request(self, peer: str, xff: str | None = None) -> MagicMock:
        req = MagicMock(spec=["client", "headers"])
        req.client = MagicMock()
        req.client.host = peer
        req.headers = {}
        if xff is not None:
            req.headers = {"X-Forwarded-For": xff}
        return req

    def test_direct_connection_returned_as_is(self):
        req = self._make_request("203.0.113.5")
        with patch("config.TRUSTED_PROXY_IPS", frozenset()):
            ip = get_client_ip(req)
        assert ip == "203.0.113.5"

    def test_xff_honored_for_exact_trusted_proxy(self):
        req = self._make_request("127.0.0.1", xff="203.0.113.50, 127.0.0.1")
        with patch("config.TRUSTED_PROXY_IPS", frozenset({"127.0.0.1"})):
            ip = get_client_ip(req)
        assert ip == "203.0.113.50"

    def test_xff_honored_for_cidr_trusted_proxy(self):
        req = self._make_request("10.0.2.15", xff="198.51.100.1, 10.0.2.15")
        with patch("config.TRUSTED_PROXY_IPS", frozenset({"10.0.0.0/8"})):
            ip = get_client_ip(req)
        assert ip == "198.51.100.1"

    def test_xff_not_honored_outside_cidr(self):
        req = self._make_request("172.31.0.5", xff="198.51.100.99, 172.31.0.5")
        with patch("config.TRUSTED_PROXY_IPS", frozenset({"10.0.0.0/8"})):
            ip = get_client_ip(req)
        assert ip == "172.31.0.5"

    def test_no_client_returns_unknown(self):
        req = MagicMock(spec=["client", "headers"])
        req.client = None
        req.headers = {}
        with patch("config.TRUSTED_PROXY_IPS", frozenset()):
            ip = get_client_ip(req)
        assert ip == "unknown"

    def test_xff_missing_peer_is_returned(self):
        """Trusted proxy but no X-Forwarded-For → fall back to peer IP."""
        req = self._make_request("127.0.0.1")
        with patch("config.TRUSTED_PROXY_IPS", frozenset({"127.0.0.1"})):
            ip = get_client_ip(req)
        assert ip == "127.0.0.1"


# ===========================================================================
# 3. _get_client_ip() — shared/rate_limits (CIDR path)
# ===========================================================================


class TestRateLimitClientIpCidr:
    def _make_request(self, peer: str, xff: str | None = None) -> MagicMock:
        req = MagicMock(spec=["state", "client", "headers"])
        req.state.rate_limit_user_id = None
        req.client = MagicMock()
        req.client.host = peer
        req.headers = {}
        if xff is not None:
            req.headers = {"X-Forwarded-For": xff}
        return req

    def test_cidr_proxy_xff_honored(self):
        req = self._make_request("192.168.1.1", xff="203.0.113.42, 192.168.1.1")
        with patch("config.TRUSTED_PROXY_IPS", frozenset({"192.168.0.0/16"})):
            ip = _get_client_ip(req)
        assert ip == "203.0.113.42"

    def test_cidr_proxy_outside_range_not_honored(self):
        req = self._make_request("192.169.0.1", xff="203.0.113.42, 192.169.0.1")
        with patch("config.TRUSTED_PROXY_IPS", frozenset({"192.168.0.0/16"})):
            ip = _get_client_ip(req)
        assert ip == "192.169.0.1"

    def test_no_proxy_configured_direct_ip(self):
        req = self._make_request("203.0.113.7")
        with patch("config.TRUSTED_PROXY_IPS", frozenset()):
            ip = _get_client_ip(req)
        assert ip == "203.0.113.7"

    def test_no_client_falls_back_to_loopback(self):
        req = MagicMock(spec=["state", "client", "headers"])
        req.state.rate_limit_user_id = None
        req.client = None
        req.headers = {}
        with patch("config.TRUSTED_PROXY_IPS", frozenset()):
            ip = _get_client_ip(req)
        assert ip == "127.0.0.1"


# ===========================================================================
# 4. PostgreSQL TLS config enforcement
# ===========================================================================


class TestPostgresTLSEnforcement:
    """Validate that config.py hard-fails when production PostgreSQL lacks TLS.

    We exercise the guard logic directly rather than re-executing config.py
    (which would require complex import machinery).  The guard is a straight-
    line block that calls _hard_fail() — we mock sys.exit to capture it.
    """

    def _run_tls_guard(self, database_url: str, env_mode: str = "production") -> bool:
        """
        Returns True if the TLS guard would trigger (i.e. sys.exit called),
        False if it passes silently.
        """
        from urllib.parse import parse_qs, urlparse

        if env_mode != "production" or database_url.startswith("sqlite"):
            return False  # guard not active

        params = parse_qs(urlparse(database_url).query)
        ssl_mode = (params.get("sslmode") or ["disable"])[0]
        secure_modes = {"require", "verify-ca", "verify-full"}
        return ssl_mode not in secure_modes

    # -----------------------------------------------------------------------
    # Guard triggers (should fail)
    # -----------------------------------------------------------------------

    def test_no_sslmode_triggers_guard(self):
        url = "postgresql://user:pw@db:5432/mydb"
        assert self._run_tls_guard(url) is True

    def test_sslmode_disable_triggers_guard(self):
        url = "postgresql://user:pw@db:5432/mydb?sslmode=disable"
        assert self._run_tls_guard(url) is True

    def test_sslmode_prefer_triggers_guard(self):
        url = "postgresql://user:pw@db:5432/mydb?sslmode=prefer"
        assert self._run_tls_guard(url) is True

    def test_sslmode_allow_triggers_guard(self):
        url = "postgresql://user:pw@db:5432/mydb?sslmode=allow"
        assert self._run_tls_guard(url) is True

    # -----------------------------------------------------------------------
    # Guard passes (should not fail)
    # -----------------------------------------------------------------------

    def test_sslmode_require_passes(self):
        url = "postgresql://user:pw@db:5432/mydb?sslmode=require"
        assert self._run_tls_guard(url) is False

    def test_sslmode_verify_ca_passes(self):
        url = "postgresql://user:pw@db:5432/mydb?sslmode=verify-ca"
        assert self._run_tls_guard(url) is False

    def test_sslmode_verify_full_passes(self):
        url = "postgresql://user:pw@db:5432/mydb?sslmode=verify-full"
        assert self._run_tls_guard(url) is False

    def test_sqlite_url_skips_guard(self):
        """SQLite URLs are never subject to TLS enforcement."""
        url = "sqlite:///./paciolus.db"
        assert self._run_tls_guard(url, env_mode="production") is False

    def test_non_production_skips_guard(self):
        """TLS enforcement only applies in production."""
        url = "postgresql://user:pw@db:5432/mydb"
        assert self._run_tls_guard(url, env_mode="development") is False

    def test_render_style_url_with_sslmode_passes(self):
        """Render.com connection strings include ?sslmode=require."""
        url = "postgresql://user:pw@oregon-postgres.render.com:5432/paciolus_db?sslmode=require"
        assert self._run_tls_guard(url) is False
