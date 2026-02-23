'use client'

import { TestResultGrid, type TierSection } from '@/components/shared/testing/TestResultGrid'
import type { APTestResult, FlaggedAPPayment } from '@/types/apTesting'

const TIER_SECTIONS: TierSection[] = [
  { tier: 'structural', label: 'Structural Tests (T1-T5)' },
  { tier: 'statistical', label: 'Statistical Tests (T6-T10)' },
  { tier: 'advanced', label: 'Fraud Indicators (T11-T13)' },
]

interface APTestResultGridProps {
  results: APTestResult[]
}

export function APTestResultGrid({ results }: APTestResultGridProps) {
  return (
    <TestResultGrid<FlaggedAPPayment, APTestResult>
      results={results}
      expandedLabel="payments"
      tierSections={TIER_SECTIONS}
      tierLabelOverrides={{ advanced: 'Fraud Indicators' }}
      entryRenderer={(fe) => (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-sans text-xs text-content-primary truncate">
              {fe.entry.vendor_name || 'Unknown Vendor'}
              {fe.entry.invoice_number && (
                <span className="text-content-tertiary ml-2">#{fe.entry.invoice_number}</span>
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
