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
  // Sprint 68: JE Testing thresholds
  je_testing_config?: JETestingConfig;
  // Sprint 76: AP Testing thresholds
  ap_testing_config?: APTestingConfig;
  // Sprint 88: Payroll Testing thresholds
  payroll_testing_config?: PayrollTestingConfig;
  // Sprint 94: Three-Way Match thresholds
  three_way_match_config?: ThreeWayMatchConfig;
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

// Sprint 68: JE Testing Config
export type JETestingPreset = 'conservative' | 'standard' | 'permissive' | 'custom';

export interface JETestingConfig {
  // T1
  balance_tolerance: number;
  // T4
  round_amount_threshold: number;
  round_amount_max_flags: number;
  // T5
  unusual_amount_stddev: number;
  unusual_amount_min_entries: number;
  // T6
  benford_min_entries: number;
  // T7
  weekend_posting_enabled: boolean;
  weekend_large_amount_threshold: number;
  // T8
  month_end_days: number;
  month_end_volume_multiplier: number;
  // T9
  single_user_volume_pct: number;
  single_user_max_flags: number;
  // T10
  after_hours_enabled: boolean;
  after_hours_start: number;
  after_hours_end: number;
  after_hours_large_threshold: number;
  // T11
  numbering_gap_enabled: boolean;
  numbering_gap_min_size: number;
  // T12
  backdate_enabled: boolean;
  backdate_days_threshold: number;
  // T13
  suspicious_keyword_enabled: boolean;
  suspicious_keyword_threshold: number;
}

export const JE_TESTING_PRESETS: Record<Exclude<JETestingPreset, 'custom'>, Partial<JETestingConfig>> = {
  conservative: {
    round_amount_threshold: 5000,
    unusual_amount_stddev: 2.5,
    single_user_volume_pct: 0.15,
    after_hours_large_threshold: 5000,
    backdate_days_threshold: 14,
    suspicious_keyword_threshold: 0.50,
    numbering_gap_min_size: 2,
  },
  standard: {
    round_amount_threshold: 10000,
    unusual_amount_stddev: 3.0,
    single_user_volume_pct: 0.25,
    after_hours_large_threshold: 10000,
    backdate_days_threshold: 30,
    suspicious_keyword_threshold: 0.60,
    numbering_gap_min_size: 2,
  },
  permissive: {
    round_amount_threshold: 25000,
    unusual_amount_stddev: 3.5,
    single_user_volume_pct: 0.40,
    after_hours_large_threshold: 25000,
    backdate_days_threshold: 60,
    suspicious_keyword_threshold: 0.80,
    numbering_gap_min_size: 5,
  },
};

export const DEFAULT_JE_TESTING_CONFIG: JETestingConfig = {
  balance_tolerance: 0.01,
  round_amount_threshold: 10000,
  round_amount_max_flags: 50,
  unusual_amount_stddev: 3.0,
  unusual_amount_min_entries: 5,
  benford_min_entries: 500,
  weekend_posting_enabled: true,
  weekend_large_amount_threshold: 10000,
  month_end_days: 3,
  month_end_volume_multiplier: 2.0,
  single_user_volume_pct: 0.25,
  single_user_max_flags: 20,
  after_hours_enabled: true,
  after_hours_start: 18,
  after_hours_end: 6,
  after_hours_large_threshold: 10000,
  numbering_gap_enabled: true,
  numbering_gap_min_size: 2,
  backdate_enabled: true,
  backdate_days_threshold: 30,
  suspicious_keyword_enabled: true,
  suspicious_keyword_threshold: 0.60,
};

export const JE_PRESET_LABELS: Record<JETestingPreset, string> = {
  conservative: 'Conservative',
  standard: 'Standard',
  permissive: 'Permissive',
  custom: 'Custom',
};

export const JE_PRESET_DESCRIPTIONS: Record<JETestingPreset, string> = {
  conservative: 'Lower thresholds, more flags — fewer false negatives',
  standard: 'Balanced defaults for most engagements',
  permissive: 'Higher thresholds, fewer flags — fewer false positives',
  custom: 'Individually configured thresholds',
};

// Sprint 76: AP Testing Config
export type APTestingPreset = 'conservative' | 'standard' | 'permissive' | 'custom';

