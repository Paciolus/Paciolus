'use client'

import type { ARTestResult, FlaggedAREntry } from '@/types/arAging'
import { TestResultGrid, type TierSection } from '@/components/shared/testing/TestResultGrid'

const TIER_SECTIONS: TierSection[] = [
  { tier: 'structural', label: 'Structural Tests (AR-01 to AR-04)' },
  { tier: 'statistical', label: 'Statistical Tests (AR-05 to AR-09)' },
  { tier: 'advanced', label: 'Advanced Tests (AR-10 to AR-11)' },
]

interface ARTestResultGridProps {
  results: ARTestResult[]
}

export function ARTestResultGrid({ results }: ARTestResultGridProps) {
  return (
    <TestResultGrid<FlaggedAREntry, ARTestResult>
      results={results}
      expandedLabel="items"
      tierSections={TIER_SECTIONS}
      entryRenderer={(fe) => (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-sans text-xs text-content-primary truncate">
              {fe.entry.customer_name || fe.entry.account_name || fe.entry.account_number || 'Unknown'}
              {fe.entry.aging_days != null && (
                <span className="text-content-tertiary ml-2">{fe.entry.aging_days}d</span>
              )}
            </p>
            <p className="font-sans text-xs text-content-secondary mt-0.5">{fe.issue}</p>
          </div>
          <span className="font-mono text-xs text-content-secondary flex-shrink-0">
            ${Math.abs(fe.entry.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
      )}
    />
  )
}
