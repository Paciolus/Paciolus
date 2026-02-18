'use client'

import { useState } from 'react'
import type { AccrualCompletenessReport } from '@/types/accrualCompleteness'

interface AccrualCompletenessSectionProps {
  data: AccrualCompletenessReport
  onExportPDF?: () => void
  onExportCSV?: () => void
}

function formatCurrency(value: number): string {
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function AccrualCompletenessSection({ data, onExportPDF, onExportCSV }: AccrualCompletenessSectionProps) {
  const [expanded, setExpanded] = useState(false)

  const ratioLabel = data.accrual_to_run_rate_pct !== null
    ? `${data.accrual_to_run_rate_pct.toFixed(1)}%`
    : 'N/A'

  return (
    <div className="theme-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface-card-secondary transition-colors"
      >
        <div className="flex items-center gap-3">
          <h3 className="font-serif text-sm text-content-primary">Accrual Completeness Estimator</h3>
          <span className="px-2 py-0.5 rounded-full bg-oatmeal-50 border border-oatmeal-200 text-xs font-mono text-content-secondary">
            {data.accrual_account_count} account{data.accrual_account_count !== 1 ? 's' : ''}
          </span>
          {data.prior_available && (
            <span className={`px-2 py-0.5 rounded-full border text-xs font-sans ${
              data.below_threshold
                ? 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300'
                : 'bg-sage-50 text-sage-700 border-sage-200'
            }`}>
              Ratio: {ratioLabel}
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-content-tertiary transform transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-theme">
          {/* Flag Card */}
          <div className="px-6 py-4 border-b border-theme">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Total Accrued:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.total_accrued_balance)}</span>
              </div>
              {data.monthly_run_rate !== null && (
                <div className="flex justify-between">
                  <span className="text-content-secondary font-sans">Monthly Run-Rate:</span>
                  <span className="font-mono text-content-primary">{formatCurrency(data.monthly_run_rate)}</span>
                </div>
              )}
              {data.accrual_to_run_rate_pct !== null && (
                <div className="flex justify-between">
                  <span className="text-content-secondary font-sans">Ratio:</span>
                  <span className="font-mono text-content-primary">{data.accrual_to_run_rate_pct.toFixed(1)}%</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Threshold:</span>
                <span className="font-mono text-content-primary">{data.threshold_pct.toFixed(0)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Below Threshold:</span>
                <span className="font-sans text-content-primary">{data.below_threshold ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Prior Data:</span>
                <span className="font-sans text-content-primary">{data.prior_available ? 'Available' : 'Not provided'}</span>
              </div>
            </div>
          </div>

          {/* Narrative */}
          {data.narrative && (
            <div className="px-6 py-3 border-b border-theme">
              <p className="font-sans text-xs text-content-secondary leading-relaxed">{data.narrative}</p>
            </div>
          )}

          {/* Accrual Accounts Table */}
          {data.accrual_accounts.length > 0 && (
            <div className="px-6 py-4 border-b border-theme">
              <h4 className="font-serif text-xs text-content-secondary mb-3">
                Identified Accrual Accounts ({data.accrual_account_count})
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-theme">
                      <th className="text-left font-serif text-content-secondary py-1.5 pr-2">Account</th>
                      <th className="text-right font-serif text-content-secondary py-1.5 pr-2">Balance</th>
                      <th className="text-left font-serif text-content-secondary py-1.5">Keyword</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.accrual_accounts.map((acct, idx) => (
                      <tr key={idx} className="border-b border-theme-divider last:border-b-0">
                        <td className="font-sans text-content-primary py-1.5 pr-2 max-w-[250px] truncate">{acct.account_name}</td>
                        <td className="font-mono text-content-primary text-right py-1.5 pr-2">{formatCurrency(acct.balance)}</td>
                        <td className="font-sans text-content-tertiary py-1.5">{acct.matched_keyword}</td>
                      </tr>
                    ))}
                    <tr className="border-t border-theme font-medium">
                      <td className="font-sans text-content-primary py-1.5 pr-2">Total</td>
                      <td className="font-mono text-content-primary text-right py-1.5 pr-2">{formatCurrency(data.total_accrued_balance)}</td>
                      <td className="py-1.5"></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Export buttons */}
          {(onExportPDF || onExportCSV) && (
            <div className="px-6 py-3 flex gap-2">
              {onExportPDF && (
                <button
                  onClick={onExportPDF}
                  className="px-3 py-1.5 text-xs font-sans rounded-lg border border-theme bg-surface-card-secondary text-content-secondary hover:bg-oatmeal-100 transition-colors"
                >
                  Export PDF
                </button>
              )}
              {onExportCSV && (
                <button
                  onClick={onExportCSV}
                  className="px-3 py-1.5 text-xs font-sans rounded-lg border border-theme bg-surface-card-secondary text-content-secondary hover:bg-oatmeal-100 transition-colors"
                >
                  Export CSV
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
