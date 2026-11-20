/**
 * Expense Category Analytics Types
 */

export interface ExpenseCategoryItem {
  label: string
  key: string
  amount: number
  pct_of_revenue: number | null
  prior_amount: number | null
  prior_pct_of_revenue: number | null
  dollar_change: number | null
  exceeds_threshold: boolean
  benchmark_pct: number | null
  /** Sprint 887: % change vs prior (null when prior is zero or absent) and its change band. */
  pct_change?: number | null
  change_band?: ExpenseChangeBand | null
}

export type ExpenseChangeBand = 'both' | 'either' | 'neither'

/** Sprint 887: the thresholds behind the change band (Paciolus defaults + the run's materiality). */
export interface ExpenseChangeThresholds {
  pct_both: number
  pct_either: number
  materiality: number
}

/** Same labels as the CSV and the memo (backend CHANGE_BAND_LABELS). */
export function changeBandLabel(band: ExpenseChangeBand, t: ExpenseChangeThresholds): string {
  if (band === 'both') return `Change \u2265 ${t.pct_both}% and over materiality`
  if (band === 'either') return `Change \u2265 ${t.pct_either}% or over materiality`
  return `Change < ${t.pct_either}% and within materiality`
}

export interface ExpenseCategoryReport {
  categories: ExpenseCategoryItem[]
  total_expenses: number
  total_revenue: number
  revenue_available: boolean
  prior_available: boolean
  materiality_threshold: number
  category_count: number
  change_thresholds?: ExpenseChangeThresholds | null
}
