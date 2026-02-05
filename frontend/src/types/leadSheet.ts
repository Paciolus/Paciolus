/**
 * Lead Sheet Types - Sprint 50
 *
 * Types for lead sheet mapping and grouping in audit workpapers.
 * Lead sheets (A-Z) organize accounts by standard audit categories.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display types only, no data persistence
 * - Lead sheet assignments computed at audit time
 */

/**
 * Lead sheet letter codes (A-Z)
 */
export type LeadSheetCode =
  | 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'I' | 'J'
  | 'K' | 'L' | 'M' | 'N' | 'O' | 'P' | 'Q' | 'R' | 'S' | 'T'
  | 'U' | 'V' | 'W' | 'X' | 'Y' | 'Z'

/**
 * Lead sheet option for dropdowns
 */
export interface LeadSheetOption {
  letter: LeadSheetCode
  name: string
  category: string
  description: string
}

/**
 * Individual account assignment to a lead sheet
 */
export interface LeadSheetAccount {
  account: string
  lead_sheet: LeadSheetCode
  lead_sheet_name: string
  confidence: number
  match_reason: string
  debit: number
  credit: number
  category?: string
}

/**
 * Summary for a single lead sheet grouping
 */
export interface LeadSheetSummary {
  lead_sheet: LeadSheetCode
  lead_sheet_name: string
  category: string
  accounts: LeadSheetAccount[]
  total_debit: number
  total_credit: number
  net_balance: number
  account_count: number
}

/**
 * Complete lead sheet grouping result from audit
 */
export interface LeadSheetGrouping {
  summaries: LeadSheetSummary[]
  unmapped_count: number
  total_accounts: number
}

/**
 * Lead sheet display colors by category type
 */
export const LEAD_SHEET_COLORS: Record<string, {
  bg: string
  border: string
  text: string
  accent: string
}> = {
  asset: {
    bg: 'bg-sage-500/10',
    border: 'border-sage-500/30',
    text: 'text-sage-400',
    accent: 'bg-sage-500',
  },
  liability: {
    bg: 'bg-clay-500/10',
    border: 'border-clay-500/30',
    text: 'text-clay-400',
    accent: 'bg-clay-500',
  },
  equity: {
    bg: 'bg-oatmeal-500/10',
    border: 'border-oatmeal-500/30',
    text: 'text-oatmeal-300',
    accent: 'bg-oatmeal-500',
  },
  revenue: {
    bg: 'bg-sage-500/10',
    border: 'border-sage-500/30',
    text: 'text-sage-400',
    accent: 'bg-sage-500',
  },
  expense: {
    bg: 'bg-clay-500/10',
    border: 'border-clay-500/30',
    text: 'text-clay-400',
    accent: 'bg-clay-500',
  },
  other: {
    bg: 'bg-obsidian-700/50',
    border: 'border-obsidian-600',
    text: 'text-oatmeal-400',
    accent: 'bg-obsidian-600',
  },
}

/**
 * Get colors for a lead sheet based on its category
 */
export function getLeadSheetColors(category: string) {
  const normalized = category.toLowerCase()
  return LEAD_SHEET_COLORS[normalized] || LEAD_SHEET_COLORS.other
}
