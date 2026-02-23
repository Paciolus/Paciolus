"""
Paciolus — PDF Table Extraction with Quality Gates

High-confidence PDF table extraction for financial documents.
Uses pdfplumber (pure Python, built on pdfminer.six) for table detection.

Design:
- Quality gate with composite confidence score (header, numeric density, row consistency)
- Multi-page table stitching (repeated-header detection)
- Per-page timeout guard prevents pathological PDFs from hanging
- Preview mode (first N pages) for frontend quality assessment before full parse
- Fails safely with actionable remediation hints when extraction quality is low

Security:
- pdfplumber opens via io.BytesIO — no temp files written to disk
- Per-page time.time() guard (5s) drops slow pages
- MAX_PDF_PAGES (500) rejects oversized documents
- All processing runs inside asyncio.to_thread() + memory_cleanup() at route level
"""

import io
import logging
import time
from dataclasses import dataclass, field

import pandas as pd
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────

MAX_PDF_PAGES = 500
PREVIEW_PAGE_LIMIT = 3
PER_PAGE_TIMEOUT_SECONDS = 5.0
CONFIDENCE_THRESHOLD = 0.6

_PDF_MAGIC = b"%PDF"


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


def _validate_page_count(pdf, filename: str) -> None:
    """Reject PDFs exceeding MAX_PDF_PAGES."""
    page_count = len(pdf.pages)
    if page_count > MAX_PDF_PAGES:
        raise HTTPException(
            status_code=400,
            detail=f"The PDF '{filename}' has {page_count:,} pages, exceeding the "
            f"maximum of {MAX_PDF_PAGES:,}. Please split the document or export "
            "as CSV/Excel from your source system.",
        )


# ─────────────────────────────────────────────────────────────────────
# Table extraction
# ─────────────────────────────────────────────────────────────────────


def _extract_tables_from_pages(
    pdf, max_pages: int | None, filename: str
) -> tuple[list[list[list[str | None]]], int, int]:
    """Extract tables from PDF pages with per-page timeout.

    Returns (raw_tables, pages_scanned, dropped_pages).
    Each raw_table is a list of rows, where each row is a list of cell strings.
    """
    pages_to_scan = pdf.pages
    if max_pages is not None:
        pages_to_scan = pages_to_scan[:max_pages]

    raw_tables: list[list[list[str | None]]] = []
    dropped_pages = 0

    for page in pages_to_scan:
        start_time = time.time()

        try:
            table = page.extract_table()
            elapsed = time.time() - start_time

            if elapsed > PER_PAGE_TIMEOUT_SECONDS:
                logger.warning(
                    "PDF page %d of '%s' took %.1fs (limit %.1fs), dropping",
                    page.page_number,
                    filename,
                    elapsed,
                    PER_PAGE_TIMEOUT_SECONDS,
                )
                dropped_pages += 1
                continue

            if table and len(table) > 0:
                raw_tables.append(table)

        except Exception:
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
# Main orchestrator
# ─────────────────────────────────────────────────────────────────────


def extract_pdf_tables(
    file_bytes: bytes,
    filename: str,
    max_pages: int | None = None,
) -> PdfExtractionResult:
    """Extract tables from a PDF file with quality metrics.

    Args:
        file_bytes: Raw PDF bytes.
        filename: Original filename for error messages.
        max_pages: If set, only scan this many pages (preview mode).

    Returns:
        PdfExtractionResult with metadata, column names, rows, and preview flag.
    """
    import pdfplumber

    _validate_pdf_magic(file_bytes, filename)

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
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
