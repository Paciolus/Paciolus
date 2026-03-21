"""
Paciolus API — Audit Preview Routes (PDF Preview)
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from auth import require_verified_user
from models import User
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.helpers import memory_cleanup, validate_file_size
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


class PdfPreviewResponse(BaseModel):
    filename: str
    page_count: int
    tables_found: int
    extraction_confidence: float
    header_confidence: float
    numeric_density: float
    row_consistency: float
    column_names: list[str]
    sample_rows: list[dict[str, str]]
    remediation_hints: list[str]
    passes_quality_gate: bool
    preflight_token: str | None = None


@router.post("/audit/preview-pdf", response_model=PdfPreviewResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def preview_pdf_endpoint(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_verified_user),
) -> PdfPreviewResponse:
    """Preview PDF table extraction with quality metrics before full parse."""
    from shared.pdf_parser import CONFIDENCE_THRESHOLD, PREVIEW_PAGE_LIMIT, extract_pdf_tables

    log_secure_operation(
        "preview_pdf_upload",
        f"Previewing PDF: {file.filename}",
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _preview() -> Any:
                return extract_pdf_tables(file_bytes, filename, max_pages=PREVIEW_PAGE_LIMIT)

            result = await asyncio.to_thread(_preview)

            # Build sample rows (first 5) as list of dicts
            sample_rows: list[dict[str, str]] = []
            for row in result.rows[:5]:
                row_dict: dict[str, str] = {}
                for i, col in enumerate(result.column_names):
                    row_dict[col] = row[i] if i < len(row) else ""
                sample_rows.append(row_dict)

            # Cache file bytes so the audit endpoint can reuse them
            from shared.preflight_cache import preflight_cache

            token = preflight_cache.put(file_bytes, filename)

            return {  # type: ignore[return-value]
                "filename": filename,
                "page_count": result.metadata.page_count,
                "tables_found": result.metadata.tables_found,
                "extraction_confidence": result.metadata.extraction_confidence,
                "header_confidence": result.metadata.header_confidence,
                "numeric_density": result.metadata.numeric_density,
                "row_consistency": result.metadata.row_consistency,
                "column_names": result.column_names,
                "sample_rows": sample_rows,
                "remediation_hints": result.metadata.remediation_hints,
                "passes_quality_gate": result.metadata.extraction_confidence >= CONFIDENCE_THRESHOLD,
                "preflight_token": token,
            }

        except (ValueError, OSError) as e:
            logger.exception("PDF preview failed")
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "upload", "preview_pdf_error"),
            )
