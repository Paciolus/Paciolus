/**
 * Prior Period Comparison Types - Sprint 51
 *
 * Types for prior period comparison functionality.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display types only, no data persistence
 * - Comparisons computed on-demand
 */

/**
 * Prior period summary for dropdown selection
 */
export interface PriorPeriodSummary {
  id: number
  period_label: string
  period_date: string | null
  period_type: string | null
  timestamp: string
  total_assets: number
  total_revenue: number
}

/**
 * Category variance data
 */
export interface CategoryVariance {
  category_key: string
  category_name: string
  current_value: number
  prior_value: number
  dollar_variance: number
  percent_variance: number | null
  is_significant: boolean
  direction: 'increase' | 'decrease' | 'unchanged'
}

/**
 * Ratio variance data
 */
export interface RatioVariance {
  ratio_key: string
  ratio_name: string
  current_value: number | null
  prior_value: number | null
  point_change: number | null
  is_significant: boolean
  direction: 'increase' | 'decrease' | 'unchanged'
  is_percentage: boolean
}

/**
 * Diagnostic variance data
 */
export interface DiagnosticVariance {
  metric_key: string
  metric_name: string
  current_value: number
  prior_value: number
  variance: number
  direction: 'increase' | 'decrease' | 'unchanged'
}

/**
 * Full period comparison result
 */
export interface PeriodComparison {
  current_period_label: string
  prior_period_label: string
  prior_period_id: number
  comparison_timestamp: string
  balance_sheet_variances: CategoryVariance[]
  income_statement_variances: CategoryVariance[]
  ratio_variances: RatioVariance[]
  diagnostic_variances: DiagnosticVariance[]
  significant_variance_count: number
  total_categories_compared: number
}

/**
 * Request to save a period
 */
export interface SavePeriodRequest {
  period_label: string
  period_date?: string
  period_type?: 'monthly' | 'quarterly' | 'annual'
  // Category totals
  total_assets: number
  current_assets: number
  inventory: number
  total_liabilities: number
  current_liabilities: number
  total_equity: number
  total_revenue: number
  cost_of_goods_sold: number
  total_expenses: number
  operating_expenses: number
  // Ratios
  current_ratio?: number | null
  quick_ratio?: number | null
  debt_to_equity?: number | null
  gross_margin?: number | null
  net_profit_margin?: number | null
  operating_margin?: number | null
  return_on_assets?: number | null
  return_on_equity?: number | null
  // Diagnostic metadata
  total_debits: number
  total_credits: number
  was_balanced: boolean
  anomaly_count: number
  materiality_threshold: number
  row_count: number
}

/**
 * Request to compare periods
 */
export interface CompareRequest {
  prior_period_id: number
  current_label: string
  // Current period data (same as SavePeriodRequest minus label/date/type)
  total_assets: number
  current_assets: number
  inventory: number
  total_liabilities: number
  current_liabilities: number
  total_equity: number
  total_revenue: number
  cost_of_goods_sold: number
  total_expenses: number
  operating_expenses: number
  current_ratio?: number | null
  quick_ratio?: number | null
  debt_to_equity?: number | null
  gross_margin?: number | null
  net_profit_margin?: number | null
  operating_margin?: number | null
  return_on_assets?: number | null
  return_on_equity?: number | null
  total_debits: number
  total_credits: number
  anomaly_count: number
  row_count: number
}

/**
 * Variance direction colors
 */
export const VARIANCE_COLORS = {
  increase: {
    text: 'text-sage-600',
    bg: 'bg-sage-50',
    border: 'border-sage-500/30',
    icon: '↑',
  },
  decrease: {
    text: 'text-clay-600',
    bg: 'bg-clay-50',
    border: 'border-clay-500/30',
    icon: '↓',
  },
  unchanged: {
    text: 'text-content-secondary',
    bg: 'bg-surface-card-secondary',
    border: 'border-theme',
    icon: '→',
  },
} as const

/**
 * Get variance color classes based on direction and significance
 */
export function getVarianceColors(direction: string, isSignificant: boolean = false) {
  const base = VARIANCE_COLORS[direction as keyof typeof VARIANCE_COLORS] || VARIANCE_COLORS.unchanged

  if (isSignificant) {
    return {
      ...base,
      text: direction === 'increase' ? 'text-sage-700 font-medium' : direction === 'decrease' ? 'text-clay-700 font-medium' : base.text,
    }
  }

  return base
}
