/**
 * Bank Reconciliation Types (Sprint 78)
 *
 * Mirrors backend BankRecResult.to_dict() shape exactly.
 */

// =============================================================================
// ENUMS & CONSTANTS
// =============================================================================

export type MatchType = 'matched' | 'bank_only' | 'ledger_only'

export const MATCH_TYPE_LABELS: Record<MatchType, string> = {
  matched: 'Matched',
  bank_only: 'Bank Only',
  ledger_only: 'Ledger Only',
}

export const MATCH_TYPE_COLORS: Record<MatchType, string> = {
  matched: 'bg-sage-500/15 text-sage-300 border-sage-500/30',
  bank_only: 'bg-clay-500/15 text-clay-300 border-clay-500/30',
  ledger_only: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
}

export const MATCH_TYPE_BORDER_COLORS: Record<MatchType, string> = {
  matched: 'border-l-sage-500',
  bank_only: 'border-l-clay-500',
  ledger_only: 'border-l-oatmeal-500',
}

// =============================================================================
// TRANSACTION DATA
// =============================================================================

export interface BankTransactionData {
  date: string | null
  description: string
  amount: number
  reference: string | null
  row_number: number
}

export interface LedgerTransactionData {
  date: string | null
  description: string
  amount: number
  reference: string | null
  row_number: number
}

// =============================================================================
// MATCH DATA
// =============================================================================

export interface ReconciliationMatchData {
  bank_txn: BankTransactionData | null
  ledger_txn: LedgerTransactionData | null
  match_type: MatchType
  match_confidence: number
}

// =============================================================================
// SUMMARY
// =============================================================================

export interface ReconciliationSummaryData {
  matched_count: number
  matched_amount: number
  bank_only_count: number
  bank_only_amount: number
  ledger_only_count: number
  ledger_only_amount: number
  reconciling_difference: number
  total_bank: number
  total_ledger: number
  matches: ReconciliationMatchData[]
}

// =============================================================================
// COLUMN DETECTION
// =============================================================================

export interface BankColumnDetectionData {
  date_column: string | null
  amount_column: string | null
  description_column: string | null
  reference_column: string | null
  balance_column: string | null
  overall_confidence: number
  requires_mapping: boolean
  all_columns: string[]
  detection_notes: string[]
}

// =============================================================================
// TOP-LEVEL RESULT
// =============================================================================

export interface BankRecResult {
  summary: ReconciliationSummaryData
  bank_column_detection: BankColumnDetectionData
  ledger_column_detection: BankColumnDetectionData
}
