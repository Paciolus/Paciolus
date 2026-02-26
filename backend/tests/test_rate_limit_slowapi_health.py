"""
Canary tests for slowapi / limits library health.

Sprint 444: slowapi (0.1.9) is unmaintained but wraps the actively-maintained
`limits` package. These tests detect breakage early — if any fail, consult
docs/runbooks/rate-limiter-modernization.md for the migration playbook.
"""

import importlib

from packaging.version import Version


class TestSlowApiHealth:
    """Verify that slowapi and its underlying limits library are functional."""

    def test_slowapi_imports(self):
        """slowapi core classes are importable."""
        from slowapi import Limiter
        from slowapi.errors import RateLimitExceeded

        assert Limiter is not None
        assert RateLimitExceeded is not None

    def test_limits_imports(self):
        """The underlying limits library is importable."""
        from limits import parse  # noqa: F401
        from limits.storage import MemoryStorage  # noqa: F401

        assert parse is not None

    def test_limiter_construction(self):
        """Limiter can be constructed with a key_func."""
        from slowapi import Limiter

        limiter = Limiter(key_func=lambda request: "test")
        assert limiter is not None
        assert callable(limiter.limit)

    def test_limits_version_minimum(self):
        """limits library is at least 3.0.0 (our pinned minimum)."""
        limits_mod = importlib.import_module("limits")
        version = getattr(limits_mod, "__version__", "0.0.0")
        assert Version(version) >= Version("3.0.0"), f"limits {version} < 3.0.0; update pin in requirements.txt"

    def test_rate_limit_string_parsing(self):
        """limits.parse can parse our rate limit strings."""
        from limits import parse

        rate = parse("10/minute")
        assert rate is not None
        # Verify the parsed rate has expected attributes
        assert rate.amount == 10
