"""Shared CSV-export helpers for routes/export_*.py (Sprint 539 + Sprint 725).

Two helpers, one shape per export style:

- ``csv_export_handler``: testing-tool flagged-entry pattern — schema-driven
  header + flagged-entry rows + summary footer. Originated as
  ``routes/export_testing.py::csv_export_handler`` (Sprint 539); promoted to
  ``shared`` in Sprint 725 so the diagnostic exports can sit alongside.

- ``diagnostic_csv_export``: free-form body pattern — caller supplies a
  ``body_writer(csv.writer)`` callable that fills the body. Wraps the
  StringIO setup, UTF-8-BOM encoding, ``streaming_csv_response`` transport,
  and exception handling. Sprint 725 collapsed 6 copy-pasted CSV endpoints
  in ``routes/export_diagnostics.py`` onto this helper.

Why two helpers and not one: the testing-tool shape has a stable schema and
summary footer that benefits from declarative column specs; the diagnostic
shape varies wildly per endpoint (TB has TOTALS, population profile has
sectioned summaries, anomalies has per-row drill-down) and a schema would
just be a worse callable. Split helpers, same transport boilerplate.
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Callable
from io import StringIO
from typing import Any

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from shared.error_messages import sanitize_error
from shared.export_helpers import streaming_csv_response, write_testing_csv_summary
from shared.filenames import safe_download_filename

logger = logging.getLogger(__name__)


# Type alias for a single column schema entry — (header_label, extractor_callable).
ColumnSpec = tuple[str, Any]

# Optional custom summary writer signature: ``(writer, composite_score) -> None``.
SummaryWriter = Any  # Callable[[csv.writer, dict], None] | None


def _write_flagged_rows(writer: Any, test_results: list[dict], schema: list[ColumnSpec]) -> None:
    """Iterate test_results → flagged_entries and emit one CSV row per entry."""
    for tr in test_results:
        for fe in tr.get("flagged_entries", []):
            entry = fe.get("entry", {})
            writer.writerow([extractor(fe, entry) for _header, extractor in schema])


def csv_export_handler(
    *,
    test_results: list[dict],
    schema: list[ColumnSpec],
    composite_score: dict[str, Any],
    filename_raw: str,
    filename_suffix: str,
    entry_label: str,
    error_log_prefix: str,
    error_code: str,
    summary_writer: SummaryWriter = None,
) -> StreamingResponse:
    """Testing-tool flagged-entry CSV pipeline (header → rows → summary → encode → respond).

    Args:
        test_results: The test_results list from the export input model.
        schema: Column schema (list of (header, extractor) tuples).
        composite_score: The composite_score dict for the summary section.
        filename_raw: Raw filename from client input.
        filename_suffix: Fallback suffix for safe_download_filename.
        entry_label: Label for write_testing_csv_summary (e.g. "Entries").
        error_log_prefix: Prefix for the logger.exception message.
        error_code: Error code slug for sanitize_error.
        summary_writer: Optional custom summary writer. If None, uses the
            standard write_testing_csv_summary. Receives (writer, composite_score).
    """
    try:
        output = StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([header for header, _extractor in schema])

        # Data rows
        _write_flagged_rows(writer, test_results, schema)

        # Summary section
        if summary_writer is not None:
            summary_writer(writer, composite_score)
        else:
            write_testing_csv_summary(writer, composite_score, entry_label)

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode("utf-8-sig")

        download_filename = safe_download_filename(filename_raw, filename_suffix, "csv")

        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("%s CSV export failed", error_log_prefix)
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", error_code))


# ---------------------------------------------------------------------------
# Diagnostic export helper (Sprint 725)
# ---------------------------------------------------------------------------


# Type alias for a body writer: receives the csv.writer, populates rows freely.
BodyWriter = Callable[[Any], None]


def diagnostic_csv_export(
    *,
    body_writer: BodyWriter,
    filename_raw: str,
    filename_suffix: str,
    error_log_prefix: str,
    error_code: str,
) -> StreamingResponse:
    """Free-form CSV body wrapper — handles StringIO, encoding, transport, and exceptions.

    Args:
        body_writer: Called with the configured ``csv.writer``. Writes header row(s)
            and data rows for the diagnostic endpoint. Free to write multiple
            sections (sectioned summary blocks etc.) — the helper does not enforce
            a schema.
        filename_raw: Raw filename from client input.
        filename_suffix: Fallback suffix for safe_download_filename.
        error_log_prefix: Prefix for the logger.exception message on failure.
        error_code: Error code slug for sanitize_error.

    Why a callable, not a schema: the diagnostic shape varies per endpoint
    (TB has TOTALS, population profile has multiple section headings, anomalies
    has per-row drill-down). A callable is the smallest abstraction that
    actually fits all six existing endpoints without papering over differences.
    """
    try:
        output = StringIO()
        writer = csv.writer(output)

        body_writer(writer)

        csv_content = output.getvalue()
        csv_bytes = csv_content.encode("utf-8-sig")

        download_filename = safe_download_filename(filename_raw, filename_suffix, "csv")
        return streaming_csv_response(csv_bytes, download_filename)
    except (ValueError, KeyError, TypeError, UnicodeEncodeError) as e:
        logger.exception("%s CSV export failed", error_log_prefix)
        raise HTTPException(status_code=500, detail=sanitize_error(e, "export", error_code))


__all__ = [
    "ColumnSpec",
    "SummaryWriter",
    "BodyWriter",
    "csv_export_handler",
    "diagnostic_csv_export",
]
