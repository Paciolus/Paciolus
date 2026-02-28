/**
 * Demo Data - Sprint 60: Homepage Demo Mode
 *
 * Hardcoded synthetic data for "Acme Manufacturing Corp" demo.
 * Renders existing UI components in read-only demo mode for guests.
 * No API calls, no storage - pure static showcase.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - All data is hardcoded constants (no user data)
 * - Used for display purposes only
 */

import type { BenchmarkComparisonResponse } from '@/hooks/useBenchmarks'
import type { LeadSheetGrouping } from '@/types/leadSheet'
import type { Analytics, AbnormalBalanceExtended, RiskSummary } from '@/types/mapping'

// =============================================================================
// DEMO FILENAME
// =============================================================================

export const DEMO_FILENAME = 'Acme_Manufacturing_Corp_TB_2025.csv'

// =============================================================================
// AUDIT RESULT
// =============================================================================

export const DEMO_ABNORMAL_BALANCES: AbnormalBalanceExtended[] = [
  {
    account: 'Clearing Account - Intercompany',
    type: 'Liability',
    issue: 'Suspense/clearing account with outstanding balance of $47,200. These accounts should be cleared at period end.',
    amount: 47200,
    debit: 0,
    credit: 47200,
    materiality: 'material' as const,
    category: 'liability',
    confidence: 0.88,
    matched_keywords: ['clearing', 'intercompany'],
    requires_review: true,
    anomaly_type: 'natural_balance_violation' as const,
    severity: 'high' as const,
  },
  {
    account: 'Raw Materials Inventory',
    type: 'Asset',
    issue: 'Concentration risk: Raw Materials Inventory represents 38% of total assets ($1,976,000 of $5,200,000). Consider diversification.',
    amount: 1976000,
    debit: 1976000,
    credit: 0,
    materiality: 'material' as const,
    category: 'asset',
    confidence: 0.92,
    matched_keywords: ['inventory', 'raw materials'],
    requires_review: true,
    anomaly_type: 'natural_balance_violation' as const,
    severity: 'high' as const,
  },
  {
    account: 'Miscellaneous Expense',
    type: 'Expense',
    issue: 'Rounding anomaly: Expense of exactly $50,000.00 detected. Round amounts may indicate estimates rather than actual transactions.',
    amount: 50000,
    debit: 50000,
    credit: 0,
    materiality: 'immaterial' as const,
    category: 'expense',
    confidence: 0.72,
    matched_keywords: ['miscellaneous'],
    requires_review: false,
    anomaly_type: 'natural_balance_violation' as const,
    severity: 'low' as const,
  },
]

export const DEMO_RISK_SUMMARY: RiskSummary = {
  total_anomalies: 3,
  high_severity: 2,
  medium_severity: 0,
  low_severity: 1,
  anomaly_types: {
    natural_balance_violation: 3,
  },
}

export const DEMO_AUDIT_RESULT = {
  status: 'success',
  balanced: true,
  total_debits: 5200000,
  total_credits: 5200000,
  difference: 0,
  row_count: 42,
  message: 'Trial balance is balanced',
  abnormal_balances: DEMO_ABNORMAL_BALANCES,
  has_risk_alerts: true,
  materiality_threshold: 52000,
  material_count: 2,
  immaterial_count: 1,
  classification_summary: {
    high: 0,
    medium: 2,
    low: 1,
    unknown: 0,
  },
  risk_summary: DEMO_RISK_SUMMARY,
}

// =============================================================================
// ANALYTICS (9 Ratios - Manufacturing Values)
// =============================================================================

