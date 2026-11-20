"""Sprint 888 (CEO brief 13C): logs carry nothing from an uploaded file.

The Data Handling document, the Security Policy, the Subprocessor List and the Privacy page say
application logs hold no uploaded content. Three parser log lines did: the PDF page-failure warning
named the file, and the OFX and IIF "parsed" lines logged the statement's currency, masked account
number and date range. Counts and format facts (dialect, encoding) are fine; values from the file
are not.
"""

import logging
from unittest.mock import MagicMock

from shared.iif_parser import parse_iif
from shared.ofx_parser import parse_ofx
from tests.test_iif_parser import MINIMAL_IIF
from tests.test_ofx_parser import SGML_V1_DOC


def _all_log_text(caplog) -> str:
    return "\n".join(record.getMessage() for record in caplog.records)


def test_ofx_parse_logs_no_statement_values(caplog):
    with caplog.at_level(logging.DEBUG):
        parse_ofx(SGML_V1_DOC.encode("ascii"), "client-statement-ACME.ofx")
    text = _all_log_text(caplog)
    assert "OFX parsed" in text  # the observability line is still there
    for value in ("USD", "9012", "123456789012", "2024-01-01", "20240101", "2024-01-31", "ACME", "CHECKING"):
        assert value not in text, value


def test_iif_parse_logs_no_dates(caplog):
    with caplog.at_level(logging.DEBUG):
        df = parse_iif(MINIMAL_IIF.encode("utf-8"), "ACME-ledger.iif")
    text = _all_log_text(caplog)
    assert "IIF parsed" in text
    assert "ACME" not in text
    dates = {str(v) for col in df.columns if "date" in col.lower() for v in df[col].dropna()}
    for value in dates:
        assert value[:10] not in text, value


def test_pdf_page_failure_does_not_log_the_filename(caplog):
    from shared.pdf_extraction import _extract_tables_from_pages

    page = MagicMock()
    page.page_number = 3
    page.extract_table.side_effect = ValueError("bad page")
    pdf = MagicMock()
    pdf.pages = [page]
    with caplog.at_level(logging.DEBUG):
        _tables, _scanned, dropped = _extract_tables_from_pages(pdf, None, "ACME-Corp-TB-2026.pdf")
    assert dropped == 1
    text = _all_log_text(caplog)
    assert "page 3" in text
    assert "ACME" not in text
