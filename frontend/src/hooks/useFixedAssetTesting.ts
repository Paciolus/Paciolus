/**
 * useFixedAssetTesting Hook (Sprint 116, factory Sprint 161)
 *
 * Thin wrapper around createTestingHook for Fixed Asset Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { createTestingHook } from './createTestingHook'
import type { FixedAssetTestingResult } from '@/types/fixedAssetTesting'

export interface UseFixedAssetTestingReturn {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: FixedAssetTestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<FixedAssetTestingResult>({ endpoint: '/audit/fixed-assets', toolName: 'Fixed asset tests' })

export function useFixedAssetTesting(): UseFixedAssetTestingReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runTests: run as (file: File) => Promise<void> }
}
