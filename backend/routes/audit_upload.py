"""
Paciolus API — Audit Upload Routes (Workbook Inspection)
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
from workbook_inspector import inspect_workbook, is_excel_file

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


class SheetInfo(BaseModel):
    name: str
    row_count: int
    column_count: int
    columns: list
    has_data: bool


class WorkbookInspectResponse(BaseModel):
    filename: str
    sheet_count: int
    sheets: list[SheetInfo]
    total_rows: int
    is_multi_sheet: bool
    format: str
    requires_sheet_selection: bool


@router.post("/audit/inspect-workbook", response_model=WorkbookInspectResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def inspect_workbook_endpoint(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(require_verified_user),
) -> WorkbookInspectResponse:
    """Inspect an Excel workbook to retrieve sheet metadata."""
    log_secure_operation("inspect_workbook_upload", f"Inspecting workbook: {file.filename}")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            if not is_excel_file(filename):
                return {
                    "filename": file.filename,
                    "sheet_count": 1,
                    "sheets": [
                        {"name": "Sheet1", "row_count": -1, "column_count": -1, "columns": [], "has_data": True}
                    ],
                    "total_rows": -1,
                    "is_multi_sheet": False,
                    "format": "csv",
                    "requires_sheet_selection": False,
                }

            def _inspect() -> dict[str, Any]:
                workbook_info = inspect_workbook(file_bytes, filename)
                result = workbook_info.to_dict()
                result["requires_sheet_selection"] = workbook_info.is_multi_sheet
                return result

            result = await asyncio.to_thread(_inspect)

            return result

        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(
                    e,
                    "upload",
                    "inspect_workbook_error",
                ),
            )
        except (KeyError, TypeError, OSError) as e:
            logger.exception("Workbook inspection failed")
            raise HTTPException(status_code=400, detail=sanitize_error(e, "upload", "inspect_workbook_error"))
