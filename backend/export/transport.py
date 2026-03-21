"""
HTTP transport layer for Paciolus diagnostic exports.

Builds StreamingResponse objects from raw file bytes, handling filename
generation and media-type selection. All response-building concerns are
centralized here so that route handlers and the pipeline never touch
HTTP response construction directly.
"""

import logging
from typing import NoReturn

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from shared.error_messages import sanitize_error
from shared.export_helpers import streaming_csv_response, streaming_excel_response, streaming_pdf_response
from shared.helpers import safe_download_filename

logger = logging.getLogger(__name__)


def build_streaming_response(
    file_bytes: bytes,
    *,
    source_filename: str,
    filename_suffix: str,
    fmt: str,
) -> StreamingResponse:
    """Build an appropriate StreamingResponse based on the output format.

    Args:
        file_bytes: The serialized file content (PDF, Excel, or CSV bytes).
        source_filename: The original filename from the client (used as prefix).
        filename_suffix: Descriptive suffix (e.g. "Diagnostic", "Workpaper", "TB").
        fmt: Output format — one of "pdf", "xlsx", "csv".

    Returns:
        A FastAPI StreamingResponse with correct media type and Content-Disposition.
    """
    extension = fmt if fmt != "xlsx" else "xlsx"
    download_filename = safe_download_filename(source_filename, filename_suffix, extension)

    if fmt == "pdf":
        return streaming_pdf_response(file_bytes, download_filename)
    elif fmt in ("xlsx", "excel"):
        return streaming_excel_response(file_bytes, download_filename)
    elif fmt == "csv":
        return streaming_csv_response(file_bytes, download_filename)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")


def handle_export_error(exc: Exception, *, log_prefix: str, error_code: str) -> NoReturn:
    """Standardized error handling for export operations.

    Logs the exception and raises an HTTPException with a sanitized message.
    This centralizes the try/except pattern that was repeated in every route handler.

    Args:
        exc: The caught exception.
        log_prefix: Human-readable prefix for the log message (e.g. "PDF export").
        error_code: Machine-readable error code slug for sanitize_error.

    Raises:
        HTTPException: Always, with status 500 and sanitized detail.
    """
    logger.exception("%s failed", log_prefix)
    raise HTTPException(status_code=500, detail=sanitize_error(exc, "export", error_code))
