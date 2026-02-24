"""
Paciolus — File Format Detection & Validation Profiles

Single source of truth for supported file formats, MIME types, magic bytes,
and format detection logic. All upload/validation code should derive its
format knowledge from this module.

Design principles:
- detect_format() never raises — it's a pure classifier
- FormatProfile is frozen/immutable — safe for module-level constants
- ALLOWED_EXTENSIONS / ALLOWED_CONTENT_TYPES are derived from active profiles
- Only profiles with parse_supported=True are considered "active"
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum, unique
from typing import NamedTuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────


@unique
class FileFormat(str, Enum):
    """Known file formats for the platform."""

    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"
    TSV = "tsv"
    TXT = "txt"
    QBO = "qbo"
    OFX = "ofx"
    IIF = "iif"
    PDF = "pdf"
    ODS = "ods"
    UNKNOWN = "unknown"


@unique
class FileValidationErrorCode(str, Enum):
    """Semantic error codes for file validation failures."""

    UNSUPPORTED_FORMAT = "unsupported_format"
    CONTENT_TYPE_REJECTED = "content_type_rejected"
    MAGIC_BYTE_MISMATCH = "magic_byte_mismatch"
    FILE_EMPTY = "file_empty"
    FILE_TOO_LARGE = "file_too_large"
    ARCHIVE_BOMB = "archive_bomb"
    XML_BOMB = "xml_bomb"
    ROW_LIMIT_EXCEEDED = "row_limit_exceeded"
    COLUMN_LIMIT_EXCEEDED = "column_limit_exceeded"
    CELL_LENGTH_EXCEEDED = "cell_length_exceeded"
    PARSE_FAILED = "parse_failed"
    DELIMITER_AMBIGUOUS = "delimiter_ambiguous"
    EXTRACTION_QUALITY_LOW = "extraction_quality_low"
    TABLE_DETECTION_FAILED = "table_detection_failed"


# ─────────────────────────────────────────────────────────────────────
# Format Profile
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FormatProfile:
    """Immutable descriptor for a file format.

    Attributes:
        format: The FileFormat enum value.
        extensions: File extensions (with leading dot, lowercase).
        content_types: Acceptable MIME types for this format.
        magic_bytes: Known file signature prefixes (empty if none).
        label: Human-readable label for error messages.
        parse_supported: Whether the platform can currently parse this format.
    """

    format: FileFormat
    extensions: frozenset[str]
    content_types: frozenset[str]
    magic_bytes: tuple[bytes, ...]
    label: str
    parse_supported: bool


# ─────────────────────────────────────────────────────────────────────
# Magic byte constants (moved from helpers.py)
# ─────────────────────────────────────────────────────────────────────

XLSX_MAGIC = b"PK\x03\x04"
XLS_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


# ─────────────────────────────────────────────────────────────────────
# Profile registry
# ─────────────────────────────────────────────────────────────────────

FORMAT_PROFILES: dict[FileFormat, FormatProfile] = {
    FileFormat.CSV: FormatProfile(
        format=FileFormat.CSV,
        extensions=frozenset({".csv"}),
        content_types=frozenset(
            {
                "text/csv",
                "application/csv",
                "application/octet-stream",
            }
        ),
        magic_bytes=(),
        label="CSV",
        parse_supported=True,
    ),
    FileFormat.XLSX: FormatProfile(
        format=FileFormat.XLSX,
        extensions=frozenset({".xlsx"}),
        content_types=frozenset(
            {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/octet-stream",
            }
        ),
        magic_bytes=(XLSX_MAGIC,),
        label="Excel (.xlsx)",
        parse_supported=True,
    ),
    FileFormat.XLS: FormatProfile(
        format=FileFormat.XLS,
        extensions=frozenset({".xls"}),
        content_types=frozenset(
            {
                "application/vnd.ms-excel",
                "application/octet-stream",
            }
        ),
        magic_bytes=(XLS_MAGIC,),
        label="Excel (.xls)",
        parse_supported=True,
    ),
    FileFormat.TSV: FormatProfile(
        format=FileFormat.TSV,
        extensions=frozenset({".tsv"}),
        content_types=frozenset({"text/tab-separated-values", "application/octet-stream"}),
        magic_bytes=(),
        label="TSV (.tsv)",
        parse_supported=True,
    ),
    FileFormat.TXT: FormatProfile(
        format=FileFormat.TXT,
        extensions=frozenset({".txt"}),
        content_types=frozenset({"text/plain", "application/octet-stream"}),
        magic_bytes=(),
        label="Text (.txt)",
        parse_supported=True,
    ),
    FileFormat.QBO: FormatProfile(
        format=FileFormat.QBO,
        extensions=frozenset({".qbo"}),
        content_types=frozenset({"application/x-ofx", "application/ofx", "application/octet-stream"}),
        magic_bytes=(),
        label="QBO (.qbo)",
        parse_supported=True,
    ),
    FileFormat.OFX: FormatProfile(
        format=FileFormat.OFX,
        extensions=frozenset({".ofx"}),
        content_types=frozenset({"application/x-ofx", "application/ofx", "application/octet-stream"}),
        magic_bytes=(),
        label="OFX (.ofx)",
        parse_supported=True,
    ),
    FileFormat.IIF: FormatProfile(
        format=FileFormat.IIF,
        extensions=frozenset({".iif"}),
        content_types=frozenset({"application/x-iif", "application/octet-stream"}),
        magic_bytes=(),
        label="IIF (.iif)",
        parse_supported=True,
    ),
    FileFormat.PDF: FormatProfile(
        format=FileFormat.PDF,
        extensions=frozenset({".pdf"}),
        content_types=frozenset({"application/pdf"}),
        magic_bytes=(b"%PDF",),
        label="PDF",
        parse_supported=True,
    ),
    FileFormat.ODS: FormatProfile(
        format=FileFormat.ODS,
        extensions=frozenset({".ods"}),
        content_types=frozenset(
            {
                "application/vnd.oasis.opendocument.spreadsheet",
                "application/octet-stream",
            }
        ),
        magic_bytes=(XLSX_MAGIC,),  # ODS is also ZIP-based
        label="ODS (.ods)",
        parse_supported=True,
    ),
}


# ─────────────────────────────────────────────────────────────────────
# Derived constants (active = parse_supported)
# ─────────────────────────────────────────────────────────────────────


def _build_active_sets() -> tuple[set[str], set[str]]:
    """Build ALLOWED_EXTENSIONS and ALLOWED_CONTENT_TYPES from active profiles."""
    extensions: set[str] = set()
    content_types: set[str] = set()
    for profile in FORMAT_PROFILES.values():
        if profile.parse_supported:
            extensions.update(profile.extensions)
            content_types.update(profile.content_types)
    return extensions, content_types


ALLOWED_EXTENSIONS, ALLOWED_CONTENT_TYPES = _build_active_sets()


# ─────────────────────────────────────────────────────────────────────
# Format detection
# ─────────────────────────────────────────────────────────────────────


class FormatDetectionResult(NamedTuple):
    """Result of detect_format(). Never raises — returns UNKNOWN for unrecognized."""

    format: FileFormat
    confidence: str  # "high", "medium", "low"
    source: str  # "extension", "magic", "content_type", "none"


def detect_format(
    filename: str | None = None,
    content_type: str | None = None,
    file_bytes: bytes | None = None,
) -> FormatDetectionResult:
    """Detect file format using extension > magic bytes > content-type priority.

    Never raises. Returns FileFormat.UNKNOWN for unrecognized inputs.
    """
    # 1. Extension-based detection (highest priority)
    if filename:
        ext = os.path.splitext(filename.lower())[1]
        if ext:
            for profile in FORMAT_PROFILES.values():
                if ext in profile.extensions:
                    return FormatDetectionResult(
                        format=profile.format,
                        confidence="high",
                        source="extension",
                    )

    # 2. Magic byte detection
    if file_bytes and len(file_bytes) >= 4:
        # ZIP-based formats (XLSX and ODS share PK\x03\x04 signature) need disambiguation
        if file_bytes[:4] == XLSX_MAGIC:
            from shared.ods_parser import _is_ods_zip

            if _is_ods_zip(file_bytes):
                return FormatDetectionResult(
                    format=FileFormat.ODS,
                    confidence="high",
                    source="magic",
                )
            return FormatDetectionResult(
                format=FileFormat.XLSX,
                confidence="high",
                source="magic",
            )

        for profile in FORMAT_PROFILES.values():
            for magic in profile.magic_bytes:
                if file_bytes[: len(magic)] == magic:
                    return FormatDetectionResult(
                        format=profile.format,
                        confidence="high",
                        source="magic",
                    )

    # 3. Content-type detection (lowest priority — browsers often misreport)
    if content_type:
        ct_lower = content_type.lower()
        # Skip application/octet-stream — too generic to be useful alone
        if ct_lower != "application/octet-stream":
            for profile in FORMAT_PROFILES.values():
                if ct_lower in profile.content_types:
                    return FormatDetectionResult(
                        format=profile.format,
                        confidence="medium",
                        source="content_type",
                    )

    return FormatDetectionResult(
        format=FileFormat.UNKNOWN,
        confidence="low",
        source="none",
    )


# ─────────────────────────────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────────────────────────────


def is_format_enabled(fmt: FileFormat) -> bool:
    """Check whether a file format is enabled via environment variable flags.

    Formats without explicit flags (CSV, XLSX, XLS, TSV, TXT) are always enabled.
    Returns True if no flag exists for the format (opt-in disabling only).
    """
    from config import (
        FORMAT_IIF_ENABLED,
        FORMAT_ODS_ENABLED,
        FORMAT_OFX_ENABLED,
        FORMAT_PDF_ENABLED,
        FORMAT_QBO_ENABLED,
    )

    _FLAG_MAP: dict[FileFormat, bool] = {
        FileFormat.ODS: FORMAT_ODS_ENABLED,
        FileFormat.PDF: FORMAT_PDF_ENABLED,
        FileFormat.IIF: FORMAT_IIF_ENABLED,
        FileFormat.OFX: FORMAT_OFX_ENABLED,
        FileFormat.QBO: FORMAT_QBO_ENABLED,
    }

    return _FLAG_MAP.get(fmt, True)


def get_active_format_labels() -> list[str]:
    """Return human-readable labels for all active (parseable) formats."""
    return [profile.label for profile in FORMAT_PROFILES.values() if profile.parse_supported]


def get_active_extensions_display() -> str:
    """Return a display string like 'CSV (.csv), TSV (.tsv), Text (.txt), Excel (.xlsx, .xls), QBO, or OFX' for error messages."""
    return "CSV (.csv), TSV (.tsv), Text (.txt), Excel (.xlsx, .xls), ODS (.ods), QBO (.qbo), OFX (.ofx), IIF (.iif), or PDF (.pdf)"
