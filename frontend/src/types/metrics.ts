/**
 * Paciolus Metric Metadata
 * Sprint 41: Centralized metric definitions
 *
 * Single source of truth for metric display names, formulas, and formatting.
 * Replaces scattered definitions in MetricCard, useTrends, and RollingWindowSection.
 */

/**
 * Complete metadata for a financial metric
 */
export interface MetricInfo {
  /** API key for this metric (e.g., 'current_ratio') */
  key: string;
  /** Human-readable display name (e.g., 'Current Ratio') */
  displayName: string;
  /** Formula for calculation */
  formula: string;
  /** Brief description of what the metric measures */
  description: string;
  /** IFRS/GAAP standards note (optional) */
  standardNote?: string;
  /** Prefix for displayed value (e.g., '$') */
  valuePrefix: string;
  /** Suffix for displayed value (e.g., '%', 'x') */
  valueSuffix: string;
  /** Whether higher values are generally better */
  higherIsBetter: boolean;
  /** Category of metric */
  category: 'liquidity' | 'leverage' | 'profitability' | 'efficiency' | 'category_total';
}

/**
 * Health status thresholds for a metric
 */
export interface MetricThresholds {
  /** Value at or above which metric is considered healthy */
  healthy: number;
  /** Value at or above which metric is considered warning (below healthy) */
  warning: number;
  /** Invert comparison for metrics where lower is better */
  invertComparison?: boolean;
}

// ============================================================================
// RATIO METRICS
// ============================================================================

export const RATIO_METRICS: Record<string, MetricInfo> = {
  // Liquidity Ratios
  current_ratio: {
    key: 'current_ratio',
    displayName: 'Current Ratio',
    formula: 'Current Assets ÷ Current Liabilities',
    description: 'Measures short-term liquidity and ability to pay debts within one year',
    standardNote: 'IFRS/GAAP: Both require current/non-current classification',
    valuePrefix: '',
    valueSuffix: 'x',
    higherIsBetter: true,
    category: 'liquidity',
  },
  quick_ratio: {
    key: 'quick_ratio',
    displayName: 'Quick Ratio',
    formula: '(Current Assets − Inventory) ÷ Current Liabilities',
    description: 'Acid-test ratio excluding inventory for stricter liquidity assessment',
    standardNote: 'Note: LIFO inventory (US GAAP only) may affect comparability with IFRS',
    valuePrefix: '',
    valueSuffix: 'x',
    higherIsBetter: true,
    category: 'liquidity',
  },

  // Leverage Ratios
  debt_to_equity: {
    key: 'debt_to_equity',
    displayName: 'Debt-to-Equity',
    formula: 'Total Liabilities ÷ Total Equity',
    description: 'Measures financial leverage and long-term solvency',
    standardNote: 'IFRS/GAAP: Equity composition may differ (redeemable preferred, revaluations)',
    valuePrefix: '',
    valueSuffix: 'x',
    higherIsBetter: false,
    category: 'leverage',
  },

  // Profitability Ratios
  gross_margin: {
    key: 'gross_margin',
    displayName: 'Gross Margin',
    formula: '(Revenue − COGS) ÷ Revenue × 100%',
    description: 'Profitability before operating expenses as percentage of revenue',
    standardNote: 'Revenue recognition converged (ASC 606/IFRS 15) since 2018',
    valuePrefix: '',
    valueSuffix: '%',
    higherIsBetter: true,
    category: 'profitability',
  },
  net_profit_margin: {
    key: 'net_profit_margin',
    displayName: 'Net Profit Margin',
    formula: '(Revenue − Total Expenses) ÷ Revenue × 100%',
    description: 'Bottom-line profitability after all expenses',
    standardNote: 'IFRS may capitalize R&D development costs, shifting expense timing',
    valuePrefix: '',
    valueSuffix: '%',
    higherIsBetter: true,
    category: 'profitability',
  },
  operating_margin: {
    key: 'operating_margin',
    displayName: 'Operating Margin',
    formula: '(Revenue − COGS − OpEx) ÷ Revenue × 100%',
    description: 'Profitability from core operations before interest and taxes',
    standardNote: 'Lease expense differs: single line (US GAAP) vs depreciation+interest (IFRS)',
    valuePrefix: '',
    valueSuffix: '%',
    higherIsBetter: true,
    category: 'profitability',
  },
  return_on_assets: {
    key: 'return_on_assets',
    displayName: 'Return on Assets',
    formula: 'Net Income ÷ Total Assets × 100%',
    description: 'Efficiency of asset utilization to generate earnings',
    standardNote: 'IFRS revaluations can inflate assets, reducing apparent ROA',
    valuePrefix: '',
    valueSuffix: '%',
    higherIsBetter: true,
    category: 'efficiency',
  },
  return_on_equity: {
    key: 'return_on_equity',
    displayName: 'Return on Equity',
    formula: 'Net Income ÷ Total Equity × 100%',
    description: 'Return generated on shareholder investment',
    standardNote: 'Revaluation surplus (IFRS) may inflate equity denominator',
    valuePrefix: '',
    valueSuffix: '%',
    higherIsBetter: true,
    category: 'efficiency',
  },
};

// ============================================================================
// CATEGORY TOTAL METRICS
// ============================================================================

