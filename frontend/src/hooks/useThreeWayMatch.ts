/**
 * useThreeWayMatch Hook (Sprint 93, factory Sprint 161)
 *
 * Three-Way Match Validator upload hook (PO, Invoice, Receipt).
 * Sprint 839: sends per-run tolerance overrides — only the fields the user
 * changed from their saved settings / the Paciolus defaults. A field left
 * alone sends nothing, so saved settings still apply and are reported as such.
 * Zero-Storage: files processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import { TWM_RUN_OVERRIDE_KEYS, type ThreeWayMatchConfig } from '@/types/settings'
import type { UploadStatus } from '@/types/shared'
import type { ThreeWayMatchResult } from '@/types/threeWayMatch'
import { useAuditUpload } from './useAuditUpload'

export interface UseThreeWayMatchReturn {
  status: UploadStatus
  result: ThreeWayMatchResult | null
  error: string
  runMatch: (poFile: File, invoiceFile: File, receiptFile: File) => Promise<void>
  reset: () => void
}

/** Per-run overrides, in engine units (fractions as 0-1). Omitted = not set. */
export type TWMRunOverrides = Partial<ThreeWayMatchConfig>

export function buildThreeWayMatchFormData(
  poFile: File | undefined,
  invoiceFile: File | undefined,
  receiptFile: File | undefined,
  overrides?: TWMRunOverrides,
): FormData {
  const fd = new FormData()
  if (poFile) fd.append('po_file', poFile)
  if (invoiceFile) fd.append('invoice_file', invoiceFile)
  if (receiptFile) fd.append('receipt_file', receiptFile)
  for (const key of TWM_RUN_OVERRIDE_KEYS) {
    const value = overrides?.[key]
    if (value !== undefined) fd.append(key, String(value))
  }
  return fd
}

export function useThreeWayMatch(overrides?: TWMRunOverrides): UseThreeWayMatchReturn {
  // Serialised so a new-but-equal object does not rebuild the upload options.
  const overridesKey = JSON.stringify(overrides ?? {})
  const options = useMemo(() => {
    const parsed = JSON.parse(overridesKey) as TWMRunOverrides
    return {
      endpoint: '/audit/three-way-match',
      toolName: 'three-way match',
      buildFormData: (...files: File[]) => buildThreeWayMatchFormData(files[0], files[1], files[2], parsed),
      parseResult: (data: unknown) => data as ThreeWayMatchResult,
    }
  }, [overridesKey])

  const { run, ...rest } = useAuditUpload<ThreeWayMatchResult>(options)
  return { ...rest, runMatch: run as (poFile: File, invoiceFile: File, receiptFile: File) => Promise<void> }
}
