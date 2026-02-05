'use client'

import { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { MappingProvider, useMappings } from '@/context/MappingContext'
import { useAuth } from '@/context/AuthContext'
import { AccountTypeDropdown, MappingIndicator, MappingToolbar, ColumnMappingModal } from '@/components/mapping'
import type { ColumnMapping, ColumnDetectionInfo } from '@/components/mapping'
import { AccountType, AbnormalBalanceExtended, ACCOUNT_TYPE_LABELS, RiskSummary, WorkbookInfo, ConsolidatedAuditResult, Analytics } from '@/types/mapping'
import { RiskDashboard } from '@/components/risk'
import { WorkbookInspector } from '@/components/workbook'
import { DownloadReportButton } from '@/components/export'
import { ProfileDropdown } from '@/components/auth'
import { KeyMetricsSection } from '@/components/analytics'
import { SensitivityToolbar, type DisplayMode } from '@/components/sensitivity'
import { FeaturePillars, ProcessTimeline } from '@/components/marketing'
import { WorkspaceHeader, QuickActionsBar, RecentHistoryMini } from '@/components/workspace'
import { MaterialityControl } from '@/components/diagnostic'
import { BenchmarkSection } from '@/components/benchmark'
import { LeadSheetSection } from '@/components/leadSheet'
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
}

