/**
 * Test Fixtures for Paciolus Frontend
 * Sprint 55: Frontend Test Foundation
 *
 * Sample data for testing components that display audit results,
 * ratios, anomalies, and other diagnostic information.
 */

/**
 * Sample ratio data for MetricCard and KeyMetricsSection tests
 */
export const sampleRatios = {
  current_ratio: {
    name: 'Current Ratio',
    value: 2.5,
    display_value: '2.50',
    is_calculable: true,
    interpretation: 'Healthy liquidity position',
    threshold_status: 'above_threshold' as const,
  },
  quick_ratio: {
    name: 'Quick Ratio',
    value: 1.8,
    display_value: '1.80',
    is_calculable: true,
    interpretation: 'Strong liquid asset coverage',
    threshold_status: 'above_threshold' as const,
  },
  debt_to_equity: {
    name: 'Debt to Equity',
    value: 0.75,
    display_value: '0.75',
    is_calculable: true,
    interpretation: 'Conservative leverage',
    threshold_status: 'above_threshold' as const,
  },
  gross_margin: {
    name: 'Gross Margin',
    value: 0.42,
    display_value: '42.00%',
    is_calculable: true,
    interpretation: 'Strong gross profit margin',
    threshold_status: 'above_threshold' as const,
  },
  net_profit_margin: {
    name: 'Net Profit Margin',
    value: 0.15,
    display_value: '15.00%',
    is_calculable: true,
    interpretation: 'Healthy net profitability',
    threshold_status: 'above_threshold' as const,
  },
  operating_margin: {
    name: 'Operating Margin',
    value: 0.20,
    display_value: '20.00%',
    is_calculable: true,
    interpretation: 'Strong operating efficiency',
    threshold_status: 'above_threshold' as const,
  },
  return_on_assets: {
    name: 'Return on Assets',
    value: 0.12,
    display_value: '12.00%',
    is_calculable: true,
    interpretation: 'Strong asset utilization',
    threshold_status: 'above_threshold' as const,
  },
  return_on_equity: {
    name: 'Return on Equity',
    value: 0.18,
    display_value: '18.00%',
    is_calculable: true,
    interpretation: 'Strong return to shareholders',
    threshold_status: 'above_threshold' as const,
  },
  dso: {
    name: 'Days Sales Outstanding',
    value: 35,
    display_value: '35 days',
    is_calculable: true,
    interpretation: 'Good collection efficiency',
    threshold_status: 'above_threshold' as const,
  },
}

/**
 * Sample analytics data for KeyMetricsSection tests
 */
export const sampleAnalytics = {
  ratios: sampleRatios,
  variances: {
    current_assets: {
      metric_name: 'Current Assets',
      current_value: 500000,
      previous_value: 450000,
      change_amount: 50000,
      change_percent: 11.1,
      direction: 'positive' as const,
      display_text: '+11.1%',
    },
    total_liabilities: {
      metric_name: 'Total Liabilities',
      current_value: 300000,
      previous_value: 280000,
      change_amount: 20000,
      change_percent: 7.1,
      direction: 'negative' as const,
      display_text: '+7.1%',
    },
  },
  has_previous_data: true,
  category_totals: {
    total_assets: 1000000,
    current_assets: 500000,
    total_liabilities: 400000,
    total_equity: 600000,
    total_revenue: 2000000,
  },
}

/**
 * Sample analytics without variance data
 */
export const sampleAnalyticsNoVariance = {
  ...sampleAnalytics,
  variances: {},
  has_previous_data: false,
}

/**
 * Sample audit result for export components
 */
export const sampleAuditResult = {
  status: 'completed',
  balanced: true,
  total_debits: 1500000,
  total_credits: 1500000,
  difference: 0,
  row_count: 150,
  message: 'Trial balance is balanced',
  abnormal_balances: [
    {
      account: 'Suspense Account',
      type: 'Liability',
      issue: 'Suspense account with balance',
      amount: 5000,
      materiality: 'material',
      confidence: 0.85,
      anomaly_type: 'suspense_account',
      severity: 'medium',
    },
    {
      account: 'Accounts Receivable',
      type: 'Asset',
      issue: 'Credit balance in asset account',
      amount: -2500,
      materiality: 'immaterial',
      confidence: 0.95,
      anomaly_type: 'abnormal_balance',
      severity: 'low',
    },
  ],
  has_risk_alerts: true,
  materiality_threshold: 10000,
  material_count: 1,
  immaterial_count: 1,
  classification_summary: {
    Asset: [{ account: 'Cash', confidence: 0.95 }],
    Liability: [{ account: 'Accounts Payable', confidence: 0.90 }],
  },
  risk_summary: {
    high_severity: 0,
    medium_severity: 1,
    low_severity: 1,
    suspense_account: 1,
    abnormal_balance: 1,
  },
}

/**
 * Sample warning ratio for testing concern states
 */
export const warningRatio = {
  name: 'Current Ratio',
  value: 0.8,
  display_value: '0.80',
  is_calculable: true,
  interpretation: 'Below healthy threshold',
  threshold_status: 'at_threshold' as const,
}

/**
 * Sample below-threshold ratio for testing critical states
 */
export const concernRatio = {
  name: 'Debt to Equity',
  value: 3.5,
  display_value: '3.50',
  is_calculable: true,
  interpretation: 'High leverage risk',
  threshold_status: 'below_threshold' as const,
}

/**
 * Sample uncalculable ratio
 */
export const uncalculableRatio = {
  name: 'Gross Margin',
  value: null,
  display_value: 'N/A',
  is_calculable: false,
  interpretation: 'Insufficient data for calculation',
  threshold_status: 'neutral' as const,
}
