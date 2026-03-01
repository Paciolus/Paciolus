/**
 * Command Registry — Sprint 396: Phase LV
 *
 * Static command definitions + scoring algorithm for the universal command palette.
 * Tool commands mirror ToolNav's TOOLS array; guards mirror UpgradeGate's TIER_TOOLS.
 */

import type {
  PaletteCommand,
  ScoredCommand,
  CommandGuard,
  GuardStatus,
  UserTier,
} from '@/types/commandPalette'

// --- Tier order for comparison ---

const TIER_ORDER: UserTier[] = ['free', 'solo', 'professional', 'team']

function tierIndex(tier: UserTier): number {
  const idx = TIER_ORDER.indexOf(tier)
  return idx === -1 ? 0 : idx
}

// --- Tool tier guards (mirrors UpgradeGate TIER_TOOLS) ---

const FREE_TOOLS = new Set(['trial_balance', 'flux_analysis'])
const SOLO_TOOLS = new Set([
  'trial_balance', 'flux_analysis', 'journal_entry_testing',
  'multi_period', 'prior_period', 'adjustments',
  'ap_testing', 'bank_reconciliation', 'revenue_testing',
])

function toolGuard(toolName: string): CommandGuard | undefined {
  // Team+ has unrestricted access (professional deprecated → maps to solo)
  if (FREE_TOOLS.has(toolName) && SOLO_TOOLS.has(toolName)) return undefined
  if (!FREE_TOOLS.has(toolName) && !SOLO_TOOLS.has(toolName)) {
    return { minTier: 'team' }
  }
  if (!FREE_TOOLS.has(toolName) && SOLO_TOOLS.has(toolName)) {
    return { minTier: 'solo' }
  }
  return undefined
}

// --- Base commands ---

const NAV_COMMANDS: PaletteCommand[] = [
  {
    id: 'nav:home',
    label: 'Home',
    detail: 'Go to homepage',
    category: 'navigation',
    keywords: ['homepage', 'landing'],
    action: () => { /* wired at runtime via router */ },
    priority: 5,
  },
  {
    id: 'nav:portfolio',
    label: 'Client Portfolio',
    detail: 'Manage clients',
    category: 'navigation',
    keywords: ['clients', 'portfolio', 'manage'],
    shortcutHint: 'Cmd+1',
    action: () => {},
    priority: 8,
  },
  {
    id: 'nav:engagements',
    label: 'Diagnostic Workspace',
    detail: 'Manage workspaces',
    category: 'navigation',
    keywords: ['workspaces', 'engagements', 'diagnostic'],
    shortcutHint: 'Cmd+2',
    action: () => {},
    priority: 8,
  },
  {
    id: 'nav:tools',
    label: 'Tools',
    detail: 'Open diagnostic tools',
    category: 'navigation',
    keywords: ['tools', 'diagnostic', 'suite'],
    action: () => {},
    priority: 6,
  },
  {
    id: 'nav:settings',
    label: 'Settings',
    detail: 'Account settings',
    category: 'settings',
    keywords: ['settings', 'account', 'profile', 'preferences'],
    action: () => {},
    priority: 4,
  },
  {
    id: 'nav:billing',
    label: 'Billing',
    detail: 'Subscription & billing',
    category: 'settings',
    keywords: ['billing', 'subscription', 'plan', 'payment', 'upgrade'],
    action: () => {},
    priority: 3,
  },
  {
    id: 'nav:practice',
    label: 'Practice Settings',
    detail: 'Firm settings & branding',
    category: 'settings',
    keywords: ['practice', 'firm', 'branding'],
    action: () => {},
    priority: 3,
  },
]

// Tool entries built from ToolNav's structure
const TOOL_ENTRIES: { id: string; label: string; href: string; toolName: string; keywords: string[] }[] = [
  { id: 'tool:tb-diagnostics', label: 'TB Diagnostics', href: '/tools/trial-balance', toolName: 'trial_balance', keywords: ['trial', 'balance', 'diagnostics', 'tb'] },
  { id: 'tool:multi-period', label: 'Multi-Period Comparison', href: '/tools/multi-period', toolName: 'multi_period', keywords: ['multi', 'period', 'comparison', 'trend'] },
  { id: 'tool:je-testing', label: 'Journal Entry Testing', href: '/tools/journal-entry-testing', toolName: 'journal_entry_testing', keywords: ['journal', 'entry', 'je', 'testing'] },
  { id: 'tool:ap-testing', label: 'AP Payment Testing', href: '/tools/ap-testing', toolName: 'ap_testing', keywords: ['accounts', 'payable', 'ap', 'payment'] },
  { id: 'tool:bank-rec', label: 'Bank Reconciliation', href: '/tools/bank-rec', toolName: 'bank_reconciliation', keywords: ['bank', 'reconciliation', 'rec', 'statement'] },
  { id: 'tool:payroll-testing', label: 'Payroll Testing', href: '/tools/payroll-testing', toolName: 'payroll_testing', keywords: ['payroll', 'employee', 'salary'] },
  { id: 'tool:three-way-match', label: 'Three-Way Match', href: '/tools/three-way-match', toolName: 'three_way_match', keywords: ['three', 'way', 'match', 'po', 'invoice', 'receipt'] },
  { id: 'tool:revenue-testing', label: 'Revenue Testing', href: '/tools/revenue-testing', toolName: 'revenue_testing', keywords: ['revenue', 'income', 'sales'] },
  { id: 'tool:ar-aging', label: 'AR Aging Analysis', href: '/tools/ar-aging', toolName: 'ar_aging', keywords: ['accounts', 'receivable', 'ar', 'aging'] },
  { id: 'tool:fixed-assets', label: 'Fixed Asset Testing', href: '/tools/fixed-assets', toolName: 'fixed_asset_testing', keywords: ['fixed', 'asset', 'ppe', 'depreciation'] },
  { id: 'tool:inventory-testing', label: 'Inventory Testing', href: '/tools/inventory-testing', toolName: 'inventory_testing', keywords: ['inventory', 'stock', 'warehouse'] },
  { id: 'tool:statistical-sampling', label: 'Statistical Sampling', href: '/tools/statistical-sampling', toolName: 'statistical_sampling', keywords: ['sampling', 'statistical', 'mus', 'isa530'] },
]

