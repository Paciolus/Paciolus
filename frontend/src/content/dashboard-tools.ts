/**
 * Dashboard tool catalog (Sprint 751 — Phase 4 dashboard decomposition).
 *
 * Single source of truth for the dashboard's view of the tool catalog:
 * label, href, description, category, and icon key. Decoupled from
 * `content/tool-ledger.ts` (which serves the marketing homepage with
 * different fields — testCount, standards, summary).
 *
 * The dashboard surface needs: a stable key (`enforce_tool_access` slug),
 * a short label for the Quick Launch grid, a one-line description, a
 * category bucket, and an icon key the `<ToolIcon>` component renders.
 *
 * When adding a tool, also update the homepage `tool-ledger.ts` if the
 * tool should appear on the marketing surface, and verify the icon key
 * exists in `components/dashboard/ToolIcon.tsx::TOOL_ICON_PATHS`.
 */

export type DashboardToolIconKey =
  | 'chart'
  | 'upload'
  | 'shield'
  | 'calculator'
  | 'search'
  | 'banknotes'
  | 'receipt'
  | 'clock'
  | 'cube'
  | 'truck'
  | 'building'
  | 'box'
  | 'percentage'

export type DashboardToolCategory = 'Core Analysis' | 'Testing Suite' | 'Advanced'

export interface DashboardToolDef {
  /** Stable key — matches backend `enforce_tool_access` slug + command palette. */
  key: string
  /** Short label for the Quick Launch grid card. */
  label: string
  /** Canonical tool URL. */
  href: string
  /** One-line description (≤ 60 chars rendered well). */
  description: string
  category: DashboardToolCategory
  icon: DashboardToolIconKey
}

export const DASHBOARD_TOOLS: DashboardToolDef[] = [
  { key: 'trial_balance', label: 'TB Diagnostics', href: '/tools/trial-balance', description: 'Ratio analysis, anomaly detection, lead sheets', category: 'Core Analysis', icon: 'chart' },
  { key: 'multi_period', label: 'Multi-Period', href: '/tools/multi-period', description: 'Trend analysis across reporting periods', category: 'Core Analysis', icon: 'clock' },
  { key: 'bank_reconciliation', label: 'Bank Rec', href: '/tools/bank-rec', description: 'Bank-to-book reconciliation testing', category: 'Core Analysis', icon: 'banknotes' },
  { key: 'three_way_match', label: 'Three-Way Match', href: '/tools/three-way-match', description: 'PO, receipt, and invoice matching', category: 'Core Analysis', icon: 'receipt' },
  { key: 'journal_entry_testing', label: 'JE Testing', href: '/tools/journal-entry-testing', description: '19-test battery: Benford, fraud indicators', category: 'Testing Suite', icon: 'shield' },
  { key: 'ap_testing', label: 'AP Testing', href: '/tools/ap-testing', description: 'Duplicate payments, vendor anomalies', category: 'Testing Suite', icon: 'calculator' },
  { key: 'revenue_testing', label: 'Revenue Testing', href: '/tools/revenue-testing', description: 'ASC 606 / IFRS 15 contract analysis', category: 'Testing Suite', icon: 'banknotes' },
  { key: 'ar_aging', label: 'AR Aging', href: '/tools/ar-aging', description: 'Receivables aging and collectibility', category: 'Testing Suite', icon: 'clock' },
  { key: 'payroll_testing', label: 'Payroll Testing', href: '/tools/payroll-testing', description: 'Ghost employees, rate anomalies', category: 'Testing Suite', icon: 'calculator' },
  { key: 'fixed_asset_testing', label: 'Fixed Assets', href: '/tools/fixed-assets', description: 'Depreciation, impairment, disposals', category: 'Testing Suite', icon: 'building' },
  { key: 'inventory_testing', label: 'Inventory Testing', href: '/tools/inventory-testing', description: 'Valuation, obsolescence, cutoff', category: 'Testing Suite', icon: 'box' },
  { key: 'statistical_sampling', label: 'Stat Sampling', href: '/tools/statistical-sampling', description: 'ISA 530 sample design and evaluation', category: 'Advanced', icon: 'percentage' },
  { key: 'flux_analysis', label: 'Flux Analysis', href: '/flux', description: 'Account-level variance analysis', category: 'Advanced', icon: 'search' },
]

/** Default favorites surfaced when the user hasn't pinned any. */
export const DEFAULT_FAVORITES: string[] = [
  'trial_balance',
  'journal_entry_testing',
  'ap_testing',
  'revenue_testing',
  'payroll_testing',
  'fixed_asset_testing',
]
