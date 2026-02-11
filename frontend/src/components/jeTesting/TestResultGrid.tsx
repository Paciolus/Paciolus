'use client'

import type { JETestResult, FlaggedJournalEntry } from '@/types/jeTesting'
import { TestResultGrid as SharedTestResultGrid, type TierSection } from '@/components/shared/testing/TestResultGrid'

const TIER_SECTIONS: TierSection[] = [
  { tier: 'structural', label: 'Structural Tests (T1-T5)' },
  { tier: 'statistical', label: 'Statistical Tests (T6-T8)' },
  { tier: 'advanced', label: 'Advanced Tests (T9-T18)' },
]

interface TestResultGridProps {
  results: JETestResult[]
}

export function TestResultGrid({ results }: TestResultGridProps) {
  return (
    <SharedTestResultGrid<FlaggedJournalEntry, JETestResult>
      results={results}
      expandedLabel="entries"
      tierSections={TIER_SECTIONS}
      entryRenderer={(fe) => (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-sans text-xs text-content-primary truncate">
              {fe.entry.account || 'Unknown Account'}
              {fe.entry.entry_id && (
                <span className="text-content-tertiary ml-2">#{fe.entry.entry_id}</span>
              )}
            </p>
            <p className="font-sans text-xs text-content-secondary mt-0.5">{fe.issue}</p>
          </div>
          <span className="font-mono text-xs text-content-secondary flex-shrink-0">
            ${Math.abs(fe.entry.debit || fe.entry.credit || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
      )}
    />
  )
}
