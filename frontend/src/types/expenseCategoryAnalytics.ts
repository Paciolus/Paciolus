/**
 * Expense Category Analytics Types
 * Sprint 289: Phase XXXIX — Expense Category Analytical Procedures
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
}

export interface ExpenseCategoryReport {
  categories: ExpenseCategoryItem[]
  total_expenses: number
  total_revenue: number
  revenue_available: boolean
  prior_available: boolean
  materiality_threshold: number
  category_count: number
}
