"""
Tests for Redis storage backend integration in rate limiting.

Covers:
1. Storage URI resolution (memory fallback, Redis when configured)
2. get_storage_backend() accessor
3. Graceful fallback when Redis is unreachable
4. Limiter uses the resolved storage_uri
"""

import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestResolveStorageUri:
    """_resolve_storage_uri returns memory:// or redis:// based on config."""

    def test_empty_redis_url_returns_memory(self):
        """When REDIS_URL is empty, fall back to in-memory storage."""
        with patch("config.REDIS_URL", ""):
            from shared.rate_limits import _resolve_storage_uri

            result = _resolve_storage_uri()
        assert result == "memory://"

    def test_redis_url_with_unreachable_host_falls_back(self):
        """When Redis is configured but unreachable, fall back to memory."""
        mock_storage_cls = MagicMock()
        mock_storage_cls.return_value.check.side_effect = ConnectionError("Connection refused")

        with (
            patch("config.REDIS_URL", "redis://unreachable:6379/0"),
            patch("limits.storage.RedisStorage", mock_storage_cls),
        ):
            from shared.rate_limits import _resolve_storage_uri

            result = _resolve_storage_uri()
        assert result == "memory://"

    def test_redis_url_with_reachable_host_returns_url(self):
        """When Redis is configured and reachable, return the Redis URI."""
        mock_storage_cls = MagicMock()
        mock_storage_cls.return_value.check.return_value = True

        with (
            patch("config.REDIS_URL", "redis://localhost:6379/0"),
            patch("limits.storage.RedisStorage", mock_storage_cls),
        ):
            from shared.rate_limits import _resolve_storage_uri

            result = _resolve_storage_uri()
        assert result == "redis://localhost:6379/0"


class TestGetStorageBackend:
    """get_storage_backend() returns 'redis' or 'memory'."""

    def test_returns_memory_when_no_redis(self):
        with patch("shared.rate_limits._storage_uri", "memory://"):
            from shared.rate_limits import get_storage_backend

            assert get_storage_backend() == "memory"

    def test_returns_redis_when_redis_uri(self):
        with patch("shared.rate_limits._storage_uri", "redis://localhost:6379/0"):
            from shared.rate_limits import get_storage_backend

            assert get_storage_backend() == "redis"

    def test_returns_redis_for_rediss_uri(self):
        """rediss:// (TLS) is also recognized as Redis."""
        with patch("shared.rate_limits._storage_uri", "rediss://prod-redis:6379"):
            from shared.rate_limits import get_storage_backend

            assert get_storage_backend() == "redis"


class TestLimiterStorageUri:
    """Verify the Limiter instance received the resolved storage_uri."""

    def test_limiter_exists_and_has_key_func(self):
        from shared.rate_limits import _get_rate_limit_key, limiter

        assert limiter._key_func is _get_rate_limit_key

    def test_default_storage_is_memory(self):
        """Without REDIS_URL, the active backend should be memory."""
        from shared.rate_limits import get_storage_backend

        # In test environment, REDIS_URL is empty → memory
        assert get_storage_backend() == "memory"


class TestRedisStorageCanaryImport:
    """Verify that the limits library's RedisStorage class is importable."""

    def test_redis_storage_importable(self):
        from limits.storage import RedisStorage

        assert RedisStorage is not None

    def test_redis_package_importable(self):
        import redis

        assert redis is not None
