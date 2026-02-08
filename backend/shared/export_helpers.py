"""
Shared export response builders for Paciolus API routes.
Sprint 96.5: Extract common StreamingResponse patterns.

Reduces boilerplate across 14+ export endpoints in routes/export.py
and routes/bank_reconciliation.py.
"""

from fastapi.responses import StreamingResponse


MEDIA_PDF = "application/pdf"
MEDIA_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MEDIA_CSV = "text/csv; charset=utf-8"


def streaming_pdf_response(pdf_bytes: bytes, filename: str, chunk_size: int = 8192) -> StreamingResponse:
    """Build a StreamingResponse for a PDF file download.

    Args:
        pdf_bytes: The generated PDF content.
        filename: Already-sanitized download filename (e.g. from safe_download_filename).
        chunk_size: Byte chunk size for streaming (default 8192).
    """
    def _iter():
        for i in range(0, len(pdf_bytes), chunk_size):
            yield pdf_bytes[i:i + chunk_size]

    return StreamingResponse(
        _iter(),
        media_type=MEDIA_PDF,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


def streaming_excel_response(excel_bytes: bytes, filename: str) -> StreamingResponse:
    """Build a StreamingResponse for an Excel file download.

    Args:
        excel_bytes: The generated Excel content.
        filename: Already-sanitized download filename.
    """
    import io

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type=MEDIA_EXCEL,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(excel_bytes)),
        },
    )


def streaming_csv_response(csv_bytes: bytes, filename: str) -> StreamingResponse:
    """Build a StreamingResponse for a CSV file download.

    Args:
        csv_bytes: The generated CSV content (UTF-8 encoded).
        filename: Already-sanitized download filename.
    """
    return StreamingResponse(
        iter([csv_bytes]),
        media_type=MEDIA_CSV,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(csv_bytes)),
        },
    )
