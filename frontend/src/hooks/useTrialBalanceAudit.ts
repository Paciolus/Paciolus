'use client'

/**
 * useTrialBalanceAudit — Thin composite hook (Sprint 519 Phase 2)
 *
 * Wires together 4 focused hooks for the trial-balance page which
 * genuinely needs the combined surface. Individual consumers should
 * import from the focused hooks directly:
 *   - useTrialBalanceUpload    (core upload, materiality, progress)
 *   - useTrialBalancePreflight (preflight, gates, column mapping)
 *   - useTrialBalanceExports   (PDF/CSV export handlers)
 *   - useTrialBalanceBenchmarks (industry benchmarks)
 */

import { useTrialBalanceBenchmarks } from './useTrialBalanceBenchmarks'
import { useTrialBalanceExports } from './useTrialBalanceExports'
import { useTrialBalancePreflight } from './useTrialBalancePreflight'
import { useTrialBalanceUpload } from './useTrialBalanceUpload'

// Sprint 225: AuditResult relocated to types/diagnostic.ts (single source of truth)
export type { AuditResult } from '@/types/diagnostic'

export function useTrialBalanceAudit() {
  const upload = useTrialBalanceUpload()

  const preflight = useTrialBalancePreflight(upload)

  const exports = useTrialBalanceExports({
    auditResult: upload.auditResult,
    preflightReport: preflight.preflightReport,
    selectedFile: upload.selectedFile,
    token: upload.token,
  })

  const benchmarks = useTrialBalanceBenchmarks({
    auditStatus: upload.auditStatus,
    auditResult: upload.auditResult,
  })

  return {
    // Auth
    user: upload.user,
    isAuthenticated: upload.isAuthenticated,
    token: upload.token,
    isVerified: upload.isVerified,
    // Pre-flight (Sprint 283)
    preflightStatus: preflight.preflightStatus,
    preflightReport: preflight.preflightReport,
    preflightError: preflight.preflightError,
    showPreflight: preflight.showPreflight,
    handlePreflightProceed: preflight.handlePreflightProceed,
    handlePreflightExportPDF: exports.handlePreflightExportPDF,
    handlePreflightExportCSV: exports.handlePreflightExportCSV,
    // Population Profile (Sprint 287)
    handlePopulationProfileExportPDF: exports.handlePopulationProfileExportPDF,
    handlePopulationProfileExportCSV: exports.handlePopulationProfileExportCSV,
    // Expense Category (Sprint 289)
    handleExpenseCategoryExportPDF: exports.handleExpenseCategoryExportPDF,
    handleExpenseCategoryExportCSV: exports.handleExpenseCategoryExportCSV,
    // Accrual Completeness (Sprint 290)
    handleAccrualCompletenessExportPDF: exports.handleAccrualCompletenessExportPDF,
    handleAccrualCompletenessExportCSV: exports.handleAccrualCompletenessExportCSV,
    // Audit state
    auditStatus: upload.auditStatus,
    auditResult: upload.auditResult,
    auditError: upload.auditError,
    selectedFile: upload.selectedFile,
    isRecalculating: upload.isRecalculating,
    scanningRows: upload.scanningRows,
    // Materiality
    materialityThreshold: upload.materialityThreshold,
    setMaterialityThreshold: upload.setMaterialityThreshold,
    displayMode: upload.displayMode,
    handleDisplayModeChange: upload.handleDisplayModeChange,
    // Column mapping
    showColumnMappingModal: preflight.showColumnMappingModal,
    pendingColumnDetection: preflight.pendingColumnDetection,
    handleColumnMappingConfirm: preflight.handleColumnMappingConfirm,
    handleColumnMappingClose: preflight.handleColumnMappingClose,
    columnMappingSource: preflight.columnMappingSource,
    // Workbook inspector
    showWorkbookInspector: preflight.showWorkbookInspector,
    pendingWorkbookInfo: preflight.pendingWorkbookInfo,
    handleWorkbookInspectorConfirm: preflight.handleWorkbookInspectorConfirm,
    handleWorkbookInspectorClose: preflight.handleWorkbookInspectorClose,
    // PDF preview (Sprint 427)
    showPdfPreview: preflight.showPdfPreview,
    pendingPdfPreview: preflight.pendingPdfPreview,
    handlePdfPreviewConfirm: preflight.handlePdfPreviewConfirm,
    handlePdfPreviewClose: preflight.handlePdfPreviewClose,
    // Benchmarks
    selectedIndustry: benchmarks.selectedIndustry,
    availableIndustries: benchmarks.availableIndustries,
    comparisonResults: benchmarks.comparisonResults,
    isLoadingComparison: benchmarks.isLoadingComparison,
    handleIndustryChange: benchmarks.handleIndustryChange,
    // File upload
    isDragging: preflight.isDragging,
    handleDrop: preflight.handleDrop,
    handleDragOver: preflight.handleDragOver,
    handleDragLeave: preflight.handleDragLeave,
    handleFileSelect: preflight.handleFileSelect,
    // Actions
    resetAudit: preflight.resetAll,
    handleRerunAudit: upload.handleRerunAudit,
  }
}

/** Inferred return type — composite of upload, preflight, exports, and benchmarks */
export type UseTrialBalanceAuditReturn = ReturnType<typeof useTrialBalanceAudit>
