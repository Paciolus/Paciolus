"""
Sprint 275: Sentry APM Integration Tests

Validates:
- Sentry is not initialized when DSN is empty
- before_send strips request bodies, frame locals, exception text and breadcrumbs
  (Sprint 840 — claims review S2)
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


# Sprint 840: test the real scrubber, not a hand-copied mirror of it.
from shared.sentry_scrubber import (  # noqa: E402
    REDACTED,
    SENTRY_INIT_OPTIONS,
    before_send_transaction,
)
from shared.sentry_scrubber import before_send as _before_send  # noqa: E402


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


class TestSprint840Scrubbing:
    """Sprint 840 (S2): nothing from a customer's file reaches Sentry."""

    def test_sdk_options_turn_off_locals_and_breadcrumbs(self):
        assert SENTRY_INIT_OPTIONS["include_local_variables"] is False
        assert SENTRY_INIT_OPTIONS["send_default_pii"] is False
        assert SENTRY_INIT_OPTIONS["max_breadcrumbs"] == 0
        assert SENTRY_INIT_OPTIONS["max_value_length"] <= 1024

    def test_sdk_accepts_every_option(self):
        import sentry_sdk

        # An unknown keyword raises TypeError — so a renamed SDK option fails here.
        sentry_sdk.Client(dsn=None, **SENTRY_INIT_OPTIONS)

    def test_main_passes_the_options_to_init(self):
        from pathlib import Path

        source = (Path(__file__).parent.parent / "main.py").read_text(encoding="utf-8")
        assert "**SENTRY_INIT_OPTIONS" in source
        assert "before_send=before_send" in source

    def test_drops_frame_locals_and_source(self):
        event = {
            "exception": {
                "values": [
                    {
                        "type": "ValueError",
                        "value": "could not convert 'Acme Holdings 4,210.55' to float",
                        "stacktrace": {
                            "frames": [
                                {
                                    "function": "upload",
                                    "lineno": 12,
                                    "vars": {"file_bytes": "b'Account,Debit'"},
                                    "context_line": "df = parse(file_bytes)",
                                }
                            ]
                        },
                    }
                ]
            }
        }
        result = _before_send(event, {})
        value = result["exception"]["values"][0]
        assert value["type"] == "ValueError"
        assert value["value"] == REDACTED
        frame = value["stacktrace"]["frames"][0]
        assert "vars" not in frame and "context_line" not in frame
        assert frame["function"] == "upload" and frame["lineno"] == 12

    def test_drops_thread_frame_locals(self):
        event = {"threads": {"values": [{"stacktrace": {"frames": [{"vars": {"df": "..."}}]}}]}}
        result = _before_send(event, {})
        assert "vars" not in result["threads"]["values"][0]["stacktrace"]["frames"][0]

    def test_drops_breadcrumbs(self):
        event = {"breadcrumbs": {"values": [{"message": "Parsing client_tb_acme.xlsx"}]}}
        assert "breadcrumbs" not in _before_send(event, {})

    def test_keeps_log_template_drops_arguments(self):
        event = {
            "logentry": {
                "message": "Upload failed for %s",
                "params": ["acme_tb.xlsx"],
                "formatted": "Upload failed for acme_tb.xlsx",
            },
            "message": "Upload failed for acme_tb.xlsx",
        }
        result = _before_send(event, {})
        assert result["logentry"] == {"message": "Upload failed for %s"}
        assert result["message"] == "Upload failed for %s"

    def test_drops_cookies_and_auth_headers(self):
        event = {
            "request": {
                "cookies": {"paciolus_access": "jwt"},
                "headers": {"Authorization": "Bearer x", "User-Agent": "ua", "X-CSRF-Token": "t"},
            }
        }
        result = _before_send(event, {})
        assert "cookies" not in result["request"]
        assert result["request"]["headers"] == {"User-Agent": "ua"}

    def test_transaction_strips_query_and_body(self):
        event = {"transaction": "/audit/x?client=acme", "request": {"data": "rows"}, "breadcrumbs": {}}
        result = before_send_transaction(event, {})
        assert result["transaction"] == "/audit/x"
        assert "data" not in result["request"]
        assert "breadcrumbs" not in result
