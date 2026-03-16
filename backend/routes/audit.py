"""
Paciolus API — Core Audit Routes (thin aggregator)

This module includes all audit sub-routers. Individual endpoint families
have been decomposed into focused modules:

  - audit_upload.py     — workbook inspection
  - audit_preview.py    — PDF preview
  - audit_pipeline.py   — trial balance analysis pipeline
  - audit_flux.py       — flux (period-over-period) analysis
  - audit_diagnostics.py — preflight, population, expense, accrual checks
"""

from fastapi import APIRouter

from routes.audit_diagnostics import router as diagnostics_router
from routes.audit_flux import router as flux_router
from routes.audit_pipeline import router as pipeline_router
from routes.audit_preview import router as preview_router
from routes.audit_upload import router as upload_router

# Re-export models for backward compatibility (used by tests)
from routes.audit_preview import PdfPreviewResponse  # noqa: F401
from routes.audit_upload import SheetInfo, WorkbookInspectResponse  # noqa: F401
from services.audit.file_tool_scaffold import execute_file_tool  # noqa: F401

router = APIRouter(tags=["audit"])

router.include_router(upload_router)
router.include_router(preview_router)
router.include_router(pipeline_router)
router.include_router(flux_router)
router.include_router(diagnostics_router)
