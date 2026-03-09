'use client'

/**
 * useTrialBalancePreflight — Preflight orchestration, inspection gates, workbook/PDF/column mapping
 * Sprint 519 Phase 2: Extracted from useTrialBalanceAudit
 */

import { useState, useCallback } from 'react'
import type { ColumnMapping, ColumnDetectionInfo } from '@/components/mapping'
import { useFileUpload } from '@/hooks/useFileUpload'
import { usePreflight } from '@/hooks/usePreflight'
import type { WorkbookInfo } from '@/types/mapping'
import type { PdfPreviewResult } from '@/types/pdf'
import type { UploadStatus } from '@/types/shared'
import { apiFetch } from '@/utils'
import type { UseTrialBalanceUploadReturn } from './useTrialBalanceUpload'

/** Subset of upload hook needed by the preflight hook */
interface UploadControls {
  runAudit: UseTrialBalanceUploadReturn['runAudit']
  selectedFile: File | null
  setSelectedFile: (file: File | null) => void
  setAuditStatus: (status: UploadStatus) => void
  materialityThreshold: number
  startProgressIndicator: () => void
  stopProgressIndicator: () => void
  token: string | null
  user: UseTrialBalanceUploadReturn['user']
  userColumnMapping: ColumnMapping | null
  setUserColumnMapping: (m: ColumnMapping | null) => void
  selectedSheets: string[] | null
  setSelectedSheets: (s: string[] | null) => void
  resetAudit: () => void
}

export interface UseTrialBalancePreflightReturn {
  // Preflight
  preflightStatus: UploadStatus
  preflightReport: ReturnType<typeof usePreflight>['report']
  preflightError: string
  showPreflight: boolean
  handlePreflightProceed: () => Promise<void>
  // Column mapping
  showColumnMappingModal: boolean
  pendingColumnDetection: ColumnDetectionInfo | null
  handleColumnMappingConfirm: (mapping: ColumnMapping) => void
  handleColumnMappingClose: () => void
  columnMappingSource: 'preflight' | 'manual' | null
  // Workbook inspector
  showWorkbookInspector: boolean
  pendingWorkbookInfo: WorkbookInfo | null
  handleWorkbookInspectorConfirm: (sheets: string[]) => void
  handleWorkbookInspectorClose: () => void
  // PDF preview
  showPdfPreview: boolean
  pendingPdfPreview: PdfPreviewResult | null
  handlePdfPreviewConfirm: () => void
  handlePdfPreviewClose: () => void
  // File upload
  isDragging: boolean
  handleDrop: (e: React.DragEvent) => void
  handleDragOver: (e: React.DragEvent) => void
  handleDragLeave: (e: React.DragEvent) => void
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  // Reset (augmented — clears preflight state too)
  resetAll: () => void
}

