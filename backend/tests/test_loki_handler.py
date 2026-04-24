"""
Test Suite: Loki Handler — Sprint 716.

Covers payload construction, HTTP push, failure handling, queue backpressure,
and thread lifecycle for the in-process Loki HTTPS push handler.
"""

import json
import logging
import time
import urllib.error
from base64 import b64decode
from unittest.mock import MagicMock, patch

from loki_handler import LokiHandler


def _make_record(
    logger_name: str = "paciolus.test",
    level: int = logging.INFO,
    message: str = "hello",
    created: float | None = None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name=logger_name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )
    if created is not None:
        record.created = created
    return record


def _new_handler(**overrides) -> LokiHandler:
    defaults = dict(
        url="https://logs.example.com/loki/api/v1/push",
        user="1234",
        token="glc_test-token",
        labels={"service": "paciolus-api", "env": "test"},
        flush_interval=0.05,
        batch_size=10,
        queue_maxsize=100,
        timeout=1.0,
    )
    defaults.update(overrides)
    return LokiHandler(**defaults)


class TestBuildPayload:
    """Unit tests for LokiHandler._build_payload()."""

    def test_groups_records_by_level_and_logger(self):
        handler = _new_handler()
        try:
            handler.setFormatter(logging.Formatter("%(message)s"))
            records = [
                _make_record("paciolus.auth", logging.INFO, "a", created=1.0),
                _make_record("paciolus.auth", logging.INFO, "b", created=2.0),
                _make_record("paciolus.auth", logging.ERROR, "c", created=3.0),
                _make_record("paciolus.audit", logging.INFO, "d", created=4.0),
            ]
            payload = handler._build_payload(records)
            # Three unique (level, logger) combinations → three streams
            assert len(payload["streams"]) == 3
            labels_seen = {(s["stream"]["level"], s["stream"]["logger"]) for s in payload["streams"]}
            assert labels_seen == {
                ("INFO", "paciolus.auth"),
                ("ERROR", "paciolus.auth"),
                ("INFO", "paciolus.audit"),
            }
        finally:
            handler.close()

    def test_includes_static_labels(self):
        handler = _new_handler(labels={"service": "paciolus-api", "env": "production"})
        try:
            handler.setFormatter(logging.Formatter("%(message)s"))
            payload = handler._build_payload([_make_record(created=1.0)])
            stream_labels = payload["streams"][0]["stream"]
            assert stream_labels["service"] == "paciolus-api"
            assert stream_labels["env"] == "production"
        finally:
            handler.close()

    def test_values_are_nanosecond_timestamp_strings(self):
        handler = _new_handler()
        try:
            handler.setFormatter(logging.Formatter("%(message)s"))
            payload = handler._build_payload([_make_record(message="hello", created=1234.5)])
            values = payload["streams"][0]["values"]
            assert values[0][0] == str(int(1234.5 * 1_000_000_000))
            assert values[0][1] == "hello"
        finally:
            handler.close()

    def test_values_sorted_by_timestamp_within_stream(self):
        handler = _new_handler()
        try:
            handler.setFormatter(logging.Formatter("%(message)s"))
            records = [
                _make_record(message="third", created=3.0),
                _make_record(message="first", created=1.0),
                _make_record(message="second", created=2.0),
            ]
            payload = handler._build_payload(records)
            lines = [v[1] for v in payload["streams"][0]["values"]]
            assert lines == ["first", "second", "third"]
        finally:
            handler.close()


class TestPost:
    """Unit tests for LokiHandler._post() HTTP behavior."""

    def test_post_sends_basic_auth_header(self):
        handler = _new_handler(user="1566612", token="glc_test-token")
        try:
            fake_resp = MagicMock()
            fake_resp.__enter__ = lambda s: s
            fake_resp.__exit__ = lambda *a: None
            fake_resp.status = 204
            with patch("loki_handler.urllib.request.urlopen", return_value=fake_resp) as mock_open:
                handler._post({"streams": []})
            req = mock_open.call_args[0][0]
            auth_header = req.get_header("Authorization")
            assert auth_header.startswith("Basic ")
            decoded = b64decode(auth_header.split(" ", 1)[1]).decode()
            assert decoded == "1566612:glc_test-token"
        finally:
            handler.close()

    def test_post_sends_json_body(self):
        handler = _new_handler()
        try:
            fake_resp = MagicMock()
            fake_resp.__enter__ = lambda s: s
            fake_resp.__exit__ = lambda *a: None
            fake_resp.status = 204
            with patch("loki_handler.urllib.request.urlopen", return_value=fake_resp) as mock_open:
                handler._post({"streams": [{"stream": {"a": "b"}, "values": []}]})
            req = mock_open.call_args[0][0]
            body = json.loads(req.data.decode("utf-8"))
            assert body == {"streams": [{"stream": {"a": "b"}, "values": []}]}
            assert req.get_header("Content-type") == "application/json"
        finally:
            handler.close()

    def test_post_swallows_connection_error(self):
        handler = _new_handler()
        try:
            with (
                patch(
                    "loki_handler.urllib.request.urlopen",
                    side_effect=urllib.error.URLError("connection refused"),
                ),
                patch.object(handler, "_warn_stderr") as mock_warn,
            ):
                handler._post({"streams": []})
            mock_warn.assert_called_once()
            assert "connection refused" in mock_warn.call_args[0][0]
        finally:
            handler.close()

    def test_post_warns_on_non_2xx_status(self):
        handler = _new_handler()
        try:
            fake_resp = MagicMock()
            fake_resp.__enter__ = lambda s: s
            fake_resp.__exit__ = lambda *a: None
            fake_resp.status = 403
            with (
                patch("loki_handler.urllib.request.urlopen", return_value=fake_resp),
                patch.object(handler, "_warn_stderr") as mock_warn,
            ):
                handler._post({"streams": []})
            mock_warn.assert_called_once()
            assert "403" in mock_warn.call_args[0][0]
        finally:
            handler.close()


class TestEmitAndQueue:
    """Unit tests for emit() and queue backpressure."""

    def test_emit_enqueues_record(self):
        handler = _new_handler()
        try:
            handler.emit(_make_record(message="queued"))
            assert handler._queue.qsize() == 1
        finally:
            handler.close()

    def test_queue_full_is_silent_drop(self):
        handler = _new_handler(queue_maxsize=2)
        try:
            for i in range(10):
                handler.emit(_make_record(message=f"msg-{i}"))
            # No exception raised; queue capped at 2
            assert handler._queue.qsize() <= 2
        finally:
            handler.close()


class TestThreadLifecycle:
    """Unit tests for background thread lifecycle."""

    def test_close_stops_flush_thread(self):
        handler = _new_handler()
        thread = handler._thread
        assert thread.is_alive()
        handler.close()
        # join() in close() should have let the thread exit
        assert not thread.is_alive()

    def test_flush_runs_on_interval(self):
        """emit() → background thread → _post() should happen within flush_interval."""
        handler = _new_handler(flush_interval=0.05)
        try:
            fake_resp = MagicMock()
            fake_resp.__enter__ = lambda s: s
            fake_resp.__exit__ = lambda *a: None
            fake_resp.status = 204
            with patch("loki_handler.urllib.request.urlopen", return_value=fake_resp) as mock_open:
                handler.setFormatter(logging.Formatter("%(message)s"))
                handler.emit(_make_record(message="background-flush"))
                # Allow the background thread up to 1s to drain and post.
                deadline = time.monotonic() + 1.0
                while time.monotonic() < deadline and mock_open.call_count == 0:
                    time.sleep(0.01)
                assert mock_open.call_count >= 1
        finally:
            handler.close()
