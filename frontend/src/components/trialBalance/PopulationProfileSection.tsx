'use client'

import { useState } from 'react'
import type { PopulationProfile } from '@/types/populationProfile'

interface PopulationProfileSectionProps {
  data: PopulationProfile
  onExportPDF?: () => void
  onExportCSV?: () => void
}

const GINI_COLORS: Record<string, string> = {
  Low: 'bg-sage-50 text-sage-700 border-sage-200',
  Moderate: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
  High: 'bg-clay-50 text-clay-700 border-clay-200',
  'Very High': 'bg-clay-50 text-clay-700 border-clay-200',
}

function formatCurrency(value: number): string {
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function PopulationProfileSection({ data, onExportPDF, onExportCSV }: PopulationProfileSectionProps) {
  const [expanded, setExpanded] = useState(false)

  const maxBucketCount = Math.max(...data.buckets.map(b => b.count), 1)

  return (
    <div className="theme-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface-card-secondary transition-colors"
      >
        <div className="flex items-center gap-3">
          <h3 className="font-serif text-sm text-content-primary">TB Population Profile</h3>
          <span className="px-2 py-0.5 rounded-full bg-oatmeal-50 border border-oatmeal-200 text-xs font-mono text-content-secondary">
            {data.account_count.toLocaleString()} accounts
          </span>
          <span className={`px-2 py-0.5 rounded-full border text-xs font-sans ${GINI_COLORS[data.gini_interpretation] || GINI_COLORS.Low}`}>
            Gini: {data.gini_coefficient.toFixed(2)} ({data.gini_interpretation})
          </span>
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
          {/* Summary Stats Grid */}
          <div className="px-6 py-4 border-b border-theme">
            <h4 className="font-serif text-xs text-content-secondary mb-3">Descriptive Statistics</h4>
            <div className="grid grid-cols-3 gap-x-6 gap-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Mean:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.mean_abs_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Median:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.median_abs_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Std Dev:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.std_dev_abs_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Min:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.min_abs_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Max:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.max_abs_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Total:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.total_abs_balance)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">P25:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.p25)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">P75:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.p75)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">IQR:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.p75 - data.p25)}</span>
              </div>
            </div>
          </div>

          {/* Magnitude Distribution */}
          <div className="px-6 py-4 border-b border-theme">
            <h4 className="font-serif text-xs text-content-secondary mb-3">Magnitude Distribution</h4>
            <div className="space-y-1.5">
              {data.buckets.map((bucket) => (
                <div key={bucket.label} className="flex items-center gap-3 text-xs">
                  <span className="w-24 text-content-secondary font-sans truncate">{bucket.label}</span>
                  <div className="flex-1 h-4 bg-oatmeal-50 rounded-sm overflow-hidden">
                    <div
                      className="h-full bg-sage-400 rounded-sm transition-all"
                      style={{ width: `${(bucket.count / maxBucketCount) * 100}%` }}
                    />
                  </div>
                  <span className="w-10 text-right font-mono text-content-primary">{bucket.count}</span>
                  <span className="w-14 text-right font-mono text-content-tertiary">{bucket.percent_count.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </div>

          {/* Gini Callout */}
          <div className="px-6 py-3 border-b border-theme">
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border ${GINI_COLORS[data.gini_interpretation] || GINI_COLORS.Low}`}>
              <span className="font-mono text-sm font-medium">{data.gini_coefficient.toFixed(4)}</span>
              <span className="text-xs font-sans">{data.gini_interpretation} Concentration</span>
            </div>
            <p className="font-sans text-xs text-content-tertiary mt-2">
              A Gini of 0 means all accounts have equal balances; 1.0 means one account holds all value.
            </p>
          </div>

          {/* Top-10 Accounts */}
          {data.top_accounts.length > 0 && (
            <div className="px-6 py-4 border-b border-theme">
              <h4 className="font-serif text-xs text-content-secondary mb-3">
                Top {data.top_accounts.length} Accounts by Absolute Balance
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-theme">
                      <th className="text-left font-serif text-content-secondary py-1.5 pr-2">#</th>
                      <th className="text-left font-serif text-content-secondary py-1.5 pr-2">Account</th>
                      <th className="text-left font-serif text-content-secondary py-1.5 pr-2">Category</th>
                      <th className="text-right font-serif text-content-secondary py-1.5 pr-2">Net Balance</th>
                      <th className="text-right font-serif text-content-secondary py-1.5">% of Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.top_accounts.map((acct) => (
                      <tr key={acct.rank} className="border-b border-theme-divider last:border-b-0">
                        <td className="font-mono text-content-tertiary py-1.5 pr-2">{acct.rank}</td>
                        <td className="font-sans text-content-primary py-1.5 pr-2 max-w-[200px] truncate">{acct.account}</td>
                        <td className="font-sans text-content-secondary py-1.5 pr-2">{acct.category}</td>
                        <td className="font-mono text-content-primary text-right py-1.5 pr-2">{formatCurrency(acct.net_balance)}</td>
                        <td className="font-mono text-content-secondary text-right py-1.5">{acct.percent_of_total.toFixed(1)}%</td>
                      </tr>
                    ))}
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
