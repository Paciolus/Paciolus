/**
 * Upload limits and accepted file types — served by the backend.
 *
 * Sprint 890 (CEO brief 15B, review ST-05): the frontend kept its own extension
 * list, accept string, MIME list, label and a 50 MB limit, and always offered
 * ODS, while the backend enforces 100 MiB and turns ODS off by default. The
 * backend now serves its effective limits and enabled formats at
 * `GET /upload/capabilities` (backend/routes/upload_capabilities.py); file
 * pickers, client-side checks, labels and the too-large message are derived
 * from that response through `useUploadCapabilities()`.
 *
 * `DEFAULT_UPLOAD_CAPABILITIES` mirrors the backend's defaults and is used only
 * until the response arrives (or if it cannot be fetched).
 */
import defaultCapabilities from '@/content/upload-capabilities.default.json'

export interface UploadFormat {
  format: string
  label: string
  extensions: string[]
  mime_types: string[]
}

export interface UploadCapabilities {
  max_file_size_bytes: number
  max_file_size_mb: number
  max_rows: number
  bulk_max_files: number
  formats: UploadFormat[]
}

/**
 * The backend's own default response, written from `upload_capabilities()`;
 * backend/tests/test_sprint_890_upload_capabilities.py fails if it drifts.
 */
export const DEFAULT_UPLOAD_CAPABILITIES: UploadCapabilities = defaultCapabilities

/* ── current capabilities (a tiny store the hook and plain functions share) ── */

let current: UploadCapabilities = DEFAULT_UPLOAD_CAPABILITIES
const listeners = new Set<() => void>()

export function getUploadCapabilities(): UploadCapabilities {
  return current
}

export function setUploadCapabilities(next: UploadCapabilities): void {
  current = next
  listeners.forEach(l => l())
}

export function subscribeUploadCapabilities(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

/* ── derived values ── */

export function acceptedExtensions(caps: UploadCapabilities = current): string[] {
  return caps.formats.flatMap(f => f.extensions)
}

/** Value for an HTML `<input accept="">` attribute. */
export function acceptString(caps: UploadCapabilities = current): string {
  return acceptedExtensions(caps).join(',')
}

/** Human-readable list of enabled formats. */
export function formatsLabel(caps: UploadCapabilities = current): string {
  const labels = caps.formats.map(f => f.label)
  if (labels.length <= 1) return labels.join('')
  return `${labels.slice(0, -1).join(', ')} or ${labels[labels.length - 1]}`
}

/** "100 MB" — the per-file limit the backend enforces. */
export function sizeLimitLabel(caps: UploadCapabilities = current): string {
  return `${caps.max_file_size_mb} MB`
}

export function fileTooLargeMessage(caps: UploadCapabilities = current): string {
  return `File is too large. Maximum upload size is ${sizeLimitLabel(caps)}. Try splitting your data into smaller files.`
}

export function unsupportedFormatMessage(caps: UploadCapabilities = current): string {
  return `Unsupported file format. Please upload a ${formatsLabel(caps)} file.`
}

/** Whether a file has an enabled extension (browsers often misreport MIME types, so the extension decides). */
export function isAcceptedFileType(file: File, caps: UploadCapabilities = current): boolean {
  const dot = file.name.lastIndexOf('.')
  if (dot < 0) return false
  return acceptedExtensions(caps).includes(file.name.slice(dot).toLowerCase())
}

/* ── kept for existing imports: the defaults, as constants ── */

/** @deprecated Sprint 890 — use `useUploadCapabilities().accept`. */
export const ACCEPTED_FILE_EXTENSIONS_STRING = acceptString(DEFAULT_UPLOAD_CAPABILITIES)
/** @deprecated Sprint 890 — use `useUploadCapabilities()`. */
export const ACCEPTED_MIME_TYPES = DEFAULT_UPLOAD_CAPABILITIES.formats.flatMap(f => f.mime_types)