export const DEMO_ANALYTICS: Analytics = {
  ratios: {
    current_ratio: {
      name: 'Current Ratio',
      value: 1.85,
      display_value: '1.85',
      is_calculable: true,
      interpretation: 'Adequate short-term liquidity',
      threshold_status: 'above_threshold',
    },
    quick_ratio: {
      name: 'Quick Ratio',
      value: 0.92,
      display_value: '0.92',
      is_calculable: true,
      interpretation: 'Moderate liquid asset coverage (inventory-heavy)',
      threshold_status: 'at_threshold',
    },
    debt_to_equity: {
      name: 'Debt to Equity',
      value: 1.15,
      display_value: '1.15',
      is_calculable: true,
      interpretation: 'Moderate leverage for manufacturing',
      threshold_status: 'above_threshold',
    },
    gross_margin: {
      name: 'Gross Margin',
      value: 0.34,
      display_value: '34.00%',
      is_calculable: true,
      interpretation: 'Typical manufacturing gross margin',
      threshold_status: 'above_threshold',
    },
    net_profit_margin: {
      name: 'Net Profit Margin',
      value: 0.08,
      display_value: '8.00%',
      is_calculable: true,
      interpretation: 'Reasonable net profitability',
      threshold_status: 'above_threshold',
    },
    operating_margin: {
      name: 'Operating Margin',
      value: 0.12,
      display_value: '12.00%',
      is_calculable: true,
      interpretation: 'Solid operating efficiency',
      threshold_status: 'above_threshold',
    },
    return_on_assets: {
      name: 'Return on Assets',
      value: 0.07,
      display_value: '7.00%',
      is_calculable: true,
      interpretation: 'Average asset utilization for capital-intensive industry',
      threshold_status: 'at_threshold',
    },
    return_on_equity: {
      name: 'Return on Equity',
      value: 0.15,
      display_value: '15.00%',
      is_calculable: true,
      interpretation: 'Good return to shareholders',
      threshold_status: 'above_threshold',
    },
    // DSO is indexed dynamically via [key] access
  } as Analytics['ratios'] & Record<string, unknown>,
  variances: {},
  has_previous_data: false,
  category_totals: {
    total_assets: 5200000,
    current_assets: 3120000,
    total_liabilities: 2780000,
    total_equity: 2420000,
    total_revenue: 4680000,
  },
}

// Add DSO via dynamic key (not in strict Analytics type but used by KeyMetricsSection)
;(DEMO_ANALYTICS.ratios as Record<string, unknown>)['dso'] = {
  name: 'Days Sales Outstanding',
  value: 42,
  display_value: '42 days',
  is_calculable: true,
  interpretation: 'Good collection efficiency for manufacturing',
  threshold_status: 'above_threshold',
}

// =============================================================================
// LEAD SHEET GROUPING (8 Lead Sheets)
// =============================================================================

