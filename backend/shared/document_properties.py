"""Document properties for every export — Sprint 885 (review OUT-34).

Workbooks identified themselves as ``openpyxl`` (creator) and
``Microsoft Excel Compatible / Openpyxl 3.1.5`` (application); PDFs as
``ReportLab PDF Library`` (producer) with ``anonymous`` as author and
creator. That advertises the libraries and their versions and says nothing
useful to the reader.

Now every export names **Paciolus** as the software (PDF creator and
producer; workbook creator, last-modified-by and application), carries a
title, and has an author only when the firm entered one (the "Prepared by"
name) — the software is never the author, and no library name, version,
path or machine user name is written.
"""

from __future__ import annotations

import io
import zipfile
from typing import Any

from openpyxl.workbook import Workbook

from shared.excel_cells import assert_no_formulas
from shared.xlsx_in_memory import workbook_to_bytes

SOFTWARE_NAME = "Paciolus"

_APP_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
    f"<Application>{SOFTWARE_NAME}</Application></Properties>"
)


def pdf_document_properties(title: str, author: str | None = None) -> dict[str, Any]:
    """Keyword arguments for ``SimpleDocTemplate``: title, author, creator, producer."""
    return {
        "title": title,
        "author": (author or "").strip(),
        "subject": "",
        "creator": SOFTWARE_NAME,
        "producer": SOFTWARE_NAME,
    }


def save_workbook(wb: Workbook, *, title: str, author: str | None = None) -> bytes:
    """Refuse formula cells, set the document properties, and return the .xlsx bytes."""
    assert_no_formulas(wb)
    props = wb.properties
    props.creator = SOFTWARE_NAME
    props.lastModifiedBy = SOFTWARE_NAME
    props.title = title
    if author and author.strip():
        # openpyxl has no separate author field; "creator" is the software, so a
        # firm-entered author is kept in the description, labelled.
        props.description = f"Prepared by: {author.strip()}"
    # Sprint 879 (DH-06): serialized in memory — openpyxl's own save writes each
    # worksheet to a temp file first.
    return _replace_app_properties(workbook_to_bytes(wb))


def _replace_app_properties(xlsx: bytes) -> bytes:
    """openpyxl always writes its own name and version in docProps/app.xml; write ours."""
    source = zipfile.ZipFile(io.BytesIO(xlsx))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for item in source.infolist():
            data = _APP_XML.encode("utf-8") if item.filename == "docProps/app.xml" else source.read(item.filename)
            target.writestr(item, data)
    return out.getvalue()
