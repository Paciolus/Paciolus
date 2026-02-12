'use client'

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { useMappings } from '@/contexts/MappingContext'
import { useAuth } from '@/contexts/AuthContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useSettings } from '@/hooks/useSettings'
import { useBenchmarks } from '@/hooks'
import { apiPost, apiFetch } from '@/utils'
import type { ColumnMapping, ColumnDetectionInfo } from '@/components/mapping'
import type { WorkbookInfo, ConsolidatedAuditResult, Analytics, AbnormalBalanceExtended, RiskSummary } from '@/types/mapping'
import type { DisplayMode } from '@/components/sensitivity'
import type { LeadSheetGrouping } from '@/types/leadSheet'

const API_URL = process.env.NEXT_PUBLIC_API_URL!

export interface AuditResult {
  status: string
  balanced: boolean
  total_debits: number
  total_credits: number
  difference: number
  row_count: number
  message: string
  abnormal_balances: AbnormalBalanceExtended[]
  has_risk_alerts: boolean
  materiality_threshold: number
  material_count: number
  immaterial_count: number
  classification_summary?: {
    high: number
    medium: number
    low: number
    unknown: number
  }
  column_detection?: ColumnDetectionInfo
  risk_summary?: RiskSummary
  is_consolidated?: boolean
  sheet_count?: number
  selected_sheets?: string[]
  sheet_results?: ConsolidatedAuditResult['sheet_results']
  analytics?: Analytics
  lead_sheet_grouping?: LeadSheetGrouping
  classification_quality?: {
    issues: Array<{
      account_number: string
      account_name: string
      issue_type: string
      description: string
      severity: string
      confidence: number
      category: string
      suggested_action: string
    }>
    quality_score: number
    issue_counts: Record<string, number>
    total_issues: number
  }
}

