/**
 * Diagnostic Types
 * Phase 2 Refactor: Extracted from DiagnosticContext.tsx
 *
 * Types for flux analysis and reconciliation results.
 */

/**
 * Risk level for flux items.
 */
export enum RiskLevel {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
  NONE = 'none',
}

/**
 * Risk band for reconciliation scores.
 */
export enum RiskBand {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
}

/**
 * Individual flux analysis item.
 */
export interface FluxItem {
  account: string;
  type: string;
  current: number;
  prior: number;
  delta_amount: number;
  delta_percent: number | null;
  display_percent: string;
  is_new: boolean;
  is_removed: boolean;
  sign_flip: boolean;
  risk_level: RiskLevel;
  risk_reasons: string[];
}

/**
 * Summary statistics for flux analysis.
 */
export interface FluxSummary {
  total_items: number;
  high_risk_count: number;
  medium_risk_count: number;
  new_accounts: number;
  removed_accounts: number;
  threshold: number;
}

/**
 * Individual reconciliation score.
 */
export interface ReconScore {
  account: string;
  score: number;
  band: RiskBand;
  factors: string[];
  action: string;
}

/**
 * Statistics for reconciliation scores by risk band.
 */
export interface ReconStats {
  high: number;
  medium: number;
  low: number;
}

/**
 * Complete diagnostic result from flux/recon analysis.
 */
export interface DiagnosticResult {
  flux: {
    items: FluxItem[];
    summary: FluxSummary;
  };
  recon: {
    scores: ReconScore[];
    stats: ReconStats;
  };
  filename: string;
  uploadedAt: string;
}

/**
 * Context type for diagnostic state management.
 */
export interface DiagnosticContextType {
  result: DiagnosticResult | null;
  setResult: (result: DiagnosticResult | null) => void;
  clearResult: () => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
}
