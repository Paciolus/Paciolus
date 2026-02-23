/**
 * PDF Extraction Preview Types (Sprint 427)
 *
 * Types for the PDF quality gate preview flow.
 * Matches backend PdfPreviewResponse schema.
 */

export interface PdfPreviewResult {
  filename: string
  page_count: number
  tables_found: number
  extraction_confidence: number
  header_confidence: number
  numeric_density: number
  row_consistency: number
  column_names: string[]
  sample_rows: Record<string, string>[]
  remediation_hints: string[]
  passes_quality_gate: boolean
}