export function useTrialBalanceAudit() {
  const mappingContext = useMappings()
  const { user, isAuthenticated, token } = useAuth()
  const engagement = useOptionalEngagementContext()

  const { practiceSettings, isLoading: settingsLoading } = useSettings()
  const {
    availableIndustries,
    comparisonResults,
    isLoadingComparison,
    fetchIndustries,
    compareToBenchmarks,
    clear: clearBenchmarks,
  } = useBenchmarks()

  const isVerified = user?.is_verified !== false

  // Audit zone state
  const [auditStatus, setAuditStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null)
  const [auditError, setAuditError] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isRecalculating, setIsRecalculating] = useState(false)

  // Materiality threshold state
  const [materialityThreshold, setMaterialityThreshold] = useState(500)
  const [showImmaterial, setShowImmaterial] = useState(false)
  const [thresholdInitialized, setThresholdInitialized] = useState(false)
  const [displayMode, setDisplayMode] = useState<DisplayMode>('strict')

  // Progress indicator state
  const [scanningRows, setScanningRows] = useState(0)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Previous state refs for deep comparison
  const prevThresholdRef = useRef<number>(materialityThreshold)
  const prevColumnMappingRef = useRef<ColumnMapping | null>(null)
  const prevSelectedSheetsRef = useRef<string[] | null>(null)
  const prevInputHashRef = useRef<string>('')

  // Column mapping state
  const [showColumnMappingModal, setShowColumnMappingModal] = useState(false)
  const [pendingColumnDetection, setPendingColumnDetection] = useState<ColumnDetectionInfo | null>(null)
  const [userColumnMapping, setUserColumnMapping] = useState<ColumnMapping | null>(null)

  // Workbook inspection state
  const [showWorkbookInspector, setShowWorkbookInspector] = useState(false)
  const [pendingWorkbookInfo, setPendingWorkbookInfo] = useState<WorkbookInfo | null>(null)
  const [selectedSheets, setSelectedSheets] = useState<string[] | null>(null)

  // Benchmark state
  const [selectedIndustry, setSelectedIndustry] = useState<string>('')
  const industriesFetchedRef = useRef(false)

  // Prepopulate threshold from user practice settings
  useEffect(() => {
    if (practiceSettings && !thresholdInitialized && !settingsLoading) {
      const formula = practiceSettings.default_materiality
      if (formula) {
        if (formula.type === 'fixed' && formula.value > 0) {
          setMaterialityThreshold(formula.value)
        }
        if (practiceSettings.show_immaterial_by_default !== undefined) {
          setShowImmaterial(practiceSettings.show_immaterial_by_default)
          setDisplayMode(practiceSettings.show_immaterial_by_default ? 'lenient' : 'strict')
        }
      }
      setThresholdInitialized(true)
    }
  }, [practiceSettings, thresholdInitialized, settingsLoading])

  const handleDisplayModeChange = useCallback((mode: DisplayMode) => {
    setDisplayMode(mode)
    setShowImmaterial(mode === 'lenient')
  }, [])

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

  const computeAuditInputHash = useCallback((
    threshold: number,
    mapping: ColumnMapping | null,
    sheets: string[] | null
  ): string => {
    const inputState = {
      t: threshold,
      m: mapping ? JSON.stringify(mapping) : null,
      s: sheets ? sheets.sort().join('|') : null,
    }
    const str = JSON.stringify(inputState)
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash
    }
    return hash.toString(36)
  }, [])

  const startProgressIndicator = useCallback(() => {
    setScanningRows(0)
    let rows = 0
    const baseIncrement = 1000
    progressIntervalRef.current = setInterval(() => {
      const increment = Math.max(100, baseIncrement - Math.floor(rows / 5000) * 100)
      rows += increment + Math.floor(Math.random() * 500)
      setScanningRows(rows)
    }, 150)
  }, [])

  const stopProgressIndicator = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
  }, [])

  const runAudit = useCallback(async (
    file: File,
    threshold: number,
    isRecalc: boolean = false,
    columnMapping?: ColumnMapping | null,
    sheets?: string[] | null
  ) => {
    if (isRecalc) {
      setIsRecalculating(true)
    } else {
      setAuditStatus('loading')
      setAuditResult(null)
      setAuditError('')
      setShowImmaterial(false)
      setShowColumnMappingModal(false)
      setPendingColumnDetection(null)
      setShowWorkbookInspector(false)
      setPendingWorkbookInfo(null)
      startProgressIndicator()
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('materiality_threshold', threshold.toString())

    const overrides = mappingContext.getOverridesForApi()
    if (Object.keys(overrides).length > 0) {
      formData.append('account_type_overrides', JSON.stringify(overrides))
    }

    if (columnMapping) {
      formData.append('column_mapping', JSON.stringify(columnMapping))
    }

    if (sheets && sheets.length > 0) {
      formData.append('selected_sheets', JSON.stringify(sheets))
    }

    if (engagement?.activeEngagement?.id) {
      formData.append('engagement_id', engagement.activeEngagement.id.toString())
    }

    try {
      const response = await fetch(`${API_URL}/audit/trial-balance`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setAuditStatus('error')
        setAuditError('Please sign in to run diagnostics.')
        stopProgressIndicator()
        setIsRecalculating(false)
        return
      }
      if (response.status === 403) {
        const errData = await response.json().catch(() => ({}))
        const detail = errData.detail
        if (typeof detail === 'object' && detail?.code === 'EMAIL_NOT_VERIFIED') {
          setAuditStatus('error')
          setAuditError('Please verify your email address before running diagnostics. Check your inbox for the verification link.')
          stopProgressIndicator()
          setIsRecalculating(false)
          return
        }
        setAuditStatus('error')
        setAuditError('Access denied.')
        stopProgressIndicator()
        setIsRecalculating(false)
        return
      }

      const data = await response.json()

      if (response.ok && data.status === 'success') {
        if (data.column_detection?.requires_mapping && !columnMapping) {
          setPendingColumnDetection(data.column_detection)
          setShowColumnMappingModal(true)
          setAuditStatus('idle')
          stopProgressIndicator()
          return
        }

        setAuditStatus('success')
        setAuditResult(data)

        if (engagement?.activeEngagement) {
          engagement.refreshToolRuns()
          engagement.triggerLinkToast('TB Diagnostics')
        }

        if (data.abnormal_balances) {
          mappingContext.initializeFromAudit(data.abnormal_balances)
        }

        if (!isRecalc && isAuthenticated && token) {
          apiPost('/activity/log', token, {
            filename: file.name,
            record_count: data.row_count,
            total_debits: data.total_debits,
            total_credits: data.total_credits,
            materiality_threshold: threshold,
            was_balanced: data.balanced,
            anomaly_count: data.abnormal_balances?.length || 0,
            material_count: data.material_count || 0,
            immaterial_count: data.immaterial_count || 0,
            is_consolidated: data.is_consolidated || false,
            sheet_count: data.sheet_count || null,
          }).catch(() => {})
        }
      } else {
        setAuditStatus('error')
        setAuditError(data.message || data.detail || 'Failed to analyze file')
      }
    } catch (error) {
      setAuditStatus('error')
      setAuditError('Unable to connect to server. Please try again.')
    } finally {
      setIsRecalculating(false)
      stopProgressIndicator()
    }
  }, [startProgressIndicator, stopProgressIndicator, mappingContext, isAuthenticated, token])

  const handleFileUpload = useCallback(async (file: File) => {
    if (user && user.is_verified === false) {
      setAuditStatus('error')
      setAuditError('Please verify your email address before running diagnostics. Check your inbox for the verification link.')
      return
    }

    setSelectedFile(file)
    setUserColumnMapping(null)
    setSelectedSheets(null)

    const isExcel = file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')

    if (isExcel) {
      setAuditStatus('loading')
      startProgressIndicator()

      try {
        const formData = new FormData()
        formData.append('file', file)

        const { data: workbookInfo, ok: inspectOk } = await apiFetch<WorkbookInfo>(
          '/audit/inspect-workbook',
          token ?? null,
          { method: 'POST', body: formData },
        )

        if (inspectOk && workbookInfo?.requires_sheet_selection) {
          setPendingWorkbookInfo(workbookInfo)
          setShowWorkbookInspector(true)
          setAuditStatus('idle')
          stopProgressIndicator()
          return
        }

        stopProgressIndicator()
        await runAudit(file, materialityThreshold, false, null, null)
      } catch (error) {
        console.error('Workbook inspection failed:', error)
        stopProgressIndicator()
        await runAudit(file, materialityThreshold, false, null, null)
      }
    } else {
      await runAudit(file, materialityThreshold, false, null, null)
    }
  }, [materialityThreshold, runAudit, startProgressIndicator, stopProgressIndicator, user, token])

  const handleWorkbookInspectorConfirm = useCallback((sheets: string[]) => {
    setSelectedSheets(sheets)
    setShowWorkbookInspector(false)
    setPendingWorkbookInfo(null)
    if (selectedFile) {
      runAudit(selectedFile, materialityThreshold, false, userColumnMapping, sheets)
    }
  }, [selectedFile, materialityThreshold, userColumnMapping, runAudit])

  const handleWorkbookInspectorClose = useCallback(() => {
    setShowWorkbookInspector(false)
    setPendingWorkbookInfo(null)
    setAuditStatus('idle')
    setSelectedFile(null)
  }, [])

  const handleColumnMappingConfirm = useCallback((mapping: ColumnMapping) => {
    setUserColumnMapping(mapping)
    setShowColumnMappingModal(false)
    setPendingColumnDetection(null)
    if (selectedFile) {
      runAudit(selectedFile, materialityThreshold, false, mapping, selectedSheets)
    }
  }, [selectedFile, materialityThreshold, selectedSheets, runAudit])

  const handleColumnMappingClose = useCallback(() => {
    setShowColumnMappingModal(false)
    setPendingColumnDetection(null)
    setAuditStatus('idle')
    setSelectedFile(null)
  }, [])

  const { isDragging, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } = useFileUpload(handleFileUpload)

  const thresholdConfig = useMemo(() => ({
    value: materialityThreshold,
    columnMapping: userColumnMapping,
    selectedSheets: selectedSheets,
  }), [materialityThreshold, userColumnMapping, selectedSheets])

  // Debounced recalculation effect
  useEffect(() => {
    if (!selectedFile || auditStatus === 'loading') return

    const currentHash = computeAuditInputHash(materialityThreshold, userColumnMapping, selectedSheets)
    if (prevInputHashRef.current === currentHash) return

    const thresholdChanged = prevThresholdRef.current !== materialityThreshold
    const columnMappingChanged = JSON.stringify(prevColumnMappingRef.current) !== JSON.stringify(userColumnMapping)
    const sheetsChanged = JSON.stringify(prevSelectedSheetsRef.current) !== JSON.stringify(selectedSheets)

    if (!thresholdChanged && !columnMappingChanged && !sheetsChanged) {
      prevInputHashRef.current = currentHash
      return
    }

    prevThresholdRef.current = materialityThreshold
    prevColumnMappingRef.current = userColumnMapping
    prevSelectedSheetsRef.current = selectedSheets
    prevInputHashRef.current = currentHash

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    debounceTimerRef.current = setTimeout(() => {
      runAudit(selectedFile, materialityThreshold, true, userColumnMapping, selectedSheets)
    }, 300)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [materialityThreshold, selectedFile, auditStatus, runAudit, userColumnMapping, selectedSheets, computeAuditInputHash])

  // Cleanup progress interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [])

  const resetAudit = useCallback(() => {
    setAuditStatus('idle')
    setAuditResult(null)
    setAuditError('')
    setSelectedFile(null)
  }, [])

  const handleRerunAudit = useCallback(() => {
    if (selectedFile) {
      runAudit(selectedFile, materialityThreshold, true, userColumnMapping)
    }
  }, [selectedFile, materialityThreshold, userColumnMapping, runAudit])

  return {
    // Auth
    user, isAuthenticated, token, isVerified,
    // Audit state
    auditStatus, auditResult, auditError,
    selectedFile, isRecalculating, scanningRows,
    // Materiality
    materialityThreshold, setMaterialityThreshold,
    displayMode, handleDisplayModeChange,
    // Column mapping modal
    showColumnMappingModal, pendingColumnDetection,
    handleColumnMappingConfirm, handleColumnMappingClose,
    // Workbook inspector
    showWorkbookInspector, pendingWorkbookInfo,
    handleWorkbookInspectorConfirm, handleWorkbookInspectorClose,
    // Benchmarks
    selectedIndustry, availableIndustries, comparisonResults, isLoadingComparison, handleIndustryChange,
    // File upload
    isDragging, handleDrop, handleDragOver, handleDragLeave, handleFileSelect,
    // Actions
    resetAudit, handleRerunAudit,
  }
}
