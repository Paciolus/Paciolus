/**
 * useThreeWayMatch Hook (Sprint 93)
 *
 * Thin wrapper around useAuditUpload for Three-Way Match Validator.
 * Handles 3-file upload (PO, Invoice, Receipt).
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { ThreeWayMatchResult } from '@/types/threeWayMatch'

export interface UseThreeWayMatchReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: ThreeWayMatchResult | null
  error: string
  runMatch: (poFile: File, invoiceFile: File, receiptFile: File) => Promise<void>
  reset: () => void
}

export function useThreeWayMatch(): UseThreeWayMatchReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/three-way-match',
    toolName: 'three-way match',
    buildFormData: (poFile: File, invoiceFile: File, receiptFile: File) => {
      const fd = new FormData()
      fd.append('po_file', poFile)
      fd.append('invoice_file', invoiceFile)
      fd.append('receipt_file', receiptFile)
      return fd
    },
    parseResult: (data: unknown) => data as ThreeWayMatchResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<ThreeWayMatchResult>(options)

  return {
    status,
    result,
    error,
    runMatch: run as (poFile: File, invoiceFile: File, receiptFile: File) => Promise<void>,
    reset,
  }
}