export function useTrialBalancePreflight(upload: UploadControls): UseTrialBalancePreflightReturn {
  const preflight = usePreflight()
  const [showPreflight, setShowPreflight] = useState(false)

  // Column mapping state
  const [showColumnMappingModal, setShowColumnMappingModal] = useState(false)
  const [pendingColumnDetection, setPendingColumnDetection] = useState<ColumnDetectionInfo | null>(null)
  const [columnMappingSource, setColumnMappingSource] = useState<'preflight' | 'manual' | null>(null)

  // Workbook inspection state
  const [showWorkbookInspector, setShowWorkbookInspector] = useState(false)
  const [pendingWorkbookInfo, setPendingWorkbookInfo] = useState<WorkbookInfo | null>(null)

  // PDF preview state
  const [showPdfPreview, setShowPdfPreview] = useState(false)
  const [pendingPdfPreview, setPendingPdfPreview] = useState<PdfPreviewResult | null>(null)

  const handleFileUpload = useCallback(async (file: File) => {
    if (upload.user && upload.user.is_verified === false) {
      upload.setAuditStatus('error')
      return
    }

    upload.setSelectedFile(file)
    upload.setUserColumnMapping(null)
    setColumnMappingSource(null)
    upload.setSelectedSheets(null)

    // Sprint 283: Run pre-flight check first
    setShowPreflight(false)
    await preflight.runPreflight(file)
    setShowPreflight(true)
  }, [preflight, upload])

  const handlePreflightProceed = useCallback(async () => {
    setShowPreflight(false)

    if (!upload.selectedFile) {
      preflight.reset()
      return
    }

    // Sprint 309: Extract column mappings from pre-flight
    let preflightMapping: ColumnMapping | null = null
    if (preflight.report?.columns) {
      const cols = preflight.report.columns
      const account = cols.find(c => c.role === 'account' && c.status === 'found' && c.confidence >= 0.8)
      const debit = cols.find(c => c.role === 'debit' && c.status === 'found' && c.confidence >= 0.8)
      const credit = cols.find(c => c.role === 'credit' && c.status === 'found' && c.confidence >= 0.8)

      if (account?.detected_name && debit?.detected_name && credit?.detected_name) {
        preflightMapping = {
          account_column: account.detected_name,
          debit_column: debit.detected_name,
          credit_column: credit.detected_name,
        }
      }
    }

    if (preflightMapping) {
      upload.setUserColumnMapping(preflightMapping)
      setColumnMappingSource('preflight')
    } else {
      setColumnMappingSource(null)
    }

    preflight.reset()

    const effectiveMapping = preflightMapping ?? null
    const selectedFile = upload.selectedFile

    const isExcel = selectedFile.name.toLowerCase().endsWith('.xlsx') || selectedFile.name.toLowerCase().endsWith('.xls')
    const isPdf = selectedFile.name.toLowerCase().endsWith('.pdf')

    if (isPdf) {
      upload.setAuditStatus('loading')
      upload.startProgressIndicator()

      try {
        const formData = new FormData()
        formData.append('file', selectedFile)

        const { data: pdfPreview, ok: previewOk } = await apiFetch<PdfPreviewResult>(
          '/audit/preview-pdf',
          upload.token ?? null,
          { method: 'POST', body: formData },
        )

        if (previewOk && pdfPreview) {
          setPendingPdfPreview(pdfPreview)
          setShowPdfPreview(true)
          upload.setAuditStatus('idle')
          upload.stopProgressIndicator()
          return
        }

        upload.stopProgressIndicator()
        await upload.runAudit(selectedFile, upload.materialityThreshold, false, effectiveMapping, null)
      } catch (error) {
        console.error('PDF preview failed:', error)
        upload.stopProgressIndicator()
        await upload.runAudit(selectedFile, upload.materialityThreshold, false, effectiveMapping, null)
      }
    } else if (isExcel) {
      upload.setAuditStatus('loading')
      upload.startProgressIndicator()

      try {
        const formData = new FormData()
        formData.append('file', selectedFile)

        const { data: workbookInfo, ok: inspectOk } = await apiFetch<WorkbookInfo>(
          '/audit/inspect-workbook',
          upload.token ?? null,
          { method: 'POST', body: formData },
        )

        if (inspectOk && workbookInfo?.requires_sheet_selection) {
          setPendingWorkbookInfo(workbookInfo)
          setShowWorkbookInspector(true)
          upload.setAuditStatus('idle')
          upload.stopProgressIndicator()
          return
        }

        upload.stopProgressIndicator()
        await upload.runAudit(selectedFile, upload.materialityThreshold, false, effectiveMapping, null)
      } catch (error) {
        console.error('Workbook inspection failed:', error)
        upload.stopProgressIndicator()
        await upload.runAudit(selectedFile, upload.materialityThreshold, false, effectiveMapping, null)
      }
    } else {
      await upload.runAudit(selectedFile, upload.materialityThreshold, false, effectiveMapping, null)
    }
  }, [upload, preflight])

  const handleWorkbookInspectorConfirm = useCallback((sheets: string[]) => {
    upload.setSelectedSheets(sheets)
    setShowWorkbookInspector(false)
    setPendingWorkbookInfo(null)
    if (upload.selectedFile) {
      upload.runAudit(upload.selectedFile, upload.materialityThreshold, false, upload.userColumnMapping, sheets)
    }
  }, [upload])

  const handleWorkbookInspectorClose = useCallback(() => {
    setShowWorkbookInspector(false)
    setPendingWorkbookInfo(null)
    upload.setAuditStatus('idle')
    upload.setSelectedFile(null)
  }, [upload])

  const handlePdfPreviewConfirm = useCallback(() => {
    setShowPdfPreview(false)
    setPendingPdfPreview(null)
    if (upload.selectedFile) {
      upload.runAudit(upload.selectedFile, upload.materialityThreshold, false, upload.userColumnMapping, null)
    }
  }, [upload])

  const handlePdfPreviewClose = useCallback(() => {
    setShowPdfPreview(false)
    setPendingPdfPreview(null)
    upload.setAuditStatus('idle')
    upload.setSelectedFile(null)
  }, [upload])

  const handleColumnMappingConfirm = useCallback((mapping: ColumnMapping) => {
    upload.setUserColumnMapping(mapping)
    setColumnMappingSource('manual')
    setShowColumnMappingModal(false)
    setPendingColumnDetection(null)
    if (upload.selectedFile) {
      upload.runAudit(upload.selectedFile, upload.materialityThreshold, false, mapping, upload.selectedSheets)
    }
  }, [upload])

  const handleColumnMappingClose = useCallback(() => {
    setShowColumnMappingModal(false)
    setPendingColumnDetection(null)
    upload.setAuditStatus('idle')
    upload.setSelectedFile(null)
  }, [upload])

  const { isDragging, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } = useFileUpload(handleFileUpload)

  const resetAll = useCallback(() => {
    setShowPreflight(false)
    setShowColumnMappingModal(false)
    setPendingColumnDetection(null)
    setShowWorkbookInspector(false)
    setPendingWorkbookInfo(null)
    setShowPdfPreview(false)
    setPendingPdfPreview(null)
    setColumnMappingSource(null)
    preflight.reset()
    upload.resetAudit()
  }, [preflight, upload])

  return {
    preflightStatus: preflight.status,
    preflightReport: preflight.report,
    preflightError: preflight.error,
    showPreflight,
    handlePreflightProceed,
    showColumnMappingModal, pendingColumnDetection,
    handleColumnMappingConfirm, handleColumnMappingClose,
    columnMappingSource,
    showWorkbookInspector, pendingWorkbookInfo,
    handleWorkbookInspectorConfirm, handleWorkbookInspectorClose,
    showPdfPreview, pendingPdfPreview,
    handlePdfPreviewConfirm, handlePdfPreviewClose,
    isDragging, handleDrop, handleDragOver, handleDragLeave, handleFileSelect,
    resetAll,
  }
}
