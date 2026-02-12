"""
Paciolus API — Export Routes (aggregator).

Sprint 155: Decomposed from 1,497-line monolith into 3 sub-modules:
  - export_diagnostics.py  (6 endpoints: PDF, Excel, CSV TB, CSV Anomalies, Lead Sheets, Financial Statements)
  - export_testing.py      (8 endpoints: JE/AP/Payroll/TWM/Revenue/AR/FA/Inventory CSV)
  - export_memos.py        (10 endpoints: all memo PDF exports)

This file aggregates the sub-routers and re-exports all Pydantic models
for backward compatibility (test files import models from routes.export).
"""
from fastapi import APIRouter

from routes.export_diagnostics import router as diagnostics_router
from routes.export_testing import router as testing_router
from routes.export_memos import router as memos_router

router = APIRouter(tags=["export"])
router.include_router(diagnostics_router)
router.include_router(testing_router)
router.include_router(memos_router)

# Backward-compatible re-exports for test imports
from shared.export_schemas import (  # noqa: F401, E402
    FluxItemInput, FluxResultSummary, FluxResultInput,
    ReconScoreInput, ReconStats, ReconResultInput, LeadSheetInput,
    FinancialStatementsInput,
    JETestingExportInput, APTestingExportInput, PayrollTestingExportInput,
    ThreeWayMatchExportInput, RevenueTestingExportInput,
    ARAgingExportInput, FixedAssetExportInput, InventoryExportInput,
    BankRecMemoInput, MultiPeriodMemoInput,
)
