'use client'

/**
 * CommandGroup — Sprint 397: Phase LV
 *
 * Groups scored commands by category with a label header.
 */

import type { ScoredCommand, CommandCategory } from '@/types/commandPalette'
import { CommandRow } from './CommandRow'

interface CommandGroupProps {
  category: CommandCategory
  label: string
  items: ScoredCommand[]
  selectedIndex: number
  flatOffset: number
  onSelect: (index: number) => void
  onHover: (index: number) => void
}

export function CommandGroup({
  label,
  items,
  selectedIndex,
  flatOffset,
  onSelect,
  onHover,
}: CommandGroupProps) {
  if (items.length === 0) return null

  return (
    <div>
      <p className="text-[10px] font-sans font-medium text-oatmeal-500 uppercase tracking-wider px-3 pt-3 pb-1">
        {label}
      </p>
      {items.map((sc, i) => {
        const flatIndex = flatOffset + i
        return (
          <CommandRow
            key={sc.command.id}
            command={sc.command}
            guardStatus={sc.guardStatus}
            isSelected={flatIndex === selectedIndex}
            onSelect={() => onSelect(flatIndex)}
            onHover={() => onHover(flatIndex)}
          />
        )
      })}
    </div>
  )
}
