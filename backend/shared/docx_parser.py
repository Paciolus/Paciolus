"""
Paciolus — DOCX (Word Document) Parser

Parses .docx files by extracting tabular data from Word document tables
using the python-docx library. Trial balances embedded in Word documents
are expected to be in table format.

Design:
- Uses python-docx to open the document and iterate over tables
- First table with >= 2 rows is used (row 1 = headers, rest = data)
- DocxMetadata frozen dataclass attached to df.attrs for downstream consumers
- If no usable tables found, raises HTTP 400

Security:
- DOCX is ZIP-based — archive bomb checks reuse _validate_xlsx_archive()
- Binary content read via io.BytesIO — no temp files
- All processing runs inside asyncio.to_thread() + memory_cleanup() at route level
"""

import io
import logging
import zipfile
from dataclasses import dataclass

import pandas as pd
from fastapi import HTTPException

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocxMetadata:
    """Metadata extracted from a DOCX file, attached to df.attrs['docx_metadata']."""

    table_count: int
    table_index: int  # which table was used (0-based)
    original_row_count: int
    original_col_count: int


def _is_docx_zip(file_bytes: bytes) -> bool:
    """Determine whether a PK-signature ZIP file is a DOCX document.

    DOCX files contain a 'word/' directory structure (word/document.xml).
    XLSX files contain 'xl/' and ODS files contain 'content.xml' or ODS mimetype.

    Returns True if the ZIP is DOCX, False otherwise.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            names = zf.namelist()
            has_word_dir = any(n.startswith("word/") for n in names)
            has_xl_dir = any(n.startswith("xl/") for n in names)
            # DOCX: has word/ directory but NOT xl/ directory
            return has_word_dir and not has_xl_dir
    except zipfile.BadZipFile:
        return False


def parse_docx(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse DOCX file bytes into a pandas DataFrame by extracting table data.

    Scans all tables in the document and uses the first table that has
    at least one header row and one data row. The first row of the chosen
    table is treated as column headers.
    """
    try:
        from docx import Document
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="DOCX parsing is not available. The python-docx package is not installed.",
        )

    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as e:
        logger.warning("DOCX file open failed for '%s': %s", filename, e)
        raise HTTPException(
            status_code=400,
            detail="The DOCX file could not be opened. Please verify it is a valid Word document.",
        )

    tables = doc.tables
    if not tables:
        raise HTTPException(
            status_code=400,
            detail="The DOCX file contains no tables. "
            "Please provide a Word document with tabular data, "
            "or use a spreadsheet format (CSV, XLSX) instead.",
        )

    # Find first table with at least 2 rows (header + data)
    chosen_table = None
    chosen_index = 0
    for idx, table in enumerate(tables):
        if len(table.rows) >= 2:
            chosen_table = table
            chosen_index = idx
            break

    if chosen_table is None:
        # Fall back to first table even if it only has headers
        chosen_table = tables[0]
        chosen_index = 0

    # Extract headers from first row
    header_row = chosen_table.rows[0]
    headers = [cell.text.strip() for cell in header_row.cells]

    # Deduplicate headers (Word tables can have merged cells producing duplicates)
    seen: dict[str, int] = {}
    deduped_headers: list[str] = []
    for h in headers:
        label = h if h else f"Column {len(deduped_headers) + 1}"
        if label in seen:
            seen[label] += 1
            label = f"{label}_{seen[label]}"
        else:
            seen[label] = 0
        deduped_headers.append(label)

    # Extract data rows
    rows: list[dict[str, str]] = []
    for row in chosen_table.rows[1:]:
        cells = [cell.text.strip() for cell in row.cells]
        # Pad or truncate to match header count
        if len(cells) < len(deduped_headers):
            cells.extend([""] * (len(deduped_headers) - len(cells)))
        elif len(cells) > len(deduped_headers):
            cells = cells[: len(deduped_headers)]
        rows.append(dict(zip(deduped_headers, cells)))

    df = pd.DataFrame(rows, columns=deduped_headers)

    # Attach metadata
    metadata = DocxMetadata(
        table_count=len(tables),
        table_index=chosen_index,
        original_row_count=len(df),
        original_col_count=len(df.columns),
    )
    df.attrs["docx_metadata"] = metadata

    return df
