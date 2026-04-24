/**
 * Tool Ledger data — Sprint 717 (expanded from Sprint 706's 12 to canonical 18).
 *
 * Canonical catalog of the 18 auditor-focused Paciolus tools, rendered
 * by `<ToolLedger>` as a bound-ledger grid on the homepage.
 *
 * Tool count history:
 *   - Sprint 706: 12 entries (original audit-tool catalog)
 *   - Sprint 689b–g: backend promoted 6 tools (SOD, Intercompany, W-2, 1099,
 *     Book-to-Tax, Cash Flow Projector) but the frontend ledger was not updated.
 *   - Sprint 717: ledger expanded 12 → 18 to match `backend/tools_registry.py`
 *     (the canonical SSOT for the catalog). Multi-Currency (689a) is a
 *     side-car panel promoted to its own page, NOT a new audit tool, and is
 *     intentionally excluded from this 18-tool ledger.
 *
 * SOURCE OF TRUTH: `backend/tools_registry.py` `MARKETING_AUDIT_TOOL_COUNT`.
 * CI test `tests/test_catalog_consistency.py` enforces equivalence — if
 * `TOOL_LEDGER` length diverges from the registry, the build fails.
 *
 * Fields:
 *   - `id`: tool ID, matches backend `enforce_tool_access` slug + command palette.
 *   - `number`: catalog order (Roman-adjacent kicker derived at render time).
 *   - `name`: short name as shown in nav.
 *   - `testCount`: number of automated tests in the engine, or null for
 *     non-test-suite tools.
 *   - `standards`: 2-3 standard codes; every code must be registered in
 *     `backend/standards_registry.py`.
 *   - `summary`: one-liner shown in the accordion body — describes auditor
 *     value in functional terms, not marketing copy.
 *   - `href`: canonical catalog URL.
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
  // ── Core Analysis (4) ────────────────────────────────
  {
    id: 'trial_balance',
    number: 1,
    name: 'Trial Balance Diagnostics',
    testCount: null,
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
    id: 'bank_reconciliation',
    number: 3,
    name: 'Bank Reconciliation',
    testCount: null,
    standards: ['ISA 505', 'ISA 500'],
    summary: 'Match bank statements against book records to surface reconciling items and unexplained discrepancies.',
    href: '/tools/bank-rec',
  },
  {
    id: 'three_way_match',
    number: 4,
    name: 'Three-Way Match',
    testCount: null,
    standards: ['ISA 500'],
    summary: 'PO / receiving report / vendor invoice reconciliation to surface procurement anomalies.',
    href: '/tools/three-way-match',
  },

  // ── Testing Suite (7) ────────────────────────────────
  {
    id: 'journal_entry_testing',
    number: 5,
    name: 'Journal Entry Testing',
    testCount: 19,
    standards: ['ISA 240', 'PCAOB AS 2401'],
    summary: "Benford's Law, structural validation, weekend/holiday posting, round-dollar, reversal-window — 19-test battery over the GL.",
    href: '/tools/journal-entry-testing',
  },
  {
    id: 'ap_testing',
    number: 6,
    name: 'AP Payment Testing',
    testCount: 14,
    standards: ['ISA 240', 'ISA 500'],
    summary: 'Duplicate payments, vendor anomalies, ghost vendors, and invoice-without-PO flags across the AP register.',
    href: '/tools/ap-testing',
  },
  {
    id: 'revenue_testing',
    number: 7,
    name: 'Revenue Testing',
    testCount: 18,
    standards: ['ASC 606', 'IFRS 15', 'ISA 240'],
    summary: 'ASC 606 / IFRS 15 contract-aware revenue testing including cut-off, prior-period timing, and contract validity.',
    href: '/tools/revenue-testing',
  },
  {
    id: 'ar_aging',
    number: 8,
    name: 'AR Aging',
    testCount: 12,
    standards: ['ISA 540', 'ISA 500'],
    summary: 'Aged receivables analysis with collectibility risk, concentration, and sign-anomaly detection.',
    href: '/tools/ar-aging',
  },
  {
    id: 'payroll_testing',
    number: 9,
    name: 'Payroll Testing',
    testCount: 13,
    standards: ['ISA 240'],
    summary: 'Ghost-employee detection, rate anomalies, overtime spikes, gross-to-net reconciliation across the payroll register.',
    href: '/tools/payroll-testing',
  },
  {
    id: 'fixed_asset_testing',
    number: 10,
    name: 'Fixed Assets',
    testCount: 11,
    standards: ['ISA 500', 'IAS 16', 'ASC 360'],
    summary: 'Depreciation recalc, impairment indicators, disposals, and lease-classification flags against the FA register.',
    href: '/tools/fixed-assets',
  },
  {
    id: 'inventory_testing',
    number: 11,
    name: 'Inventory Testing',
    testCount: 10,
    standards: ['ISA 501', 'IAS 2', 'ASC 330'],
    summary: 'Valuation anomalies, LCM/NRV, obsolescence indicators, and cutoff issues across inventory records.',
    href: '/tools/inventory-testing',
  },

  // ── Advanced — Original (1) ──────────────────────────
  {
    id: 'statistical_sampling',
    number: 12,
    name: 'Statistical Sampling',
    testCount: null,
    standards: ['ISA 530', 'PCAOB AS 2315'],
    summary: 'MUS + classical variables + attribute sampling per ISA 530 with full projection + evaluation workflow.',
    href: '/tools/statistical-sampling',
  },

  // ── Advanced — Promoted in 689b–g (6) ────────────────
  {
    id: 'sod_checker',
    number: 13,
    name: 'Segregation of Duties',
    testCount: null,
    standards: ['SOC 1', 'COSO 2013'],
    summary: 'User-role × role-permission matrix analysis against an SoD rule library — per-user risk ranking with mitigating-control suggestions.',
    href: '/tools/sod',
  },
  {
    id: 'intercompany_elimination',
    number: 14,
    name: 'Intercompany Elimination',
    testCount: null,
    standards: ['ASC 810', 'IFRS 10', 'ISA 600'],
    summary: 'Multi-entity TB upload to match reciprocal intercompany balances, propose elimination journal entries, and render a consolidation worksheet.',
    href: '/tools/intercompany',
  },
  {
    id: 'w2_reconciliation',
    number: 15,
    name: 'W-2 / W-3 Reconciliation',
    testCount: null,
    standards: ['IRC §6051', 'Form 941'],
    summary: 'Reconcile payroll YTD to draft W-2s and Form 941 quarterlies before year-end — box mismatches, SS wage-base overages, 941-to-W-2 tie-out gaps.',
    href: '/tools/w2-reconciliation',
  },
  {
    id: 'form_1099',
    number: 16,
    name: 'Form 1099 Preparation',
    testCount: null,
    standards: ['IRC §6041', 'Pub 1220'],
    summary: 'Identify vendors meeting 1099-NEC / 1099-MISC / 1099-INT thresholds — corporate safe-harbor, processor exemptions, W-9-on-file flags.',
    href: '/tools/form-1099',
  },
  {
    id: 'book_to_tax',
    number: 17,
    name: 'Book-to-Tax Reconciliation',
    testCount: null,
    standards: ['Form 1120 Schedule M-1', 'ASC 740'],
    summary: 'Bridge book pretax income to taxable income via Schedule M-1 / M-3 reconciliation; ASC 740 deferred-tax roll with effective-rate reconciliation.',
    href: '/tools/book-to-tax',
  },
  {
    id: 'cash_flow_projector',
    number: 18,
    name: 'Cash Flow Projector',
    testCount: null,
    standards: ['ASC 230'],
    summary: 'Direct-method 90-day cash projection across base / stress / best scenarios — AR/AP aging plus recurring flows for liquidity-breach flagging.',
    href: '/tools/cash-flow-projector',
  },
]

/**
 * Canonical tool count. Must equal TOOL_LEDGER.length and must equal
 * `MARKETING_AUDIT_TOOL_COUNT` in `backend/tools_registry.py`. Both
 * invariants are enforced — TOOL_LEDGER.length by the build-time assertion
 * below, and the cross-language tie by `tests/test_catalog_consistency.py`.
 */
export const CANONICAL_TOOL_COUNT = 18

if (TOOL_LEDGER.length !== CANONICAL_TOOL_COUNT) {
  throw new Error(
    `Tool ledger count mismatch: CANONICAL_TOOL_COUNT=${CANONICAL_TOOL_COUNT} but TOOL_LEDGER has ${TOOL_LEDGER.length} entries`,
  )
}
