/**
 * Cash Flow Projector — Sprint 689g.
 */

export type ForecastFrequency = 'weekly' | 'biweekly' | 'monthly' | 'quarterly'

export interface AgingBucketsRequest {
  current: string
  days_1_30: string
  days_31_60: string
  days_61_90: string
  days_over_90: string
}

export interface RecurringFlowRequest {
  label: string
  amount: string
  frequency: ForecastFrequency
  first_date: string
}

export interface CashFlowProjectionRequest {
  opening_balance: string
  start_date: string
  ar_aging: AgingBucketsRequest
  ap_aging: AgingBucketsRequest
  recurring_flows: RecurringFlowRequest[]
  min_safe_cash?: string | null
}

export interface DailyPoint {
  day_index: number
  day_date: string
  ar_inflow: string
  ap_outflow: string
  recurring_net: string
  net_change: string
  ending_balance: string
}

export interface HorizonSummary {
  day: number
  cumulative_inflow: string
  cumulative_outflow: string
  ending_balance: string
  lowest_balance: string
  lowest_balance_day: number
}

export interface CollectionPriority {
  bucket: string
  amount_outstanding: string
  expected_collection: string
  collection_probability: string
  [key: string]: unknown
}

export interface ScenarioResult {
  scenario: string
  daily: DailyPoint[]
  horizon: Record<string, HorizonSummary>
  goes_negative: boolean
  first_negative_day: number | null
  breach_min_safe_cash: boolean
  collection_priorities: CollectionPriority[]
  ap_deferral_candidates: Record<string, unknown>[]
}

export interface CashFlowForecastResponse {
  inputs: Record<string, unknown>
  scenarios: Record<string, ScenarioResult>
  horizon_days: number[]
}
