/**
 * Tool Ledger data (Sprint 706).
 *
 * Canonical catalog of the 12 auditor-focused Paciolus tools, rendered
 * by `<ToolLedger>` as a bound-ledger grid on the homepage in place of
 * the slideshow-one-card-at-a-time pattern.
 *
 * Fields:
 *   - `id`: tool ID, matches `routes/tools` + command palette keys.
 *   - `number`: the catalog order (Roman-adjacent "I. / II. / …" kicker
 *     is derived at render time; we store the Arabic number here for
 *     sort + oldstyle-figure rendering).
 *   - `name`: short name as it appears in the nav.
 *   - `testCount`: optional — the number of automated tests in the tool's
 *     test battery (nullable because not every tool has a fixed battery;
 *     "TB Diagnostics" runs analytical procedures rather than a discrete
 *     test count, for example).
 *   - `standards`: short list of standard codes the tool primarily cites.
 *     Kept to 2-3 codes per tool so the row stays scannable.
 *   - `summary`: one-liner shown in the accordion body. Not marketing copy —
 *     describes the auditor value proposition in functional terms.
 *   - `href`: canonical catalog URL.
 *
 * Canonical tool-count source: backend `shared/entitlements.py`
 * (`CANONICAL_TOOL_COUNT = 12`). When Sprint 689 reconciles the catalog
 * (promote / defer / remove hidden backend tools), update this file.
 */

export interface LedgerEntry {
  id: string
  number: number
  name: string
  testCount: number | null
  standards: string[]
  summary: string
  href: string
}

export const TOOL_LEDGER: LedgerEntry[] = [
  {
    id: 'trial_balance',
    number: 1,
    name: 'Trial Balance Diagnostics',
    testCount: null, // runs ratios + anomaly detection, not a discrete test count
    standards: ['ISA 520', 'ISA 315'],
    summary: 'Ratio analysis, anomaly detection, lead-sheet mapping, and financial-statement generation from a single TB upload.',
    href: '/tools/trial-balance',
  },
  {
    id: 'multi_period',
    number: 2,
    name: 'Multi-Period Comparison',
    testCount: null,
    standards: ['ISA 520'],
    summary: 'Side-by-side variance analysis across up to three periods with reclassification detection.',
    href: '/tools/multi-period',
  },
  {
    id: 'journal_entry_testing',
    number: 3,
    name: 'Journal Entry Testing',
    testCount: 19,
    standards: ['ISA 240', 'PCAOB AS 2401'],
    summary: "Benford's Law, structural validation, weekend/holiday posting, round-dollar, reversal-window — 19-test battery over the GL.",
    href: '/tools/journal-entry-testing',
  },
  {
    id: 'ap_testing',
    number: 4,
    name: 'AP Payment Testing',
    testCount: 14,
    standards: ['ISA 240', 'ISA 500'],
    summary: 'Duplicate payments, vendor anomalies, ghost vendors, and invoice-without-PO flags across the AP register.',
    href: '/tools/ap-testing',
  },
  {
    id: 'revenue_testing',
    number: 5,
    name: 'Revenue Testing',
    testCount: 18,
    standards: ['ASC 606', 'IFRS 15', 'ISA 240'],
    summary: 'ASC 606 / IFRS 15 contract-aware revenue testing including cut-off, prior-period timing, and contract validity.',
    href: '/tools/revenue-testing',
  },
  {
    id: 'ar_aging',
    number: 6,
    name: 'AR Aging',
    testCount: 12,
    standards: ['ISA 540', 'ISA 500'],
    summary: 'Aged receivables analysis with collectibility risk, concentration, and sign-anomaly detection.',
    href: '/tools/ar-aging',
  },
  {
    id: 'payroll_testing',
    number: 7,
    name: 'Payroll Testing',
    testCount: 13,
    standards: ['ISA 240'],
    summary: 'Ghost-employee detection, rate anomalies, overtime spikes, gross-to-net reconciliation across the payroll register.',
    href: '/tools/payroll-testing',
  },
  {
    id: 'fixed_asset_testing',
    number: 8,
    name: 'Fixed Assets',
    testCount: 11,
    standards: ['ISA 500', 'IAS 16', 'ASC 360'],
    summary: 'Depreciation recalc, impairment indicators, disposals, and lease-classification flags against the FA register.',
    href: '/tools/fixed-assets',
  },
  {
    id: 'inventory_testing',
    number: 9,
    name: 'Inventory Testing',
    testCount: 10,
    standards: ['ISA 501', 'IAS 2', 'ASC 330'],
    summary: 'Valuation anomalies, LCM/NRV, obsolescence indicators, and cutoff issues across inventory records.',
    href: '/tools/inventory-testing',
  },
  {
    id: 'bank_reconciliation',
    number: 10,
    name: 'Bank Reconciliation',
    testCount: null,
    standards: ['ISA 505', 'ISA 500'],
    summary: 'Match bank statements against book records to surface reconciling items and unexplained discrepancies.',
    href: '/tools/bank-rec',
  },
  {
    id: 'three_way_match',
    number: 11,
    name: 'Three-Way Match',
    testCount: null,
    standards: ['ISA 500'],
    summary: 'PO / receiving report / vendor invoice reconciliation to surface procurement anomalies.',
    href: '/tools/three-way-match',
  },
  {
    id: 'statistical_sampling',
    number: 12,
    name: 'Statistical Sampling',
    testCount: null,
    standards: ['ISA 530', 'PCAOB AS 2315'],
    summary: 'MUS + classical variables + attribute sampling per ISA 530 with full projection + evaluation workflow.',
    href: '/tools/statistical-sampling',
  },
]

/**
 * Canonical tool count. Must equal TOOL_LEDGER.length — enforced by a
 * build-time assertion below. Keep in sync with the backend
 * `shared/entitlements.py` constant (currently `CANONICAL_TOOL_COUNT = 12`).
 */
export const CANONICAL_TOOL_COUNT = 12

if (TOOL_LEDGER.length !== CANONICAL_TOOL_COUNT) {
  throw new Error(
    `Tool ledger count mismatch: CANONICAL_TOOL_COUNT=${CANONICAL_TOOL_COUNT} but TOOL_LEDGER has ${TOOL_LEDGER.length} entries`,
  )
}
