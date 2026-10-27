"""
Paciolus — PDF Table Extraction with Quality Gates

High-confidence PDF table extraction for financial documents.
Uses pdfplumber (pure Python, built on pdfminer.six) for table detection.

Design:
- Extraction itself lives in ``shared.pdf_extraction`` and runs in a child
  process (Sprint 850); this module is the parent side
- Quality gate with composite confidence score (header, numeric density, row consistency)
- Multi-page table stitching (repeated-header detection)
- Preview mode (first N pages) for frontend quality assessment before full parse
- Fails safely with actionable remediation hints when extraction quality is low

Security:
- pdfplumber opens via io.BytesIO — no temp files written to disk
- MAX_PDF_PAGES (500) rejects oversized documents
- Sprint 850 (security review M6): parsing runs in a ``spawn``-context child
  process capped at 1 GiB of address space (RLIMIT_AS, Linux only) with a
  30 s overall deadline, after which the parent kills it. pdfminer inflates
  FlateDecode streams with no output cap, so a few-MB PDF can expand to
  gigabytes; the cap turns that into a MemoryError in the child instead of
  an OOM-killed API worker. A memory abort, a dead child or a timeout is a
  422 and increments ``paciolus_pdf_parse_aborted_total{reason}``.
- All processing runs inside asyncio.to_thread() + memory_cleanup() at route level
"""

import logging
import multiprocessing
import time
from typing import Any

import pandas as pd
from fastapi import HTTPException

from shared.parser_metrics import pdf_parse_aborted_total
from shared.pdf_extraction import (
    CONFIDENCE_THRESHOLD,
    MAX_PDF_PAGES,
    PREVIEW_PAGE_LIMIT,
    PdfExtractionMetadata,
    PdfExtractionResult,
    _build_remediation_hints,
    _compute_quality_metrics,
    _is_numeric,
    _normalize_row,
    _rows_match,
    _stitch_tables,
    sandbox_main,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CONFIDENCE_THRESHOLD",
    "MAX_PDF_PAGES",
    "PDF_TOO_COMPLEX_DETAIL",
    "PREVIEW_PAGE_LIMIT",
    "PdfExtractionMetadata",
    "PdfExtractionResult",
    "_build_remediation_hints",
    "_compute_quality_metrics",
    "_is_numeric",
    "_normalize_row",
    "_rows_match",
    "_stitch_tables",
    "extract_pdf_tables",
    "parse_pdf",
]

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

# Sandbox limits (Sprint 850). The deadline covers the whole child lifetime —
# interpreter start, pdfplumber import and parse — not just the parse.
PDF_PARSE_TIMEOUT_SECONDS = 30.0
PDF_CHILD_MEMORY_LIMIT_BYTES = 1024 * 1024 * 1024  # 1 GiB
_KILL_GRACE_SECONDS = 2.0

PDF_TOO_COMPLEX_DETAIL = "This PDF is too complex to parse. Export the trial balance as Excel or CSV instead."

_PDF_MAGIC = b"%PDF"

# ``spawn``, never ``fork``: forking a gunicorn worker would copy the whole app
# (DB pools, Redis clients, threads) into the child. The target lives in
# ``shared.pdf_extraction`` so the child imports only that and pdfplumber.
_SPAWN = multiprocessing.get_context("spawn")

# Indirection so a test can swap in a target that dies without a result.
_sandbox_target: Any = sandbox_main


# ─────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────


def _validate_pdf_magic(file_bytes: bytes, filename: str) -> None:
    """Check %PDF prefix. Raises HTTP 400 on mismatch."""
    if not file_bytes.startswith(_PDF_MAGIC):
        raise HTTPException(
            status_code=400,
            detail=f"The file '{filename}' does not appear to be a valid PDF. "
            "Please verify the file is a PDF document.",
        )


# ─────────────────────────────────────────────────────────────────────
# Sandboxed extraction
# ─────────────────────────────────────────────────────────────────────


def _abort(reason: str) -> HTTPException:
    """Count a sandbox abort and build the client-facing 422."""
    pdf_parse_aborted_total.labels(reason=reason).inc()
    logger.warning("PDF parse aborted in sandbox [reason=%s]", reason)  # Sprint 840 (S6): no filename
    return HTTPException(status_code=422, detail=PDF_TOO_COMPLEX_DETAIL)


