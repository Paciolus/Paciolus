'use client'

/**
 * useTrialBalanceExports — PDF/CSV export handlers for TB diagnostics
 * Sprint 519 Phase 2: Extracted from useTrialBalanceAudit
 */

import { useCallback } from 'react'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useToast } from '@/contexts/ToastContext'
import type { AuditResult } from '@/types/diagnostic'
import type { PreFlightReport } from '@/types/preflight'
import { apiDownload } from '@/utils/apiClient'
import { deliverDownload } from '@/utils/deliverDownload'
import { withLinkedEngagement } from '@/utils/linkedEngagement'

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
  // Sprint 886 (OUT-18): memos resolve the client's reporting framework from it.
  const engagementId = useOptionalEngagementContext()?.engagementId ?? null
  // Sprint 893: a failed export says so (apiDownload resolves ok: false; it does not throw).
  const toast = useToast()

  const handlePreflightExportPDF = useCallback(async () => {
    if (!preflightReport || !token) return
    const result = await apiDownload('/export/preflight-memo', token, {
      method: 'POST',
      body: withLinkedEngagement({ ...preflightReport, filename: selectedFile?.name || 'preflight_report' }, engagementId),
    })
    deliverDownload(result, 'PreFlight_Memo.pdf', 'PDF memo', toast)
  }, [preflightReport, token, selectedFile, engagementId, toast])

  const handlePreflightExportCSV = useCallback(async () => {
    if (!preflightReport || !token) return
    const result = await apiDownload('/export/csv/preflight-issues', token, {
      method: 'POST',
      body: { issues: preflightReport.issues, filename: selectedFile?.name || 'preflight_issues' },
    })
    deliverDownload(result, 'PreFlight_Issues.csv', 'CSV export', toast)
  }, [preflightReport, token, selectedFile, toast])

  const handlePopulationProfileExportPDF = useCallback(async () => {
    if (!auditResult?.population_profile || !token) return
    const result = await apiDownload('/export/population-profile-memo', token, {
      method: 'POST',
      body: withLinkedEngagement({ ...auditResult.population_profile, filename: selectedFile?.name || 'population_profile' }, engagementId),
    })
    deliverDownload(result, 'PopProfile_Memo.pdf', 'PDF memo', toast)
  }, [auditResult?.population_profile, token, selectedFile, engagementId, toast])

  const handlePopulationProfileExportCSV = useCallback(async () => {
    if (!auditResult?.population_profile || !token) return
    const result = await apiDownload('/export/csv/population-profile', token, {
      method: 'POST',
      body: { ...auditResult.population_profile, filename: selectedFile?.name || 'population_profile' },
    })
    deliverDownload(result, 'PopProfile.csv', 'CSV export', toast)
  }, [auditResult?.population_profile, token, selectedFile, toast])

  const handleExpenseCategoryExportPDF = useCallback(async () => {
    if (!auditResult?.expense_category_analytics || !token) return
    const result = await apiDownload('/export/expense-category-memo', token, {
      method: 'POST',
      body: withLinkedEngagement({ ...auditResult.expense_category_analytics, filename: selectedFile?.name || 'expense_category' }, engagementId),
    })
    deliverDownload(result, 'ExpenseCategory_Memo.pdf', 'PDF memo', toast)
  }, [auditResult?.expense_category_analytics, token, selectedFile, engagementId, toast])

  const handleExpenseCategoryExportCSV = useCallback(async () => {
    if (!auditResult?.expense_category_analytics || !token) return
    const result = await apiDownload('/export/csv/expense-category-analytics', token, {
      method: 'POST',
      body: { ...auditResult.expense_category_analytics, filename: selectedFile?.name || 'expense_category' },
    })
    deliverDownload(result, 'ExpenseCategory.csv', 'CSV export', toast)
  }, [auditResult?.expense_category_analytics, token, selectedFile, toast])

  const handleAccrualCompletenessExportPDF = useCallback(async () => {
    if (!auditResult?.accrual_completeness || !token) return
    const result = await apiDownload('/export/accrual-completeness-memo', token, {
      method: 'POST',
      body: withLinkedEngagement({ ...auditResult.accrual_completeness, filename: selectedFile?.name || 'accrual_completeness' }, engagementId),
    })
    deliverDownload(result, 'AccrualCompleteness_Memo.pdf', 'PDF memo', toast)
  }, [auditResult?.accrual_completeness, token, selectedFile, engagementId, toast])

  const handleAccrualCompletenessExportCSV = useCallback(async () => {
    if (!auditResult?.accrual_completeness || !token) return
    const result = await apiDownload('/export/csv/accrual-completeness', token, {
      method: 'POST',
      body: { ...auditResult.accrual_completeness, filename: selectedFile?.name || 'accrual_completeness' },
    })
    deliverDownload(result, 'AccrualCompleteness.csv', 'CSV export', toast)
  }, [auditResult?.accrual_completeness, token, selectedFile, toast])

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
