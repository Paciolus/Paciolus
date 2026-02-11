'use client'

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { MappingProvider, useMappings } from '@/contexts/MappingContext'
import { useAuth } from '@/contexts/AuthContext'
import { AccountTypeDropdown, MappingIndicator, MappingToolbar, ColumnMappingModal } from '@/components/mapping'
import type { ColumnMapping, ColumnDetectionInfo } from '@/components/mapping'
import { AccountType, AbnormalBalanceExtended, ACCOUNT_TYPE_LABELS, RiskSummary, WorkbookInfo, ConsolidatedAuditResult, Analytics } from '@/types/mapping'
import { RiskDashboard } from '@/components/risk'
import { WorkbookInspector } from '@/components/workbook'
import { DownloadReportButton } from '@/components/export'
import { VerificationBanner } from '@/components/auth'
import { ToolNav } from '@/components/shared'
import { KeyMetricsSection } from '@/components/analytics'
import { ClassificationQualitySection } from '@/components/diagnostics/ClassificationQualitySection'
import { SensitivityToolbar, type DisplayMode } from '@/components/sensitivity'
import { FeaturePillars, ProcessTimeline, DemoZone } from '@/components/marketing'
import { apiPost, apiFetch } from '@/utils'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useFileUpload } from '@/hooks/useFileUpload'
import { WorkspaceHeader, QuickActionsBar, RecentHistoryMini } from '@/components/workspace'
import { MaterialityControl } from '@/components/diagnostic'
import { BenchmarkSection } from '@/components/benchmark'
import { LeadSheetSection } from '@/components/leadSheet'
import { FinancialStatementsPreview } from '@/components/financialStatements'
import { useSettings } from '@/hooks/useSettings'
import type { LeadSheetGrouping } from '@/types/leadSheet'
import { useBenchmarks, type BenchmarkComparisonResponse } from '@/hooks'

// Hard fail if API URL is not configured
const API_URL = process.env.NEXT_PUBLIC_API_URL
if (!API_URL) {
  throw new Error(
    '\n\n' +
    '='.repeat(60) + '\n' +
    'CONFIGURATION ERROR - Paciolus cannot start\n' +
    '='.repeat(60) + '\n\n' +
    'Required environment variable NEXT_PUBLIC_API_URL is not set.\n\n' +
    'Please create a .env.local file based on .env.example\n' +
    '='.repeat(60) + '\n'
  )
}

interface AuditResult {
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
  // Day 9.2: Column detection info
  column_detection?: ColumnDetectionInfo
  // Day 10: Risk summary for Risk Dashboard
  risk_summary?: RiskSummary
  // Day 11: Multi-sheet consolidation info
  is_consolidated?: boolean
  sheet_count?: number
  selected_sheets?: string[]
  sheet_results?: ConsolidatedAuditResult['sheet_results']
  // Sprint 19: Analytics data for ratio intelligence
  analytics?: Analytics
  // Sprint 50: Lead sheet grouping for workpaper organization
  lead_sheet_grouping?: LeadSheetGrouping
  // Sprint 95: Classification quality from structural COA checks
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

function HomeContent() {
  const [email, setEmail] = useState('')
  const mappingContext = useMappings()
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuth()
  // Sprint 103: Engagement integration — auto-link tool runs to workspace
  const engagement = useOptionalEngagementContext()
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  // Sprint 21: Fetch user practice settings for dynamic materiality
  const { practiceSettings, isLoading: settingsLoading } = useSettings()

  // Sprint 47: Benchmark comparison integration
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

  // Sprint 70: Verification gate for diagnostic zone
  const isVerified = user?.is_verified !== false

  // Audit zone state
  const [auditStatus, setAuditStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null)
  const [auditError, setAuditError] = useState('')

  // Store selected file for reactive recalculation
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isRecalculating, setIsRecalculating] = useState(false)

  // Materiality threshold state (default $500, overridden by user settings)
  const [materialityThreshold, setMaterialityThreshold] = useState(500)
  const [showImmaterial, setShowImmaterial] = useState(false)
  const [thresholdInitialized, setThresholdInitialized] = useState(false)

  // Sprint 22: Display mode for SensitivityToolbar (strict = material only, lenient = all)
  const [displayMode, setDisplayMode] = useState<DisplayMode>('strict')

  // Progress indicator state for streaming processing
  const [scanningRows, setScanningRows] = useState(0)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Ref for debounce timer
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Sprint 15 Fix: Track previous threshold to prevent unnecessary re-audits
  // Sprint 20 Enhancement: Deep-hash comparison for UI stability
  const prevThresholdRef = useRef<number>(materialityThreshold)
  const prevColumnMappingRef = useRef<ColumnMapping | null>(null)
  const prevSelectedSheetsRef = useRef<string[] | null>(null)
  const prevInputHashRef = useRef<string>('')

