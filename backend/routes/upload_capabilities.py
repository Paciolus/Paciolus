"""Upload capabilities — Sprint 890 (CEO brief 15B, review ST-05).

The frontend kept its own size limit (50 MB), extension list, MIME list and label, and always
offered ODS, while this backend enforces 100 MiB per file and turns ODS off by default
(``FORMAT_ODS_ENABLED``). This public, reference-data endpoint serves the effective values, and
the frontend derives its file pickers, client-side checks, labels and too-large message from it
(``frontend/src/hooks/useUploadCapabilities.ts``).

Logo uploads and shared-export sizes have their own limits for other purposes and are not here.
"""

from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import BaseModel

from routes.bulk_upload import BULK_MAX_FILES
from shared.file_formats import FORMAT_PROFILES, is_format_enabled
from shared.upload_pipeline import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB, MAX_ROW_COUNT

router = APIRouter(tags=["reference"])


class UploadFormatResponse(BaseModel):
    format: str
    label: str
    extensions: list[str]
    mime_types: list[str]


class UploadCapabilitiesResponse(BaseModel):
    max_file_size_bytes: int
    max_file_size_mb: int
    max_rows: int
    bulk_max_files: int
    formats: list[UploadFormatResponse]


def upload_capabilities() -> UploadCapabilitiesResponse:
    """The limits and the formats this deployment accepts right now."""
    formats = [
        UploadFormatResponse(
            format=fmt.value,
            label=profile.label,
            extensions=sorted(profile.extensions),
            mime_types=sorted(profile.content_types),
        )
        for fmt, profile in FORMAT_PROFILES.items()
        if profile.parse_supported and is_format_enabled(fmt)
    ]
    return UploadCapabilitiesResponse(
        max_file_size_bytes=MAX_FILE_SIZE_BYTES,
        max_file_size_mb=MAX_FILE_SIZE_MB,
        max_rows=MAX_ROW_COUNT,
        bulk_max_files=BULK_MAX_FILES,
        formats=formats,
    )


@router.get("/upload/capabilities", response_model=UploadCapabilitiesResponse)
def get_upload_capabilities(response: Response) -> UploadCapabilitiesResponse:
    """Effective upload limits and enabled file formats (public reference data)."""
    response.headers["Cache-Control"] = "public, max-age=300"
    return upload_capabilities()