export const CATEGORY_METRICS: Record<string, MetricInfo> = {
  total_assets: {
    key: 'total_assets',
    displayName: 'Total Assets',
    formula: 'Sum of all asset accounts',
    description: 'Total resources owned or controlled by the entity',
    valuePrefix: '$',
    valueSuffix: '',
    higherIsBetter: true,
    category: 'category_total',
  },
  total_liabilities: {
    key: 'total_liabilities',
    displayName: 'Total Liabilities',
    formula: 'Sum of all liability accounts',
    description: 'Total obligations owed to external parties',
    valuePrefix: '$',
    valueSuffix: '',
    higherIsBetter: false,
    category: 'category_total',
  },
  total_equity: {
    key: 'total_equity',
    displayName: 'Total Equity',
    formula: 'Total Assets − Total Liabilities',
    description: 'Residual interest in assets after deducting liabilities',
    valuePrefix: '$',
    valueSuffix: '',
    higherIsBetter: true,
    category: 'category_total',
  },
  total_revenue: {
    key: 'total_revenue',
    displayName: 'Total Revenue',
    formula: 'Sum of all revenue accounts',
    description: 'Total income from operations',
    valuePrefix: '$',
    valueSuffix: '',
    higherIsBetter: true,
    category: 'category_total',
  },
  total_expenses: {
    key: 'total_expenses',
    displayName: 'Total Expenses',
    formula: 'Sum of all expense accounts',
    description: 'Total costs incurred in operations',
    valuePrefix: '$',
    valueSuffix: '',
    higherIsBetter: false,
    category: 'category_total',
  },
  current_assets: {
    key: 'current_assets',
    displayName: 'Current Assets',
    formula: 'Sum of assets expected to convert to cash within one year',
    description: 'Short-term resources available for operations',
    valuePrefix: '$',
    valueSuffix: '',
    higherIsBetter: true,
    category: 'category_total',
  },
  current_liabilities: {
    key: 'current_liabilities',
    displayName: 'Current Liabilities',
    formula: 'Sum of obligations due within one year',
    description: 'Short-term obligations that must be settled soon',
    valuePrefix: '$',
    valueSuffix: '',
    higherIsBetter: false,
    category: 'category_total',
  },
};

// ============================================================================
// COMBINED METRICS
// ============================================================================

/**
 * All metrics combined for easy lookup
 */
export const ALL_METRICS: Record<string, MetricInfo> = {
  ...RATIO_METRICS,
  ...CATEGORY_METRICS,
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get metric info by key, falling back to a default if not found
 */
export function getMetricInfo(key: string): MetricInfo | undefined {
  return ALL_METRICS[key];
}

/**
 * Get display name for a metric key
 */
export function getMetricDisplayName(key: string): string {
  return ALL_METRICS[key]?.displayName || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Format a metric value for display
 */
export function formatMetricValue(key: string, value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }

  const metric = ALL_METRICS[key];
  if (!metric) {
    return value.toFixed(2);
  }

  const { valuePrefix, valueSuffix } = metric;

  // Format based on metric type
  if (valueSuffix === '%') {
    return `${valuePrefix}${value.toFixed(1)}${valueSuffix}`;
  } else if (valueSuffix === 'x') {
    return `${valuePrefix}${value.toFixed(2)}${valueSuffix}`;
  } else if (valuePrefix === '$') {
    return `${valuePrefix}${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}${valueSuffix}`;
  }

  return `${valuePrefix}${value.toFixed(2)}${valueSuffix}`;
}

/**
 * Check if a metric uses percentage format
 */
export function isPercentageMetric(key: string): boolean {
  return ALL_METRICS[key]?.valueSuffix === '%';
}

/**
 * Check if a metric uses currency format
 */
export function isCurrencyMetric(key: string): boolean {
  return ALL_METRICS[key]?.valuePrefix === '$';
}

/**
 * Get formula info for tooltip display (matching old RATIO_FORMULAS format)
 */
export function getRatioFormulaInfo(displayName: string): { formula: string; description: string; standardNote?: string } | undefined {
  // Find by display name (for backward compatibility with MetricCard)
  const metric = Object.values(RATIO_METRICS).find(m => m.displayName === displayName);
  if (!metric) return undefined;

  return {
    formula: metric.formula,
    description: metric.description,
    standardNote: metric.standardNote,
  };
}

// ============================================================================
// LEGACY COMPATIBILITY EXPORTS
// ============================================================================

/**
 * RATIO_FORMULAS for backward compatibility with MetricCard
 * Maps display name to formula info
 */
export const RATIO_FORMULAS: Record<string, { formula: string; description: string; standardNote?: string }> =
  Object.values(RATIO_METRICS).reduce((acc, metric) => {
    acc[metric.displayName] = {
      formula: metric.formula,
      description: metric.description,
      standardNote: metric.standardNote,
    };
    return acc;
  }, {} as Record<string, { formula: string; description: string; standardNote?: string }>);

/**
 * METRIC_DISPLAY_NAMES for backward compatibility with useTrends
 * Maps API key to display name
 */
export const METRIC_DISPLAY_NAMES: Record<string, string> =
  Object.entries(ALL_METRICS).reduce((acc, [key, metric]) => {
    acc[key] = metric.displayName;
    return acc;
  }, {} as Record<string, string>);

/**
 * Sets for checking metric types (for backward compatibility)
 */
export const PERCENTAGE_METRICS = new Set(
  Object.entries(ALL_METRICS)
    .filter(([, m]) => m.valueSuffix === '%')
    .map(([key]) => key)
);

export const CURRENCY_METRICS = new Set(
  Object.entries(ALL_METRICS)
    .filter(([, m]) => m.valuePrefix === '$')
    .map(([key]) => key)
);
