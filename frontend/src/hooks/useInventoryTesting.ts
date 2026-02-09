/**
 * useInventoryTesting Hook (Sprint 119)
 *
 * Thin wrapper around useAuditUpload for Inventory Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { useAuditUpload } from './useAuditUpload'
import type { InventoryTestingResult } from '@/types/inventoryTesting'

export interface UseInventoryTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: InventoryTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export function useInventoryTesting(): UseInventoryTestingReturn {
  const options = useMemo(() => ({
    endpoint: '/audit/inventory-testing',
    toolName: 'Inventory tests',
    buildFormData: (file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return fd
    },
    parseResult: (data: unknown) => data as InventoryTestingResult,
  }), [])

  const { status, result, error, run, reset } = useAuditUpload<InventoryTestingResult>(options)

  return { status, result, error, runTests: run as (file: File) => Promise<void>, reset }
}
