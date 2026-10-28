"""
Shared export response builders for Paciolus API routes.
Sprint 96.5: Extract common StreamingResponse patterns.

Sprint 819 item 7: every file-download endpoint builds its response here
(``attachment_response`` and the three per-format wrappers). Exports are
generated fully in memory, so the body goes out as one chunk — the PDF
builders' 8 KB chunking bought nothing. ``Cache-Control: no-store`` is added to
every attachment by ``SecurityHeadersMiddleware`` (decided 2026-10-24), not here.

Why still a ``StreamingResponse`` and not a plain ``Response``: GZipMiddleware
(``minimum_size=500``) cannot see a streamed body's size, so it gzips every
download today, small ones included. A plain ``Response`` would stop
compressing downloads under 500 bytes — a change on the wire the Sprint 819
"output must not change" rule does not allow a refactor to make. Callers are
typed against ``Response`` (the base class), so that switch, if wanted, is a
one-line change here.
"""

from typing import Any

from fastapi.responses import Response, StreamingResponse

MEDIA_PDF = "application/pdf"
MEDIA_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MEDIA_CSV = "text/csv; charset=utf-8"
MEDIA_ZIP = "application/zip"


def attachment_response(
    content: bytes | str,
    filename: str,
    media_type: str,
    *,
    quote_filename: bool = True,
) -> Response:
    """Build a file-download response for content already in memory.

    Args:
        content: The file body. ``str`` is encoded as UTF-8 (no BOM; callers
            that want a BOM encode with ``utf-8-sig`` themselves).
        filename: Already-sanitized download filename.
        media_type: The ``Content-Type``. A ``text/*`` type without a charset
            gets ``; charset=utf-8`` appended by Starlette.
        quote_filename: ``filename="..."`` (default). ``False`` keeps the bare
            ``filename=...`` form the form-input tool exports have always sent,
            so their headers stay byte-identical.
    """
    body = content.encode("utf-8") if isinstance(content, str) else content
    disposition = f'attachment; filename="{filename}"' if quote_filename else f"attachment; filename={filename}"
    return StreamingResponse(
        iter([body]),
        media_type=media_type,
        headers={
            "Content-Disposition": disposition,
            "Content-Length": str(len(body)),
        },
    )


def pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    """PDF download (quoted filename)."""
    return attachment_response(pdf_bytes, filename, MEDIA_PDF)


def excel_response(excel_bytes: bytes, filename: str) -> Response:
    """XLSX download (quoted filename)."""
    return attachment_response(excel_bytes, filename, MEDIA_EXCEL)


def csv_response(csv_bytes: bytes, filename: str) -> Response:
    """CSV download (quoted filename). ``csv_bytes`` is already encoded."""
    return attachment_response(csv_bytes, filename, MEDIA_CSV)


def write_testing_csv_summary(writer: Any, composite_score: dict[str, Any], entry_label: str = "Entries") -> None:
    """Write standardized CSV summary section for testing exports.

    Used by 6 of 8 testing CSV endpoints (JE, AP, Payroll, Revenue, FA, Inventory).
    TWM and AR Aging have custom summary layouts.
    """
    writer.writerow([])
    writer.writerow(["SUMMARY"])
    writer.writerow(["Composite Score", f"{composite_score.get('score', 0):.1f}"])
    writer.writerow(["Diagnostic Tier", composite_score.get("risk_tier", "")])
    writer.writerow([f"Total {entry_label}", composite_score.get("total_entries", 0)])
    writer.writerow(["Total Flagged", composite_score.get("total_flagged", 0)])
    writer.writerow(["Flag Rate", f"{composite_score.get('flag_rate', 0):.1%}"])
