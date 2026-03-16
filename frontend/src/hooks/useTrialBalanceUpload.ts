'use client'

/**
 * useTrialBalanceUpload — Core upload lifecycle, progress, materiality, debounced recalc
 * Sprint 519 Phase 2: Extracted from useTrialBalanceAudit
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { useMappings } from '@/contexts/MappingContext'
import type { ColumnMapping } from '@/components/mapping'
import type { DisplayMode } from '@/components/sensitivity'
import { useSettings } from '@/hooks/useSettings'
import type { AuditResult, AuditResultResponse } from '@/types/diagnostic'
import type { UploadStatus } from '@/types/shared'
import { uploadFetch } from '@/utils/uploadTransport'
import { apiPost } from '@/utils'

export interface UseTrialBalanceUploadReturn {
  // Auth (forwarded for consumer convenience)
  user: ReturnType<typeof useAuth>['user']
  isAuthenticated: boolean
  token: string | null
  isVerified: boolean
  // Audit state
  auditStatus: UploadStatus
  auditResult: AuditResult | null
  auditError: string
  selectedFile: File | null
  isRecalculating: boolean
  scanningRows: number
  // Materiality
  materialityThreshold: number
  setMaterialityThreshold: (v: number) => void
  displayMode: DisplayMode
  handleDisplayModeChange: (mode: DisplayMode) => void
  // Actions
  resetAudit: () => void
  handleRerunAudit: () => void
  // Internal controls (exposed for preflight hook)
  runAudit: (
    file: File,
    threshold: number,
    isRecalc?: boolean,
    columnMapping?: ColumnMapping | null,
    sheets?: string[] | null,
  ) => Promise<void>
  setSelectedFile: (file: File | null) => void
  setAuditStatus: (status: UploadStatus) => void
  startProgressIndicator: () => void
  stopProgressIndicator: () => void
  // For debounce coordination
  userColumnMapping: ColumnMapping | null
  setUserColumnMapping: (m: ColumnMapping | null) => void
  selectedSheets: string[] | null
  setSelectedSheets: (s: string[] | null) => void
}

export function useTrialBalanceUpload(): UseTrialBalanceUploadReturn {
  const mappingContext = useMappings()
  const { user, isAuthenticated, token } = useAuth()
  const engagement = useOptionalEngagementContext()
  const { practiceSettings, isLoading: settingsLoading } = useSettings()

  const isVerified = user?.is_verified !== false

  // Audit zone state
  const [auditStatus, setAuditStatus] = useState<UploadStatus>('idle')
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

  // Column mapping + sheet state (owned here for debounce coordination)
  const [userColumnMapping, setUserColumnMapping] = useState<ColumnMapping | null>(null)
  const [selectedSheets, setSelectedSheets] = useState<string[] | null>(null)

  // Previous state refs for deep comparison
  const prevThresholdRef = useRef<number>(materialityThreshold)
  const prevColumnMappingRef = useRef<ColumnMapping | null>(null)
  const prevSelectedSheetsRef = useRef<string[] | null>(null)
  const prevInputHashRef = useRef<string>('')

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

  // Sprint 310: Pre-fill materiality from engagement cascade
  useEffect(() => {
    const pm = engagement?.materiality?.performance_materiality
    if (pm && pm > 0) {
      setMaterialityThreshold(pm)
    }
  }, [engagement?.materiality?.performance_materiality])

  const handleDisplayModeChange = useCallback((mode: DisplayMode) => {
    setDisplayMode(mode)
    setShowImmaterial(mode === 'lenient' || mode === 'all')
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

    if (engagement?.engagementId) {
      formData.append('engagement_id', engagement.engagementId.toString())
    }

    try {
      const result = await uploadFetch('/audit/trial-balance', formData, token ?? null)

      if (!result.ok) {
        setAuditStatus('error')
        if (result.status === 401) {
          setAuditError('Please sign in to run diagnostics.')
        } else if (result.errorCode === 'EMAIL_NOT_VERIFIED') {
          setAuditError('Please verify your email address before running diagnostics. Check your inbox for the verification link.')
        } else if (result.status === 403) {
          setAuditError('Access denied.')
        } else {
          setAuditError(result.error || 'Failed to analyze file')
        }
        stopProgressIndicator()
        setIsRecalculating(false)
        return
      }

      const data = result.data as AuditResultResponse

      if (data.status === 'success') {
        if (data.column_detection?.requires_mapping && !columnMapping) {
          // Signal to preflight hook via return — handled by composite
          setAuditResult(data as AuditResult)
          setAuditStatus('success')
          stopProgressIndicator()
          return
        }

        setAuditStatus('success')
        setAuditResult(data as AuditResult)

        if (engagement?.engagementId) {
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
        setAuditError((data as unknown as Record<string, string>).message || (data as unknown as Record<string, string>).detail || 'Failed to analyze file')
      }
    } catch {
      setAuditStatus('error')
      setAuditError('Unable to connect to server. Please try again.')
    } finally {
      setIsRecalculating(false)
      stopProgressIndicator()
    }
  }, [startProgressIndicator, stopProgressIndicator, mappingContext, isAuthenticated, token, engagement])

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
    user, isAuthenticated, token, isVerified,
    auditStatus, auditResult, auditError,
    selectedFile, isRecalculating, scanningRows,
    materialityThreshold, setMaterialityThreshold,
    displayMode, handleDisplayModeChange,
    resetAudit, handleRerunAudit,
    // Internal controls
    runAudit, setSelectedFile, setAuditStatus,
    startProgressIndicator, stopProgressIndicator,
    userColumnMapping, setUserColumnMapping,
    selectedSheets, setSelectedSheets,
  }
}
