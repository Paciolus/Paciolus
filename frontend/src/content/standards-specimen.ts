/**
 * Standards Specimen data (Sprint 705).
 *
 * Canonical list of every auditing / accounting standard cited by a
 * Paciolus tool or memo. Rendered by `<StandardsSpecimen>` on the
 * homepage as a two-column specimen page from a bound reference volume.
 *
 * Conventions:
 *   - `code`: the standard identifier as auditors write it (e.g. "ISA 240").
 *   - `paragraphs`: optional — paragraph citation suffix (e.g. ".A24" or
 *     "paras. 30-35"). Kept separate so the code can be rendered with a
 *     footnote-style superscript.
 *   - `scope`: one line. Short enough to not break the two-column layout.
 *   - `body`: the governing body (IAASB, PCAOB, FASB, IASB).
 *   - `tools`: array of tool IDs that cite this standard — used to wire
 *     deep-links from the specimen row to the matching tool page.
 *     Tool IDs match `lib/commandRegistry.ts` TOOL_ENTRIES + the tool
 *     catalog at `app/tools/page.tsx`.
 *
 * When adding a new standard: update this file only; the component
 * renders the full list automatically. New tools citing existing
 * standards can be added by appending to `tools`.
 */

export interface SpecimenEntry {
  code: string
  paragraphs?: string
  scope: string
  body: 'IAASB' | 'PCAOB' | 'FASB' | 'IASB'
  tools: string[]
}

export const STANDARDS_SPECIMEN: SpecimenEntry[] = [
  // ─── IAASB — International Standards on Auditing ───────────────
  {
    code: 'ISA 240',
    paragraphs: 'paras. 26–33, A24–A27',
    scope: 'The auditor\'s responsibilities relating to fraud in a financial-statement audit.',
    body: 'IAASB',
    tools: ['journal_entry_testing', 'revenue_testing', 'ap_testing', 'payroll_testing'],
  },
  {
    code: 'ISA 315',
    paragraphs: 'Revised 2019, Appendix 1',
    scope: 'Identifying and assessing risks of material misstatement through understanding the entity.',
    body: 'IAASB',
    tools: ['composite_risk', 'account_risk_heatmap', 'trial_balance'],
  },
  {
    code: 'ISA 500',
    scope: 'Sufficient appropriate audit evidence — nature, sources, and reliability.',
    body: 'IAASB',
    tools: ['ar_aging', 'fixed_asset_testing', 'three_way_match'],
  },
  {
    code: 'ISA 501',
    scope: 'Specific considerations for selected items — inventory, litigation, segment info.',
    body: 'IAASB',
    tools: ['inventory_testing'],
  },
  {
    code: 'ISA 505',
    scope: 'External confirmations — design, procedures, and evaluating responses.',
    body: 'IAASB',
    tools: ['bank_reconciliation'],
  },
  {
    code: 'ISA 520',
    scope: 'Analytical procedures — expectations, plausibility, and investigation thresholds.',
    body: 'IAASB',
    tools: ['trial_balance', 'multi_period', 'account_risk_heatmap'],
  },
  {
    code: 'ISA 530',
    scope: 'Audit sampling — design, selection, projection, and evaluation of results.',
    body: 'IAASB',
    tools: ['statistical_sampling'],
  },
  {
    code: 'ISA 540',
    scope: 'Auditing accounting estimates, including fair value and related disclosures.',
    body: 'IAASB',
    tools: ['ar_aging', 'inventory_testing'],
  },
  {
    code: 'ISA 570',
    scope: 'Going concern — auditor\'s responsibilities and indicators framework.',
    body: 'IAASB',
    tools: ['trial_balance', 'account_risk_heatmap'],
  },

  // ─── PCAOB Auditing Standards ──────────────────────────────────
  {
    code: 'PCAOB AS 1215',
    scope: 'Audit documentation — content, completion, and retention requirements (governs every memo/export, not a procedure standard).',
    body: 'PCAOB',
    tools: [],
  },
  {
    code: 'PCAOB AS 2315',
    scope: 'Audit sampling — PCAOB-aligned variant of ISA 530 for US issuer audits.',
    body: 'PCAOB',
    tools: ['statistical_sampling'],
  },
  {
    code: 'PCAOB AS 2401',
    scope: 'Consideration of fraud in a financial-statement audit — US public company analog to ISA 240.',
    body: 'PCAOB',
    tools: ['journal_entry_testing', 'revenue_testing'],
  },
  {
    code: 'PCAOB AS 2501',
    scope: 'Auditing accounting estimates — revised guidance effective 2020.',
    body: 'PCAOB',
    tools: ['ar_aging', 'fixed_asset_testing'],
  },

  // ─── FASB — US Generally Accepted Accounting Principles ────────
  {
    code: 'ASC 230',
    scope: 'Statement of cash flows — classification of operating, investing, financing activities.',
    body: 'FASB',
    tools: ['trial_balance'],
  },
  {
    code: 'ASC 330',
    scope: 'Inventory — cost-flow assumptions, lower-of-cost-or-market/NRV measurement.',
    body: 'FASB',
    tools: ['inventory_testing'],
  },
  {
    code: 'ASC 360',
    scope: 'Property, plant, equipment — capitalization thresholds, impairment, disposals.',
    body: 'FASB',
    tools: ['fixed_asset_testing'],
  },
  {
    code: 'ASC 606',
    scope: 'Revenue from contracts with customers — five-step recognition framework.',
    body: 'FASB',
    tools: ['revenue_testing'],
  },

  // ─── IASB — International Financial Reporting Standards ────────
  {
    code: 'IAS 2',
    scope: 'Inventories — cost measurement, NRV rules, disclosure requirements.',
    body: 'IASB',
    tools: ['inventory_testing'],
  },
  {
    code: 'IAS 7',
    scope: 'Statement of cash flows — indirect method classification + reconciliation.',
    body: 'IASB',
    tools: ['trial_balance'],
  },
  {
    code: 'IAS 16',
    scope: 'Property, plant, equipment — recognition, depreciation, revaluation model.',
    body: 'IASB',
    tools: ['fixed_asset_testing'],
  },
  {
    code: 'IFRS 15',
    scope: 'Revenue from contracts with customers — IFRS converged standard with ASC 606.',
    body: 'IASB',
    tools: ['revenue_testing'],
  },
]

/** Governing-body order preserved for rendering — keeps IAASB → PCAOB → FASB → IASB grouping intact. */
export const BODY_ORDER: SpecimenEntry['body'][] = ['IAASB', 'PCAOB', 'FASB', 'IASB']

export const BODY_LABELS: Record<SpecimenEntry['body'], string> = {
  IAASB: 'IAASB · International Standards on Auditing',
  PCAOB: 'PCAOB · US Public Company Accounting Oversight Board',
  FASB: 'FASB · US GAAP (ASC codification)',
  IASB: 'IASB · International Financial Reporting Standards',
}
