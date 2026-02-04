/**
 * Paciolus Mapping Types
 * Account type definitions for the manual mapping system
 *
 * See: logs/dev-log.md for IP documentation
 */

// Account categories - must match backend classification_rules.py
export type AccountType =
  | 'asset'
  | 'liability'
  | 'equity'
  | 'revenue'
  | 'expense'
  | 'unknown';

export const ACCOUNT_TYPES: AccountType[] = [
  'asset',
  'liability',
  'equity',
  'revenue',
  'expense',
  'unknown'
];

// Human-readable labels for account types
export const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  asset: 'Asset',
  liability: 'Liability',
  equity: 'Equity',
  revenue: 'Revenue',
  expense: 'Expense',
  unknown: 'Unknown'
};

// Account mapping state for an individual account
export interface AccountMapping {
  accountName: string;
  detectedType: AccountType | null;  // Auto-detected by classifier
  overrideType: AccountType | null;  // User manual override
  confidence: number;
  isManual: boolean;
}

// Configuration for export/import (Zero-Storage: user's local machine only)
export interface MappingConfig {
  version: string;
  createdAt: string;
  mappings: Record<string, AccountType>;  // accountName -> overrideType
}

// Anomaly types for Risk Dashboard (Day 10)
export type AnomalyType = 'natural_balance_violation';
export type Severity = 'high' | 'low';

// Extended AbnormalBalance with Day 9 classification fields + Day 10 anomaly fields
export interface AbnormalBalanceExtended {
  // Original fields
  account: string;
  type: string;
  issue: string;
  amount: number;
  debit: number;
  credit: number;
  materiality: 'material' | 'immaterial';
  // Day 9 new fields
  category?: AccountType;
  confidence?: number;
  matched_keywords?: string[];
  requires_review?: boolean;
  // Day 10: Anomaly categorization for Risk Dashboard
  anomaly_type?: AnomalyType;
  expected_balance?: 'debit' | 'credit';
  actual_balance?: 'debit' | 'credit';
  severity?: Severity;
}

// Risk summary from API (Day 10)
export interface RiskSummary {
  total_anomalies: number;
  high_severity: number;
  low_severity: number;
  anomaly_types: {
    natural_balance_violation: number;
  };
}

// Mapping storage key for sessionStorage
export const MAPPING_STORAGE_KEY = 'paciolus_account_mappings';

// Day 11: Multi-Sheet Excel Support Types

export interface SheetInfo {
  name: string;
  row_count: number;
  column_count: number;
  columns: string[];
  has_data: boolean;
}

export interface WorkbookInfo {
  filename: string;
  sheet_count: number;
  sheets: SheetInfo[];
  total_rows: number;
  is_multi_sheet: boolean;
  format: 'xlsx' | 'xls' | 'csv';
  requires_sheet_selection: boolean;
}

// Consolidated audit result with per-sheet breakdown
export interface ConsolidatedAuditResult {
  is_consolidated: boolean;
  sheet_count: number;
  selected_sheets: string[];
  sheet_results: {
    [sheetName: string]: {
      balanced: boolean;
      total_debits: number;
      total_credits: number;
      difference: number;
      row_count: number;
      abnormal_count: number;
    };
  };
}

// Sprint 19: Analytics Types for Ratio Intelligence

export type HealthStatus = 'healthy' | 'warning' | 'concern' | 'neutral';
export type VarianceDirection = 'positive' | 'negative' | 'neutral';

export interface RatioData {
  name: string;
  value: number | null;
  display_value: string;
  is_calculable: boolean;
  interpretation: string;
  health_status: HealthStatus;
}

export interface VarianceData {
  metric_name: string;
  current_value: number;
  previous_value: number;
  change_amount: number;
  change_percent: number;
  direction: VarianceDirection;
  display_text: string;
}

export interface CategoryTotals {
  total_assets: number;
  current_assets: number;
  total_liabilities: number;
  total_equity: number;
  total_revenue: number;
}

export interface Analytics {
  ratios: {
    current_ratio: RatioData;
    quick_ratio: RatioData;
    debt_to_equity: RatioData;
    gross_margin: RatioData;
    net_profit_margin?: RatioData;
    operating_margin?: RatioData;
    return_on_assets?: RatioData;
    return_on_equity?: RatioData;
  };
  variances: Record<string, VarianceData>;
  has_previous_data: boolean;
  category_totals: CategoryTotals;
}
