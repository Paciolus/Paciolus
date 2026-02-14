/**
 * useThreeWayMatch Hook (Sprint 93, factory Sprint 161)
 *
 * Wrapper around createTestingHook for Three-Way Match Validator.
 * Handles 3-file upload (PO, Invoice, Receipt).
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { createTestingHook } from './createTestingHook'
import type { ThreeWayMatchResult } from '@/types/threeWayMatch'
import type { UploadStatus } from '@/types/shared'

export interface UseThreeWayMatchReturn {
  status: UploadStatus
  result: ThreeWayMatchResult | null
  error: string
  runMatch: (poFile: File, invoiceFile: File, receiptFile: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<ThreeWayMatchResult>({
  endpoint: '/audit/three-way-match',
  toolName: 'three-way match',
  buildFormData: (poFile: File, invoiceFile: File, receiptFile: File) => {
    const fd = new FormData()
    fd.append('po_file', poFile)
    fd.append('invoice_file', invoiceFile)
    fd.append('receipt_file', receiptFile)
    return fd
  },
})

export function useThreeWayMatch(): UseThreeWayMatchReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runMatch: run as (poFile: File, invoiceFile: File, receiptFile: File) => Promise<void> }
}
