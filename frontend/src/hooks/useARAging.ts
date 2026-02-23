/**
 * useARAging Hook (Sprint 109, factory Sprint 161)
 *
 * Dual-file upload wrapper around createTestingHook for AR Aging Analysis.
 * TB file required, sub-ledger file optional.
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import type { ARAgingResult } from '@/types/arAging'
import type { UploadStatus } from '@/types/shared'
import { createTestingHook } from './createTestingHook'

export interface UseARAgingReturn {
  status: UploadStatus
  result: ARAgingResult | null
  error: string
  runTests: (tbFile: File, slFile?: File) => Promise<void>
  reset: () => void
}

const useBase = createTestingHook<ARAgingResult>({
  endpoint: '/audit/ar-aging',
  toolName: 'AR aging analysis',
  buildFormData: (tbFile: File, slFile?: File) => {
    const fd = new FormData()
    fd.append('tb_file', tbFile)
    if (slFile) {
      fd.append('subledger_file', slFile)
    }
    return fd
  },
})

export function useARAging(): UseARAgingReturn {
  const { run, ...rest } = useBase()
  return { ...rest, runTests: run as (tbFile: File, slFile?: File) => Promise<void> }
}
