"""Serialize an openpyxl workbook without touching disk (Sprint 879e, review DH-06).

openpyxl's ``ExcelWriter.write_worksheet`` builds ``WorksheetWriter(ws)`` with
no ``out``, so each worksheet's XML — account names and amounts — is written to
``NamedTemporaryFile(prefix='openpyxl.', delete=False)`` and only then zipped,
even when the workbook is saved into a ``BytesIO``. The file is removed on
success, or at interpreter exit; a failure in between, or a killed worker,
leaves it on disk.

:func:`workbook_to_bytes` is the one way Paciolus serializes an XLSX:

- worksheets are written into a ``BytesIO`` and added with ``writestr`` — the
  workbook never leaves memory, so there is nothing to clean up on failure;
- :func:`_forbid_openpyxl_tempfiles` makes openpyxl's temp-file factory raise,
  so any path that bypasses this helper (``wb.save``, pandas ``to_excel``,
  write-only workbooks) fails loudly instead of writing to disk.

The override mirrors ``ExcelWriter.write_worksheet`` in the pinned openpyxl
(``requirements.txt``: ``openpyxl==3.1.5``). ``tests/test_sprint_879_xlsx_no_disk``
fails on any other version until this module is re-checked against it.
"""

from __future__ import annotations

import datetime
import io
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

import openpyxl
from openpyxl import Workbook
from openpyxl.drawing.spreadsheet_drawing import SpreadsheetDrawing
from openpyxl.worksheet import _writer as _ws_writer
from openpyxl.worksheet._writer import WorksheetWriter
from openpyxl.writer.excel import ExcelWriter

VERIFIED_OPENPYXL_VERSION = "3.1.5"


class InMemoryWorksheetError(RuntimeError):
    """openpyxl tried to create a temporary file."""


def _forbid_openpyxl_tempfiles(suffix: str = "") -> str:
    raise InMemoryWorksheetError(
        "openpyxl tried to write a worksheet to a temporary file; serialize workbooks with "
        "shared.xlsx_in_memory.workbook_to_bytes"
    )


# Installed on import: every openpyxl temp file in this process now raises.
ORIGINAL_CREATE_TEMPORARY_FILE = _ws_writer.create_temporary_file
_ws_writer.create_temporary_file = _forbid_openpyxl_tempfiles


class _InMemoryExcelWriter(ExcelWriter):
    def write_worksheet(self, ws: Any) -> None:  # mirrors openpyxl's signature
        ws._drawing = SpreadsheetDrawing()
        ws._drawing.charts = ws._charts
        ws._drawing.images = ws._images
        writer = WorksheetWriter(ws, out=io.BytesIO())
        writer.write()
        ws._rels = writer._rels
        self._archive.writestr(ws.path[1:], writer.read())
        self.manifest.append(ws)


def workbook_to_bytes(wb: Workbook) -> bytes:
    """The workbook as XLSX bytes, built entirely in memory."""
    if wb.write_only:
        raise ValueError("write-only workbooks stream through temporary files; use a normal Workbook")
    if wb.read_only:
        raise ValueError("cannot save a read-only workbook")
    # As openpyxl.writer.excel.save_workbook does.
    wb.properties.modified = datetime.datetime.now(tz=datetime.timezone.utc).replace(tzinfo=None)
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED, allowZip64=True) as archive:
        _InMemoryExcelWriter(wb, archive).save()
    return buffer.getvalue()


def openpyxl_version_is_verified() -> bool:
    return bool(openpyxl.__version__ == VERIFIED_OPENPYXL_VERSION)