export interface APTestingConfig {
  // AP-T1: Exact Duplicate tolerance
  duplicate_tolerance: number;
  // AP-T3: Check Number Gaps
  check_number_gap_enabled: boolean;
  check_number_gap_min_size: number;
  // AP-T4: Round Dollar Amounts
  round_amount_threshold: number;
  // AP-T5: Payment Before Invoice
  payment_before_invoice_enabled: boolean;
  // AP-T6: Fuzzy Duplicate date window
  duplicate_days_window: number;
  // AP-T7: Invoice Number Reuse
  invoice_reuse_check: boolean;
  // AP-T8: Unusual Payment Amounts
  unusual_amount_stddev: number;
  // AP-T9: Weekend Payments
  weekend_payment_enabled: boolean;
  // AP-T10: High-Frequency Vendors
  high_frequency_vendor_enabled: boolean;
  // AP-T11: Vendor Name Variations
  vendor_variation_enabled: boolean;
  // AP-T12: Just-Below-Threshold
  threshold_proximity_enabled: boolean;
  // AP-T13: Suspicious Descriptions
  suspicious_keyword_enabled: boolean;
  suspicious_keyword_threshold: number;
}

export const AP_TESTING_PRESETS: Record<Exclude<APTestingPreset, 'custom'>, Partial<APTestingConfig>> = {
  conservative: {
    round_amount_threshold: 5000,
    duplicate_days_window: 45,
    unusual_amount_stddev: 2.5,
    suspicious_keyword_threshold: 0.50,
    check_number_gap_min_size: 2,
  },
  standard: {
    round_amount_threshold: 10000,
    duplicate_days_window: 30,
    unusual_amount_stddev: 3.0,
    suspicious_keyword_threshold: 0.60,
    check_number_gap_min_size: 2,
  },
  permissive: {
    round_amount_threshold: 25000,
    duplicate_days_window: 14,
    unusual_amount_stddev: 3.5,
    suspicious_keyword_threshold: 0.80,
    check_number_gap_min_size: 5,
  },
};

export const DEFAULT_AP_TESTING_CONFIG: APTestingConfig = {
  duplicate_tolerance: 0.01,
  check_number_gap_enabled: true,
  check_number_gap_min_size: 2,
  round_amount_threshold: 10000,
  payment_before_invoice_enabled: true,
  duplicate_days_window: 30,
  invoice_reuse_check: true,
  unusual_amount_stddev: 3.0,
  weekend_payment_enabled: true,
  high_frequency_vendor_enabled: true,
  vendor_variation_enabled: true,
  threshold_proximity_enabled: true,
  suspicious_keyword_enabled: true,
  suspicious_keyword_threshold: 0.60,
};

export const AP_PRESET_LABELS: Record<APTestingPreset, string> = {
  conservative: 'Conservative',
  standard: 'Standard',
  permissive: 'Permissive',
  custom: 'Custom',
};

export const AP_PRESET_DESCRIPTIONS: Record<APTestingPreset, string> = {
  conservative: 'Lower thresholds, more flags — catches more potential duplicates',
  standard: 'Balanced defaults for most AP engagements',
  permissive: 'Higher thresholds, fewer flags — reduces noise for high-volume AP',
  custom: 'Individually configured thresholds',
};

// Sprint 88: Payroll Testing Config
export type PayrollTestingPreset = 'conservative' | 'standard' | 'permissive' | 'custom';

export interface PayrollTestingConfig {
  // PR-T3: Round Salary Amounts
  round_amount_threshold: number;
  // PR-T5: Check Number Gaps
  check_gap_enabled: boolean;
  // PR-T6: Unusual Pay Amounts
  unusual_pay_stddev: number;
  // PR-T7: Pay Frequency Anomalies
  frequency_enabled: boolean;
  frequency_deviation_threshold: number;
  // PR-T8: Benford's Law
  benford_enabled: boolean;
  benford_min_entries: number;
  // PR-T9: Ghost Employee Indicators
  ghost_enabled: boolean;
  ghost_min_indicators: number;
  // PR-T10: Duplicate Bank/Address
  duplicate_bank_enabled: boolean;
  address_similarity_threshold: number;
  // PR-T11: Duplicate Tax IDs
  duplicate_tax_enabled: boolean;
}