export const DEMO_LEAD_SHEETS: LeadSheetGrouping = {
  summaries: [
    {
      lead_sheet: 'A',
      lead_sheet_name: 'Cash & Cash Equivalents',
      category: 'asset',
      accounts: [
        { account: 'Cash - Operating', lead_sheet: 'A', lead_sheet_name: 'Cash & Cash Equivalents', confidence: 0.95, match_reason: 'Keyword: cash', debit: 284000, credit: 0, category: 'asset' },
        { account: 'Petty Cash', lead_sheet: 'A', lead_sheet_name: 'Cash & Cash Equivalents', confidence: 0.90, match_reason: 'Keyword: petty cash', debit: 2000, credit: 0, category: 'asset' },
        { account: 'Money Market Account', lead_sheet: 'A', lead_sheet_name: 'Cash & Cash Equivalents', confidence: 0.85, match_reason: 'Keyword: money market', debit: 150000, credit: 0, category: 'asset' },
      ],
      total_debit: 436000,
      total_credit: 0,
      net_balance: 436000,
      account_count: 3,
    },
    {
      lead_sheet: 'B',
      lead_sheet_name: 'Receivables',
      category: 'asset',
      accounts: [
        { account: 'Accounts Receivable - Trade', lead_sheet: 'B', lead_sheet_name: 'Receivables', confidence: 0.95, match_reason: 'Keyword: accounts receivable', debit: 538000, credit: 0, category: 'asset' },
        { account: 'Allowance for Doubtful Accounts', lead_sheet: 'B', lead_sheet_name: 'Receivables', confidence: 0.88, match_reason: 'Keyword: allowance', debit: 0, credit: 27000, category: 'asset' },
      ],
      total_debit: 538000,
      total_credit: 27000,
      net_balance: 511000,
      account_count: 2,
    },
    {
      lead_sheet: 'C',
      lead_sheet_name: 'Inventory',
      category: 'asset',
      accounts: [
        { account: 'Raw Materials Inventory', lead_sheet: 'C', lead_sheet_name: 'Inventory', confidence: 0.95, match_reason: 'Keyword: inventory', debit: 1976000, credit: 0, category: 'asset' },
        { account: 'Work in Process', lead_sheet: 'C', lead_sheet_name: 'Inventory', confidence: 0.90, match_reason: 'Keyword: work in process', debit: 324000, credit: 0, category: 'asset' },
        { account: 'Finished Goods', lead_sheet: 'C', lead_sheet_name: 'Inventory', confidence: 0.85, match_reason: 'Keyword: finished goods', debit: 418000, credit: 0, category: 'asset' },
      ],
      total_debit: 2718000,
      total_credit: 0,
      net_balance: 2718000,
      account_count: 3,
    },
    {
      lead_sheet: 'E',
      lead_sheet_name: 'Fixed Assets',
      category: 'asset',
      accounts: [
        { account: 'Machinery & Equipment', lead_sheet: 'E', lead_sheet_name: 'Fixed Assets', confidence: 0.92, match_reason: 'Keyword: machinery', debit: 1850000, credit: 0, category: 'asset' },
        { account: 'Accumulated Depreciation - M&E', lead_sheet: 'E', lead_sheet_name: 'Fixed Assets', confidence: 0.90, match_reason: 'Keyword: accumulated depreciation', debit: 0, credit: 620000, category: 'asset' },
        { account: 'Building', lead_sheet: 'E', lead_sheet_name: 'Fixed Assets', confidence: 0.88, match_reason: 'Keyword: building', debit: 950000, credit: 0, category: 'asset' },
        { account: 'Accumulated Depreciation - Building', lead_sheet: 'E', lead_sheet_name: 'Fixed Assets', confidence: 0.88, match_reason: 'Keyword: accumulated depreciation', debit: 0, credit: 190000, category: 'asset' },
      ],
      total_debit: 2800000,
      total_credit: 810000,
      net_balance: 1990000,
      account_count: 4,
    },
    {
      lead_sheet: 'G',
      lead_sheet_name: 'Payables',
      category: 'liability',
      accounts: [
        { account: 'Accounts Payable - Trade', lead_sheet: 'G', lead_sheet_name: 'Payables', confidence: 0.95, match_reason: 'Keyword: accounts payable', debit: 0, credit: 892000, category: 'liability' },
        { account: 'Accrued Expenses', lead_sheet: 'G', lead_sheet_name: 'Payables', confidence: 0.88, match_reason: 'Keyword: accrued', debit: 0, credit: 156000, category: 'liability' },
        { account: 'Clearing Account - Intercompany', lead_sheet: 'G', lead_sheet_name: 'Payables', confidence: 0.72, match_reason: 'Category fallback: liability', debit: 0, credit: 47200, category: 'liability' },
      ],
      total_debit: 0,
      total_credit: 1095200,
      net_balance: -1095200,
      account_count: 3,
    },
    {
      lead_sheet: 'K',
      lead_sheet_name: 'Equity',
      category: 'equity',
      accounts: [
        { account: 'Common Stock', lead_sheet: 'K', lead_sheet_name: 'Equity', confidence: 0.95, match_reason: 'Keyword: common stock', debit: 0, credit: 1000000, category: 'equity' },
        { account: 'Retained Earnings', lead_sheet: 'K', lead_sheet_name: 'Equity', confidence: 0.95, match_reason: 'Keyword: retained earnings', debit: 0, credit: 1420000, category: 'equity' },
      ],
      total_debit: 0,
      total_credit: 2420000,
      net_balance: -2420000,
      account_count: 2,
    },
    {
      lead_sheet: 'L',
      lead_sheet_name: 'Revenue',
      category: 'revenue',
      accounts: [
        { account: 'Product Sales', lead_sheet: 'L', lead_sheet_name: 'Revenue', confidence: 0.90, match_reason: 'Keyword: sales', debit: 0, credit: 4200000, category: 'revenue' },
        { account: 'Service Revenue', lead_sheet: 'L', lead_sheet_name: 'Revenue', confidence: 0.92, match_reason: 'Keyword: service revenue', debit: 0, credit: 480000, category: 'revenue' },
      ],
      total_debit: 0,
      total_credit: 4680000,
      net_balance: -4680000,
      account_count: 2,
    },
    {
      lead_sheet: 'M',
      lead_sheet_name: 'Cost of Goods Sold',
      category: 'expense',
      accounts: [
        { account: 'Direct Materials', lead_sheet: 'M', lead_sheet_name: 'Cost of Goods Sold', confidence: 0.90, match_reason: 'Keyword: direct materials', debit: 1820000, credit: 0, category: 'expense' },
        { account: 'Direct Labor', lead_sheet: 'M', lead_sheet_name: 'Cost of Goods Sold', confidence: 0.90, match_reason: 'Keyword: direct labor', debit: 980000, credit: 0, category: 'expense' },
        { account: 'Manufacturing Overhead', lead_sheet: 'M', lead_sheet_name: 'Cost of Goods Sold', confidence: 0.85, match_reason: 'Keyword: manufacturing overhead', debit: 288800, credit: 0, category: 'expense' },
      ],
      total_debit: 3088800,
      total_credit: 0,
      net_balance: 3088800,
      account_count: 3,
    },
  ],
  unmapped_count: 0,
  total_accounts: 42,
}

