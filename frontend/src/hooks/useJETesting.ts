/**
 * useJETesting Hook (Sprint 66, refactored Sprint 82, factory Sprint 161)
 *
 * Thin wrapper around createTestingHook for Journal Entry Testing.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { createTestingHook } from './createTestingHook'
import type { JETestingResult } from '@/types/jeTesting'
import type { UploadStatus } from '@/types/shared'

export interface UseJETestingReturn {
  status: UploadStatus
  result: JETestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<JETestingResult>({ endpoint: '/audit/journal-entries', toolName: 'JE tests' })

export function useJETesting(): UseJETestingReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runTests: run as (file: File) => Promise<void> }
}
