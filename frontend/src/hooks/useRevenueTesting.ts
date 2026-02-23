/**
 * useRevenueTesting Hook (Sprint 106, factory Sprint 161)
 *
 * Thin wrapper around createTestingHook for Revenue Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import type { RevenueTestingResult } from '@/types/revenueTesting'
import type { UploadStatus } from '@/types/shared'
import { createTestingHook } from './createTestingHook'

export interface UseRevenueTestingReturn {
  status: UploadStatus
  result: RevenueTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<RevenueTestingResult>({ endpoint: '/audit/revenue-testing', toolName: 'Revenue tests' })

export function useRevenueTesting(): UseRevenueTestingReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runTests: run as (file: File) => Promise<void> }
}