// =============================================================================
// BENCHMARK COMPARISON (Manufacturing Industry, Score 72)
// =============================================================================

export const DEMO_BENCHMARKS: BenchmarkComparisonResponse = {
  industry: 'manufacturing',
  fiscal_year: 2025,
  comparisons: [
    {
      ratio_name: 'current_ratio',
      client_value: 1.85,
      percentile: 58,
      percentile_label: '58th percentile',
      vs_median: 0.05,
      vs_mean: -0.02,
      position: 'average',
      interpretation: 'Current ratio is at the industry median for manufacturing companies.',
      health_indicator: 'neutral',
      benchmark_median: 1.80,
      benchmark_mean: 1.87,
    },
    {
      ratio_name: 'quick_ratio',
      client_value: 0.92,
      percentile: 45,
      percentile_label: '45th percentile',
      vs_median: -0.08,
      vs_mean: -0.13,
      position: 'below_average',
      interpretation: 'Quick ratio is slightly below industry median. Typical for inventory-heavy manufacturers.',
      health_indicator: 'neutral',
      benchmark_median: 1.00,
      benchmark_mean: 1.05,
    },
    {
      ratio_name: 'debt_to_equity',
      client_value: 1.15,
      percentile: 52,
      percentile_label: '52nd percentile',
      vs_median: 0.05,
      vs_mean: 0.02,
      position: 'average',
      interpretation: 'Leverage is in line with manufacturing industry norms.',
      health_indicator: 'neutral',
      benchmark_median: 1.10,
      benchmark_mean: 1.13,
    },
    {
      ratio_name: 'gross_margin',
      client_value: 0.34,
      percentile: 65,
      percentile_label: '65th percentile',
      vs_median: 0.04,
      vs_mean: 0.03,
      position: 'above_average',
      interpretation: 'Gross margin exceeds the manufacturing industry median, indicating strong cost control.',
      health_indicator: 'positive',
      benchmark_median: 0.30,
      benchmark_mean: 0.31,
    },
    {
      ratio_name: 'net_profit_margin',
      client_value: 0.08,
      percentile: 70,
      percentile_label: '70th percentile',
      vs_median: 0.02,
      vs_mean: 0.01,
      position: 'above_average',
      interpretation: 'Net profitability is above the manufacturing industry median.',
      health_indicator: 'positive',
      benchmark_median: 0.06,
      benchmark_mean: 0.07,
    },
    {
      ratio_name: 'operating_margin',
      client_value: 0.12,
      percentile: 72,
      percentile_label: '72nd percentile',
      vs_median: 0.03,
      vs_mean: 0.02,
      position: 'above_average',
      interpretation: 'Operating efficiency is strong relative to manufacturing peers.',
      health_indicator: 'positive',
      benchmark_median: 0.09,
      benchmark_mean: 0.10,
    },
    {
      ratio_name: 'return_on_assets',
      client_value: 0.07,
      percentile: 55,
      percentile_label: '55th percentile',
      vs_median: 0.01,
      vs_mean: 0.00,
      position: 'average',
      interpretation: 'Asset returns are at the manufacturing industry average. Capital-intensive operations are typical.',
      health_indicator: 'neutral',
      benchmark_median: 0.06,
      benchmark_mean: 0.07,
    },
    {
      ratio_name: 'return_on_equity',
      client_value: 0.15,
      percentile: 68,
      percentile_label: '68th percentile',
      vs_median: 0.03,
      vs_mean: 0.02,
      position: 'above_average',
      interpretation: 'Strong shareholder returns, above the manufacturing industry median.',
      health_indicator: 'positive',
      benchmark_median: 0.12,
      benchmark_mean: 0.13,
    },
    {
      ratio_name: 'dso',
      client_value: 42,
      percentile: 60,
      percentile_label: '60th percentile',
      vs_median: -3,
      vs_mean: -2,
      position: 'above_average',
      interpretation: 'Collection efficiency is above average for manufacturing. Lower DSO is better.',
      health_indicator: 'positive',
      benchmark_median: 45,
      benchmark_mean: 44,
    },
  ],
  overall_score: 72,
  overall_health: 'mid_range',
  source_attribution: 'Demo data based on manufacturing industry benchmarks (RMA, SEC EDGAR)',
  generated_at: '2025-12-31T00:00:00Z',
  disclaimer: 'This is sample demo data for illustration purposes only. Actual benchmark comparisons use aggregated industry data from RMA Annual Statement Studies and SEC EDGAR filings.',
}
