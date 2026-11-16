"""Sprint 877: a revoked impersonation token must not come back to life when Redis misbehaves.

Each worker probed Redis once; a failed first probe pinned it to a private
in-memory store for life, so a revocation posted to another worker was never
seen. A failing EXISTS also fell back to that empty memory and answered "not
revoked". Where revocation is meant to be shared (production + REDIS_URL), an
unconfirmable check now means revoked, and the probe is retried.
"""

from unittest.mock import MagicMock, patch

import pytest

from shared import impersonation_revocation as rev


@pytest.fixture(autouse=True)
def _clean():
    rev._reset_for_tests()
    yield
    rev._reset_for_tests()


def _prod(redis_url="redis://example:6379/0"):
    return patch.multiple("config", ENV_MODE="production", REDIS_URL=redis_url)


def test_production_unreachable_redis_treats_tokens_as_revoked():
    with _prod(), patch("redis.Redis.from_url", side_effect=ConnectionError("down")):
        assert rev.is_revoked("jti-never-revoked") is True


def test_production_exists_error_treats_tokens_as_revoked():
    client = MagicMock()
    client.exists.side_effect = ConnectionError("blip")
    with _prod(), patch("redis.Redis.from_url", return_value=client):
        assert rev.is_revoked("jti-x") is True


def test_production_healthy_redis_answers_from_redis():
    client = MagicMock()
    client.exists.side_effect = lambda key: key == rev._KEY_PREFIX + "revoked-jti"
    with _prod(), patch("redis.Redis.from_url", return_value=client):
        assert rev.is_revoked("revoked-jti") is True
        assert rev.is_revoked("live-jti") is False


def test_a_failed_probe_is_retried_not_cached_for_life():
    healthy = MagicMock()
    healthy.exists.return_value = False
    calls = {"n": 0}

    def _from_url(_url, **_kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("first probe fails")
        return healthy

    with _prod(), patch("redis.Redis.from_url", side_effect=_from_url), patch.object(rev, "_REDIS_RETRY_SECONDS", 0.0):
        assert rev.is_revoked("live-jti") is True  # cannot confirm -> revoked
        assert rev.is_revoked("live-jti") is False  # re-probed, Redis answers
    assert calls["n"] == 2


def test_development_without_redis_keeps_the_memory_store():
    with patch.multiple("config", ENV_MODE="development", REDIS_URL=""):
        assert rev.is_revoked("jti-a") is False
        rev.revoke("jti-a", 60)
        assert rev.is_revoked("jti-a") is True
