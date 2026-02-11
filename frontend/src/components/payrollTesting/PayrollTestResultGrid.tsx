'use client'

import type { PayrollTestResult, FlaggedPayrollEntry } from '@/types/payrollTesting'
import { TestResultGrid, type TierSection } from '@/components/shared/testing/TestResultGrid'

const TIER_SECTIONS: TierSection[] = [
  { tier: 'structural', label: 'Structural Tests (PR-T1 to PR-T5)' },
  { tier: 'statistical', label: 'Statistical Tests (PR-T6 to PR-T8)' },
  { tier: 'advanced', label: 'Fraud Indicators (PR-T9 to PR-T11)' },
]

interface PayrollTestResultGridProps {
  results: PayrollTestResult[]
}

export function PayrollTestResultGrid({ results }: PayrollTestResultGridProps) {
  return (
    <TestResultGrid<FlaggedPayrollEntry, PayrollTestResult>
      results={results}
      expandedLabel="employees"
      tierSections={TIER_SECTIONS}
      tierLabelOverrides={{ advanced: 'Fraud Indicators' }}
      entryRenderer={(fe) => (
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-sans text-xs text-content-primary truncate">
              {fe.entry.employee_name || 'Unknown Employee'}
              {fe.entry.employee_id && (
                <span className="text-content-tertiary ml-2">#{fe.entry.employee_id}</span>
              )}
            </p>
            <p className="font-sans text-xs text-content-secondary mt-0.5">{fe.issue}</p>
          </div>
          <span className="font-mono text-xs text-content-secondary flex-shrink-0">
            ${Math.abs(fe.entry.gross_pay).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>
      )}
    />
  )
}
