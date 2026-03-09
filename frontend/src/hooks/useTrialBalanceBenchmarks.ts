'use client'

/**
 * useTrialBalanceBenchmarks — Industry benchmark sidecar
 * Sprint 519 Phase 2: Extracted from useTrialBalanceAudit
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useBenchmarks } from '@/hooks'
import type { AuditResult } from '@/types/diagnostic'
import type { Analytics } from '@/types/mapping'
import type { UploadStatus } from '@/types/shared'

interface UseTrialBalanceBenchmarksInput {
  auditStatus: UploadStatus
  auditResult: AuditResult | null
}

export interface UseTrialBalanceBenchmarksReturn {
  selectedIndustry: string
  availableIndustries: ReturnType<typeof useBenchmarks>['availableIndustries']
  comparisonResults: ReturnType<typeof useBenchmarks>['comparisonResults']
  isLoadingComparison: boolean
  handleIndustryChange: (industry: string) => Promise<void>
}

export function useTrialBalanceBenchmarks({
  auditStatus,
  auditResult,
}: UseTrialBalanceBenchmarksInput): UseTrialBalanceBenchmarksReturn {
  const {
    availableIndustries,
    comparisonResults,
    isLoadingComparison,
    fetchIndustries,
    compareToBenchmarks,
    clear: clearBenchmarks,
  } = useBenchmarks()

  const [selectedIndustry, setSelectedIndustry] = useState<string>('')
  const industriesFetchedRef = useRef(false)

  const extractRatiosForBenchmark = useCallback((analytics: Analytics | undefined): Record<string, number> => {
    if (!analytics?.ratios) return {}
    const ratioMap: Record<string, number> = {}
    Object.entries(analytics.ratios).forEach(([key, ratioData]) => {
      if (ratioData && ratioData.is_calculable && ratioData.value !== null) {
        ratioMap[key] = ratioData.value
      }
    })
    return ratioMap
  }, [])

  // Fetch available industries when audit succeeds
  useEffect(() => {
    if (auditStatus === 'success' && auditResult?.analytics && !industriesFetchedRef.current) {
      fetchIndustries()
      industriesFetchedRef.current = true
    }
    if (auditStatus === 'idle') {
      industriesFetchedRef.current = false
      setSelectedIndustry('')
      clearBenchmarks()
    }
  }, [auditStatus, auditResult?.analytics, fetchIndustries, clearBenchmarks])

  const handleIndustryChange = useCallback(async (industry: string) => {
    setSelectedIndustry(industry)
    if (industry && auditResult?.analytics) {
      const ratios = extractRatiosForBenchmark(auditResult.analytics)
      if (Object.keys(ratios).length > 0) {
        await compareToBenchmarks(ratios, industry)
      }
    }
  }, [auditResult?.analytics, extractRatiosForBenchmark, compareToBenchmarks])

  return {
    selectedIndustry,
    availableIndustries,
    comparisonResults,
    isLoadingComparison,
    handleIndustryChange,
  }
}
