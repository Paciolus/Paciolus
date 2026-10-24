/**
 * Bank Reconciliation Types (Sprint 78)
 *
 * Mirrors backend BankRecResult.to_dict() shape exactly.
 */

// =============================================================================
// ENUMS & CONSTANTS
// =============================================================================

export type MatchType = 'matched' | 'bank_only' | 'ledger_only' | 'split'

export const MATCH_TYPE_LABELS: Record<MatchType, string> = {
  matched: 'Matched',
  bank_only: 'Bank Only',
  ledger_only: 'Ledger Only',
  split: 'Split Match',
}

export const MATCH_TYPE_COLORS: Record<MatchType, string> = {
  matched: 'bg-sage-50 text-sage-700 border-sage-200',
  bank_only: 'bg-clay-50 text-clay-700 border-clay-200',
  ledger_only: 'bg-oatmeal-100 text-obsidian-500 border-oatmeal-300',
  split: 'bg-sage-50 text-sage-700 border-sage-200',
}

export const MATCH_TYPE_BORDER_COLORS: Record<MatchType, string> = {
  matched: 'border-l-sage-500',
  bank_only: 'border-l-clay-500',
  ledger_only: 'border-l-oatmeal-500',
  split: 'border-l-sage-500',
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

/** Discriminated union by match_type — Sprint 226
 *  - 'matched': both transactions present
 *  - 'bank_only': bank transaction only (outstanding item)
 *  - 'ledger_only': ledger transaction only (in-transit item)
 *  - 'split': one bank transaction matched to 2–4 ledger transactions
 *    (Sprint 639; surfaced by the API from Sprint 833). `ledger_txn` is the
 *    first piece, `ledger_txns` all of them.
 *  `split_search_limited` (Sprint 833) marks a bank_only item whose split
 *  search hit the candidate cap — it stays an open reconciling item.
 */
export type ReconciliationMatchData =
  | { match_type: 'matched'; bank_txn: BankTransactionData; ledger_txn: LedgerTransactionData; match_confidence: number; ledger_txns?: null; split_search_limited?: null }
  | { match_type: 'bank_only'; bank_txn: BankTransactionData; ledger_txn?: never; match_confidence: number; ledger_txns?: null; split_search_limited?: boolean | null }
  | { match_type: 'ledger_only'; bank_txn?: never; ledger_txn: LedgerTransactionData; match_confidence: number; ledger_txns?: null; split_search_limited?: null }
  | { match_type: 'split'; bank_txn: BankTransactionData; ledger_txn: LedgerTransactionData; ledger_txns: LedgerTransactionData[]; match_confidence: number; split_search_limited?: null }

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

/** Sprint 833: bounds the split-match search ran under (a Paciolus convention). */
export interface SplitSearchDisclosure {
  date_window_days: number
  max_candidates: number
  max_set_size: number
  /** Open bank items whose split search hit the candidate cap. */
  limited_count: number
  note: string
}

/**
 * Sprint 838: a proposed JE for an unmatched bank-only item (engine since
 * Sprint 639; returned by the API since Sprint 838). Generic accounts --
 * the practitioner maps and posts. No UI renders these yet.
 */
export interface SuggestedJournalEntry {
  bank_txn: BankTransactionData
  kind: 'bank_fee' | 'interest_income' | 'interest_expense' | 'nsf_charge' | 'wire_fee' | 'service_charge' | 'overdraft' | 'other'
  debit_account: string
  credit_account: string
  amount: number
  description: string
  confidence: number
}

/** Where a threshold came from: supplied for this run ('caller') or the Paciolus default. */
export type ThresholdSource = 'caller' | 'default'

/**
 * Sprint 763 / 839: the thresholds the engine applied. Monetary values are
 * strings (Decimal precision). `threshold_sources` (Sprint 839) says per
 * threshold whether this run supplied it; `materiality_source` is 'caller'
 * when either was supplied.
 */
export interface BankRecActiveThresholds {
  materiality: string
  performance_materiality: string
  amount_tolerance: string
  date_tolerance_days: number
  split_match_max_candidates?: number
  materiality_source: ThresholdSource
  threshold_sources?: {
    materiality: ThresholdSource
    performance_materiality: ThresholdSource
  }
}

export interface BankRecResult {
  summary: ReconciliationSummaryData
  bank_column_detection: BankColumnDetectionData
  ledger_column_detection: BankColumnDetectionData
  split_search?: SplitSearchDisclosure | null
  suggested_journal_entries?: SuggestedJournalEntry[] | null
  active_thresholds?: BankRecActiveThresholds | null
}
