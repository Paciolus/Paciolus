'use client'

import { useState, useMemo } from 'react'
import type { AccountMovement } from '@/hooks'
import { MovementBadge } from './MovementBadge'
import { formatCurrency, SIGNIFICANCE_COLORS } from './constants'

export function AccountMovementTable({ movements, filter, hasBudget }: {
  movements: AccountMovement[]
  filter: { type: string; significance: string; search: string }
  hasBudget: boolean
}) {
  const [sortKey, setSortKey] = useState<string>('change_amount')
  const [sortDesc, setSortDesc] = useState(true)

  const filtered = useMemo(() => {
    let result = movements
    if (filter.type !== 'all') result = result.filter(m => m.movement_type === filter.type)
    if (filter.significance !== 'all') result = result.filter(m => m.significance === filter.significance)
    if (filter.search) {
      const q = filter.search.toLowerCase()
      result = result.filter(m => m.account_name.toLowerCase().includes(q))
    }
    return [...result].sort((a, b) => {
      const aVal = sortKey === 'change_amount' ? Math.abs(a.change_amount) :
                   sortKey === 'account_name' ? a.account_name.toLowerCase() :
                   sortKey === 'change_percent' ? Math.abs(a.change_percent || 0) :
                   sortKey === 'budget_variance' ? Math.abs(a.budget_variance?.variance_amount || 0) :
                   Math.abs(a.change_amount)
      const bVal = sortKey === 'change_amount' ? Math.abs(b.change_amount) :
                   sortKey === 'account_name' ? b.account_name.toLowerCase() :
                   sortKey === 'change_percent' ? Math.abs(b.change_percent || 0) :
                   sortKey === 'budget_variance' ? Math.abs(b.budget_variance?.variance_amount || 0) :
                   Math.abs(b.change_amount)
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDesc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal)
      }
      return sortDesc ? (bVal as number) - (aVal as number) : (aVal as number) - (bVal as number)
    })
  }, [movements, filter, sortKey, sortDesc])

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDesc(!sortDesc)
    else { setSortKey(key); setSortDesc(true) }
  }

  const SortHeader = ({ label, field }: { label: string; field: string }) => (
    <th
      className="px-3 py-2 text-left text-xs font-serif font-medium text-content-secondary cursor-pointer hover:text-content-primary select-none"
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field ? (sortDesc ? '\u25BC' : '\u25B2') : ''}
    </th>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-theme-divider">
          <tr>
            <SortHeader label="Account" field="account_name" />
            <th className="px-3 py-2 text-right text-xs font-serif font-medium text-content-secondary">Prior</th>
            <th className="px-3 py-2 text-right text-xs font-serif font-medium text-content-secondary">Current</th>
            <SortHeader label="Change" field="change_amount" />
            <SortHeader label="%" field="change_percent" />
            {hasBudget && (
              <>
                <th className="px-3 py-2 text-right text-xs font-serif font-medium text-content-secondary">Budget</th>
                <SortHeader label="Bgt Var" field="budget_variance" />
              </>
            )}
            <th className="px-3 py-2 text-center text-xs font-serif font-medium text-content-secondary">Movement</th>
            <th className="px-3 py-2 text-center text-xs font-serif font-medium text-content-secondary">Significance</th>
          </tr>
        </thead>
        <tbody>
          {filtered.slice(0, 100).map((m, i) => (
            <tr key={`${m.account_name}-${i}`} className="border-b border-theme-divider hover:bg-surface-card-secondary transition-colors">
              <td className="px-3 py-2 font-sans text-content-primary max-w-[200px] truncate" title={m.account_name}>
                {m.account_name}
                {m.is_dormant && <span className="ml-1 text-xs text-content-tertiary">(dormant)</span>}
              </td>
              <td className="px-3 py-2 text-right font-mono text-content-secondary">{formatCurrency(m.prior_balance)}</td>
              <td className="px-3 py-2 text-right font-mono text-content-secondary">{formatCurrency(m.current_balance)}</td>
              <td className={`px-3 py-2 text-right font-mono ${m.change_amount > 0 ? 'text-sage-600' : m.change_amount < 0 ? 'text-clay-600' : 'text-content-tertiary'}`}>
                {m.change_amount > 0 ? '+' : ''}{formatCurrency(m.change_amount)}
              </td>
              <td className={`px-3 py-2 text-right font-mono ${(m.change_percent || 0) > 0 ? 'text-sage-600' : (m.change_percent || 0) < 0 ? 'text-clay-600' : 'text-content-tertiary'}`}>
                {m.change_percent !== null ? `${m.change_percent > 0 ? '+' : ''}${m.change_percent.toFixed(1)}%` : '--'}
              </td>
              {hasBudget && (
                <>
                  <td className="px-3 py-2 text-right font-mono text-content-secondary">
                    {m.budget_variance ? formatCurrency(m.budget_variance.budget_balance) : '--'}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${
                    m.budget_variance
                      ? m.budget_variance.variance_amount > 0 ? 'text-sage-600' : m.budget_variance.variance_amount < 0 ? 'text-clay-600' : 'text-content-tertiary'
                      : 'text-content-tertiary'
                  }`}>
                    {m.budget_variance
                      ? `${m.budget_variance.variance_amount > 0 ? '+' : ''}${formatCurrency(m.budget_variance.variance_amount)}`
                      : '--'}
                  </td>
                </>
              )}
              <td className="px-3 py-2 text-center"><MovementBadge type={m.movement_type} /></td>
              <td className={`px-3 py-2 text-center text-xs font-sans capitalize ${SIGNIFICANCE_COLORS[m.significance] || ''}`}>
                {m.significance}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {filtered.length > 100 && (
        <p className="text-center text-xs text-content-tertiary font-sans mt-2">
          Showing 100 of {filtered.length} accounts
        </p>
      )}
      {filtered.length === 0 && (
        <p className="text-center text-sm text-content-tertiary font-sans py-8">No accounts match filters</p>
      )}
    </div>
  )
}
