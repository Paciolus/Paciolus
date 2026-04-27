/**
 * Sprint 729b — Uncorrected Misstatements (ISA 450) types.
 *
 * Frontend mirror of backend/schemas/uncorrected_misstatement_schemas.py.
 */

export type MisstatementSourceType =
  | 'adjusting_entry_passed'
  | 'sample_projection'
  | 'known_error';

export type MisstatementClassification = 'factual' | 'judgmental' | 'projected';

export type MisstatementDisposition =
  | 'not_yet_reviewed'
  | 'auditor_proposes_correction'
  | 'auditor_accepts_as_immaterial';

export type MaterialityBucket =
  | 'clearly_trivial'
  | 'immaterial'
  | 'approaching_material'
  | 'material';

export interface AccountAffected {
  account: string;
  debit_credit: 'DR' | 'CR';
  amount: number;
}

export interface UncorrectedMisstatement {
  id: number;
  engagement_id: number;
  source_type: MisstatementSourceType;
  source_reference: string;
  description: string;
  accounts_affected: AccountAffected[];
  classification: MisstatementClassification;
  fs_impact_net_income: number;
  fs_impact_net_assets: number;
  cpa_disposition: MisstatementDisposition;
  cpa_notes: string | null;
  created_by: number;
  created_at: string;
  updated_by: number | null;
  updated_at: string;
}

export interface UncorrectedMisstatementCreateInput {
  source_type: MisstatementSourceType;
  source_reference: string;
  description: string;
  accounts_affected: AccountAffected[];
  classification: MisstatementClassification;
  fs_impact_net_income: number;
  fs_impact_net_assets: number;
  cpa_disposition?: MisstatementDisposition;
  cpa_notes?: string | null;
}

export interface UncorrectedMisstatementUpdateInput {
  source_reference?: string;
  description?: string;
  accounts_affected?: AccountAffected[];
  classification?: MisstatementClassification;
  fs_impact_net_income?: number;
  fs_impact_net_assets?: number;
  cpa_disposition?: MisstatementDisposition;
  cpa_notes?: string | null;
}

export interface SumScheduleResponse {
  engagement_id: number;
  items: UncorrectedMisstatement[];
  subtotals: {
    factual_judgmental_net_income: number;
    factual_judgmental_net_assets: number;
    projected_net_income: number;
    projected_net_assets: number;
  };
  aggregate: {
    net_income: number;
    net_assets: number;
    driver: number;
  };
  materiality: {
    overall: number;
    performance: number;
    trivial: number;
  };
  bucket: MaterialityBucket;
  unreviewed_count: number;
}

export const SOURCE_TYPE_LABELS: Record<MisstatementSourceType, string> = {
  adjusting_entry_passed: 'Passed AJE',
  sample_projection: 'Sample Projection',
  known_error: 'Known Error',
};

export const CLASSIFICATION_LABELS: Record<MisstatementClassification, string> = {
  factual: 'Factual',
  judgmental: 'Judgmental',
  projected: 'Projected',
};

export const DISPOSITION_LABELS: Record<MisstatementDisposition, string> = {
  not_yet_reviewed: 'Not Yet Reviewed',
  auditor_proposes_correction: 'Auditor Proposes Correction',
  auditor_accepts_as_immaterial: 'Auditor Accepts as Immaterial',
};

export const BUCKET_LABELS: Record<MaterialityBucket, string> = {
  clearly_trivial: 'Clearly Trivial',
  immaterial: 'Immaterial',
  approaching_material: 'Approaching Material',
  material: 'Material',
};

/**
 * Bucket color treatment per design mandate. Sage = safe (trivial /
 * immaterial); Clay = elevated attention (approaching) and error
 * (material). Approaching uses reduced-opacity clay because Oat &
 * Obsidian has no yellow / amber token (documented in
 * docs/04-compliance/isa-450-coverage.md).
 */
export const BUCKET_TONE: Record<MaterialityBucket, 'sage' | 'clay-soft' | 'clay'> = {
  clearly_trivial: 'sage',
  immaterial: 'sage',
  approaching_material: 'clay-soft',
  material: 'clay',
};
