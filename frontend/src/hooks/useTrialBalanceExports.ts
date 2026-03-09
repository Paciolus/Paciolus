'use client'

/**
 * useTrialBalanceExports — PDF/CSV export handlers for TB diagnostics
 * Sprint 519 Phase 2: Extracted from useTrialBalanceAudit
 */

import { useCallback } from 'react'
import type { AuditResult } from '@/types/diagnostic'
import type { PreFlightReport } from '@/types/preflight'
import { apiDownload, downloadBlob } from '@/utils/apiClient'

interface UseTrialBalanceExportsInput {
  auditResult: AuditResult | null
  preflightReport: PreFlightReport | null
  selectedFile: File | null
  token: string | null
}

export interface UseTrialBalanceExportsReturn {
  handlePreflightExportPDF: () => Promise<void>
  handlePreflightExportCSV: () => Promise<void>
  handlePopulationProfileExportPDF: () => Promise<void>
  handlePopulationProfileExportCSV: () => Promise<void>
  handleExpenseCategoryExportPDF: () => Promise<void>
  handleExpenseCategoryExportCSV: () => Promise<void>
  handleAccrualCompletenessExportPDF: () => Promise<void>
  handleAccrualCompletenessExportCSV: () => Promise<void>
}

export function useTrialBalanceExports({
  auditResult,
  preflightReport,
  selectedFile,
  token,
}: UseTrialBalanceExportsInput): UseTrialBalanceExportsReturn {

  const handlePreflightExportPDF = useCallback(async () => {
    if (!preflightReport || !token) return
    const result = await apiDownload('/export/preflight-memo', token, {
      method: 'POST',
      body: { ...preflightReport, filename: selectedFile?.name || 'preflight_report' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'PreFlight_Memo.pdf')
    }
  }, [preflightReport, token, selectedFile])

  const handlePreflightExportCSV = useCallback(async () => {
    if (!preflightReport || !token) return
    const result = await apiDownload('/export/csv/preflight-issues', token, {
      method: 'POST',
      body: { issues: preflightReport.issues, filename: selectedFile?.name || 'preflight_issues' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'PreFlight_Issues.csv')
    }
  }, [preflightReport, token, selectedFile])

  const handlePopulationProfileExportPDF = useCallback(async () => {
    if (!auditResult?.population_profile || !token) return
    const result = await apiDownload('/export/population-profile-memo', token, {
      method: 'POST',
      body: { ...auditResult.population_profile, filename: selectedFile?.name || 'population_profile' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'PopProfile_Memo.pdf')
    }
  }, [auditResult?.population_profile, token, selectedFile])

  const handlePopulationProfileExportCSV = useCallback(async () => {
    if (!auditResult?.population_profile || !token) return
    const result = await apiDownload('/export/csv/population-profile', token, {
      method: 'POST',
      body: { ...auditResult.population_profile, filename: selectedFile?.name || 'population_profile' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'PopProfile.csv')
    }
  }, [auditResult?.population_profile, token, selectedFile])

  const handleExpenseCategoryExportPDF = useCallback(async () => {
    if (!auditResult?.expense_category_analytics || !token) return
    const result = await apiDownload('/export/expense-category-memo', token, {
      method: 'POST',
      body: { ...auditResult.expense_category_analytics, filename: selectedFile?.name || 'expense_category' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'ExpenseCategory_Memo.pdf')
    }
  }, [auditResult?.expense_category_analytics, token, selectedFile])

  const handleExpenseCategoryExportCSV = useCallback(async () => {
    if (!auditResult?.expense_category_analytics || !token) return
    const result = await apiDownload('/export/csv/expense-category-analytics', token, {
      method: 'POST',
      body: { ...auditResult.expense_category_analytics, filename: selectedFile?.name || 'expense_category' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'ExpenseCategory.csv')
    }
  }, [auditResult?.expense_category_analytics, token, selectedFile])

  const handleAccrualCompletenessExportPDF = useCallback(async () => {
    if (!auditResult?.accrual_completeness || !token) return
    const result = await apiDownload('/export/accrual-completeness-memo', token, {
      method: 'POST',
      body: { ...auditResult.accrual_completeness, filename: selectedFile?.name || 'accrual_completeness' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'AccrualCompleteness_Memo.pdf')
    }
  }, [auditResult?.accrual_completeness, token, selectedFile])

  const handleAccrualCompletenessExportCSV = useCallback(async () => {
    if (!auditResult?.accrual_completeness || !token) return
    const result = await apiDownload('/export/csv/accrual-completeness', token, {
      method: 'POST',
      body: { ...auditResult.accrual_completeness, filename: selectedFile?.name || 'accrual_completeness' },
    })
    if (result.ok && result.blob) {
      downloadBlob(result.blob, result.filename || 'AccrualCompleteness.csv')
    }
  }, [auditResult?.accrual_completeness, token, selectedFile])

  return {
    handlePreflightExportPDF,
    handlePreflightExportCSV,
    handlePopulationProfileExportPDF,
    handlePopulationProfileExportCSV,
    handleExpenseCategoryExportPDF,
    handleExpenseCategoryExportCSV,
    handleAccrualCompletenessExportPDF,
    handleAccrualCompletenessExportCSV,
  }
}
