'use client'

import type { MatchVarianceData } from '@/types/threeWayMatch'
import { VARIANCE_SEVERITY_COLORS } from '@/types/threeWayMatch'

interface VarianceDetailCardProps {
  variances: MatchVarianceData[]
}

const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const pct = (n: number) => `${(n * 100).toFixed(1)}%`

const FIELD_LABELS: Record<string, string> = {
  amount: 'Amount Variance',
  quantity: 'Quantity Variance',
  price: 'Price Variance',
  date: 'Date Variance',
}

const FIELD_ICONS: Record<string, string> = {
  amount: '$',
  quantity: '#',
  price: '¢',
  date: '📅',
}

export function VarianceDetailCard({ variances }: VarianceDetailCardProps) {
  if (variances.length === 0) return null

  // Group by field type
  const grouped = variances.reduce<Record<string, MatchVarianceData[]>>((acc, v) => {
    const key = v.field
    if (!acc[key]) acc[key] = []
    acc[key].push(v)
    return acc
  }, {})

  const countBySeverity = {
    high: variances.filter(v => v.severity === 'high').length,
    medium: variances.filter(v => v.severity === 'medium').length,
    low: variances.filter(v => v.severity === 'low').length,
  }

  return (
    <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-serif text-sm text-oatmeal-200">Material Variances</h3>
        <div className="flex items-center gap-2">
          {countBySeverity.high > 0 && (
            <span className="px-2 py-0.5 rounded text-xs font-sans bg-clay-500/15 text-clay-400 border border-clay-500/30">
              {countBySeverity.high} High
            </span>
          )}
          {countBySeverity.medium > 0 && (
            <span className="px-2 py-0.5 rounded text-xs font-sans bg-oatmeal-500/10 text-oatmeal-400 border border-oatmeal-500/20">
              {countBySeverity.medium} Medium
            </span>
          )}
          {countBySeverity.low > 0 && (
            <span className="px-2 py-0.5 rounded text-xs font-sans bg-sage-500/10 text-sage-400 border border-sage-500/20">
              {countBySeverity.low} Low
            </span>
          )}
        </div>
      </div>

      {/* Variance Groups */}
      <div className="space-y-3">
        {Object.entries(grouped).map(([field, fieldVars]) => (
          <div key={field} className="bg-obsidian-700/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">{FIELD_ICONS[field] || '?'}</span>
              <h4 className="font-sans text-sm font-medium text-oatmeal-300">
                {FIELD_LABELS[field] || field} ({fieldVars.length})
              </h4>
            </div>
            <div className="space-y-2">
              {fieldVars.slice(0, 10).map((v, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <span className={`inline-block px-1.5 py-0.5 rounded border ${VARIANCE_SEVERITY_COLORS[v.severity]}`}>
                      {v.severity}
                    </span>
                    <span className="font-sans text-oatmeal-400">
                      {field === 'date'
                        ? `${v.variance_amount.toFixed(0)} days late`
                        : `PO: $${fmt(v.po_value || 0)} → Inv: $${fmt(v.invoice_value || 0)}`
                      }
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-oatmeal-300">
                      {field === 'date'
                        ? `${v.variance_amount.toFixed(0)} days`
                        : `$${fmt(v.variance_amount)}`
                      }
                    </span>
                    {v.variance_pct > 0 && field !== 'date' && (
                      <span className="font-mono text-oatmeal-500">{pct(v.variance_pct)}</span>
                    )}
                  </div>
                </div>
              ))}
              {fieldVars.length > 10 && (
                <p className="text-xs font-sans text-oatmeal-600 text-center pt-1">
                  + {fieldVars.length - 10} more
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
