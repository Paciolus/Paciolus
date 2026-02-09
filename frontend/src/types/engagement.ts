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
  | 'three_way_match'
  | 'revenue_testing'
  | 'ar_aging';

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
  revenue_testing: 'Revenue Testing',
  ar_aging: 'AR Aging',
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
  revenue_testing: 'revenue-testing',
  ar_aging: 'ar-aging',
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

// ---------------------------------------------------------------------------
// Follow-Up Items (Sprint 100)
// ---------------------------------------------------------------------------

export type FollowUpSeverity = 'high' | 'medium' | 'low';

export type FollowUpDisposition =
  | 'not_reviewed'
  | 'investigated_no_issue'
  | 'investigated_adjustment_posted'
  | 'investigated_further_review'
  | 'immaterial';

/** Human-readable labels for disposition states (Guardrail 4: no audit terminology). */
export const DISPOSITION_LABELS: Record<FollowUpDisposition, string> = {
  not_reviewed: 'Not Reviewed',
  investigated_no_issue: 'Investigated \u2014 No Issue',
  investigated_adjustment_posted: 'Investigated \u2014 Adjustment Posted',
  investigated_further_review: 'Investigated \u2014 Further Review',
  immaterial: 'Immaterial',
};

/** Severity badge styles (Oat & Obsidian). */
export const SEVERITY_COLORS: Record<FollowUpSeverity, { bg: string; text: string; border: string }> = {
  high: { bg: 'bg-clay-500/15', text: 'text-clay-400', border: 'border-clay-500/30' },
  medium: { bg: 'bg-oatmeal-500/15', text: 'text-oatmeal-400', border: 'border-oatmeal-500/30' },
  low: { bg: 'bg-sage-500/15', text: 'text-sage-400', border: 'border-sage-500/30' },
};

/** Disposition badge styles (Oat & Obsidian). */
export const DISPOSITION_COLORS: Record<FollowUpDisposition, { bg: string; text: string; border: string }> = {
  not_reviewed: { bg: 'bg-obsidian-700/50', text: 'text-oatmeal-400', border: 'border-obsidian-600/50' },
  investigated_no_issue: { bg: 'bg-sage-500/15', text: 'text-sage-400', border: 'border-sage-500/30' },
  investigated_adjustment_posted: { bg: 'bg-oatmeal-500/15', text: 'text-oatmeal-300', border: 'border-oatmeal-500/30' },
  investigated_further_review: { bg: 'bg-clay-500/15', text: 'text-clay-400', border: 'border-clay-500/30' },
  immaterial: { bg: 'bg-obsidian-600/50', text: 'text-oatmeal-500', border: 'border-obsidian-500/50' },
};

export interface FollowUpItem {
  id: number;
  engagement_id: number;
  tool_run_id: number | null;
  description: string;
  tool_source: string;
  severity: FollowUpSeverity;
  disposition: FollowUpDisposition;
  auditor_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface FollowUpItemCreateInput {
  description: string;
  tool_source: string;
  severity?: string;
  tool_run_id?: number;
  auditor_notes?: string;
}

export interface FollowUpItemUpdateInput {
  disposition?: string;
  auditor_notes?: string;
  severity?: string;
}

export interface FollowUpSummary {
  total_count: number;
  by_severity: Record<string, number>;
  by_disposition: Record<string, number>;
  by_tool_source: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Workpaper Index (Sprint 100)
// ---------------------------------------------------------------------------

export interface WorkpaperEntry {
  tool_name: string;
  tool_label: string;
  run_count: number;
  last_run_date: string | null;
  status: 'completed' | 'not_started';
  lead_sheet_refs: string[];
}

export interface WorkpaperIndex {
  engagement_id: number;
  client_name: string;
  period_start: string;
  period_end: string;
  generated_at: string;
  document_register: WorkpaperEntry[];
  follow_up_summary: FollowUpSummary;
  sign_off: {
    prepared_by: string;
    reviewed_by: string;
    date: string;
  };
}
