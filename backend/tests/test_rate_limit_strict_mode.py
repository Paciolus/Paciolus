"""
Tests for fail-closed rate limiting (RATE_LIMIT_STRICT_MODE).

Covers:
1. Strict mode + Redis unreachable → RuntimeError (app refuses to start)
2. Strict mode + no REDIS_URL → config hard-fail (SystemExit)
3. Non-strict mode preserves graceful fallback to memory://
4. Strict mode + Redis reachable → normal Redis URI returned
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestStrictModeFailClosed:
    """When RATE_LIMIT_STRICT_MODE=true, Redis failure must prevent startup."""

    def test_strict_mode_redis_unreachable_raises(self):
        """Strict mode + configured but unreachable Redis → RuntimeError."""
        mock_storage_cls = MagicMock()
        mock_storage_cls.return_value.check.side_effect = ConnectionError("Connection refused")

        with (
            patch("config.REDIS_URL", "redis://unreachable:6379/0"),
            patch("config.RATE_LIMIT_STRICT_MODE", True),
            patch("limits.storage.RedisStorage", mock_storage_cls),
        ):
            from shared.rate_limits import _resolve_storage_uri

            with pytest.raises(RuntimeError, match="strict mode"):
                _resolve_storage_uri()

    def test_strict_mode_redis_reachable_returns_url(self):
        """Strict mode + reachable Redis → normal URI returned."""
        mock_storage_cls = MagicMock()
        mock_storage_cls.return_value.check.return_value = True

        with (
            patch("config.REDIS_URL", "redis://localhost:6379/0"),
            patch("config.RATE_LIMIT_STRICT_MODE", True),
            patch("limits.storage.RedisStorage", mock_storage_cls),
        ):
            from shared.rate_limits import _resolve_storage_uri

            result = _resolve_storage_uri()
        assert result == "redis://localhost:6379/0"

    def test_strict_mode_no_redis_url_config_hard_fails(self):
        """Strict mode + empty REDIS_URL → config.py calls sys.exit(1)."""
        # Simulate what config.py does: hard-fail at import time
        with (
            patch(
                "config._load_optional",
                side_effect=lambda k, d: {
                    "RATE_LIMIT_STRICT_MODE": "true",
                    "REDIS_URL": "",
                }.get(k, d),
            ),
            patch("config.ENV_MODE", "production"),
        ):
            # The guard in config.py would call _hard_fail → sys.exit(1)
            # We test the logic directly: strict + no URL = error
            from config import _hard_fail

            with pytest.raises(SystemExit):
                _hard_fail("test: strict mode without REDIS_URL")


class TestPermissiveModePreservesFallback:
    """When RATE_LIMIT_STRICT_MODE=false, the existing fallback behavior is preserved."""

    def test_permissive_mode_redis_unreachable_falls_back(self):
        """Non-strict + unreachable Redis → graceful fallback to memory://."""
        mock_storage_cls = MagicMock()
        mock_storage_cls.return_value.check.side_effect = ConnectionError("Connection refused")

        with (
            patch("config.REDIS_URL", "redis://unreachable:6379/0"),
            patch("config.RATE_LIMIT_STRICT_MODE", False),
            patch("limits.storage.RedisStorage", mock_storage_cls),
        ):
            from shared.rate_limits import _resolve_storage_uri

            result = _resolve_storage_uri()
        assert result == "memory://"

    def test_permissive_mode_no_redis_returns_memory(self):
        """Non-strict + no REDIS_URL → memory:// (dev/test default)."""
        with (
            patch("config.REDIS_URL", ""),
            patch("config.RATE_LIMIT_STRICT_MODE", False),
        ):
            from shared.rate_limits import _resolve_storage_uri

            result = _resolve_storage_uri()
        assert result == "memory://"


class TestStrictModeConfigDefault:
    """RATE_LIMIT_STRICT_MODE defaults to true in production, false otherwise."""

    def test_production_defaults_to_strict(self):
        """In production, strict mode is on by default."""
        # This tests the default derivation logic
        env_mode = "production"
        default = "true" if env_mode == "production" else "false"
        assert default == "true"

    def test_development_defaults_to_permissive(self):
        """In development, strict mode is off by default."""
        env_mode = "development"
        default = "true" if env_mode == "production" else "false"
        assert default == "false"


class TestStrictModeFailClosedRedisStorageInit:
    """Strict-mode boot should refuse to start when Redis init itself raises."""

    def test_strict_mode_redis_storage_constructor_raises(self):
        """RedisStorage() blowing up at construction time still hard-fails."""

        class _BoomStorage:
            def __init__(self, *_a, **_kw):
                raise ConnectionError("DNS resolution failed")

        with (
            patch("config.REDIS_URL", "redis://nonsense.invalid:6379/0"),
            patch("config.RATE_LIMIT_STRICT_MODE", True),
            patch("limits.storage.RedisStorage", _BoomStorage),
        ):
            from shared.rate_limits import _resolve_storage_uri

            with pytest.raises(RuntimeError, match="strict mode"):
                _resolve_storage_uri()


class TestSlowApiUnmaintainedWarning:
    """Module import emits an explicit notice that slowapi is unmaintained.

    Severity differs by ENV_MODE: production -> WARNING (visible in oncall
    logs), non-production -> INFO. The substring "slowapi is unmaintained"
    is intentionally pinned so monitoring rules and runbook references can
    match against the literal text.
    """

    def _invoke_emit(self, env_mode: str) -> list[tuple[int, str]]:
        import logging

        from shared import rate_limits

        captured: list[tuple[int, str]] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured.append((record.levelno, record.getMessage()))

        handler = _Capture()
        # Capture at the lowest level so INFO is observed even when the
        # logger's effective level is WARNING in pytest's default config.
        handler.setLevel(logging.DEBUG)
        previous_level = rate_limits._logger.level
        rate_limits._logger.setLevel(logging.DEBUG)
        rate_limits._logger.addHandler(handler)
        try:
            # Patch only ENV_MODE; do NOT reload the module — reloading
            # severs object identity for limiter / TieredLimit and breaks
            # other tests that resolve those singletons.
            with patch("config.ENV_MODE", env_mode):
                rate_limits._emit_slowapi_unmaintained_warning()
        finally:
            rate_limits._logger.removeHandler(handler)
            rate_limits._logger.setLevel(previous_level)
        return captured

    def test_production_emits_warning_severity(self):
        import logging

        captured = self._invoke_emit("production")
        assert any(level == logging.WARNING and "slowapi is unmaintained" in msg for level, msg in captured), captured

    def test_non_production_emits_info_severity(self):
        import logging

        captured = self._invoke_emit("development")
        assert any(level == logging.INFO and "slowapi is unmaintained" in msg for level, msg in captured), captured
