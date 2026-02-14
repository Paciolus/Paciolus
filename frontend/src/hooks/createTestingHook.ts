/**
 * Testing Hook Factory — Sprint 161
 *
 * Creates audit-upload hooks from endpoint config.
 * Eliminates boilerplate shared by 9 testing hooks.
 *
 * Single-file tools use the default buildFormData (appends 'file').
 * Multi-file tools provide a custom buildFormData.
 */

import { useMemo } from 'react'
import { useAuditUpload, type UseAuditUploadReturn } from './useAuditUpload'

interface TestingHookConfig {
  endpoint: string
  toolName: string
  /** Custom FormData builder for multi-file uploads. Default: single 'file' field. */
  buildFormData?: (...files: File[]) => FormData
}

export function createTestingHook<T>(config: TestingHookConfig): () => UseAuditUploadReturn<T> {
  const { endpoint, toolName, buildFormData } = config

  return function useTestingHook(): UseAuditUploadReturn<T> {
    const options = useMemo(() => ({
      endpoint,
      toolName,
      buildFormData: buildFormData ?? ((...files: File[]) => {
        const fd = new FormData()
        if (files[0]) fd.append('file', files[0])
        return fd
      }),
      parseResult: (data: unknown) => data as T,
    }), [])

    return useAuditUpload<T>(options)
  }
}