const TOOL_COMMANDS: PaletteCommand[] = TOOL_ENTRIES.map(t => ({
  id: t.id,
  label: t.label,
  detail: t.href,
  category: 'tool' as const,
  keywords: t.keywords,
  action: () => {},
  guard: toolGuard(t.toolName),
  priority: 7,
}))

const ACTION_COMMANDS: PaletteCommand[] = [
  {
    id: 'action:new-workspace',
    label: 'New Workspace',
    detail: 'Create a new diagnostic workspace',
    category: 'action',
    keywords: ['new', 'create', 'workspace', 'engagement'],
    action: () => {},
    priority: 6,
  },
]

export const BASE_COMMANDS: PaletteCommand[] = [
  ...NAV_COMMANDS,
  ...TOOL_COMMANDS,
  ...ACTION_COMMANDS,
]

/** Navigation href map for wiring actions at runtime */
export const COMMAND_HREFS: Record<string, string> = {
  'nav:home': '/',
  'nav:portfolio': '/portfolio',
  'nav:engagements': '/engagements',
  'nav:tools': '/tools/trial-balance',
  'nav:settings': '/settings',
  'nav:billing': '/settings/billing',
  'nav:practice': '/settings/practice',
  'action:new-workspace': '/engagements?new=1',
  ...Object.fromEntries(TOOL_ENTRIES.map(t => [t.id, t.href])),
}

// --- Fuzzy matching (extracted from QuickSwitcher) ---

export function fuzzyMatch(query: string, text: string): boolean {
  const q = query.toLowerCase()
  const t = text.toLowerCase()
  if (t.includes(q)) return true

  // Simple subsequence match
  let qi = 0
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) qi++
  }
  return qi === q.length
}

// --- Scoring ---

const RECENCY_LIMIT = 10

export function scoreCommand(
  command: PaletteCommand,
  query: string,
  recentIds: string[],
): number {
  if (!query) {
    // No query: priority + recency only
    let score = command.priority ?? 0
    const recencyIdx = recentIds.indexOf(command.id)
    if (recencyIdx !== -1 && recencyIdx < RECENCY_LIMIT) {
      score += 15 - (recencyIdx * 2)
    }
    return score
  }

  const q = query.toLowerCase()
  let score = 0

  // Label matching
  const label = command.label.toLowerCase()
  if (label.startsWith(q)) {
    score += 100
  } else if (label.includes(q)) {
    score += 70
  } else if (fuzzyMatch(q, label)) {
    score += 40
  }

  // Keyword matching
  if (command.keywords?.some(kw => kw.toLowerCase().includes(q))) {
    score += 20
  }

  // Detail matching
  if (command.detail && command.detail.toLowerCase().includes(q)) {
    score += 10
  }

  // Recency bonus
  const recencyIdx = recentIds.indexOf(command.id)
  if (recencyIdx !== -1 && recencyIdx < RECENCY_LIMIT) {
    score += 15 - (recencyIdx * 2)
  }

  // Priority bonus
  score += (command.priority ?? 0)

  return score
}

// --- Guard evaluation ---

export function evaluateGuard(
  guard: CommandGuard | undefined,
  user: { tier?: UserTier; is_verified?: boolean } | null,
): GuardStatus {
  if (!guard) return 'allowed'

  if (guard.requireVerified && !user?.is_verified) {
    return 'unverified'
  }

  if (guard.minTier) {
    const userTier = user?.tier ?? 'free'
    if (tierIndex(userTier) < tierIndex(guard.minTier)) {
      return 'tier_blocked'
    }
  }

  if (guard.predicate && !guard.predicate()) {
    return 'tier_blocked'
  }

  return 'allowed'
}

// --- Full scoring pipeline ---

export function scoreAndFilterCommands(
  commands: PaletteCommand[],
  query: string,
  recentIds: string[],
  user: { tier?: UserTier; is_verified?: boolean } | null,
): ScoredCommand[] {
  return commands
    .map(command => ({
      command,
      score: scoreCommand(command, query, recentIds),
      guardStatus: evaluateGuard(command.guard, user),
    }))
    .filter(sc => query === '' || sc.score > 0)
    .sort((a, b) => b.score - a.score)
}
