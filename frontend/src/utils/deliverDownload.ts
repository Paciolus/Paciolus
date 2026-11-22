/**
 * Sprint 893 (follow-up to CEO brief 15A): `apiDownload` resolves `{ ok: false }` on failure;
 * it does not throw. Callers that only handled success left the user with a button that reset
 * and no file. `deliverDownload` saves the file on success and shows an error toast otherwise.
 */
import type { ToastActions } from '@/contexts/ToastContext'
import { downloadBlob } from '@/utils'

export interface DownloadResult {
  ok: boolean
  blob?: Blob
  filename?: string
  error?: string
}

/** Message for an export that came back without a file (Sprint 890). */
export function exportFailureMessage(ok: boolean, error: string | undefined, what: string): string {
  if (!ok) return error || `Unable to generate ${what}. Please try again.`
  return `The server returned no file for the ${what}. Please try again.`
}

/** Save the file, or tell the user why there is none. Returns whether a file was saved. */
export function deliverDownload(
  result: DownloadResult,
  fallbackFilename: string,
  what: string,
  toast: Pick<ToastActions, 'error'>,
): boolean {
  if (result.ok && result.blob) {
    downloadBlob(result.blob, result.filename || fallbackFilename)
    return true
  }
  toast.error('Export failed', exportFailureMessage(result.ok, result.error, what))
  return false
}
