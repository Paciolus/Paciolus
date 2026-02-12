'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { MovementSummaryResponse } from '@/hooks'
import { MovementBadge } from './MovementBadge'
import { formatCurrency } from './constants'

export function CategoryMovementSection({ comparison, hasBudget }: { comparison: MovementSummaryResponse; hasBudget: boolean }) {
  const [expandedLS, setExpandedLS] = useState<Set<string>>(new Set())

  const toggleLS = (ls: string) => {
    setExpandedLS(prev => {
      const next = new Set(prev)
      if (next.has(ls)) next.delete(ls)
      else next.add(ls)
      return next
    })
  }

  return (
    <div className="space-y-2">
      {comparison.lead_sheet_summaries.map(ls => (
        <div key={ls.lead_sheet} className="bg-surface-card border border-theme rounded-lg overflow-hidden shadow-theme-card">
          <button
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-surface-card-secondary transition-colors"
            onClick={() => toggleLS(ls.lead_sheet)}
          >
            <div className="flex items-center gap-3">
              <span className="w-7 h-7 bg-surface-card-secondary rounded flex items-center justify-center text-xs font-mono font-bold text-content-primary">
                {ls.lead_sheet}
              </span>
              <span className="font-sans text-sm text-content-primary">{ls.lead_sheet_name}</span>
              <span className="text-xs font-sans text-content-tertiary">({ls.account_count} accounts)</span>
            </div>
            <div className="flex items-center gap-4">
              <span className={`font-mono text-sm ${ls.net_change > 0 ? 'text-sage-600' : ls.net_change < 0 ? 'text-clay-600' : 'text-content-tertiary'}`}>
                {ls.net_change > 0 ? '+' : ''}{formatCurrency(ls.net_change)}
              </span>
              {hasBudget && ls.budget_variance != null && (
                <span className={`font-mono text-xs ${ls.budget_variance > 0 ? 'text-sage-600' : ls.budget_variance < 0 ? 'text-clay-600' : 'text-content-tertiary'}`}>
                  Bgt: {ls.budget_variance > 0 ? '+' : ''}{formatCurrency(ls.budget_variance)}
                </span>
              )}
              <svg className={`w-4 h-4 text-content-tertiary transition-transform ${expandedLS.has(ls.lead_sheet) ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>
          <AnimatePresence>
            {expandedLS.has(ls.lead_sheet) && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="px-4 pb-3 border-t border-theme-divider">
                  <table className="w-full text-xs mt-2">
                    <thead>
                      <tr className="text-content-secondary font-serif">
                        <th className="text-left py-1 px-2">Account</th>
                        <th className="text-right py-1 px-2">Prior</th>
                        <th className="text-right py-1 px-2">Current</th>
                        <th className="text-right py-1 px-2">Change</th>
                        {hasBudget && <th className="text-right py-1 px-2">Bgt Var</th>}
                        <th className="text-center py-1 px-2">Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ls.movements.map((m, i) => (
                        <tr key={i} className="border-b border-theme-divider">
                          <td className="py-1 px-2 font-sans text-content-primary max-w-[180px] truncate">{m.account_name}</td>
                          <td className="py-1 px-2 text-right font-mono text-content-secondary">${Math.abs(m.prior_balance).toLocaleString()}</td>
                          <td className="py-1 px-2 text-right font-mono text-content-secondary">${Math.abs(m.current_balance).toLocaleString()}</td>
                          <td className={`py-1 px-2 text-right font-mono ${m.change_amount > 0 ? 'text-sage-600' : m.change_amount < 0 ? 'text-clay-600' : 'text-content-tertiary'}`}>
                            {m.change_amount > 0 ? '+' : ''}{formatCurrency(m.change_amount)}
                          </td>
                          {hasBudget && (
                            <td className={`py-1 px-2 text-right font-mono ${
                              m.budget_variance
                                ? m.budget_variance.variance_amount > 0 ? 'text-sage-600' : m.budget_variance.variance_amount < 0 ? 'text-clay-600' : 'text-content-tertiary'
                                : 'text-content-tertiary'
                            }`}>
                              {m.budget_variance ? `${m.budget_variance.variance_amount > 0 ? '+' : ''}${formatCurrency(m.budget_variance.variance_amount)}` : '--'}
                            </td>
                          )}
                          <td className="py-1 px-2 text-center"><MovementBadge type={m.movement_type} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  )
}
