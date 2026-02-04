/**
 * Settings Types
 * Sprint 21: Customization & Practice Settings
 *
 * Type definitions for practice and client settings.
 */

export type MaterialityFormulaType =
  | 'fixed'
  | 'percentage_of_revenue'
  | 'percentage_of_assets'
  | 'percentage_of_equity';

export interface MaterialityFormula {
  type: MaterialityFormulaType;
  value: number;
  min_threshold?: number | null;
  max_threshold?: number | null;
}

// Sprint 32: Account type weights for weighted materiality
export type AccountCategory = 'asset' | 'liability' | 'equity' | 'revenue' | 'expense' | 'unknown';

export interface WeightedMaterialityConfig {
  account_weights: Record<AccountCategory, number>;
  balance_sheet_weight: number;
  income_statement_weight: number;
  enabled: boolean;
}

// Default account weights (matches backend)
export const DEFAULT_ACCOUNT_WEIGHTS: Record<AccountCategory, number> = {
  asset: 1.0,
  liability: 1.2,
  equity: 1.5,
  revenue: 1.3,
  expense: 0.8,
  unknown: 1.0,
};

// Display labels for account categories
export const ACCOUNT_CATEGORY_LABELS: Record<AccountCategory, string> = {
  asset: 'Assets',
  liability: 'Liabilities',
  equity: 'Equity',
  revenue: 'Revenue',
  expense: 'Expenses',
  unknown: 'Unknown',
};

// Weight descriptions for user education
export const WEIGHT_DESCRIPTIONS: Record<AccountCategory, string> = {
  asset: 'Cash, receivables, inventory, fixed assets',
  liability: 'Payables, loans, accrued expenses',
  equity: 'Capital, retained earnings, distributions',
  revenue: 'Sales, service income, interest income',
  expense: 'Cost of goods, operating expenses',
  unknown: 'Accounts not yet classified',
};

export interface PracticeSettings {
  default_materiality: MaterialityFormula;
  show_immaterial_by_default: boolean;
  default_fiscal_year_end: string;
  theme_preference: string;
  default_export_format: string;
  auto_save_summaries: boolean;
  // Sprint 32: Weighted materiality configuration
  weighted_materiality?: WeightedMaterialityConfig;
}

export interface ClientSettings {
  materiality_override: MaterialityFormula | null;
  notes: string;
  industry_multiplier: number;
  diagnostic_frequency: string;
}

export interface MaterialityPreview {
  threshold: number;
  formula_display: string;
  explanation: string;
  formula: MaterialityFormula;
}

export interface ResolvedMateriality {
  formula: MaterialityFormula;
  formula_display: string;
  session_override: number | null;
  source: 'session' | 'client' | 'practice';
}

// Display labels for formula types
export const FORMULA_TYPE_LABELS: Record<MaterialityFormulaType, string> = {
  fixed: 'Fixed Amount',
  percentage_of_revenue: '% of Revenue',
  percentage_of_assets: '% of Total Assets',
  percentage_of_equity: '% of Total Equity',
};

// Display labels for diagnostic frequency
export const FREQUENCY_LABELS: Record<string, string> = {
  weekly: 'Weekly',
  monthly: 'Monthly',
  quarterly: 'Quarterly',
  annually: 'Annually',
};

// Default formula
export const DEFAULT_MATERIALITY_FORMULA: MaterialityFormula = {
  type: 'fixed',
  value: 500,
  min_threshold: null,
  max_threshold: null,
};

// Sprint 32: Default weighted materiality config
export const DEFAULT_WEIGHTED_MATERIALITY: WeightedMaterialityConfig = {
  account_weights: DEFAULT_ACCOUNT_WEIGHTS,
  balance_sheet_weight: 1.0,
  income_statement_weight: 0.9,
  enabled: false,
};

// Sprint 32: Weighted preview response
export interface WeightedMaterialityPreview {
  base_threshold: number;
  weighted_enabled: boolean;
  thresholds_by_category: Record<AccountCategory, number>;
  formula: MaterialityFormula;
  weighted_config: WeightedMaterialityConfig | null;
}
