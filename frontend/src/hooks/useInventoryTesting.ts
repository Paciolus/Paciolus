/**
 * useInventoryTesting Hook (Sprint 119, factory Sprint 161)
 *
 * Thin wrapper around createTestingHook for Inventory Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { createTestingHook } from './createTestingHook'
import type { InventoryTestingResult } from '@/types/inventoryTesting'

export interface UseInventoryTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: InventoryTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<InventoryTestingResult>({ endpoint: '/audit/inventory-testing', toolName: 'Inventory tests' })

export function useInventoryTesting(): UseInventoryTestingReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runTests: run as (file: File) => Promise<void> }
}
