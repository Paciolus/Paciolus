"""
Paciolus — ODS (OpenDocument Spreadsheet) Parser

Parses .ods files via pandas with the odf engine (odfpy).
ODS files are ZIP-based (like XLSX) but contain content.xml instead of xl/.

Design:
- Uses pd.read_excel(engine='odf') for parsing (odfpy backend)
- OdsMetadata frozen dataclass attached to df.attrs for downstream consumers
- Multi-sheet support follows XLSX pattern (default: first sheet)
- ZIP disambiguation: _is_ods_zip() inspects ZIP contents to differentiate ODS vs XLSX

Security:
- Archive bomb checks reuse _validate_xlsx_archive() (both are ZIP containers)
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
class OdsMetadata:
    """Metadata extracted from an ODS file, attached to df.attrs['ods_metadata']."""

    sheet_name: str
    sheet_count: int
    original_row_count: int
    original_col_count: int


def _is_ods_zip(file_bytes: bytes) -> bool:
    """Determine whether a PK-signature ZIP file is an ODS document.

    ODS files contain either:
    - A 'mimetype' entry with 'opendocument.spreadsheet' content
    - A 'content.xml' entry (fallback for minimal ODS files)

    XLSX files contain an 'xl/' directory structure.

    Returns True if the ZIP is ODS, False otherwise.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            names = zf.namelist()

            # Primary check: mimetype file with ODS content
            if "mimetype" in names:
                try:
                    mimetype_content = zf.read("mimetype").decode("utf-8", errors="ignore").strip()
                    if "opendocument.spreadsheet" in mimetype_content:
                        return True
                except (KeyError, zipfile.BadZipFile):
                    pass

            # Fallback: content.xml present AND no xl/ directory AND mimetype
            # file is absent (some ODS generators omit it). If mimetype exists
            # but didn't match, this is NOT an ODS file.
            has_content_xml = "content.xml" in names
            has_xl_dir = any(n.startswith("xl/") for n in names)
            has_mimetype = "mimetype" in names

            if has_content_xml and not has_xl_dir and not has_mimetype:
                return True

            return False

    except zipfile.BadZipFile:
        return False


def parse_ods(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Parse ODS file bytes into a pandas DataFrame.

    Reads the first sheet by default. Attaches OdsMetadata to df.attrs.
    """
    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes), engine="odf")
    except Exception as e:
        logger.warning("ODS file open failed for '%s': %s", filename, e)
        raise HTTPException(
            status_code=400,
            detail="The ODS file could not be opened. Please verify it is a valid OpenDocument Spreadsheet.",
        )

    try:
        sheet_names = excel_file.sheet_names
        if not sheet_names:
            raise HTTPException(
                status_code=400,
                detail="The ODS file contains no sheets. Please provide a file with at least one sheet.",
            )

        # Read first sheet
        first_sheet = sheet_names[0]
        try:
            df = pd.read_excel(excel_file, sheet_name=first_sheet, engine="odf")
        except Exception as e:
            logger.warning("ODS sheet parse failed for '%s' sheet '%s': %s", filename, first_sheet, e)
            raise HTTPException(
                status_code=400,
                detail=f"Could not read sheet '{first_sheet}' from the ODS file. "
                "Please verify the file contains valid spreadsheet data.",
            )

        # Attach metadata
        metadata = OdsMetadata(
            sheet_name=first_sheet,
            sheet_count=len(sheet_names),
            original_row_count=len(df),
            original_col_count=len(df.columns),
        )
        df.attrs["ods_metadata"] = metadata

        return df

    finally:
        excel_file.close()
