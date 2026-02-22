/**
 * Command Palette Types — Sprint 396: Phase LV
 *
 * Type definitions for the universal command palette system.
 * Used by commandRegistry, CommandPaletteContext, and GlobalCommandPalette.
 */

export type CommandCategory = 'navigation' | 'tool' | 'workspace' | 'action' | 'settings'

export type UserTier = 'free' | 'starter' | 'professional' | 'team' | 'enterprise'

export type GuardStatus = 'allowed' | 'tier_blocked' | 'unverified'

export interface CommandGuard {
  /** Minimum tier required to execute this command */
  minTier?: UserTier
  /** Whether email verification is required */
  requireVerified?: boolean
  /** Custom predicate for dynamic gating */
  predicate?: () => boolean
}

export interface PaletteCommand {
  /** Unique identifier (e.g., 'nav:portfolio', 'tool:revenue-testing') */
  id: string
  /** Display label shown in the palette */
  label: string
  /** Secondary text (e.g., tool description, page subtitle) */
  detail?: string
  /** Category for grouping */
  category: CommandCategory
  /** Additional search keywords (not displayed) */
  keywords?: string[]
  /** BrandIcon name or category-based default */
  icon?: string
  /** Keyboard shortcut hint (e.g., 'Cmd+1') */
  shortcutHint?: string
  /** Action to execute on selection */
  action: () => void
  /** Access guard (tier, verification, custom) */
  guard?: CommandGuard
  /** Static priority boost (higher = appears first when scores tie) */
  priority?: number
}

export interface ScoredCommand {
  command: PaletteCommand
  score: number
  guardStatus: GuardStatus
}
