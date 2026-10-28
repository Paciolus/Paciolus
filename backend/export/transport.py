"""
HTTP transport layer for Paciolus diagnostic exports.

Builds Response objects from raw file bytes, handling filename
generation and media-type selection. All response-building concerns are
centralized here so that route handlers and the pipeline never touch
HTTP response construction directly.
"""

import logging
from typing import NoReturn

from fastapi import HTTPException
from fastapi.responses import Response

from shared.error_messages import sanitize_error
from shared.export_helpers import csv_response, excel_response, pdf_response
from shared.filenames import safe_download_filename

logger = logging.getLogger(__name__)


def build_streaming_response(
    file_bytes: bytes,
    *,
    source_filename: str,
    filename_suffix: str,
    fmt: str,
) -> Response:
    """Build an appropriate Response based on the output format.

    Args:
        file_bytes: The serialized file content (PDF, Excel, or CSV bytes).
        source_filename: The original filename from the client (used as prefix).
        filename_suffix: Descriptive suffix (e.g. "Diagnostic", "Workpaper", "TB").
        fmt: Output format — one of "pdf", "xlsx", "csv".

    Returns:
        A FastAPI Response with correct media type and Content-Disposition.
    """
    download_filename = safe_download_filename(source_filename, filename_suffix, fmt)

    if fmt == "pdf":
        return pdf_response(file_bytes, download_filename)
    elif fmt == "xlsx":
        return excel_response(file_bytes, download_filename)
    elif fmt == "csv":
        return csv_response(file_bytes, download_filename)
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
