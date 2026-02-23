/**
 * File Format Constants — Single source of truth for accepted file types.
 *
 * All file-upload components and validation logic should import from here
 * instead of hardcoding `.csv,.xlsx,.xls` strings.
 */

/** Accepted file extensions (with leading dot, lowercase). */
export const ACCEPTED_FILE_EXTENSIONS = ['.csv', '.xlsx', '.xls'] as const

/** Comma-separated string for HTML `<input accept="">` attributes. */
export const ACCEPTED_FILE_EXTENSIONS_STRING = '.csv,.xlsx,.xls'

/** Accepted MIME types (matches backend ALLOWED_CONTENT_TYPES). */
export const ACCEPTED_MIME_TYPES = [
  'text/csv',
  'application/csv',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/octet-stream',
] as const

/** Human-readable label for error messages and UI text. */
export const ACCEPTED_FORMATS_LABEL = 'CSV or Excel (.xlsx, .xls)'

/**
 * Check whether a File object has an accepted type.
 * Uses MIME type check with extension fallback (browsers often misreport MIME).
 */
export function isAcceptedFileType(file: File): boolean {
  const validTypes: readonly string[] = ACCEPTED_MIME_TYPES
  if (validTypes.includes(file.type)) return true
  const ext = file.name.toLowerCase().split('.').pop()
  return ext === 'csv' || ext === 'xlsx' || ext === 'xls'
}
