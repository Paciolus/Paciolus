"""
Paciolus — PDF table extraction core (runs inside the sandbox child)

Sprint 850 (security review M6): PDF parsing moved into a resource-limited
child process. This module is everything that child needs and nothing more —
stdlib plus pdfplumber, imported lazily. It must never import FastAPI, pandas
or the app: the child is started with the ``spawn`` context, so every module
it imports is paid for on every PDF upload. ``shared.pdf_parser`` owns the
parent side (process lifecycle, HTTP errors, DataFrame build).

Design:
- Quality gate with composite confidence score (header, numeric density, row consistency)
- Multi-page table stitching (repeated-header detection)
- Preview mode (first N pages) for frontend quality assessment before full parse
- Fails safely with actionable remediation hints when extraction quality is low

Security:
- pdfplumber opens via io.BytesIO — no temp files written to disk
- MAX_PDF_PAGES (500) rejects oversized documents
- The child caps its own address space (RLIMIT_AS, Linux only) before parsing;
  the parent enforces the overall wall-clock deadline and kills the child.
"""

import io
import logging
import sys
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

MAX_PDF_PAGES = 500
PREVIEW_PAGE_LIMIT = 3
CONFIDENCE_THRESHOLD = 0.6


# ─────────────────────────────────────────────────────────────────────
# Metadata
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PdfExtractionMetadata:
    """Quality metrics and extraction metadata for a PDF parse attempt."""

    page_count: int
    tables_found: int
    extraction_confidence: float
    header_confidence: float
    numeric_density: float
    row_consistency: float
    dropped_rows: int
    remediation_hints: list[str] = field(default_factory=list)
    pages_scanned: int = 0


@dataclass(frozen=True)
class PdfExtractionResult:
    """Complete result of a PDF table extraction attempt."""

    metadata: PdfExtractionMetadata
    column_names: list[str]
    rows: list[list[str]]
    is_preview: bool


class PdfRejectedError(Exception):
    """The PDF was refused for a user-facing reason (corrupt, too many pages).

    A plain exception rather than ``HTTPException`` so this module stays free
    of FastAPI; the parent turns it into an HTTP error with the same status
    and detail.
    """

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code, detail)
        self.status_code = status_code
        self.detail = detail


def _is_memory_error(exc: BaseException | None) -> bool:
    """True if ``exc`` is, or wraps, a MemoryError.

    pdfplumber re-raises anything from pdfminer's interpreter as
    ``PdfminerException(e)``, so an allocation failure under RLIMIT_AS
    arrives wrapped.
    """
    seen = 0
    while exc is not None and seen < 10:
        if isinstance(exc, MemoryError):
            return True
        inner = exc.args[0] if exc.args and isinstance(exc.args[0], BaseException) else None
        exc = inner or exc.__cause__ or exc.__context__
        seen += 1
    return False


# ─────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────


def _validate_page_count(pdf: object, filename: str) -> None:
    """Reject PDFs exceeding MAX_PDF_PAGES."""
    page_count = len(pdf.pages)  # type: ignore[attr-defined]
    if page_count > MAX_PDF_PAGES:
        raise PdfRejectedError(
            400,
            f"The PDF '{filename}' has {page_count:,} pages, exceeding the "
            f"maximum of {MAX_PDF_PAGES:,}. Please split the document or export "
            "as CSV/Excel from your source system.",
        )


# ─────────────────────────────────────────────────────────────────────
# Table extraction
# ─────────────────────────────────────────────────────────────────────


def _extract_tables_from_pages(
    pdf: object, max_pages: int | None, filename: str
) -> tuple[list[list[list[str | None]]], int, int]:
    """Extract tables from PDF pages.

    Returns (raw_tables, pages_scanned, dropped_pages).
    Each raw_table is a list of rows, where each row is a list of cell strings.

    Sprint 850: there is no per-page timeout here. The old one compared the
    clock *after* ``extract_table()`` returned, so it could never interrupt a
    slow page. Time is bounded by the parent's overall deadline (it kills
    this process) and work by MAX_PDF_PAGES.
    """
    pages_to_scan = pdf.pages  # type: ignore[attr-defined]
    if max_pages is not None:
        pages_to_scan = pages_to_scan[:max_pages]

    raw_tables: list[list[list[str | None]]] = []
    dropped_pages = 0

    for page in pages_to_scan:
        try:
            table = page.extract_table()
            if table and len(table) > 0:
                raw_tables.append(table)

        except Exception as e:
            # An allocation failure is the memory cap doing its job — abort
            # the whole parse rather than quietly dropping the page.
            if _is_memory_error(e):
                raise MemoryError from e
            logger.warning(
                "PDF page %d of '%s' extraction failed, skipping",
                page.page_number,
                filename,
            )
            dropped_pages += 1
            continue

    return raw_tables, len(pages_to_scan), dropped_pages


