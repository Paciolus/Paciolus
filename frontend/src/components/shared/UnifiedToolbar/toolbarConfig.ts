/**
 * UnifiedToolbar configuration — Sprint 499
 *
 * Defines tool categories, column layout, and tier badge mapping
 * for the mega-dropdown navigation. Three-zone model: Identity | Primary Nav | User/System.
 */

import type { BrandIconName } from '@/components/shared/BrandIcon/types'

export interface ToolItem {
  label: string
  href: string
  /** Tool key matching backend entitlement names */
  toolKey: string
}

export interface NavItem {
  label: string
  href: string
  /** BrandIcon name for icon+label nav items */
  icon?: BrandIconName
  /** Whether this is a divider before this item */
  dividerAbove?: boolean
}

export interface ToolColumn {
  heading: string
  items: ToolItem[]
}

/** Core Analysis column */
const CORE_ANALYSIS: ToolColumn = {
  heading: 'Core Analysis',
  items: [
    { label: 'TB Diagnostics', href: '/tools/trial-balance', toolKey: 'trial_balance' },
    { label: 'Multi-Period Analysis', href: '/tools/multi-period', toolKey: 'multi_period' },
    { label: 'Bank Reconciliation', href: '/tools/bank-rec', toolKey: 'bank_reconciliation' },
    { label: 'Three-Way Match', href: '/tools/three-way-match', toolKey: 'three_way_match' },
  ],
}

/** Testing Suite column */
const TESTING_SUITE: ToolColumn = {
  heading: 'Testing Suite',
  items: [
    { label: 'Journal Entry Testing', href: '/tools/journal-entry-testing', toolKey: 'journal_entry_testing' },
    { label: 'AP Testing', href: '/tools/ap-testing', toolKey: 'ap_testing' },
    { label: 'Revenue Testing', href: '/tools/revenue-testing', toolKey: 'revenue_testing' },
    { label: 'AR Aging', href: '/tools/ar-aging', toolKey: 'ar_aging' },
    { label: 'Payroll Testing', href: '/tools/payroll-testing', toolKey: 'payroll_testing' },
    { label: 'Fixed Assets', href: '/tools/fixed-assets', toolKey: 'fixed_asset_testing' },
    { label: 'Inventory Testing', href: '/tools/inventory-testing', toolKey: 'inventory_testing' },
    { label: 'Segregation of Duties', href: '/tools/sod', toolKey: 'sod_checker' },
  ],
}

/** Tax & Filings column — Sprint 788 (the 689d-f tools, previously unreachable here) */
const TAX_AND_FILINGS: ToolColumn = {
  heading: 'Tax & Filings',
  items: [
    { label: 'W-2 / W-3 Reconciliation', href: '/tools/w2-reconciliation', toolKey: 'w2_reconciliation' },
    { label: 'Form 1099 Preparation', href: '/tools/form-1099', toolKey: 'form_1099' },
    { label: 'Book-to-Tax', href: '/tools/book-to-tax', toolKey: 'book_to_tax' },
  ],
}

/** Advanced column */
const ADVANCED: ToolColumn = {
  heading: 'Advanced',
  items: [
    { label: 'Statistical Sampling', href: '/tools/statistical-sampling', toolKey: 'statistical_sampling' },
    { label: 'Intercompany Elimination', href: '/tools/intercompany', toolKey: 'intercompany_elimination' },
    { label: 'Cash Flow Projector', href: '/tools/cash-flow-projector', toolKey: 'cash_flow_projector' },
    { label: 'Flux Analysis', href: '/flux', toolKey: 'flux_analysis' },
    { label: 'Reconciliation Intel', href: '/recon', toolKey: 'reconciliation_intel' },
  ],
}

/** Account column nav items */
export const ACCOUNT_NAV: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Portfolio', href: '/portfolio' },
  { label: 'History', href: '/history' },
  { label: 'Profile', href: '/settings/profile', dividerAbove: true },
  { label: 'Practice Settings', href: '/settings/practice' },
  { label: 'Billing', href: '/settings/billing' },
]

/** All tool columns for the mega-dropdown.
 *
 * Every tool in `content/tool-ledger.ts` must appear in exactly one column —
 * enforced by `__tests__/MegaDropdown.test.tsx`. The ledger is itself tied to
 * `backend/tools_registry.py` by `tests/test_catalog_consistency.py`, so the
 * chain registry -> ledger -> navigation is now closed end to end.
 */
export const TOOL_COLUMNS: ToolColumn[] = [CORE_ANALYSIS, TESTING_SUITE, TAX_AND_FILINGS, ADVANCED]

/** Primary nav links shown in the toolbar center zone (ordered by frequency of use) */
export const TOOLBAR_NAV: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: 'bar-chart' },
  { label: 'Portfolio', href: '/portfolio', icon: 'building' },
  { label: 'History', href: '/history', icon: 'clock' },
]

/** All tool hrefs for active-page detection (includes /tools catalog) */
export const ALL_TOOL_HREFS = ['/tools', ...TOOL_COLUMNS.flatMap(col => col.items.map(i => i.href))]
