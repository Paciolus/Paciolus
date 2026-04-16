/**
 * Sprint 649 — export filename context.
 *
 * Builds `Paciolus_<Tool>[_<Client>]_<YYYYMMDD>.<ext>` so CPAs who run
 * multiple engagements in a day don't end up with ten identical
 * `Paciolus_Report.pdf` files in their Downloads folder.
 */

const SLUG_FALLBACK = 'Unknown'
const SLUG_MAX_LEN = 40

function slugify(value: string | null | undefined): string {
  if (!value) return ''
  const trimmed = value.trim()
  if (!trimmed) return ''
  const slug = trimmed
    .replace(/[^A-Za-z0-9\-_]+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
  if (!slug) return ''
  return slug.slice(0, SLUG_MAX_LEN)
}

function formatDate(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}${m}${d}`
}

export interface ExportFilenameInput {
  /** Tool identifier — e.g. "TB_Diagnostic", "AP_Testing". Required. */
  tool: string
  /** Client or engagement name — optional; omitted from filename when absent. */
  client?: string | null
  /** File extension without the leading dot. Defaults to "pdf". */
  extension?: string
  /** Override for deterministic testing. */
  date?: Date
}

export function buildExportFilename({
  tool,
  client,
  extension = 'pdf',
  date = new Date(),
}: ExportFilenameInput): string {
  const toolSlug = slugify(tool) || SLUG_FALLBACK
  const clientSlug = slugify(client)
  const ext = slugify(extension) || 'pdf'
  const parts = ['Paciolus', toolSlug]
  if (clientSlug) parts.push(clientSlug)
  parts.push(formatDate(date))
  return `${parts.join('_')}.${ext.toLowerCase()}`
}
