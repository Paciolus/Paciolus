'use client'

import type { RevenueTestResult, FlaggedRevenueEntry } from '@/types/revenueTesting'
import { TestResultGrid, type TierSection } from '@/components/shared/testing/TestResultGrid'

const TIER_SECTIONS: TierSection[] = [
  { tier: 'structural', label: 'Structural Tests (RT-01 to RT-05)' },
  { tier: 'statistical', label: 'Statistical Tests (RT-06 to RT-09)' },
  { tier: 'advanced', label: 'Advanced Tests (RT-10 to RT-12)' },
]

interface RevenueTestResultGridProps {
  results: RevenueTestResult[]
}

export function RevenueTestResultGrid({ results }: RevenueTestResultGridProps) {
  return (
    <TestResultGrid<FlaggedRevenueEntry, RevenueTestResult>
      results={results}
      expandedLabel="entries"
      tierSections={TIER_SECTIONS}
      entryRenderer={(fe) => (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-sans text-xs text-content-primary truncate">
              {fe.entry.account_name || fe.entry.account_number || 'Unknown Account'}
              {fe.entry.date && (
                <span className="text-content-tertiary ml-2">{fe.entry.date}</span>
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
