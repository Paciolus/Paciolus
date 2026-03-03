'use client'

import { TestResultGrid, type TierSection } from '@/components/shared/testing/TestResultGrid'
import type { InvTestResult, FlaggedInventoryEntry } from '@/types/inventoryTesting'

const TIER_SECTIONS: TierSection[] = [
  { tier: 'structural', label: 'Structural Tests' },
  { tier: 'statistical', label: 'Statistical Tests' },
  { tier: 'advanced', label: 'Advanced Tests' },
]

interface InventoryTestResultGridProps {
  results: InvTestResult[]
}

export function InventoryTestResultGrid({ results }: InventoryTestResultGridProps) {
  return (
    <TestResultGrid<FlaggedInventoryEntry, InvTestResult>
      results={results}
      expandedLabel="entries"
      tierSections={TIER_SECTIONS}
      entryRenderer={(fe) => (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-sans text-xs text-content-primary truncate">
              {fe.entry.item_id || fe.entry.description || 'Unknown Item'}
              {fe.entry.category && (
                <span className="text-content-tertiary ml-2">{fe.entry.category}</span>
              )}
            </p>
            <p className="font-sans text-xs text-content-secondary mt-0.5">{fe.issue}</p>
          </div>
          <span className="font-mono text-xs text-content-secondary flex-shrink-0">
            ${fe.entry.extended_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
      )}
    />
  )
}