# ─────────────────────────────────────────────────────────────────────
# Table stitching
# ─────────────────────────────────────────────────────────────────────


def _normalize_row(row: list[str | None]) -> list[str]:
    """Convert None cells to empty strings."""
    return [cell if cell is not None else "" for cell in row]


def _rows_match(row_a: list[str], row_b: list[str]) -> bool:
    """Check if two rows have the same content (header continuation detection)."""
    if len(row_a) != len(row_b):
        return False
    return all((a or "").strip().lower() == (b or "").strip().lower() for a, b in zip(row_a, row_b))


def _stitch_tables(raw_tables: list[list[list[str | None]]]) -> tuple[list[str], list[list[str]]]:
    """Stitch multi-page tables into a single (headers, data_rows) result.

    Strategy:
    - If a subsequent table's first row matches the first table's header,
      treat it as a continuation and merge data rows (skip repeated header).
    - Otherwise, pick the largest table by row count.
    """
    if not raw_tables:
        return [], []

    if len(raw_tables) == 1:
        table = raw_tables[0]
        if len(table) < 2:
            headers = _normalize_row(table[0]) if table else []
            return headers, []
        headers = _normalize_row(table[0])
        data_rows = [_normalize_row(row) for row in table[1:]]
        return headers, data_rows

    # Use first table's first row as the reference header
    first_table = raw_tables[0]
    headers = _normalize_row(first_table[0])
    all_data_rows: list[list[str]] = [_normalize_row(row) for row in first_table[1:]]

    stitched = True
    for table in raw_tables[1:]:
        if not table:
            continue
        candidate_header = _normalize_row(table[0])
        if _rows_match(candidate_header, headers):
            # Continuation — skip header row, append data
            for row in table[1:]:
                all_data_rows.append(_normalize_row(row))
        else:
            # Different table structure — cannot stitch
            stitched = False
            break

    if stitched:
        return headers, all_data_rows

    # Fallback: pick the largest table
    largest = max(raw_tables, key=len)
    headers = _normalize_row(largest[0])
    data_rows = [_normalize_row(row) for row in largest[1:]]
    return headers, data_rows


# ─────────────────────────────────────────────────────────────────────
# Quality metrics
# ─────────────────────────────────────────────────────────────────────


def _is_numeric(value: str) -> bool:
    """Check if a string is parseable as a float (for numeric density)."""
    if not value or not value.strip():
        return False
    cleaned = value.strip().replace(",", "").replace("$", "").replace("(", "-").replace(")", "")
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _compute_quality_metrics(headers: list[str], data_rows: list[list[str]]) -> tuple[float, float, float, float]:
    """Compute 3 quality metrics and composite confidence score.

    Returns (composite, header_confidence, numeric_density, row_consistency).
    """
    # Header confidence: ratio of non-empty, non-numeric header cells
    if not headers:
        return 0.0, 0.0, 0.0, 0.0

    non_empty_text_headers = sum(1 for h in headers if h.strip() and not _is_numeric(h))
    header_confidence = non_empty_text_headers / len(headers)

    # Numeric density: ratio of data cells parseable as numbers
    if not data_rows:
        return 0.0, header_confidence, 0.0, 0.0

    total_cells = 0
    numeric_cells = 0
    for row in data_rows:
        for cell in row:
            total_cells += 1
            if _is_numeric(cell):
                numeric_cells += 1

    numeric_density = numeric_cells / total_cells if total_cells > 0 else 0.0

    # Row consistency: ratio of rows matching header column count
    expected_cols = len(headers)
    matching_rows = sum(1 for row in data_rows if len(row) == expected_cols)
    row_consistency = matching_rows / len(data_rows) if data_rows else 0.0

    # Composite: weighted average
    composite = 0.4 * header_confidence + 0.3 * numeric_density + 0.3 * row_consistency

    return composite, header_confidence, numeric_density, row_consistency