function HomeContent() {
  const [email, setEmail] = useState('')
  const mappingContext = useMappings()
  const { user, isAuthenticated, isLoading: authLoading, logout, token } = useAuth()
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

  // Audit zone state
  const [isDragging, setIsDragging] = useState(false)
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

    try {
      const response = await fetch(`${API_URL}/audit/trial-balance`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      // Debug: Log the full API response
      console.log('Audit API Response:', data)
      console.log('Abnormal balances:', data.abnormal_balances)
      console.log('Classification summary:', data.classification_summary)
      console.log('Column detection:', data.column_detection)

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
        // Initialize mapping context with detected types
        if (data.abnormal_balances) {
          mappingContext.initializeFromAudit(data.abnormal_balances)
        }

        // Day 14: Log activity for authenticated users (only on initial audit, not recalc)
        if (!isRecalc && isAuthenticated && token) {
          try {
            await fetch(`${API_URL}/activity/log`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
              },
              body: JSON.stringify({
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
              }),
            })
            console.log('Activity logged successfully')
          } catch (logError) {
            // Don't fail the audit if logging fails
            console.error('Failed to log activity:', logError)
          }
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

        const response = await fetch(`${API_URL}/audit/inspect-workbook`, {
          method: 'POST',
          body: formData,
        })

        const workbookInfo: WorkbookInfo = await response.json()
        console.log('Workbook inspection result:', workbookInfo)

        if (response.ok && workbookInfo.requires_sheet_selection) {
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
  }, [materialityThreshold, runAudit, startProgressIndicator, stopProgressIndicator])

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

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }, [handleFileUpload])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileUpload(file)
    }
  }, [handleFileUpload])

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
    <main className="min-h-screen bg-gradient-obsidian">
      {/* Navigation - Enhanced with subtle glow */}
      <nav className="fixed top-0 w-full bg-obsidian-900/90 backdrop-blur-lg border-b border-obsidian-600/30 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative">
              <img
                src="/PaciolusLogo_DarkBG.png"
                alt="Paciolus"
                className="h-10 w-auto max-h-10 object-contain transition-all duration-300 group-hover:logo-glow"
                style={{ imageRendering: 'crisp-edges' }}
              />
              {/* Subtle glow behind logo on hover */}
              <div className="absolute inset-0 bg-sage-500/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10" />
            </div>
            <span className="text-xl font-bold font-serif text-oatmeal-200 tracking-tight group-hover:text-oatmeal-100 transition-colors">
              Paciolus
            </span>
          </Link>

          {/* Auth Section */}
          <div className="flex items-center gap-6">
            <span className="text-sm text-oatmeal-500 font-sans hidden sm:block tracking-wide">
              For Financial Professionals
            </span>
            {!authLoading && (
              isAuthenticated && user ? (
                <ProfileDropdown user={user} onLogout={logout} />
              ) : (
                <Link
                  href="/login"
                  className="px-5 py-2.5 bg-sage-500/10 border border-sage-500/30 rounded-xl text-sage-400 text-sm font-sans font-medium hover:bg-sage-500/20 hover:border-sage-500/50 hover:shadow-lg hover:shadow-sage-500/10 transition-all duration-300"
                >
                  Sign In
                </Link>
              )
            )}
          </div>
        </div>
      </nav>

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
                className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-8"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
                }}
              >
                <span className="w-2 h-2 bg-sage-400 rounded-full animate-pulse"></span>
                <span className="text-sage-300 text-sm font-sans font-medium tracking-wide">Zero-Storage Processing</span>
              </motion.div>

              {/* Main Headline - Enhanced Typography */}
              <motion.h1
                className="text-5xl md:text-6xl lg:text-8xl font-serif font-bold text-oatmeal-200 mb-6 leading-[0.95] tracking-tight text-shadow-lg"
                variants={{
                  hidden: { opacity: 0, y: 30 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
                }}
              >
                Surgical Precision
                <span className="block text-sage-400 mt-2">for Trial Balance Diagnostics</span>
              </motion.h1>

              {/* Sub-headline */}
              <motion.p
                className="text-xl md:text-2xl text-oatmeal-300 font-sans mb-10 max-w-3xl mx-auto leading-relaxed"
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
                }}
              >
                Financial Professionals: Eliminate sign errors and misclassifications with automated
                <span className="text-oatmeal-100 font-semibold"> Close Health Reports</span>.
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
                      <svg className="w-6 h-6 text-oatmeal-500 hidden md:block mr-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                    <div className="w-12 h-12 rounded-full bg-sage-500/20 border border-sage-500/40 flex items-center justify-center backdrop-blur-sm">
                      <span className="text-sage-400 font-bold font-mono text-lg">{item.step}</span>
                    </div>
                    <span className="text-oatmeal-200 font-sans font-medium text-lg">{item.label}</span>
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
                    className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-sage-500/25"
                  >
                    {status === 'loading' ? 'Joining...' : 'Join Waitlist'}
                  </button>
                </div>

                {/* Status Message */}
                {status === 'success' && (
                  <p className="mt-4 text-sage-400 font-sans font-medium">{message}</p>
                )}
                {status === 'error' && (
                  <p className="mt-4 text-clay-400 font-sans font-medium">{message}</p>
                )}
              </motion.form>

              <motion.p
                className="mt-6 text-oatmeal-500 text-sm font-sans"
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

          {/* Secure Audit Zone */}
          <section className="py-16 px-6 bg-obsidian-700/30">
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-4">
                  <svg className="w-4 h-4 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="text-sage-300 text-sm font-sans font-medium">Zero-Storage Processing</span>
                </div>
                <h2 className="text-3xl font-serif font-bold text-oatmeal-200 mb-2">Diagnostic Intelligence Zone</h2>
                <p className="text-oatmeal-400 font-sans">Upload your trial balance for instant analysis. Your data never leaves your browser's memory.</p>
              </div>

              {/* Materiality Threshold Control - Sprint 25: Extracted component */}
              <MaterialityControl
                idPrefix="guest"
                value={materialityThreshold}
                onChange={setMaterialityThreshold}
                showLiveIndicator={!!selectedFile && auditStatus === 'success'}
                filename={selectedFile?.name}
              />

              {/* Drop Zone - Enhanced with premium styling */}
              {/* Sprint 22: Fixed ghost click issue - input only active in idle state */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`drop-zone ${auditStatus === 'idle' ? 'cursor-pointer' : ''} ${isDragging ? 'dragging' : ''}`}
              >
                {/* File input only active and visible when in idle state to prevent ghost clicks */}
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={handleFileSelect}
                  className={`absolute inset-0 w-full h-full opacity-0 ${auditStatus === 'idle' ? 'cursor-pointer' : 'pointer-events-none'
                    }`}
                  tabIndex={auditStatus === 'idle' ? 0 : -1}
                />

                {auditStatus === 'idle' && (
                  <>
                    <svg className="w-12 h-12 text-oatmeal-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-oatmeal-300 text-lg font-sans mb-2">Drag and drop your trial balance</p>
                    <p className="text-oatmeal-500 text-sm font-sans">or click to browse. Supports CSV and Excel files.</p>
                  </>
                )}

                {auditStatus === 'loading' && (
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin mb-4"></div>
                    <p className="text-oatmeal-300 font-sans mb-2">Streaming analysis in progress...</p>

                    {/* Progress Indicator */}
                    <div className="w-full max-w-xs">
                      {/* Progress bar background */}
                      <div className="h-2 bg-obsidian-600 rounded-full overflow-hidden mb-2">
                        {/* Animated progress bar (indeterminate style with pulse) */}
                        <div className="h-full bg-gradient-sage rounded-full animate-pulse"
                          style={{ width: '100%' }}></div>
                      </div>

                      {/* Scanning rows counter */}
                      <div className="flex items-center justify-center gap-2 text-sm font-sans">
                        <svg className="w-4 h-4 text-sage-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <span className="text-sage-300 font-mono">
                          Scanning rows: <span className="text-oatmeal-200">{scanningRows.toLocaleString()}</span>...
                        </span>
                      </div>
                    </div>

                    <p className="text-oatmeal-500 text-xs font-sans mt-3">
                      Processing in memory-efficient chunks
                    </p>
                  </div>
                )}

                {auditStatus === 'success' && auditResult && (
                  <div className="space-y-4 transition-opacity">
                    {/* Sprint 15: Tier 1 Skeleton Loader with shimmer effect */}
                    {isRecalculating && (
                      <div className="space-y-4">
                        {/* Recalculating header */}
                        <div className="flex items-center justify-center gap-2 bg-sage-500/20 border border-sage-500/30 rounded-lg px-4 py-2">
                          <div className="w-4 h-4 border-2 border-sage-400/30 border-t-sage-400 rounded-full animate-spin"></div>
                          <span className="text-sage-300 text-sm font-sans font-medium">Recalculating with new threshold...</span>
                        </div>

                        {/* Skeleton placeholder for status icon */}
                        <div className="flex flex-col items-center">
                          <div className="w-16 h-16 rounded-full bg-obsidian-700 animate-pulse relative overflow-hidden">
                            <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
                          </div>
                          <div className="w-24 h-6 mt-3 rounded bg-obsidian-700 animate-pulse relative overflow-hidden">
                            <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
                          </div>
                        </div>

                        {/* Skeleton placeholder for summary table */}
                        <div className="bg-obsidian-800/50 rounded-xl p-4 max-w-sm mx-auto">
                          <div className="space-y-3">
                            {[1, 2, 3, 4].map((i) => (
                              <div key={i} className="flex justify-between">
                                <div className="w-24 h-4 rounded bg-obsidian-700 animate-pulse relative overflow-hidden">
                                  <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
                                </div>
                                <div className="w-20 h-4 rounded bg-obsidian-700 animate-pulse relative overflow-hidden">
                                  <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Actual content - hidden during recalculation */}
                    <div className={isRecalculating ? 'hidden' : ''}>

                      {auditResult.balanced ? (
                        <>
                          <div className="w-16 h-16 bg-sage-500/20 rounded-full flex items-center justify-center mx-auto">
                            <svg className="w-10 h-10 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                          <p className="text-sage-400 text-xl font-serif font-semibold">Balanced</p>
                        </>
                      ) : (
                        <>
                          <div className="w-16 h-16 bg-clay-500/20 rounded-full flex items-center justify-center mx-auto">
                            <svg className="w-10 h-10 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          </div>
                          <p className="text-clay-400 text-xl font-serif font-semibold">Out of Balance</p>
                        </>
                      )}

                      <div className="bg-obsidian-800/50 rounded-xl p-4 text-left max-w-sm mx-auto">
                        <div className="grid grid-cols-2 gap-2 text-sm font-sans">
                          <span className="text-oatmeal-400">Total Debits:</span>
                          <span className="text-oatmeal-200 text-right font-mono">${auditResult.total_debits.toLocaleString()}</span>
                          <span className="text-oatmeal-400">Total Credits:</span>
                          <span className="text-oatmeal-200 text-right font-mono">${auditResult.total_credits.toLocaleString()}</span>
                          <span className="text-oatmeal-400">Difference:</span>
                          <span className={`text-right font-mono ${auditResult.difference === 0 ? 'text-sage-400' : 'text-clay-400'}`}>
                            ${auditResult.difference.toLocaleString()}
                          </span>
                          <span className="text-oatmeal-400">Rows Analyzed:</span>
                          <span className="text-oatmeal-200 text-right font-mono">{auditResult.row_count}</span>
                        </div>
                      </div>

                      {/* Mapping Toolbar (Day 9) */}
                      {(auditResult.material_count > 0 || auditResult.immaterial_count > 0) && (
                        <div className="max-w-md mx-auto mt-4">
                          <MappingToolbar
                            disabled={isRecalculating}
                            onRerunAudit={() => selectedFile && runAudit(selectedFile, materialityThreshold, true, userColumnMapping)}
                          />
                        </div>
                      )}

                      {/* Sprint 22: Sensitivity Toolbar - "Control Surface" for live parameter tuning */}
                      <div className="mt-6 max-w-2xl mx-auto">
                        <SensitivityToolbar
                          threshold={materialityThreshold}
                          displayMode={displayMode}
                          onThresholdChange={setMaterialityThreshold}
                          onDisplayModeChange={handleDisplayModeChange}
                          disabled={isRecalculating}
                        />
                      </div>

                      {/* Day 10: Risk Dashboard with Animated Anomaly Cards */}
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

                      {/* Sprint 19: Key Metrics Section with Ratio Intelligence */}
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
                        <div className="mt-6 p-4 bg-obsidian-800/50 rounded-xl border border-obsidian-700">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                            <div>
                              <h4 className="font-serif text-sm font-medium text-oatmeal-200 mb-1">
                                Industry Benchmark Comparison
                              </h4>
                              <p className="text-xs text-oatmeal-500">
                                Compare your ratios against industry benchmarks
                              </p>
                            </div>
                            <select
                              value={selectedIndustry}
                              onChange={(e) => handleIndustryChange(e.target.value)}
                              disabled={isRecalculating || isLoadingComparison}
                              className="
                                px-3 py-2 rounded-lg text-sm font-sans
                                bg-obsidian-700 border border-obsidian-600 text-oatmeal-200
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

                      {/* Sprint 18: Legal Disclaimer Banner */}
                      <div className="mt-4 p-3 bg-obsidian-700/30 border border-obsidian-600/50 rounded-lg">
                        <p className="text-oatmeal-500 text-xs font-sans text-center leading-relaxed">
                          This output is generated by an automated analytical system and supports internal evaluation
                          and professional judgment. It does not constitute an audit, review, or attestation engagement
                          and provides no assurance.
                        </p>
                      </div>

                      {/* Sprint 18: PDF Export Button (Diagnostic Summary) */}
                      <div className="mt-6 pt-4 border-t border-obsidian-700">
                        <DownloadReportButton
                          auditResult={auditResult}
                          filename={selectedFile?.name || 'diagnostic'}
                          disabled={isRecalculating}
                        />
                      </div>

                      <button
                        onClick={() => {
                          setAuditStatus('idle')
                          setAuditResult(null)
                          setSelectedFile(null)
                        }}
                        className="text-sage-400 hover:text-sage-300 text-sm font-sans font-medium mt-2"
                        disabled={isRecalculating}
                      >
                        Upload another file
                      </button>
                    </div>{/* End: Actual content - hidden during recalculation */}
                  </div>
                )}

                {auditStatus === 'error' && (
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-clay-500/20 rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                    <p className="text-clay-400 font-sans font-medium">{auditError}</p>
                    <button
                      onClick={() => {
                        setAuditStatus('idle')
                        setAuditError('')
                        setSelectedFile(null)
                      }}
                      className="text-sage-400 hover:text-sage-300 text-sm font-sans font-medium"
                    >
                      Try again
                    </button>
                  </div>
                )}
              </div>

              <p className="text-center text-oatmeal-500 text-xs font-sans mt-4">
                Your file is processed entirely in-memory and is never saved to any disk or server.
              </p>
            </div>
          </section>

          {/* CTA Section */}
          <section className="py-20 px-6">
            <div className="max-w-3xl mx-auto text-center bg-gradient-to-r from-sage-500/10 to-sage-600/10 border border-sage-500/20 rounded-3xl p-12">
              <h2 className="text-3xl font-serif font-bold text-oatmeal-200 mb-4">
                Ready to streamline your close process?
              </h2>
              <p className="text-oatmeal-300 font-sans mb-8">
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
          <footer className="py-12 px-6 border-t border-obsidian-600/50 relative overflow-hidden">
            {/* Subtle decorative background */}
            <div className="absolute inset-0 opacity-[0.02]">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[20rem] font-serif text-oatmeal-200 select-none pointer-events-none">
                P
              </div>
            </div>

            <div className="max-w-6xl mx-auto relative">
              {/* Main footer content */}
              <div className="flex flex-col md:flex-row justify-between items-center gap-6 mb-8">
                <div className="text-oatmeal-500 text-sm font-sans">
                  © 2025 Paciolus. Built for Financial Professionals.
                </div>
                <div className="text-oatmeal-500 text-sm font-sans">
                  Zero-Storage Architecture. Your data stays yours.
                </div>
              </div>

              {/* Maker's Mark - Pacioli tribute */}
              <div className="text-center pt-6 border-t border-obsidian-700/50">
                <p className="makers-mark mb-2">
                  In the tradition of Luca Pacioli
                </p>
                <p className="text-oatmeal-500/70 text-xs font-mono tracking-wider">
                  Assets = Liabilities + Equity
                </p>
              </div>
            </div>
          </footer>

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
      ) : (
        // AUTHENTICATED VIEW: Workspace
        <>
          {/* Workspace Header with Dashboard Stats */}
          <WorkspaceHeader user={user!} token={token || undefined} />

          {/* Quick Actions Bar */}
          <QuickActionsBar />

          {/* Diagnostic Zone (reused from guest view but in workspace context) */}
          <section className="py-16 px-6 bg-obsidian-700/30">
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <div className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-4">
                  <svg className="w-4 h-4 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="text-sage-300 text-sm font-sans font-medium">Zero-Storage Processing</span>
                </div>
                <h2 className="text-3xl font-serif font-bold text-oatmeal-200 mb-2">Diagnostic Intelligence Zone</h2>
                <p className="text-oatmeal-400 font-sans">Upload your trial balance for instant analysis. Your data never leaves your browser's memory.</p>
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
                    <svg className="w-12 h-12 text-oatmeal-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-oatmeal-300 text-lg font-sans mb-2">Drag and drop your trial balance</p>
                    <p className="text-oatmeal-500 text-sm font-sans">or click to browse. Supports CSV and Excel files.</p>
                  </>
                )}

                {auditStatus === 'loading' && (
                  <div className="flex flex-col items-center">
                    <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin mb-4"></div>
                    <p className="text-oatmeal-300 font-sans mb-2">Streaming analysis in progress...</p>
                    <div className="w-full max-w-xs">
                      <div className="h-2 bg-obsidian-600 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-gradient-sage rounded-full animate-pulse" style={{ width: '100%' }}></div>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm font-sans">
                        <svg className="w-4 h-4 text-sage-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <span className="text-sage-300 font-mono">
                          Scanning rows: <span className="text-oatmeal-200">{scanningRows.toLocaleString()}</span>...
                        </span>
                      </div>
                    </div>
                    <p className="text-oatmeal-500 text-xs font-sans mt-3">Processing in memory-efficient chunks</p>
                  </div>
                )}

                {auditStatus === 'success' && auditResult && (
                  <div className="space-y-4 transition-opacity">
                    {isRecalculating && (
                      <div className="space-y-4">
                        <div className="flex items-center justify-center gap-2 bg-sage-500/20 border border-sage-500/30 rounded-lg px-4 py-2">
                          <div className="w-4 h-4 border-2 border-sage-400/30 border-t-sage-400 rounded-full animate-spin"></div>
                          <span className="text-sage-300 text-sm font-sans font-medium">Recalculating with new threshold...</span>
                        </div>
                        <div className="flex flex-col items-center">
                          <div className="w-16 h-16 rounded-full bg-obsidian-700 animate-pulse relative overflow-hidden">
                            <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
                          </div>
                          <div className="w-24 h-6 mt-3 rounded bg-obsidian-700 animate-pulse relative overflow-hidden">
                            <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
                          </div>
                        </div>
                        <div className="bg-obsidian-800/50 rounded-xl p-4 max-w-sm mx-auto">
                          <div className="space-y-3">
                            {[1, 2, 3, 4].map((i) => (
                              <div key={i} className="flex justify-between">
                                <div className="w-24 h-4 rounded bg-obsidian-700 animate-pulse relative overflow-hidden">
                                  <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
                                </div>
                                <div className="w-20 h-4 rounded bg-obsidian-700 animate-pulse relative overflow-hidden">
                                  <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.5s_infinite] bg-gradient-to-r from-transparent via-obsidian-600/50 to-transparent" />
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
                          <div className="w-16 h-16 bg-sage-500/20 rounded-full flex items-center justify-center mx-auto">
                            <svg className="w-10 h-10 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                          <p className="text-sage-400 text-xl font-serif font-semibold">Balanced</p>
                        </>
                      ) : (
                        <>
                          <div className="w-16 h-16 bg-clay-500/20 rounded-full flex items-center justify-center mx-auto">
                            <svg className="w-10 h-10 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                          </div>
                          <p className="text-clay-400 text-xl font-serif font-semibold">Out of Balance</p>
                        </>
                      )}

                      <div className="bg-obsidian-800/50 rounded-xl p-4 text-left max-w-sm mx-auto">
                        <div className="grid grid-cols-2 gap-2 text-sm font-sans">
                          <span className="text-oatmeal-400">Total Debits:</span>
                          <span className="text-oatmeal-200 text-right font-mono">${auditResult.total_debits.toLocaleString()}</span>
                          <span className="text-oatmeal-400">Total Credits:</span>
                          <span className="text-oatmeal-200 text-right font-mono">${auditResult.total_credits.toLocaleString()}</span>
                          <span className="text-oatmeal-400">Difference:</span>
                          <span className={`text-right font-mono ${auditResult.difference === 0 ? 'text-sage-400' : 'text-clay-400'}`}>
                            ${auditResult.difference.toLocaleString()}
                          </span>
                          <span className="text-oatmeal-400">Rows Analyzed:</span>
                          <span className="text-oatmeal-200 text-right font-mono">{auditResult.row_count}</span>
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
                        <div className="mt-6 p-4 bg-obsidian-800/50 rounded-xl border border-obsidian-700">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                            <div>
                              <h4 className="font-serif text-sm font-medium text-oatmeal-200 mb-1">
                                Industry Benchmark Comparison
                              </h4>
                              <p className="text-xs text-oatmeal-500">
                                Compare your ratios against industry benchmarks
                              </p>
                            </div>
                            <select
                              value={selectedIndustry}
                              onChange={(e) => handleIndustryChange(e.target.value)}
                              disabled={isRecalculating || isLoadingComparison}
                              className="
                                px-3 py-2 rounded-lg text-sm font-sans
                                bg-obsidian-700 border border-obsidian-600 text-oatmeal-200
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

                      <div className="mt-4 p-3 bg-obsidian-700/30 border border-obsidian-600/50 rounded-lg">
                        <p className="text-oatmeal-500 text-xs font-sans text-center leading-relaxed">
                          This output is generated by an automated analytical system and supports internal evaluation
                          and professional judgment. It does not constitute an audit, review, or attestation engagement
                          and provides no assurance.
                        </p>
                      </div>

                      <div className="mt-6 pt-4 border-t border-obsidian-700">
                        <DownloadReportButton
                          auditResult={auditResult}
                          filename={selectedFile?.name || 'diagnostic'}
                          disabled={isRecalculating}
                        />
                      </div>

                      <button
                        onClick={() => {
                          setAuditStatus('idle')
                          setAuditResult(null)
                          setSelectedFile(null)
                        }}
                        className="text-sage-400 hover:text-sage-300 text-sm font-sans font-medium mt-2"
                        disabled={isRecalculating}
                      >
                        Upload another file
                      </button>
                    </div>
                  </div>
                )}

                {auditStatus === 'error' && (
                  <div className="space-y-4">
                    <div className="w-16 h-16 bg-clay-500/20 rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                    <p className="text-clay-400 font-sans font-medium">{auditError}</p>
                    <button
                      onClick={() => {
                        setAuditStatus('idle')
                        setAuditError('')
                        setSelectedFile(null)
                      }}
                      className="text-sage-400 hover:text-sage-300 text-sm font-sans font-medium"
                    >
                      Try again
                    </button>
                  </div>
                )}
              </div>

              <p className="text-center text-oatmeal-500 text-xs font-sans mt-4">
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
