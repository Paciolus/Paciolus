/**
 * UnifiedToolbar configuration — Sprint 499
 *
 * Defines tool categories, column layout, and tier badge mapping
 * for the mega-dropdown navigation. Three-zone model: Identity | Primary Nav | User/System.
 */

import type { BrandIconName } from '@/components/shared/BrandIcon/types'

export type TierBadge = 'Solo' | 'Team' | 'Org'

export interface ToolItem {
  label: string
  href: string
  /** Tool key matching backend entitlement names */
  toolKey: string
  /** Minimum tier required */
  tier: TierBadge
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

/** Tier badge styling tokens */
export const TIER_BADGE_STYLES: Record<TierBadge, string> = {
  Solo: 'bg-sage-50 text-sage-700 border-sage-200',
  Team: 'bg-oatmeal-100 text-obsidian-800 border-oatmeal-300',
  Org: 'bg-obsidian-800 text-oatmeal-200 border-obsidian-600',
}

/** Core Analysis column */
const CORE_ANALYSIS: ToolColumn = {
  heading: 'Core Analysis',
  items: [
    { label: 'TB Diagnostics', href: '/tools/trial-balance', toolKey: 'trial_balance', tier: 'Solo' },
    { label: 'Multi-Period Analysis', href: '/tools/multi-period', toolKey: 'multi_period', tier: 'Solo' },
    { label: 'Bank Reconciliation', href: '/tools/bank-rec', toolKey: 'bank_reconciliation', tier: 'Team' },
    { label: 'Three-Way Match', href: '/tools/three-way-match', toolKey: 'three_way_match', tier: 'Team' },
  ],
}

/** Testing Suite column */
const TESTING_SUITE: ToolColumn = {
  heading: 'Testing Suite',
  items: [
    { label: 'Journal Entry Testing', href: '/tools/journal-entry-testing', toolKey: 'journal_entry', tier: 'Solo' },
    { label: 'AP Testing', href: '/tools/ap-testing', toolKey: 'ap_testing', tier: 'Solo' },
    { label: 'Revenue Testing', href: '/tools/revenue-testing', toolKey: 'revenue_testing', tier: 'Team' },
    { label: 'AR Aging', href: '/tools/ar-aging', toolKey: 'ar_aging', tier: 'Team' },
    { label: 'Payroll Testing', href: '/tools/payroll-testing', toolKey: 'payroll_testing', tier: 'Team' },
    { label: 'Fixed Assets', href: '/tools/fixed-assets', toolKey: 'fixed_assets', tier: 'Team' },
    { label: 'Inventory Testing', href: '/tools/inventory-testing', toolKey: 'inventory_testing', tier: 'Team' },
  ],
}

/** Advanced column */
const ADVANCED: ToolColumn = {
  heading: 'Advanced',
  items: [
    { label: 'Statistical Sampling', href: '/tools/statistical-sampling', toolKey: 'statistical_sampling', tier: 'Org' },
    { label: 'Flux Analysis', href: '/flux', toolKey: 'flux_analysis', tier: 'Solo' },
    { label: 'Reconciliation Intel', href: '/recon', toolKey: 'reconciliation_intel', tier: 'Org' },
  ],
}

/** Account column nav items */
export const ACCOUNT_NAV: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Portfolio', href: '/portfolio' },
  { label: 'Workspaces', href: '/engagements' },
  { label: 'History', href: '/history' },
  { label: 'Profile', href: '/settings/profile', dividerAbove: true },
  { label: 'Practice Settings', href: '/settings/practice' },
  { label: 'Billing', href: '/settings/billing' },
]

/** All 3 tool columns for the mega-dropdown */
export const TOOL_COLUMNS: ToolColumn[] = [CORE_ANALYSIS, TESTING_SUITE, ADVANCED]

/** Primary nav links shown in the toolbar center zone (ordered by frequency of use) */
export const TOOLBAR_NAV: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: 'bar-chart' },
  { label: 'Workspaces', href: '/engagements', icon: 'clipboard-check' },
  { label: 'Portfolio', href: '/portfolio', icon: 'building' },
  { label: 'History', href: '/history', icon: 'clock' },
]

/** All tool hrefs for active-page detection */
export const ALL_TOOL_HREFS = TOOL_COLUMNS.flatMap(col => col.items.map(i => i.href))
