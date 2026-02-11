/**
 * Adjusting Entry Types - Sprint 52
 *
 * TypeScript interfaces for adjusting journal entries.
 * Supports GAAP/IFRS compliant adjusting entries workflow.
 */

/**
 * Types of adjusting entries per GAAP/IFRS.
 */
export type AdjustmentType =
  | 'accrual'
  | 'deferral'
  | 'estimate'
  | 'error_correction'
  | 'reclassification'
  | 'other'

/**
 * Status of an adjusting entry in the workflow.
 */
export type AdjustmentStatus = 'proposed' | 'approved' | 'rejected' | 'posted'

/**
 * Individual line in an adjusting journal entry.
 */
export interface AdjustmentLine {
  account_name: string
  debit: number
  credit: number
  description?: string
}

/**
 * Complete adjusting journal entry.
 */
export interface AdjustingEntry {
  id: string
  reference: string
  description: string
  adjustment_type: AdjustmentType
  status: AdjustmentStatus
  lines: AdjustmentLine[]
  total_debits: number
  total_credits: number
  is_balanced: boolean
  entry_total: number
  account_count: number
  prepared_by?: string
  reviewed_by?: string
  created_at: string
  updated_at?: string
  notes?: string
  is_reversing: boolean
}

/**
 * Request to create an adjusting entry.
 */
export interface AdjustingEntryRequest {
  reference: string
  description: string
  adjustment_type: AdjustmentType
  lines: AdjustmentLine[]
  notes?: string
  is_reversing?: boolean
}

/**
 * Request to update entry status.
 */
export interface AdjustmentStatusUpdate {
  status: AdjustmentStatus
  reviewed_by?: string
}

/**
 * Response from creating an entry.
 */
export interface CreateEntryResponse {
  success: boolean
  entry_id: string
  reference: string
  is_balanced: boolean
  total_amount: number
  status: AdjustmentStatus
}

/**
 * List response with entries and statistics.
 */
export interface AdjustmentListResponse {
  entries: AdjustingEntry[]
  total_adjustments: number
  proposed_count: number
  approved_count: number
  rejected_count: number
  posted_count: number
  total_adjustment_amount: number
}

/**
 * Account balance with adjustments applied.
 */
export interface AdjustedAccountBalance {
  account_name: string
  unadjusted_debit: number
  unadjusted_credit: number
  unadjusted_balance: number
  adjustment_debit: number
  adjustment_credit: number
  net_adjustment: number
  adjusted_debit: number
  adjusted_credit: number
  adjusted_balance: number
  has_adjustment: boolean
}

/**
 * Full adjusted trial balance response.
 */
export interface AdjustedTrialBalance {
  accounts: AdjustedAccountBalance[]
  adjustments_applied: string[]
  totals: {
    unadjusted_debits: number
    unadjusted_credits: number
    adjustment_debits: number
    adjustment_credits: number
    adjusted_debits: number
    adjusted_credits: number
  }
  is_balanced: boolean
  adjustment_count: number
  accounts_with_adjustments_count: number
  generated_at: string
}

/**
 * Request to apply adjustments to trial balance.
 */
export interface ApplyAdjustmentsRequest {
  trial_balance: Array<{
    account: string
    debit: number
    credit: number
  }>
  adjustment_ids: string[]
  include_proposed?: boolean
}

/**
 * Type option for dropdown.
 */
export interface AdjustmentTypeOption {
  value: AdjustmentType
  label: string
}

/**
 * Status option for dropdown.
 */
export interface AdjustmentStatusOption {
  value: AdjustmentStatus
  label: string
}

/**
 * Colors for adjustment status badges.
 */
export const ADJUSTMENT_STATUS_COLORS: Record<
  AdjustmentStatus,
  { bg: string; text: string; border: string }
> = {
  proposed: {
    bg: 'bg-oatmeal-200/20',
    text: 'text-oatmeal-300',
    border: 'border-oatmeal-300/30',
  },
  approved: {
    bg: 'bg-sage-500/20',
    text: 'text-sage-400',
    border: 'border-sage-500/30',
  },
  rejected: {
    bg: 'bg-clay-500/20',
    text: 'text-clay-400',
    border: 'border-clay-500/30',
  },
  posted: {
    bg: 'bg-sage-600/20',
    text: 'text-sage-300',
    border: 'border-sage-600/30',
  },
}

/**
 * Colors for adjustment types.
 */
export const ADJUSTMENT_TYPE_COLORS: Record<
  AdjustmentType,
  { bg: string; text: string }
> = {
  accrual: { bg: 'bg-sage-500/20', text: 'text-sage-400' },
  deferral: { bg: 'bg-sage-300/20', text: 'text-sage-300' },
  estimate: { bg: 'bg-oatmeal-600/20', text: 'text-oatmeal-500' },
  error_correction: { bg: 'bg-clay-500/20', text: 'text-clay-400' },
  reclassification: { bg: 'bg-obsidian-500/20', text: 'text-oatmeal-400' },
  other: { bg: 'bg-oatmeal-400/20', text: 'text-oatmeal-400' },
}

/**
 * Get human-readable label for adjustment type.
 */
export function getAdjustmentTypeLabel(type: AdjustmentType): string {
  const labels: Record<AdjustmentType, string> = {
    accrual: 'Accrual',
    deferral: 'Deferral',
    estimate: 'Estimate',
    error_correction: 'Error Correction',
    reclassification: 'Reclassification',
    other: 'Other',
  }
  return labels[type] || type
}

/**
 * Get human-readable label for adjustment status.
 */
export function getAdjustmentStatusLabel(status: AdjustmentStatus): string {
  const labels: Record<AdjustmentStatus, string> = {
    proposed: 'Proposed',
    approved: 'Approved',
    rejected: 'Rejected',
    posted: 'Posted',
  }
  return labels[status] || status
}

/**
 * Format currency amount.
 */
export function formatAmount(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount)
}

/**
 * Check if an adjustment line is valid.
 */
export function isValidLine(line: Partial<AdjustmentLine>): boolean {
  if (!line.account_name?.trim()) return false
  const hasDebit = (line.debit ?? 0) > 0
  const hasCredit = (line.credit ?? 0) > 0
  // Must have exactly one of debit or credit
  return (hasDebit || hasCredit) && !(hasDebit && hasCredit)
}

/**
 * Check if entry lines balance.
 */
export function linesBalance(lines: AdjustmentLine[]): boolean {
  const totalDebits = lines.reduce((sum, l) => sum + (l.debit || 0), 0)
  const totalCredits = lines.reduce((sum, l) => sum + (l.credit || 0), 0)
  return Math.abs(totalDebits - totalCredits) < 0.01
}

/**
 * Calculate totals for a set of lines.
 */
export function calculateLineTotals(lines: AdjustmentLine[]): {
  debits: number
  credits: number
  difference: number
  isBalanced: boolean
} {
  const debits = lines.reduce((sum, l) => sum + (l.debit || 0), 0)
  const credits = lines.reduce((sum, l) => sum + (l.credit || 0), 0)
  const difference = debits - credits
  return {
    debits,
    credits,
    difference,
    isBalanced: Math.abs(difference) < 0.01,
  }
}
