'use client'

/**
 * CommandRow — Sprint 397: Phase LV
 *
 * Individual command row in the palette. Shows icon, label, detail,
 * shortcut hint, and guard status badge (tier_blocked → "Upgrade", unverified → "Verify").
 */

import type { PaletteCommand, GuardStatus, CommandCategory } from '@/types/commandPalette'

interface CommandRowProps {
  command: PaletteCommand
  guardStatus: GuardStatus
  isSelected: boolean
  onSelect: () => void
  onHover: () => void
}

const CATEGORY_ICONS: Record<CommandCategory, string> = {
  navigation: '\u2192',
  tool: '\u2699',
  workspace: 'W',
  action: '+',
  settings: '\u2630',
}

const CATEGORY_COLORS: Record<CommandCategory, string> = {
  navigation: 'bg-obsidian-700 text-oatmeal-400',
  tool: 'bg-sage-500/20 text-sage-400',
  workspace: 'bg-obsidian-700 text-oatmeal-400',
  action: 'bg-sage-500/20 text-sage-400',
  settings: 'bg-obsidian-700 text-oatmeal-400',
}

export function CommandRow({ command, guardStatus, isSelected, onSelect, onHover }: CommandRowProps) {
  const isBlocked = guardStatus !== 'allowed'

  return (
    <button
      data-result-item
      onClick={onSelect}
      onMouseEnter={onHover}
      className={`
        w-full text-left px-3 py-2 flex items-center gap-3 transition-colors
        ${isBlocked ? 'opacity-50' : ''}
        ${isSelected ? 'bg-sage-500/10 text-oatmeal-200' : 'text-oatmeal-400 hover:bg-obsidian-700/50'}
      `}
    >
      {/* Category icon */}
      <span className={`w-6 h-6 rounded-md flex items-center justify-center text-[10px] font-mono shrink-0 ${CATEGORY_COLORS[command.category]}`}>
        {CATEGORY_ICONS[command.category]}
      </span>

      {/* Label + detail */}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-sans truncate">{command.label}</p>
        {command.detail && (
          <p className="text-[10px] font-sans text-oatmeal-500 truncate">{command.detail}</p>
        )}
      </div>

      {/* Guard badge */}
      {guardStatus === 'tier_blocked' && (
        <span className="text-[9px] font-sans font-medium text-clay-400 bg-clay-500/10 px-1.5 py-0.5 rounded shrink-0">
          Upgrade
        </span>
      )}
      {guardStatus === 'unverified' && (
        <span className="text-[9px] font-sans font-medium text-clay-400 bg-clay-500/10 px-1.5 py-0.5 rounded shrink-0">
          Verify
        </span>
      )}

      {/* Shortcut hint */}
      {command.shortcutHint && guardStatus === 'allowed' && (
        <kbd className="text-[9px] font-mono text-oatmeal-500 px-1 py-0.5 bg-obsidian-700/60 border border-obsidian-600/30 rounded shrink-0">
          {command.shortcutHint}
        </kbd>
      )}

      {/* Enter hint when selected */}
      {isSelected && !isBlocked && (
        <kbd className="text-[9px] font-mono text-oatmeal-500 px-1 py-0.5 bg-obsidian-700/60 border border-obsidian-600/30 rounded shrink-0">
          Enter
        </kbd>
      )}
    </button>
  )
}
