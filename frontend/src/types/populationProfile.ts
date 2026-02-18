/**
 * Population Profile Types
 * Sprint 287: Phase XXXIX — TB Population Profile Report
 */

export interface BucketBreakdown {
  label: string
  lower: number
  upper: number | null
  count: number
  sum_abs: number
  percent_count: number
}

export interface TopAccount {
  rank: number
  account: string
  category: string
  net_balance: number
  abs_balance: number
  percent_of_total: number
}

export interface PopulationProfile {
  account_count: number
  total_abs_balance: number
  mean_abs_balance: number
  median_abs_balance: number
  std_dev_abs_balance: number
  min_abs_balance: number
  max_abs_balance: number
  p25: number
  p75: number
  gini_coefficient: number
  gini_interpretation: 'Low' | 'Moderate' | 'High' | 'Very High'
  buckets: BucketBreakdown[]
  top_accounts: TopAccount[]
}
