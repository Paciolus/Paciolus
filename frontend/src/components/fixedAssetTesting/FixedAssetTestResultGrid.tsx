'use client'

import type { FATestResult, FlaggedFixedAssetEntry } from '@/types/fixedAssetTesting'
import { TestResultGrid, type TierSection } from '@/components/shared/testing/TestResultGrid'

const TIER_SECTIONS: TierSection[] = [
  { tier: 'structural', label: 'Structural Tests (FA-01 to FA-04)' },
  { tier: 'statistical', label: 'Statistical Tests (FA-05 to FA-07)' },
  { tier: 'advanced', label: 'Advanced Tests (FA-08 to FA-09)' },
]

interface FixedAssetTestResultGridProps {
  results: FATestResult[]
}

export function FixedAssetTestResultGrid({ results }: FixedAssetTestResultGridProps) {
  return (
    <TestResultGrid<FlaggedFixedAssetEntry, FATestResult>
      results={results}
      expandedLabel="entries"
      tierSections={TIER_SECTIONS}
      entryRenderer={(fe) => (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-sans text-xs text-content-primary truncate">
              {fe.entry.asset_id || fe.entry.description || 'Unknown Asset'}
              {fe.entry.category && (
                <span className="text-content-tertiary ml-2">{fe.entry.category}</span>
              )}
            </p>
            <p className="font-sans text-xs text-content-secondary mt-0.5">{fe.issue}</p>
          </div>
          <span className="font-mono text-xs text-content-secondary flex-shrink-0">
            ${fe.entry.cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
      )}
    />
  )
}
