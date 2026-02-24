"""Fast inspection of Excel workbooks to retrieve sheet metadata without full processing."""

import gc
import io
from dataclasses import asdict, dataclass

import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from security_utils import log_secure_operation


@dataclass
class SheetInfo:
    """Metadata for a single sheet in a workbook."""

    name: str
    row_count: int
    column_count: int
    columns: list[str]  # First row headers
    has_data: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkbookInfo:
    """Metadata for an Excel workbook."""

    filename: str
    sheet_count: int
    sheets: list[SheetInfo]
    total_rows: int
    is_multi_sheet: bool
    format: str  # 'xlsx' or 'xls'

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "sheet_count": self.sheet_count,
            "sheets": [s.to_dict() for s in self.sheets],
            "total_rows": self.total_rows,
            "is_multi_sheet": self.is_multi_sheet,
            "format": self.format,
        }


def inspect_workbook(file_bytes: bytes, filename: str = "") -> WorkbookInfo:
    """Quickly inspect an Excel workbook and return sheet metadata."""
    log_secure_operation("inspect_workbook", f"Inspecting workbook: {filename}")

    filename_lower = filename.lower()
    is_xlsx = filename_lower.endswith(".xlsx")
    is_xls = filename_lower.endswith(".xls") and not is_xlsx

    is_ods = filename_lower.endswith(".ods")

    if not (is_xlsx or is_xls or is_ods):
        # Try to detect format from content
        if file_bytes[:4] == b"PK\x03\x04":  # ZIP signature (xlsx or ods)
            from shared.ods_parser import _is_ods_zip

            if _is_ods_zip(file_bytes):
                is_ods = True
            else:
                is_xlsx = True
        elif file_bytes[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":  # OLE signature (xls)
            is_xls = True
        else:
            raise ValueError("File is not a recognized spreadsheet format (.xlsx, .xls, or .ods)")

    buffer = io.BytesIO(file_bytes)
    sheets: list[SheetInfo] = []

    try:
        if is_ods:
            sheets = _inspect_ods(buffer, filename)
            file_format = "ods"
        elif is_xlsx:
            # Use openpyxl for .xlsx (faster metadata access)
            sheets = _inspect_xlsx(buffer, filename)
            file_format = "xlsx"
        else:
            # Use pandas with xlrd for .xls
            sheets = _inspect_xls(buffer, filename)
            file_format = "xls"

    except InvalidFileException as e:
        log_secure_operation("inspect_workbook_error", f"Invalid Excel file: {e}")
        raise ValueError(f"Invalid Excel file: {e}")
    except (KeyError, TypeError, OSError) as e:
        log_secure_operation("inspect_workbook_error", f"Error inspecting workbook: {e}")
        raise ValueError(f"Error inspecting workbook: {e}")
    finally:
        buffer.close()
        del buffer
        gc.collect()

    total_rows = sum(s.row_count for s in sheets)
    is_multi_sheet = len(sheets) > 1

    workbook_info = WorkbookInfo(
        filename=filename,
        sheet_count=len(sheets),
        sheets=sheets,
        total_rows=total_rows,
        is_multi_sheet=is_multi_sheet,
        format=file_format,
    )

    log_secure_operation("inspect_workbook_complete", f"Found {len(sheets)} sheet(s), {total_rows} total rows")

    return workbook_info


def _inspect_xlsx(buffer: io.BytesIO, filename: str) -> list[SheetInfo]:
    """Inspect an .xlsx file using openpyxl in read-only mode."""
    sheets: list[SheetInfo] = []

    # Use read_only mode for faster inspection
    wb = load_workbook(buffer, read_only=True, data_only=True)

    try:
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]

            # Get dimensions
            row_count = ws.max_row or 0
            col_count = ws.max_column or 0

            # Get column headers (first row)
            columns: list[str] = []
            if row_count > 0:
                first_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
                if first_row:
                    columns = [str(cell) if cell is not None else f"Column {i + 1}" for i, cell in enumerate(first_row)]

            has_data = row_count > 1 or (row_count == 1 and col_count > 0)

            sheets.append(
                SheetInfo(
                    name=sheet_name,
                    row_count=max(0, row_count - 1) if row_count > 0 else 0,  # Exclude header
                    column_count=col_count,
                    columns=columns,
                    has_data=has_data,
                )
            )

            log_secure_operation("inspect_sheet", f"Sheet '{sheet_name}': {row_count} rows, {col_count} cols")
    finally:
        wb.close()
        del wb
        gc.collect()

    return sheets


def _inspect_xls(buffer: io.BytesIO, filename: str) -> list[SheetInfo]:
    """Inspect an .xls file using pandas with xlrd."""
    sheets: list[SheetInfo] = []

    # Read just the sheet names first
    excel_file = pd.ExcelFile(buffer, engine="xlrd")

    try:
        for sheet_name in excel_file.sheet_names:
            # Read only the header row to get column names
            df_header = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=0)
            columns = list(df_header.columns.astype(str))

            # Read a small sample to get row count
            # For .xls, we need to read the full sheet to get accurate count
            # but we'll use a reasonable limit for inspection
            df_sample = pd.read_excel(excel_file, sheet_name=sheet_name)
            row_count = len(df_sample)
            col_count = len(columns)

            has_data = row_count > 0

            sheets.append(
                SheetInfo(
                    name=sheet_name,
                    row_count=row_count,
                    column_count=col_count,
                    columns=columns,
                    has_data=has_data,
                )
            )

            log_secure_operation("inspect_sheet", f"Sheet '{sheet_name}': {row_count} rows, {col_count} cols")

            # Clean up sample data
            del df_sample
            del df_header
            gc.collect()

    finally:
        excel_file.close()
        del excel_file
        gc.collect()

    return sheets


def _inspect_ods(buffer: io.BytesIO, filename: str) -> list[SheetInfo]:
    """Inspect an .ods file using pandas with odf engine."""
    sheets: list[SheetInfo] = []

    excel_file = pd.ExcelFile(buffer, engine="odf")

    try:
        for sheet_name in excel_file.sheet_names:
            df_header = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=0, engine="odf")
            columns = list(df_header.columns.astype(str))

            df_sample = pd.read_excel(excel_file, sheet_name=sheet_name, engine="odf")
            row_count = len(df_sample)
            col_count = len(columns)

            has_data = row_count > 0

            sheets.append(
                SheetInfo(
                    name=sheet_name,
                    row_count=row_count,
                    column_count=col_count,
                    columns=columns,
                    has_data=has_data,
                )
            )

            log_secure_operation("inspect_sheet", f"Sheet '{sheet_name}': {row_count} rows, {col_count} cols")

            del df_sample
            del df_header
            gc.collect()

    finally:
        excel_file.close()
        del excel_file
        gc.collect()

    return sheets


def is_excel_file(filename: str) -> bool:
    """Check if a filename indicates an Excel or ODS spreadsheet file."""
    lower = filename.lower()
    return lower.endswith(".xlsx") or lower.endswith(".xls") or lower.endswith(".ods")


def is_multi_sheet_file(file_bytes: bytes, filename: str) -> bool:
    """
    Quick check if an Excel file has multiple sheets.
    Returns False for non-Excel files.
    """
    if not is_excel_file(filename):
        return False

    try:
        info = inspect_workbook(file_bytes, filename)
        return info.is_multi_sheet
    except (ValueError, OSError):
        return False