export const PAYROLL_TESTING_PRESETS: Record<Exclude<PayrollTestingPreset, 'custom'>, Partial<PayrollTestingConfig>> = {
  conservative: {
    round_amount_threshold: 5000,
    unusual_pay_stddev: 2.5,
    benford_min_entries: 300,
    ghost_min_indicators: 1,
    address_similarity_threshold: 0.85,
    frequency_deviation_threshold: 0.30,
  },
  standard: {
    round_amount_threshold: 10000,
    unusual_pay_stddev: 3.0,
    benford_min_entries: 500,
    ghost_min_indicators: 2,
    address_similarity_threshold: 0.90,
    frequency_deviation_threshold: 0.50,
  },
  permissive: {
    round_amount_threshold: 25000,
    unusual_pay_stddev: 3.5,
    benford_min_entries: 1000,
    ghost_min_indicators: 3,
    address_similarity_threshold: 0.95,
    frequency_deviation_threshold: 0.70,
  },
};

export const DEFAULT_PAYROLL_TESTING_CONFIG: PayrollTestingConfig = {
  round_amount_threshold: 10000,
  check_gap_enabled: true,
  unusual_pay_stddev: 3.0,
  frequency_enabled: true,
  frequency_deviation_threshold: 0.50,
  benford_enabled: true,
  benford_min_entries: 500,
  ghost_enabled: true,
  ghost_min_indicators: 2,
  duplicate_bank_enabled: true,
  address_similarity_threshold: 0.90,
  duplicate_tax_enabled: true,
};

export const PAYROLL_PRESET_LABELS: Record<PayrollTestingPreset, string> = {
  conservative: 'Conservative',
  standard: 'Standard',
  permissive: 'Permissive',
  custom: 'Custom',
};

export const PAYROLL_PRESET_DESCRIPTIONS: Record<PayrollTestingPreset, string> = {
  conservative: 'Lower thresholds, more flags — catches more payroll anomalies',
  standard: 'Balanced defaults for most payroll engagements',
  permissive: 'Higher thresholds, fewer flags — reduces noise for large payrolls',
  custom: 'Individually configured thresholds',
};

// Sprint 94: Three-Way Match Config
export type ThreeWayMatchPreset = 'tight' | 'standard' | 'loose' | 'custom';

export interface ThreeWayMatchConfig {
  amount_tolerance: number;
  quantity_tolerance: number;
  date_window_days: number;
  fuzzy_vendor_threshold: number;
  price_variance_threshold: number;
  enable_fuzzy_matching: boolean;
}

export const THREE_WAY_MATCH_PRESETS: Record<Exclude<ThreeWayMatchPreset, 'custom'>, Partial<ThreeWayMatchConfig>> = {
  tight: {
    amount_tolerance: 0.01,
    quantity_tolerance: 0.0,
    date_window_days: 15,
    fuzzy_vendor_threshold: 0.90,
    price_variance_threshold: 0.01,
  },
  standard: {
    amount_tolerance: 0.01,
    quantity_tolerance: 0.0,
    date_window_days: 30,
    fuzzy_vendor_threshold: 0.85,
    price_variance_threshold: 0.05,
  },
  loose: {
    amount_tolerance: 0.50,
    quantity_tolerance: 0.05,
    date_window_days: 60,
    fuzzy_vendor_threshold: 0.75,
    price_variance_threshold: 0.10,
  },
};

export const DEFAULT_THREE_WAY_MATCH_CONFIG: ThreeWayMatchConfig = {
  amount_tolerance: 0.01,
  quantity_tolerance: 0.0,
  date_window_days: 30,
  fuzzy_vendor_threshold: 0.85,
  price_variance_threshold: 0.05,
  enable_fuzzy_matching: true,
};

export const TWM_PRESET_LABELS: Record<ThreeWayMatchPreset, string> = {
  tight: 'Tight',
  standard: 'Standard',
  loose: 'Loose',
  custom: 'Custom',
};

export const TWM_PRESET_DESCRIPTIONS: Record<ThreeWayMatchPreset, string> = {
  tight: 'Exact matching, minimal tolerance — strictest controls',
  standard: 'Balanced defaults for most procurement audits',
  loose: 'Higher tolerances, wider date window — high-volume environments',
  custom: 'Individually configured thresholds',
};