def _build_remediation_hints(
    header_confidence: float,
    numeric_density: float,
    row_consistency: float,
) -> list[str]:
    """Generate actionable remediation hints for low-quality extractions."""
    hints: list[str] = []

    if header_confidence < 0.5:
        hints.append(
            "Column headers could not be reliably detected. "
            "Export the data as CSV or Excel from your source system for best results."
        )

    if numeric_density < 0.2:
        hints.append(
            "Very few numeric values were detected. The PDF may contain "
            "scanned images rather than extractable text. Use a text-based PDF export."
        )

    if row_consistency < 0.7:
        hints.append(
            "Row structure is inconsistent across the document. "
            "This often happens with merged cells or complex layouts. "
            "Export as CSV or Excel for reliable parsing."
        )

    if not hints:
        hints.append(
            "Extraction quality is below the confidence threshold. "
            "For best results, export the data as CSV or Excel from your source system."
        )

    return hints


# ─────────────────────────────────────────────────────────────────────
# Extraction (in the current process)
# ─────────────────────────────────────────────────────────────────────


def extract_tables_in_process(
    file_bytes: bytes,
    filename: str,
    max_pages: int | None = None,
) -> PdfExtractionResult:
    """Extract tables from a PDF in *this* process, with no resource limits.

    Only the sandbox child should call this; request handlers go through
    ``shared.pdf_parser.extract_pdf_tables``. Raises PdfRejectedError for a
    corrupt or oversized document.
    """
    import pdfplumber

    try:
        pdf_handle = pdfplumber.open(io.BytesIO(file_bytes))
    except Exception as e:
        if _is_memory_error(e):
            raise MemoryError from e
        logger.warning("PDF open failed [%s]", type(e).__name__)  # Sprint 840 (S6): no filename/text
        raise PdfRejectedError(
            400,
            f"The PDF file '{filename}' is corrupted or not a valid PDF document. "
            "Please verify the file integrity and try again.",
        )

    with pdf_handle as pdf:
        _validate_page_count(pdf, filename)

        page_count = len(pdf.pages)
        is_preview = max_pages is not None

        raw_tables, pages_scanned, dropped_pages = _extract_tables_from_pages(pdf, max_pages, filename)

    if not raw_tables:
        metadata = PdfExtractionMetadata(
            page_count=page_count,
            tables_found=0,
            extraction_confidence=0.0,
            header_confidence=0.0,
            numeric_density=0.0,
            row_consistency=0.0,
            dropped_rows=0,
            remediation_hints=[
                "No tables were detected in the PDF. "
                "The document may contain only text, images, or scanned content. "
                "Please export the data as CSV or Excel from your source system."
            ],
            pages_scanned=pages_scanned,
        )
        return PdfExtractionResult(
            metadata=metadata,
            column_names=[],
            rows=[],
            is_preview=is_preview,
        )

    headers, data_rows = _stitch_tables(raw_tables)
    composite, h_conf, n_dens, r_cons = _compute_quality_metrics(headers, data_rows)

    hints: list[str] = []
    if composite < CONFIDENCE_THRESHOLD:
        hints = _build_remediation_hints(h_conf, n_dens, r_cons)

    metadata = PdfExtractionMetadata(
        page_count=page_count,
        tables_found=len(raw_tables),
        extraction_confidence=round(composite, 3),
        header_confidence=round(h_conf, 3),
        numeric_density=round(n_dens, 3),
        row_consistency=round(r_cons, 3),
        dropped_rows=dropped_pages,
        remediation_hints=hints,
        pages_scanned=pages_scanned,
    )

    return PdfExtractionResult(
        metadata=metadata,
        column_names=headers,
        rows=data_rows,
        is_preview=is_preview,
    )


# ─────────────────────────────────────────────────────────────────────
# Sandbox child entry point
# ─────────────────────────────────────────────────────────────────────


def sandbox_main(
    conn: Any,
    file_bytes: bytes,
    filename: str,
    max_pages: int | None,
    memory_limit_bytes: int,
) -> None:
    """Child-process entry: cap memory, extract, send one message, exit.

    Messages (always a tuple, sent exactly once):
    - ("ok", PdfExtractionResult)
    - ("rejected", status_code, detail)
    - ("aborted", "memory")
    - ("error", exception type name)
    """
    # Production is Linux; dev is Windows, where the resource module doesn't
    # exist. There the parent's deadline is the only bound.
    if sys.platform != "win32":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))

    message: tuple[Any, ...]
    try:
        message = ("ok", extract_tables_in_process(file_bytes, filename, max_pages))
    except PdfRejectedError as e:
        message = ("rejected", e.status_code, e.detail)
    except MemoryError:
        message = ("aborted", "memory")
    except Exception as e:
        message = ("aborted", "memory") if _is_memory_error(e) else ("error", type(e).__name__)

    try:
        conn.send(message)
    finally:
        conn.close()
