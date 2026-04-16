"""
Sprint 275: Sentry APM Integration Tests

Validates:
- Sentry is not initialized when DSN is empty
- before_send strips request bodies (Zero-Storage compliance)
- Config loads SENTRY_DSN and SENTRY_TRACES_SAMPLE_RATE correctly
"""


class TestSentryNotInitWithoutDSN:
    """Verify Sentry SDK is not active when SENTRY_DSN is empty."""

    def test_sentry_dsn_empty_by_default(self):
        from config import SENTRY_DSN

        # In test environment, SENTRY_DSN should be empty (not configured)
        assert SENTRY_DSN == ""

    def test_sentry_sdk_not_initialized_when_dsn_empty(self):
        import sentry_sdk

        # With no DSN configured, the hub client should have no DSN
        client = sentry_sdk.get_client()
        assert client.dsn is None or str(client.dsn) == ""


_SAFE_EXTRA_KEYS = frozenset({"sentry_logger", "sys.argv", "celery-job"})
_SAFE_CONTEXT_KEYS = frozenset({"runtime", "os", "device", "browser", "trace", "threadpool"})


def _before_send(event: dict, hint: dict) -> dict:
    """Mirror of main.py _before_send for test isolation."""
    req = event.get("request")
    if req:
        req.pop("data", None)
        req.pop("query_string", None)
    extra = event.get("extra")
    if extra:
        event["extra"] = {k: v for k, v in extra.items() if k in _SAFE_EXTRA_KEYS}
    contexts = event.get("contexts")
    if contexts:
        event["contexts"] = {k: v for k, v in contexts.items() if k in _SAFE_CONTEXT_KEYS}
    return event


class TestBeforeSendStripsBody:
    """Verify the before_send callback strips request bodies."""

    def test_strips_request_data(self):
        event = {
            "request": {
                "url": "/audit/trial-balance",
                "method": "POST",
                "data": '{"sensitive": "financial_data"}',
            }
        }
        result = _before_send(event, {})
        assert "data" not in result["request"]
        assert result["request"]["url"] == "/audit/trial-balance"

    def test_strips_query_string(self):
        event = {"request": {"url": "/api", "query_string": "token=secret123"}}
        result = _before_send(event, {})
        assert "query_string" not in result["request"]

    def test_passes_through_events_without_request_body(self):
        event = {"exception": {"values": [{"type": "ValueError"}]}}
        result = _before_send(event, {})
        assert result == event

    def test_passes_through_request_without_data(self):
        event = {"request": {"url": "/health", "method": "GET"}}
        result = _before_send(event, {})
        assert "data" not in result["request"]

    def test_strips_unsafe_extra(self):
        event = {
            "extra": {
                "sentry_logger": "ok",
                "financial_data": '{"accounts": [...]}',
                "user_tb_rows": "sensitive",
            }
        }
        result = _before_send(event, {})
        assert set(result["extra"].keys()) == {"sentry_logger"}

    def test_strips_unsafe_contexts(self):
        event = {
            "contexts": {
                "runtime": {"name": "CPython"},
                "custom_audit_data": {"tb_rows": 500},
                "os": {"name": "Linux"},
            }
        }
        result = _before_send(event, {})
        assert set(result["contexts"].keys()) == {"runtime", "os"}
