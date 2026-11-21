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
 * Sprint 891: tools come from the registry; add a tool there (with `dashboard_description` and
 * `dashboard_icon`) and regenerate with `python scripts/generate_tool_catalog_ts.py`.
 */

import { TOOL_CATALOG } from '@/content/tool-catalog.generated'

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

/**
 * Sprint 891 (16A): derived from the tool registry (backend/tools_registry.py, via the generated
 * content/tool-catalog.generated.ts) — every tool with dashboard details, in registry order. The
 * list used to be kept by hand and was missing the six most recently promoted tools.
 */
const FROM_CATALOG: DashboardToolDef[] = TOOL_CATALOG.filter(t => t.dashboard && t.href).map(t => ({
  key: t.slug,
  label: t.shortLabel,
  href: t.href as string,
  description: t.dashboard!.description,
  category: t.category,
  icon: t.dashboard!.icon as DashboardToolIconKey,
}))

/** Explicit extra: Flux Analysis has a page but is not a registry tool (it is part of multi-period). */
const EXTRAS: DashboardToolDef[] = [
  { key: 'flux_analysis', label: 'Flux Analysis', href: '/flux', description: 'Account-level variance analysis', category: 'Advanced', icon: 'search' },
]

export const DASHBOARD_TOOLS: DashboardToolDef[] = [...FROM_CATALOG, ...EXTRAS]

/** Default favorites surfaced when the user hasn't pinned any. */
export const DEFAULT_FAVORITES: string[] = [
  'trial_balance',
  'journal_entry_testing',
  'ap_testing',
  'revenue_testing',
  'payroll_testing',
  'fixed_asset_testing',
]
