"""
Paciolus API — User-Friendly Error Messages

Maps common exception patterns to safe, descriptive messages.
Prevents leaking internal tracebacks, file paths, or SQL errors to API responses.
"""

import re

from security_utils import log_secure_operation

# Pattern → user-friendly message mapping
_ERROR_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Pandas CSV/Excel parsing errors
    (re.compile(r"(No columns to parse|EmptyDataError)", re.IGNORECASE),
     "The uploaded file appears to be empty or has no readable columns."),
    (re.compile(r"(ParserError|tokenizing data|expected \d+ fields)", re.IGNORECASE),
     "The file format is invalid or corrupted. Please verify it is a valid CSV or Excel file."),
    (re.compile(r"(UnicodeDecodeError|codec can't decode)", re.IGNORECASE),
     "The file contains characters that could not be decoded. Try saving the file as UTF-8 CSV."),
    (re.compile(r"(xlrd|openpyxl|BadZipFile|not a zip file)", re.IGNORECASE),
     "The Excel file could not be read. Please verify it is a valid .xlsx or .xls file."),
    # Column mapping errors
    (re.compile(r"(KeyError|column.*not found|missing.*column)", re.IGNORECASE),
     "A required column was not found in the uploaded file. Please check your column mapping."),
    # Memory/size errors
    (re.compile(r"(MemoryError|out of memory)", re.IGNORECASE),
     "The file is too large to process. Please reduce the file size or split into smaller files."),
    # Permission/file system errors
    (re.compile(r"(PermissionError|FileNotFoundError|IOError)", re.IGNORECASE),
     "A server error occurred while processing the file. Please try again."),
    # PDF generation errors
    (re.compile(r"(reportlab|canvas|pdf)", re.IGNORECASE),
     "Failed to generate the PDF report. Please try again."),
    # Database errors
    (re.compile(r"(IntegrityError|OperationalError|sqlalchemy)", re.IGNORECASE),
     "A database error occurred. Please try again."),
    # Numeric conversion errors
    (re.compile(r"(ValueError.*convert|could not convert.*float|invalid literal)", re.IGNORECASE),
     "The file contains non-numeric values in numeric columns. Please verify the data format."),
]

# Fallback messages by operation type
_FALLBACK_MESSAGES: dict[str, str] = {
    "export": "Failed to generate the export. Please try again.",
    "upload": "Failed to process the uploaded file. Please verify the file format and try again.",
    "analysis": "An error occurred during analysis. Please try again.",
    "default": "An unexpected error occurred. Please try again.",
}


def sanitize_error(
    exception: Exception,
    operation: str = "default",
    log_label: str = "",
    *,
    allow_passthrough: bool = False,
) -> str:
    """
    Convert an exception to a user-friendly message.

    Logs the full error for debugging, returns a safe message for the API response.

    Args:
        exception: The caught exception
        operation: One of "export", "upload", "analysis", "default"
        log_label: Label for secure logging (e.g., "pdf_export_error")
        allow_passthrough: If True and no dangerous pattern matches, return the
            original message instead of a generic fallback. Use for business-logic
            ValueError messages that are already user-facing.
    """
    raw_message = str(exception)

    # Always log the full error for debugging
    if log_label:
        log_secure_operation(log_label, raw_message)

    # Check against known patterns
    for pattern, friendly_message in _ERROR_PATTERNS:
        if pattern.search(raw_message):
            return friendly_message

    # Passthrough mode: return original message if no dangerous pattern matched
    if allow_passthrough:
        return raw_message

    # Return operation-specific fallback
    return _FALLBACK_MESSAGES.get(operation, _FALLBACK_MESSAGES["default"])
