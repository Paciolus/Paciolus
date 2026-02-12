/**
 * useAPTesting Hook (Sprint 75, refactored Sprint 82, factory Sprint 161)
 *
 * Thin wrapper around createTestingHook for AP Payment Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { createTestingHook } from './createTestingHook'
import type { APTestingResult } from '@/types/apTesting'

export interface UseAPTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: APTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<APTestingResult>({ endpoint: '/audit/ap-payments', toolName: 'AP tests' })

export function useAPTesting(): UseAPTestingReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runTests: run as (file: File) => Promise<void> }
}
