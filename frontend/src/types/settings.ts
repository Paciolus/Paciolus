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

export interface PracticeSettings {
  default_materiality: MaterialityFormula;
  show_immaterial_by_default: boolean;
  default_fiscal_year_end: string;
  theme_preference: string;
  default_export_format: string;
  auto_save_summaries: boolean;
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
