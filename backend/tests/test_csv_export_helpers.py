"""Sprint 725 — direct tests for shared.csv_export.

The existing ``test_export_*_routes.py`` suites cover end-to-end behavior of
the diagnostic and testing CSV endpoints. This file unit-tests the helpers
themselves so a regression in (a) the body-writer signature, (b) UTF-8-BOM
encoding, or (c) the exception → HTTPException pipeline is detectable without
spinning up FastAPI's request stack.

Why both helpers and not just one: ``csv_export_handler`` is schema-driven
(testing-tool flagged-entry shape); ``diagnostic_csv_export`` is body-writer
driven (free-form per-endpoint shape). Sprint 725 promoted both to
``shared.csv_export``; tests live alongside.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.csv_export import (
    csv_export_handler,
    diagnostic_csv_export,
)

# ---------------------------------------------------------------------------
# diagnostic_csv_export
# ---------------------------------------------------------------------------


def _read_streaming_response_body(resp: Any) -> bytes:
    """Drain a Starlette StreamingResponse's async body iterator into bytes."""
    import asyncio

    async def _drain() -> bytes:
        chunks: list[bytes] = []
        async for chunk in resp.body_iterator:
            chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode("utf-8"))
        return b"".join(chunks)

    return asyncio.run(_drain())


class TestDiagnosticCsvExport:
    def test_body_writer_invoked_and_output_streamed(self):
        def _body(writer: Any) -> None:
            writer.writerow(["A", "B"])
            writer.writerow(["1", "2"])

        resp = diagnostic_csv_export(
            body_writer=_body,
            filename_raw="test.xlsx",
            filename_suffix="Smoke",
            error_log_prefix="smoke",
            error_code="smoke_err",
        )

        body = _read_streaming_response_body(resp)
        # UTF-8-BOM prefix.
        assert body.startswith(b"\xef\xbb\xbf")
        assert b"A,B" in body
        assert b"1,2" in body

    def test_filename_uses_suffix_when_filename_raw_blank(self):
        def _body(writer: Any) -> None:
            writer.writerow(["x"])

        resp = diagnostic_csv_export(
            body_writer=_body,
            filename_raw="",
            filename_suffix="Fallback",
            error_log_prefix="smoke",
            error_code="smoke_err",
        )
        cd = resp.headers.get("content-disposition", "")
        assert "Fallback" in cd
        assert ".csv" in cd

    def test_value_error_in_body_returns_http_500(self, caplog: pytest.LogCaptureFixture):
        def _body(_writer: Any) -> None:
            raise ValueError("boom in body writer")

        with pytest.raises(HTTPException) as exc_info:
            diagnostic_csv_export(
                body_writer=_body,
                filename_raw="test.xlsx",
                filename_suffix="Boom",
                error_log_prefix="boom",
                error_code="boom_err",
            )
        assert exc_info.value.status_code == 500
        # Detail is sanitized (no raw exception text leaks). Just assert the helper
        # surfaces a non-empty user-facing message and the raw exception is not present.
        detail = str(exc_info.value.detail)
        assert detail
        assert "boom in body writer" not in detail

    def test_unhandled_exception_propagates(self):
        # The helper catches ValueError/KeyError/TypeError/UnicodeEncodeError. Other
        # exception classes should propagate so the framework's middleware can
        # surface them as 500s with the standard error envelope.
        def _body(_writer: Any) -> None:
            raise RuntimeError("not in catch list")

        with pytest.raises(RuntimeError, match="not in catch list"):
            diagnostic_csv_export(
                body_writer=_body,
                filename_raw="test.xlsx",
                filename_suffix="Smoke",
                error_log_prefix="smoke",
                error_code="smoke_err",
            )


# ---------------------------------------------------------------------------
# csv_export_handler
# ---------------------------------------------------------------------------


class TestCsvExportHandler:
    def test_schema_header_and_flagged_rows(self):
        schema = [
            ("Test", lambda fe, _e: fe.get("test_name", "")),
            ("Account", lambda _fe, e: e.get("account", "")),
            ("Amount", lambda _fe, e: f"{e.get('amount', 0):.2f}"),
        ]
        test_results = [
            {
                "test_name": "X",
                "flagged_entries": [
                    {"test_name": "X", "entry": {"account": "1000", "amount": 100}},
                    {"test_name": "X", "entry": {"account": "2000", "amount": 200}},
                ],
            }
        ]
        composite_score = {"score": 5.0, "risk_tier": "low", "tests_run": 1, "total_flagged": 2}

        resp = csv_export_handler(
            test_results=test_results,
            schema=schema,
            composite_score=composite_score,
            filename_raw="test.xlsx",
            filename_suffix="Smoke",
            entry_label="Items",
            error_log_prefix="smoke",
            error_code="smoke_err",
        )
        body = _read_streaming_response_body(resp)
        text = body.decode("utf-8-sig")
        assert "Test,Account,Amount" in text
        assert "X,1000,100.00" in text
        assert "X,2000,200.00" in text
        # Default summary is appended (write_testing_csv_summary).
        assert "SUMMARY" in text or "Composite" in text

    def test_custom_summary_writer_used(self):
        schema = [("A", lambda _fe, _e: "x")]
        test_results = [{"flagged_entries": []}]
        composite_score = {"score": 1.0}

        captured: dict[str, Any] = {}

        def _custom_summary(writer: Any, score: dict) -> None:
            writer.writerow(["CUSTOM", score.get("score")])
            captured["called"] = True

        resp = csv_export_handler(
            test_results=test_results,
            schema=schema,
            composite_score=composite_score,
            filename_raw="t.xlsx",
            filename_suffix="S",
            entry_label="Items",
            error_log_prefix="smoke",
            error_code="smoke_err",
            summary_writer=_custom_summary,
        )
        body = _read_streaming_response_body(resp).decode("utf-8-sig")
        assert "CUSTOM,1.0" in body
        assert captured.get("called") is True

    def test_value_error_returns_http_500(self):
        # ValueError raised inside an extractor lambda triggers the helper's catch.
        bad_schema = [("X", lambda _fe, _e: int("not-a-number"))]
        test_results = [{"flagged_entries": [{"entry": {}}]}]

        with pytest.raises(HTTPException) as exc_info:
            csv_export_handler(
                test_results=test_results,
                schema=bad_schema,
                composite_score={"score": 0},
                filename_raw="t.xlsx",
                filename_suffix="S",
                entry_label="Items",
                error_log_prefix="smoke",
                error_code="ce_err",
            )
        assert exc_info.value.status_code == 500
        detail = str(exc_info.value.detail)
        assert detail
        # Raw exception text must not leak into the user-facing error.
        assert "not-a-number" not in detail
