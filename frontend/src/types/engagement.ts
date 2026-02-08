/**
 * Engagement Types — Sprint 98: Engagement Workspace
 * Phase X: The Engagement Layer
 *
 * Types matching backend EngagementResponse, ToolRunResponse, MaterialityResponse.
 *
 * ZERO-STORAGE: These types describe metadata only.
 * No account numbers, amounts, or PII.
 */

// ---------------------------------------------------------------------------
// Enums / Literal Unions
// ---------------------------------------------------------------------------

export type EngagementStatus = 'active' | 'archived';

export type MaterialityBasis = 'revenue' | 'assets' | 'manual';

export type ToolName =
  | 'trial_balance'
  | 'multi_period'
  | 'journal_entry_testing'
  | 'ap_testing'
  | 'bank_reconciliation'
  | 'payroll_testing'
  | 'three_way_match';

export type ToolRunStatus = 'completed' | 'failed';

// ---------------------------------------------------------------------------
// Display Maps
// ---------------------------------------------------------------------------

/** Human-readable labels for each tool (Guardrail 4: no audit terminology). */
export const TOOL_NAME_LABELS: Record<ToolName, string> = {
  trial_balance: 'TB Diagnostics',
  multi_period: 'Multi-Period',
  journal_entry_testing: 'JE Testing',
  ap_testing: 'AP Testing',
  bank_reconciliation: 'Bank Rec',
  payroll_testing: 'Payroll Testing',
  three_way_match: 'Three-Way Match',
};

/** Tool slug map for navigation. */
export const TOOL_SLUGS: Record<ToolName, string> = {
  trial_balance: 'trial-balance',
  multi_period: 'multi-period',
  journal_entry_testing: 'journal-entry-testing',
  ap_testing: 'ap-testing',
  bank_reconciliation: 'bank-rec',
  payroll_testing: 'payroll-testing',
  three_way_match: 'three-way-match',
};

/** Oat & Obsidian status colors. */
export const ENGAGEMENT_STATUS_COLORS: Record<EngagementStatus, { bg: string; text: string; border: string }> = {
  active: {
    bg: 'bg-sage-500/15',
    text: 'text-sage-400',
    border: 'border-sage-500/30',
  },
  archived: {
    bg: 'bg-oatmeal-500/15',
    text: 'text-oatmeal-400',
    border: 'border-oatmeal-500/30',
  },
};

// ---------------------------------------------------------------------------
// API Response Types
// ---------------------------------------------------------------------------

export interface Engagement {
  id: number;
  client_id: number;
  period_start: string;
  period_end: string;
  status: EngagementStatus;
  materiality_basis: MaterialityBasis | null;
  materiality_percentage: number | null;
  materiality_amount: number | null;
  performance_materiality_factor: number;
  trivial_threshold_factor: number;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface EngagementListResponse {
  engagements: Engagement[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface ToolRun {
  id: number;
  engagement_id: number;
  tool_name: ToolName;
  run_number: number;
  status: ToolRunStatus;
  composite_score: number | null;
  run_at: string;
}

export interface MaterialityCascade {
  overall_materiality: number;
  performance_materiality: number;
  trivial_threshold: number;
  materiality_basis: MaterialityBasis | null;
  materiality_percentage: number | null;
  performance_materiality_factor: number;
  trivial_threshold_factor: number;
}

// ---------------------------------------------------------------------------
// Input Types
// ---------------------------------------------------------------------------

export interface EngagementCreateInput {
  client_id: number;
  period_start: string;
  period_end: string;
  materiality_basis?: MaterialityBasis;
  materiality_percentage?: number;
  materiality_amount?: number;
  performance_materiality_factor?: number;
  trivial_threshold_factor?: number;
}

export interface EngagementUpdateInput {
  period_start?: string;
  period_end?: string;
  status?: EngagementStatus;
  materiality_basis?: MaterialityBasis;
  materiality_percentage?: number;
  materiality_amount?: number;
  performance_materiality_factor?: number;
  trivial_threshold_factor?: number;
}