def _stop_child(proc: Any) -> None:
    """Terminate, then kill, a child that is still running."""
    if proc.is_alive():
        proc.terminate()
        proc.join(_KILL_GRACE_SECONDS)
    if proc.is_alive():
        proc.kill()
        proc.join(_KILL_GRACE_SECONDS)


def _run_in_sandbox(file_bytes: bytes, filename: str, max_pages: int | None) -> tuple[Any, ...]:
    """Run the extraction in a child process and return its message.

    Raises the 422 abort for a timeout or a child that exits without a result.
    """
    recv_conn, send_conn = _SPAWN.Pipe(duplex=False)
    proc = _SPAWN.Process(
        target=_sandbox_target,
        args=(send_conn, file_bytes, filename, max_pages, PDF_CHILD_MEMORY_LIMIT_BYTES),
        daemon=True,
    )
    deadline = time.monotonic() + PDF_PARSE_TIMEOUT_SECONDS
    proc.start()
    # Drop the parent's copy of the send end, so a child that dies without
    # sending shows up as EOF on recv instead of a hang.
    send_conn.close()
    received = False
    try:
        if not recv_conn.poll(max(0.0, deadline - time.monotonic())):
            raise _abort("timeout")
        try:
            message: tuple[Any, ...] = recv_conn.recv()
        except EOFError:
            raise _abort("killed") from None
        received = True
        return message
    finally:
        recv_conn.close()
        # A child that has sent its result exits on its own; anything else
        # (timeout, dead child) is stopped now.
        proc.join(_KILL_GRACE_SECONDS if received else 0)
        _stop_child(proc)
        proc.close()


def extract_pdf_tables(
    file_bytes: bytes,
    filename: str,
    max_pages: int | None = None,
) -> PdfExtractionResult:
    """Extract tables from a PDF file with quality metrics.

    Runs in a resource-limited child process (Sprint 850).

    Args:
        file_bytes: Raw PDF bytes.
        filename: Original filename for error messages.
        max_pages: If set, only scan this many pages (preview mode).

    Returns:
        PdfExtractionResult with metadata, column names, rows, and preview flag.

    Raises:
        HTTPException(400) for a non-PDF, corrupt or oversized document;
        HTTPException(422) when the sandbox runs out of memory, dies or times out.
    """
    _validate_pdf_magic(file_bytes, filename)

    message = _run_in_sandbox(file_bytes, filename, max_pages)
    kind = message[0]
    if kind == "ok":
        result: PdfExtractionResult = message[1]
        return result
    if kind == "rejected":
        raise HTTPException(status_code=message[1], detail=message[2])
    if kind == "aborted":
        raise _abort(message[1])
    # An unexpected bug in extraction — same outcome as before the sandbox,
    # where it would have propagated out of the parse.
    raise RuntimeError(f"PDF extraction failed in sandbox: {message[1]}")


# ─────────────────────────────────────────────────────────────────────
# Entry point (for helpers.py dispatch)
# ─────────────────────────────────────────────────────────────────────


def parse_pdf(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse PDF file bytes into a DataFrame with quality gate.

    Raises HTTPException(422) if extraction confidence is below threshold.
    Attaches PdfExtractionMetadata to df.attrs["pdf_metadata"].
    """
    result = extract_pdf_tables(file_bytes, filename, max_pages=None)

    if not result.column_names or not result.rows:
        hints = result.metadata.remediation_hints
        hint_text = " ".join(hints) if hints else "Export as CSV or Excel from your source system."
        raise HTTPException(
            status_code=422,
            detail=f"No tables could be extracted from the PDF '{filename}'. {hint_text}",
        )

    if result.metadata.extraction_confidence < CONFIDENCE_THRESHOLD:
        hints = result.metadata.remediation_hints
        hint_text = " ".join(hints) if hints else "Export as CSV or Excel from your source system."
        raise HTTPException(
            status_code=422,
            detail=f"PDF extraction quality is too low (confidence: "
            f"{result.metadata.extraction_confidence:.0%}). {hint_text}",
        )

    # Build DataFrame from extracted data
    df = pd.DataFrame(result.rows, columns=result.column_names)

    # Store metadata as DataFrame attribute
    df.attrs["pdf_metadata"] = result.metadata

    logger.info(
        "PDF parsed: pages=%d, tables=%d, confidence=%.2f, headers=%d, rows=%d, dropped=%d",
        result.metadata.page_count,
        result.metadata.tables_found,
        result.metadata.extraction_confidence,
        len(result.column_names),
        len(result.rows),
        result.metadata.dropped_rows,
    )

    return df
