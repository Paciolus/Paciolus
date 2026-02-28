'use client'

import { useState } from 'react'
import type { ExpenseCategoryReport } from '@/types/expenseCategoryAnalytics'

interface ExpenseCategorySectionProps {
  data: ExpenseCategoryReport
  onExportPDF?: () => void
  onExportCSV?: () => void
}

function formatCurrency(value: number): string {
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function formatPercent(value: number | null): string {
  if (value === null) return 'N/A'
  return `${value.toFixed(2)}%`
}

export function ExpenseCategorySection({ data, onExportPDF, onExportCSV }: ExpenseCategorySectionProps) {
  const [expanded, setExpanded] = useState(false)

  const hasPrior = data.prior_available && data.categories.some(c => c.prior_amount !== null)
  const activeCategories = data.categories.filter(c => Math.abs(c.amount) > 0.01)
  const maxAmount = Math.max(...activeCategories.map(c => Math.abs(c.amount)), 1)

  return (
    <div className="theme-card overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface-card-secondary transition-colors"
      >
        <div className="flex items-center gap-3">
          <h3 className="font-serif text-sm text-content-primary">Expense Category Analysis</h3>
          <span className="px-2 py-0.5 rounded-full bg-oatmeal-50 border border-oatmeal-200 text-xs font-mono text-content-secondary">
            {data.category_count} categories
          </span>
          <span className="px-2 py-0.5 rounded-full bg-oatmeal-50 border border-oatmeal-200 text-xs font-mono text-content-secondary">
            {formatCurrency(data.total_expenses)}
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
          {/* Summary Stats */}
          <div className="px-6 py-4 border-b border-theme">
            <h4 className="font-serif text-xs text-content-secondary mb-3">Summary</h4>
            <div className="grid grid-cols-3 gap-x-6 gap-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Total Expenses:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.total_expenses)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Total Revenue:</span>
                <span className="font-mono text-content-primary">
                  {data.revenue_available ? formatCurrency(data.total_revenue) : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Expense Ratio:</span>
                <span className="font-mono text-content-primary">
                  {data.revenue_available && Math.abs(data.total_revenue) > 0.01
                    ? `${(data.total_expenses / data.total_revenue * 100).toFixed(2)}%`
                    : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Active Categories:</span>
                <span className="font-mono text-content-primary">{data.category_count}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Materiality:</span>
                <span className="font-mono text-content-primary">{formatCurrency(data.materiality_threshold)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-content-secondary font-sans">Prior Data:</span>
                <span className="font-sans text-content-primary">{data.prior_available ? 'Available' : 'Not provided'}</span>
              </div>
            </div>
          </div>

          {/* Category Bars */}
          <div className="px-6 py-4 border-b border-theme">
            <h4 className="font-serif text-xs text-content-secondary mb-3">Category Distribution</h4>
            <div className="space-y-1.5">
              {data.categories.map((cat) => (
                <div key={cat.key} className="flex items-center gap-3 text-xs">
                  <span className="w-40 text-content-secondary font-sans truncate" title={cat.label}>{cat.label}</span>
                  <div className="flex-1 h-4 bg-oatmeal-50 rounded-xs overflow-hidden">
                    <div
                      className="h-full bg-sage-400 rounded-xs transition-all"
                      style={{ width: `${(Math.abs(cat.amount) / maxAmount) * 100}%` }}
                    />
                  </div>
                  <span className="w-20 text-right font-mono text-content-primary">{formatCurrency(cat.amount)}</span>
                  <span className="w-14 text-right font-mono text-content-tertiary">{formatPercent(cat.pct_of_revenue)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Detailed Table */}
          <div className="px-6 py-4 border-b border-theme">
            <h4 className="font-serif text-xs text-content-secondary mb-3">Category Breakdown</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-theme">
                    <th className="text-left font-serif text-content-secondary py-1.5 pr-2">Category</th>
                    <th className="text-right font-serif text-content-secondary py-1.5 pr-2">Amount</th>
                    <th className="text-right font-serif text-content-secondary py-1.5 pr-2">% of Revenue</th>
                    {hasPrior && (
                      <>
                        <th className="text-right font-serif text-content-secondary py-1.5 pr-2">Prior Amount</th>
                        <th className="text-right font-serif text-content-secondary py-1.5 pr-2">$ Change</th>
                        <th className="text-center font-serif text-content-secondary py-1.5">Exceeds Mat.</th>
                      </>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {data.categories.map((cat) => (
                    <tr key={cat.key} className="border-b border-theme-divider last:border-b-0">
                      <td className="font-sans text-content-primary py-1.5 pr-2">{cat.label}</td>
                      <td className="font-mono text-content-primary text-right py-1.5 pr-2">{formatCurrency(cat.amount)}</td>
                      <td className="font-mono text-content-secondary text-right py-1.5 pr-2">{formatPercent(cat.pct_of_revenue)}</td>
                      {hasPrior && (
                        <>
                          <td className="font-mono text-content-secondary text-right py-1.5 pr-2">
                            {cat.prior_amount !== null ? formatCurrency(cat.prior_amount) : 'N/A'}
                          </td>
                          <td className="font-mono text-content-primary text-right py-1.5 pr-2">
                            {cat.dollar_change !== null ? formatCurrency(cat.dollar_change) : 'N/A'}
                          </td>
                          <td className="font-sans text-content-secondary text-center py-1.5">
                            {cat.dollar_change !== null ? (cat.exceeds_threshold ? 'Yes' : 'No') : 'N/A'}
                          </td>
                        </>
                      )}
                    </tr>
                  ))}
                  {/* Total row */}
                  <tr className="border-t border-theme font-medium">
                    <td className="font-sans text-content-primary py-1.5 pr-2">Total</td>
                    <td className="font-mono text-content-primary text-right py-1.5 pr-2">{formatCurrency(data.total_expenses)}</td>
                    <td className="font-mono text-content-secondary text-right py-1.5 pr-2">
                      {data.revenue_available && Math.abs(data.total_revenue) > 0.01
                        ? formatPercent(data.total_expenses / data.total_revenue * 100)
                        : 'N/A'}
                    </td>
                    {hasPrior && (
                      <>
                        <td className="py-1.5 pr-2"></td>
                        <td className="py-1.5 pr-2"></td>
                        <td className="py-1.5"></td>
                      </>
                    )}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

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
