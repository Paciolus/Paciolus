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
from routes.export_memos import router as memos_router
from routes.export_testing import router as testing_router

router = APIRouter(tags=["export"])
router.include_router(diagnostics_router)
router.include_router(testing_router)
router.include_router(memos_router)

# TODO: remove after Sprint 545 — migrate all test imports to shared.export_schemas
# These re-exports exist because ~30 test files import from routes.export.
# Canonical source: shared/export_schemas.py
from shared.export_schemas import (  # noqa: F401, E402
    APTestingExportInput,
    ARAgingExportInput,
    BankRecMemoInput,
    CurrencyConversionMemoInput,
    FinancialStatementsInput,
    FixedAssetExportInput,
    FluxItemInput,
    FluxResultInput,
    FluxResultSummary,
    InventoryExportInput,
    JETestingExportInput,
    LeadSheetInput,
    MultiPeriodMemoInput,
    PayrollTestingExportInput,
    ReconResultInput,
    ReconScoreInput,
    ReconStats,
    RevenueTestingExportInput,
    ThreeWayMatchExportInput,
)