  // Sprint 20: Deep-Hash Comparison function for audit input state
  // Generates a stable hash of all audit parameters to detect real changes
  const computeAuditInputHash = useCallback((
    threshold: number,
    mapping: ColumnMapping | null,
    sheets: string[] | null
  ): string => {
    // Create a deterministic string representation of all audit inputs
    const inputState = {
      t: threshold,
      m: mapping ? JSON.stringify(mapping) : null,
      s: sheets ? sheets.sort().join('|') : null,
    }
    // Simple hash function for browser compatibility
    const str = JSON.stringify(inputState)
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash // Convert to 32bit integer
    }
    return hash.toString(36)
  }, [])

  // Day 9.2: Column mapping state (Zero-Storage: React state only)
  const [showColumnMappingModal, setShowColumnMappingModal] = useState(false)
  const [pendingColumnDetection, setPendingColumnDetection] = useState<ColumnDetectionInfo | null>(null)
  const [userColumnMapping, setUserColumnMapping] = useState<ColumnMapping | null>(null)

  // Day 11: Workbook inspection state (Zero-Storage: React state only)
  const [showWorkbookInspector, setShowWorkbookInspector] = useState(false)
  const [pendingWorkbookInfo, setPendingWorkbookInfo] = useState<WorkbookInfo | null>(null)
  const [selectedSheets, setSelectedSheets] = useState<string[] | null>(null)

  // Sprint 21: Prepopulate threshold from user practice settings
  useEffect(() => {
    if (practiceSettings && !thresholdInitialized && !settingsLoading) {
      const formula = practiceSettings.default_materiality
      if (formula) {
        // For fixed type, use the value directly
        // For percentage types, the actual calculation happens at audit time
        // We just prepopulate with the formula value as a starting point
        if (formula.type === 'fixed' && formula.value > 0) {
          setMaterialityThreshold(formula.value)
        }
        // Also apply show_immaterial_by_default preference
        if (practiceSettings.show_immaterial_by_default !== undefined) {
          setShowImmaterial(practiceSettings.show_immaterial_by_default)
          // Sprint 22: Sync display mode with showImmaterial preference
          setDisplayMode(practiceSettings.show_immaterial_by_default ? 'lenient' : 'strict')
        }
      }
      setThresholdInitialized(true)
    }
  }, [practiceSettings, thresholdInitialized, settingsLoading])

  // Sprint 22: Handle display mode change from SensitivityToolbar
  const handleDisplayModeChange = useCallback((mode: DisplayMode) => {
    setDisplayMode(mode)
    setShowImmaterial(mode === 'lenient')
  }, [])

  // Sprint 47: Extract calculable ratios from analytics for benchmark comparison
  const extractRatiosForBenchmark = useCallback((analytics: Analytics | undefined): Record<string, number> => {
    if (!analytics?.ratios) return {}

    const ratioMap: Record<string, number> = {}

    // Extract all calculable ratios with non-null values
    Object.entries(analytics.ratios).forEach(([key, ratioData]) => {
      if (ratioData && ratioData.is_calculable && ratioData.value !== null) {
        ratioMap[key] = ratioData.value
      }
    })

    return ratioMap
  }, [])

  // Sprint 47: Fetch available industries when audit succeeds
  useEffect(() => {
    if (auditStatus === 'success' && auditResult?.analytics && !industriesFetchedRef.current) {
      fetchIndustries()
      industriesFetchedRef.current = true
    }
    // Reset when audit resets
    if (auditStatus === 'idle') {
      industriesFetchedRef.current = false
      setSelectedIndustry('')
      clearBenchmarks()
    }
  }, [auditStatus, auditResult?.analytics, fetchIndustries, clearBenchmarks])

  // Sprint 47: Trigger benchmark comparison when industry is selected
  const handleIndustryChange = useCallback(async (industry: string) => {
    setSelectedIndustry(industry)
    if (industry && auditResult?.analytics) {
      const ratios = extractRatiosForBenchmark(auditResult.analytics)
      if (Object.keys(ratios).length > 0) {
        await compareToBenchmarks(ratios, industry)
      }
    }
  }, [auditResult?.analytics, extractRatiosForBenchmark, compareToBenchmarks])

  // Start simulated progress indicator
  const startProgressIndicator = useCallback(() => {
    setScanningRows(0)
    let rows = 0
    const baseIncrement = 1000 // Start with larger increments

    progressIntervalRef.current = setInterval(() => {
      // Slow down as we "progress" to simulate realistic streaming
      const increment = Math.max(100, baseIncrement - Math.floor(rows / 5000) * 100)
      rows += increment + Math.floor(Math.random() * 500)
      setScanningRows(rows)
    }, 150)
  }, [])

  // Stop progress indicator
  const stopProgressIndicator = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
  }, [])

  // Core audit function - can be called for initial upload or recalculation
  // Day 9.2: Now accepts optional columnMapping for user override
  // Day 11: Now accepts optional selectedSheets for multi-sheet consolidation
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

    // Add account type overrides if any (Day 9: Manual Mapping)
    const overrides = mappingContext.getOverridesForApi()
    if (Object.keys(overrides).length > 0) {
      formData.append('account_type_overrides', JSON.stringify(overrides))
    }

    // Add column mapping if provided (Day 9.2: User override)
    if (columnMapping) {
      formData.append('column_mapping', JSON.stringify(columnMapping))
    }

    // Day 11: Add selected sheets for multi-sheet consolidation
    if (sheets && sheets.length > 0) {
      formData.append('selected_sheets', JSON.stringify(sheets))
    }

    // Sprint 103: Link to engagement workspace if active
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

      // Sprint 59: Handle auth/verification errors before parsing JSON
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
        // Day 9.2: Check if column mapping is required
        if (data.column_detection?.requires_mapping && !columnMapping) {
          // Show modal for user to select columns
          setPendingColumnDetection(data.column_detection)
          setShowColumnMappingModal(true)
          setAuditStatus('idle') // Reset to idle since we need user input
          stopProgressIndicator()
          return
        }

        setAuditStatus('success')
        setAuditResult(data)

        // Sprint 103: Refresh tool runs + show toast when linked to workspace
        if (engagement?.activeEngagement) {
          engagement.refreshToolRuns()
          engagement.triggerLinkToast('TB Diagnostics')
        }

        // Initialize mapping context with detected types
        if (data.abnormal_balances) {
          mappingContext.initializeFromAudit(data.abnormal_balances)
        }

        // Day 14: Log activity for authenticated users (only on initial audit, not recalc)
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
          }).catch(() => {
            // Don't fail the audit if logging fails
          })
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

  // Handle initial file upload
  // Day 11: Now inspects Excel files for multi-sheet support
  const handleFileUpload = useCallback(async (file: File) => {
    // Sprint 59: Pre-check verification status before network call
    if (user && user.is_verified === false) {
      setAuditStatus('error')
      setAuditError('Please verify your email address before running diagnostics. Check your inbox for the verification link.')
      return
    }

    setSelectedFile(file)
    // Clear any previous state for new files
    setUserColumnMapping(null)
    setSelectedSheets(null)

    // Check if this is an Excel file that might have multiple sheets
    const isExcel = file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')

    if (isExcel) {
      // First, inspect the workbook for sheet information
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
          // Multi-sheet file - show inspector modal
          setPendingWorkbookInfo(workbookInfo)
          setShowWorkbookInspector(true)
          setAuditStatus('idle')
          stopProgressIndicator()
          return
        }

        // Single sheet or inspection failed - proceed with normal audit
        stopProgressIndicator()
        await runAudit(file, materialityThreshold, false, null, null)

      } catch (error) {
        console.error('Workbook inspection failed:', error)
        stopProgressIndicator()
        // Fall back to normal audit
        await runAudit(file, materialityThreshold, false, null, null)
      }
    } else {
      // CSV file - proceed directly with audit
      await runAudit(file, materialityThreshold, false, null, null)
    }
  }, [materialityThreshold, runAudit, startProgressIndicator, stopProgressIndicator, user, token])

  // Day 11: Handle workbook inspector confirmation
  const handleWorkbookInspectorConfirm = useCallback((sheets: string[]) => {
    setSelectedSheets(sheets)
    setShowWorkbookInspector(false)
    setPendingWorkbookInfo(null)

    // Run audit with selected sheets
    if (selectedFile) {
      runAudit(selectedFile, materialityThreshold, false, userColumnMapping, sheets)
    }
  }, [selectedFile, materialityThreshold, userColumnMapping, runAudit])

  // Day 11: Handle workbook inspector close (cancel)
  const handleWorkbookInspectorClose = useCallback(() => {
    setShowWorkbookInspector(false)
    setPendingWorkbookInfo(null)
    setAuditStatus('idle')
    setSelectedFile(null)
  }, [])

  // Day 9.2: Handle column mapping confirmation from modal
  const handleColumnMappingConfirm = useCallback((mapping: ColumnMapping) => {
    setUserColumnMapping(mapping)
    setShowColumnMappingModal(false)
    setPendingColumnDetection(null)

    // Re-run audit with user-provided column mapping
    if (selectedFile) {
      runAudit(selectedFile, materialityThreshold, false, mapping, selectedSheets)
    }
  }, [selectedFile, materialityThreshold, selectedSheets, runAudit])

  // Day 9.2: Handle column mapping modal close (cancel)
  const handleColumnMappingClose = useCallback(() => {
    setShowColumnMappingModal(false)
    setPendingColumnDetection(null)
    // Reset to idle state
    setAuditStatus('idle')
    setSelectedFile(null)
  }, [])

  const { isDragging, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } = useFileUpload(handleFileUpload)

  // Sprint 15 Fix: Memoize threshold object to prevent reference changes
  const thresholdConfig = useMemo(() => ({
    value: materialityThreshold,
    columnMapping: userColumnMapping,
    selectedSheets: selectedSheets,
  }), [materialityThreshold, userColumnMapping, selectedSheets])

  // Debounced effect: Re-run audit when materiality threshold changes
  // Only triggers if a file is already loaded (selectedFile exists)
  // Day 9.2: Now preserves user column mapping on recalculation
  // Day 11: Now preserves selected sheets on recalculation
  // Sprint 15 Fix: Deep comparison to prevent unnecessary re-audits
  // Sprint 20 Enhancement: Hash-based comparison for UI stability
  useEffect(() => {
    // Skip if no file is loaded or if we're in initial loading state
    if (!selectedFile || auditStatus === 'loading') {
      return
    }

    // Sprint 20: Compute hash of current audit input state
    const currentHash = computeAuditInputHash(materialityThreshold, userColumnMapping, selectedSheets)

    // Skip if the input hash hasn't changed (prevents referential loop and unnecessary re-audits)
    // This is the "state guard" that compares previous hash with current
    if (prevInputHashRef.current === currentHash) {
      return
    }

    // Also check individual values for explicit tracking (Sprint 15 compatibility)
    const thresholdChanged = prevThresholdRef.current !== materialityThreshold
    const columnMappingChanged = JSON.stringify(prevColumnMappingRef.current) !== JSON.stringify(userColumnMapping)
    const sheetsChanged = JSON.stringify(prevSelectedSheetsRef.current) !== JSON.stringify(selectedSheets)

    // Double-check: Skip if nothing actually changed (belt-and-suspenders approach)
    if (!thresholdChanged && !columnMappingChanged && !sheetsChanged) {
      // Update hash ref anyway to stay in sync
      prevInputHashRef.current = currentHash
      return
    }

    // Update all refs with current values
    prevThresholdRef.current = materialityThreshold
    prevColumnMappingRef.current = userColumnMapping
    prevSelectedSheetsRef.current = selectedSheets
    prevInputHashRef.current = currentHash

    // Clear any existing debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Set new debounce timer (300ms delay)
    // During this delay, the Tier 1 Skeleton Loader will be visible if isRecalculating is true
    debounceTimerRef.current = setTimeout(() => {
      runAudit(selectedFile, materialityThreshold, true, userColumnMapping, selectedSheets)
    }, 300)

    // Cleanup on unmount or when dependencies change
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')

    try {
      const response = await fetch(`${API_URL}/waitlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setMessage(data.message)
        setEmail('')
      } else {
        setStatus('error')
        setMessage(data.detail || 'Something went wrong. Please try again.')
      }
    } catch (error) {
      setStatus('error')
      setMessage('Unable to connect. Please try again later.')
    }
  }

  return (
    <main className="min-h-screen bg-surface-page">
      <ToolNav currentTool="tb-diagnostics" showBrandText />

      {/* Conditional Rendering: Guest vs Authenticated Views */}
      {!isAuthenticated ? (
        // GUEST VIEW: Marketing Content
        <>
          {/* Hero Section with Staggered Animations */}
          <section className="pt-32 pb-20 px-6">
            <motion.div
              className="max-w-4xl mx-auto text-center"
              initial="hidden"
              animate="visible"
              variants={{
                hidden: { opacity: 0 },
                visible: {
                  opacity: 1,
                  transition: { staggerChildren: 0.15, delayChildren: 0.1 }
                }
              }}
            >
              {/* Badge */}
              <motion.div
                className="inline-flex items-center gap-2 bg-sage-50 border border-sage-200 rounded-full px-4 py-1.5 mb-8"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
                }}
              >
                <span className="w-2 h-2 bg-sage-500 rounded-full animate-pulse"></span>
                <span className="text-sage-700 text-sm font-sans font-medium tracking-wide">Zero-Storage Processing</span>
              </motion.div>

              {/* Main Headline - Enhanced Typography */}
              <motion.h1
                className="text-5xl md:text-6xl lg:text-8xl font-serif font-bold text-content-primary mb-6 leading-[0.95] tracking-tight"
                variants={{
                  hidden: { opacity: 0, y: 30 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' as const } }
                }}
              >
                Surgical Precision
                <span className="block text-sage-600 mt-2">for Trial Balance Diagnostics</span>
              </motion.h1>

              {/* Sub-headline */}
              <motion.p
                className="text-xl md:text-2xl text-content-secondary font-sans mb-10 max-w-3xl mx-auto leading-relaxed"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
                }}
              >
                Financial Professionals: Eliminate sign errors and misclassifications with automated
                <span className="text-content-primary font-semibold"> Close Health Reports</span>.
              </motion.p>

              {/* 3-Step Workflow with Staggered Entrance */}
              <motion.div
                className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-8 mb-12"
                variants={{
                  hidden: { opacity: 0 },
                  visible: {
                    opacity: 1,
                    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
                  }
                }}
              >
                {[
                  { step: '1', label: 'Upload' },
                  { step: '2', label: 'Map' },
                  { step: '3', label: 'Export' }
                ].map((item, index) => (
                  <motion.div
                    key={item.step}
                    className="flex items-center gap-3"
                    variants={{
                      hidden: { opacity: 0, scale: 0.8 },
                      visible: { opacity: 1, scale: 1, transition: { duration: 0.4 } }
                    }}
                  >
                    {index > 0 && (
                      <svg className="w-6 h-6 text-content-tertiary hidden md:block mr-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                    <div className="w-12 h-12 rounded-full bg-sage-50 border border-sage-200 flex items-center justify-center">
                      <span className="text-sage-600 font-bold font-mono text-lg">{item.step}</span>
                    </div>
                    <span className="text-content-primary font-sans font-medium text-lg">{item.label}</span>
                  </motion.div>
                ))}
              </motion.div>

              {/* Waitlist Form */}
              <motion.form
                onSubmit={handleSubmit}
                className="max-w-md mx-auto"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
                }}
              >
                <div className="flex flex-col sm:flex-row gap-3">
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your work email"
                    required
                    className="input flex-1"
                  />
                  <button
                    type="submit"
                    disabled={status === 'loading'}
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-sage-500/30"
                  >
                    {status === 'loading' ? 'Joining...' : 'Join Waitlist'}
                  </button>
                </div>

                {/* Status Message */}
                {status === 'success' && (
                  <p className="mt-4 text-sage-600 font-sans font-medium">{message}</p>
                )}
                {status === 'error' && (
                  <p className="mt-4 text-clay-600 font-sans font-medium" role="alert">{message}</p>
                )}
              </motion.form>

              <motion.p
                className="mt-6 text-content-tertiary text-sm font-sans"
                variants={{
                  hidden: { opacity: 0 },
                  visible: { opacity: 1, transition: { duration: 0.5, delay: 0.2 } }
                }}
              >
                Your data never leaves your browser&apos;s memory. Zero storage, zero risk.
              </motion.p>
            </motion.div>
          </section>

          {/* Sprint 23: Feature Pillars - Three value propositions */}
          <FeaturePillars />

          {/* Sprint 23: Process Timeline - Visual transformation flow */}
          <ProcessTimeline />

          {/* Sprint 60: Interactive Demo Zone (replaces Sprint 59 sign-in CTA) */}
          <DemoZone />

          {/* CTA Section */}
          <section className="py-20 px-6">
            <div className="max-w-3xl mx-auto text-center bg-sage-50 border border-sage-200 rounded-3xl p-12">
              <h2 className="text-3xl font-serif font-bold text-content-primary mb-4">
                Ready to streamline your close process?
              </h2>
              <p className="text-content-secondary font-sans mb-8">
                Join the waitlist and be the first to know when we launch.
              </p>
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault()
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
                className="btn-primary inline-block"
              >
                Get Early Access
              </a>
            </div>
          </section>

          {/* Footer with Maker's Mark */}
          <footer className="py-12 px-6 border-t border-theme relative overflow-hidden">
            {/* Subtle decorative background */}
            <div className="absolute inset-0 opacity-[0.02]">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[20rem] font-serif text-content-primary select-none pointer-events-none">
                P
              </div>
            </div>

            <div className="max-w-6xl mx-auto relative">
              {/* Main footer content */}
              <div className="flex flex-col md:flex-row justify-between items-center gap-6 mb-8">
                <div className="text-content-tertiary text-sm font-sans">
                  © 2025 Paciolus. Built for Financial Professionals.
                </div>
                <div className="text-content-tertiary text-sm font-sans">
                  Zero-Storage Architecture. Your data stays yours.
                </div>
              </div>

              {/* Maker's Mark - Pacioli tribute */}
              <div className="text-center pt-6 border-t border-theme">
                <p className="makers-mark mb-2">
                  In the tradition of Luca Pacioli
                </p>
                <p className="text-content-tertiary text-xs font-mono tracking-wider">
                  Assets = Liabilities + Equity
                </p>
              </div>
            </div>
          </footer>

        </>
      ) : (
        // AUTHENTICATED VIEW: Workspace
        <>
          {/* Email Verification Banner (Sprint 58) */}
          <VerificationBanner />

          {/* Workspace Header with Dashboard Stats */}
          <WorkspaceHeader user={user!} token={token || undefined} />

          {/* Quick Actions Bar */}
          <QuickActionsBar />

          {/* Sprint 70: Verification gate — unverified users cannot access diagnostic zone */}
          {!isVerified ? (
            <section className="py-16 px-6">
 <div className="max-w-lg mx-auto theme-card rounded-2xl p-10 text-center">
                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-clay-50 border border-clay-200 flex items-center justify-center">
                  <svg className="w-8 h-8 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-serif font-bold text-content-primary mb-3">Verify Your Email</h2>
                <p className="text-content-secondary font-sans mb-2">
                  Trial Balance Diagnostics requires a verified account.
                </p>
                <p className="text-content-tertiary font-sans text-sm">
                  Check your inbox for a verification link, or use the banner above to resend.
                </p>
              </div>
            </section>
          ) : (
          <>
          {/* Diagnostic Zone (reused from guest view but in workspace context) */}
          <section className="py-16 px-6 bg-surface-card-secondary">
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 bg-sage-50 border border-sage-200 rounded-full px-4 py-1.5 mb-4">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="text-sage-700 text-sm font-sans font-medium">Zero-Storage Processing</span>
                </div>
                <h2 className="text-3xl font-serif font-bold text-content-primary mb-2">Diagnostic Intelligence Zone</h2>
                <p className="text-content-secondary font-sans">Upload your trial balance for instant analysis. Your data never leaves your browser's memory.</p>
              </div>

              {/* Materiality Threshold Control - Sprint 25: Extracted component */}
              <MaterialityControl
                idPrefix="workspace"
                value={materialityThreshold}
                onChange={setMaterialityThreshold}
                showLiveIndicator={!!selectedFile && auditStatus === 'success'}
                filename={selectedFile?.name}
              />

              {/* Drop Zone - Same as guest view */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`drop-zone ${auditStatus === 'idle' ? 'cursor-pointer' : ''} ${isDragging ? 'dragging' : ''}`}
              >
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileSelect}
                  className={`absolute inset-0 w-full h-full opacity-0 ${auditStatus === 'idle' ? 'cursor-pointer' : 'pointer-events-none'}`}
                  tabIndex={auditStatus === 'idle' ? 0 : -1}
                />

                {auditStatus === 'idle' && (
                  <>
                    <svg className="w-12 h-12 text-content-tertiary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-content-secondary text-lg font-sans mb-2">Drag and drop your trial balance</p>
                    <p className="text-content-tertiary text-sm font-sans">or click to browse. Supports CSV and Excel files.</p>
                  </>
                )}

                {auditStatus === 'loading' && (
                  <div className="flex flex-col items-center" aria-live="polite">
                    <div className="w-12 h-12 border-4 border-sage-200 border-t-sage-500 rounded-full animate-spin mb-4"></div>
                    <p className="text-content-secondary font-sans mb-2">Streaming analysis in progress...</p>
                    <div className="w-full max-w-xs">
                      <div className="h-2 bg-oatmeal-200 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-sage-500 rounded-full animate-pulse" style={{ width: '100%' }}></div>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm font-sans">
                        <svg className="w-4 h-4 text-sage-600 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <span className="text-sage-700 font-mono">
                          Scanning rows: <span className="text-content-primary">{scanningRows.toLocaleString()}</span>...
                        </span>
                      </div>
                    </div>
                    <p className="text-content-tertiary text-xs font-sans mt-3">Processing in memory-efficient chunks</p>
                  </div>
                )}

                {auditStatus === 'success' && auditResult && (
                  <div className="space-y-4 transition-opacity">
                    {isRecalculating && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-center gap-2 bg-sage-50 border border-sage-200 rounded-lg px-4 py-2">
                          <div className="w-4 h-4 border-2 border-sage-200 border-t-sage-500 rounded-full animate-spin"></div>
                          <span className="text-sage-700 text-sm font-sans font-medium">Recalculating with new threshold...</span>
                        </div>
                        <div className="flex flex-col items-center">
                          <div className="w-16 h-16 rounded-full bg-oatmeal-200 animate-pulse relative overflow-hidden">
                            <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
                          </div>
                          <div className="w-24 h-6 mt-3 rounded bg-oatmeal-200 animate-pulse relative overflow-hidden">
                            <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
                          </div>
                        </div>
                        <div className="bg-surface-card border border-theme rounded-xl p-4 max-w-sm mx-auto">
                          <div className="space-y-3">
                            {[1, 2, 3, 4].map((i) => (
                              <div key={i} className="flex justify-between">
                                <div className="w-24 h-4 rounded bg-oatmeal-200 animate-pulse relative overflow-hidden">
                                  <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
                                </div>
                                <div className="w-20 h-4 rounded bg-oatmeal-200 animate-pulse relative overflow-hidden">
                                  <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-oatmeal-100 to-transparent" />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    <div className={isRecalculating ? 'hidden' : ''}>
                      {auditResult.balanced ? (
                        <>
                          <div className="w-16 h-16 bg-sage-50 rounded-full flex items-center justify-center mx-auto">
                            <svg className="w-10 h-10 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                          <p className="text-sage-600 text-xl font-serif font-semibold">Balanced</p>
                        </>
                      ) : (
                        <>
                          <div className="w-16 h-16 bg-clay-50 rounded-full flex items-center justify-center mx-auto">
                            <svg className="w-10 h-10 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          </div>
                          <p className="text-clay-600 text-xl font-serif font-semibold">Out of Balance</p>
                        </>
                      )}

 <div className="theme-card p-4 text-left max-w-sm mx-auto">
                        <div className="grid grid-cols-2 gap-2 text-sm font-sans">
                          <span className="text-content-secondary">Total Debits:</span>
                          <span className="text-content-primary text-right font-mono">${auditResult.total_debits.toLocaleString()}</span>
                          <span className="text-content-secondary">Total Credits:</span>
                          <span className="text-content-primary text-right font-mono">${auditResult.total_credits.toLocaleString()}</span>
                          <span className="text-content-secondary">Difference:</span>
                          <span className={`text-right font-mono ${auditResult.difference === 0 ? 'text-sage-600' : 'text-clay-600'}`}>
                            ${auditResult.difference.toLocaleString()}
                          </span>
                          <span className="text-content-secondary">Rows Analyzed:</span>
                          <span className="text-content-primary text-right font-mono">{auditResult.row_count}</span>
                        </div>
                      </div>

                      {(auditResult.material_count > 0 || auditResult.immaterial_count > 0) && (
                        <div className="max-w-md mx-auto mt-4">
                          <MappingToolbar
                            disabled={isRecalculating}
                            onRerunAudit={() => selectedFile && runAudit(selectedFile, materialityThreshold, true, userColumnMapping)}
                          />
                        </div>
                      )}

                      <div className="mt-6 max-w-2xl mx-auto">
                        <SensitivityToolbar
                          threshold={materialityThreshold}
                          displayMode={displayMode}
                          onThresholdChange={setMaterialityThreshold}
                          onDisplayModeChange={handleDisplayModeChange}
                          disabled={isRecalculating}
                        />
                      </div>

                      {(auditResult.material_count > 0 || auditResult.immaterial_count > 0) && (
                        <div className="mt-4">
                          <RiskDashboard
                            anomalies={auditResult.abnormal_balances}
                            riskSummary={auditResult.risk_summary}
                            materialityThreshold={auditResult.materiality_threshold}
                            disabled={isRecalculating}
                            getMappingForAccount={(accountName) => {
                              const mapping = mappingContext.mappings.get(accountName)
                              const anomaly = auditResult.abnormal_balances.find(a => a.account === accountName)
                              return {
                                currentType: mapping?.overrideType || (anomaly?.category as AccountType) || 'unknown',
                                isManual: mapping?.isManual || false,
                              }
                            }}
                            onTypeChange={(accountName, type, detectedType) => {
                              mappingContext.setAccountType(accountName, type, detectedType)
                            }}
                          />
                        </div>
                      )}

                      {/* Sprint 95: Classification Quality Section */}
                      {auditResult.classification_quality && (
                        <div className="mt-4">
                          <ClassificationQualitySection data={auditResult.classification_quality} />
                        </div>
                      )}

                      {auditResult.analytics && (
                        <div className="mt-6">
                          <KeyMetricsSection
                            analytics={auditResult.analytics}
                            disabled={isRecalculating}
                          />
                        </div>
                      )}

                      {/* Sprint 47: Industry Benchmark Comparison */}
                      {auditResult.analytics && availableIndustries.length > 0 && (
 <div className="mt-6 p-4 theme-card">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                            <div>
                              <h4 className="font-serif text-sm font-medium text-content-primary mb-1">
                                Industry Benchmark Comparison
                              </h4>
                              <p className="text-xs text-content-tertiary">
                                Compare your ratios against industry benchmarks
                              </p>
                            </div>
                            <select
                              value={selectedIndustry}
                              onChange={(e) => handleIndustryChange(e.target.value)}
                              disabled={isRecalculating || isLoadingComparison}
                              className="
                                px-3 py-2 rounded-lg text-sm font-sans
                                bg-surface-input border border-theme text-content-primary
                                focus:outline-none focus:ring-2 focus:ring-sage-500/50 focus:border-sage-500
                                disabled:opacity-50 disabled:cursor-not-allowed
                              "
                            >
                              <option value="">Select an industry...</option>
                              {availableIndustries.map((industry) => (
                                <option key={industry} value={industry}>
                                  {industry.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                                </option>
                              ))}
                            </select>
                          </div>

                          {selectedIndustry && (
                            <BenchmarkSection
                              data={comparisonResults}
                              isLoading={isLoadingComparison}
                              industryDisplay={selectedIndustry.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                              disabled={isRecalculating}
                            />
                          )}
                        </div>
                      )}

                      {/* Sprint 50: Lead Sheet Grouping */}
                      {auditResult.lead_sheet_grouping && (
                        <LeadSheetSection
                          data={auditResult.lead_sheet_grouping}
                          disabled={isRecalculating}
                        />
                      )}

                      {/* Sprint 72: Financial Statements Preview */}
                      {auditResult.lead_sheet_grouping && (
                        <FinancialStatementsPreview
                          leadSheetGrouping={auditResult.lead_sheet_grouping}
                          filename={selectedFile?.name || 'financial_statements'}
                          token={token}
                          disabled={isRecalculating}
                        />
                      )}

                      {/* Disclaimer */}
                      <div className="bg-surface-card-secondary border border-theme rounded-xl p-4 mt-8">
                        <p className="font-sans text-xs text-content-tertiary leading-relaxed">
                          <span className="text-content-secondary font-medium">Disclaimer:</span> This automated trial balance
                          diagnostic tool provides analytical procedures to assist professional auditors. Results should be
                          interpreted in the context of the specific engagement and are not a substitute for professional
                          judgment or sufficient audit evidence per ISA 500.
                        </p>
                      </div>

                      <div className="mt-6 pt-4 border-t border-theme">
                        <DownloadReportButton
                          auditResult={auditResult}
                          filename={selectedFile?.name || 'diagnostic'}
                          disabled={isRecalculating}
                          token={token}
                        />
                      </div>

                      <button
                        onClick={() => {
                          setAuditStatus('idle')
                          setAuditResult(null)
                          setSelectedFile(null)
                        }}
                        className="text-sage-600 hover:text-sage-700 text-sm font-sans font-medium mt-2"
                        disabled={isRecalculating}
                      >
                        Upload another file
                      </button>
                    </div>
                  </div>
                )}

                {auditStatus === 'error' && (
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-clay-50 rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                    <p className="text-clay-600 font-sans font-medium">{auditError}</p>
                    <button
                      onClick={() => {
                        setAuditStatus('idle')
                        setAuditError('')
                        setSelectedFile(null)
                      }}
                      className="text-sage-600 hover:text-sage-700 text-sm font-sans font-medium"
                    >
                      Try again
                    </button>
                  </div>
                )}
              </div>

              <p className="text-center text-content-tertiary text-xs font-sans mt-4">
                Your file is processed entirely in-memory and is never saved to any disk or server.
              </p>
            </div>
          </section>

          {/* Recent History Widget */}
          <RecentHistoryMini token={token || undefined} />

          {/* Day 9.2: Column Mapping Modal */}
          {pendingColumnDetection && (
            <ColumnMappingModal
              isOpen={showColumnMappingModal}
              onClose={handleColumnMappingClose}
              onConfirm={handleColumnMappingConfirm}
              columnDetection={pendingColumnDetection}
              filename={selectedFile?.name || 'uploaded file'}
            />
          )}

          {/* Day 11: Workbook Inspector Modal */}
          {pendingWorkbookInfo && (
            <WorkbookInspector
              isOpen={showWorkbookInspector}
              onClose={handleWorkbookInspectorClose}
              onConfirm={handleWorkbookInspectorConfirm}
              workbookInfo={pendingWorkbookInfo}
            />
          )}
          </>
          )}
        </>
      )}
    </main>
  )
}

// Wrapper component to provide MappingContext
export default function Home() {
  return (
    <MappingProvider>
      <HomeContent />
    </MappingProvider>
  )
}
