/**
 * Export Sharing Types — Sprint 545c
 *
 * Interfaces for export share links (Professional+ tier).
 */

export interface ExportShareInfo {
  token: string
  tool: string
  format: string
  created_at: string
  expires_at: string
  access_count: number
}
