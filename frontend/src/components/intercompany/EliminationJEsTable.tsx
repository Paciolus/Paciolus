'use client'

/**
 * Proposed elimination JEs — Sprint 689c.
 */

import type { EliminationJE } from '@/types/intercompany'

interface Props {
  entries: EliminationJE[]
}

function formatAmount(raw: string): string {
  const n = Number.parseFloat(raw)
  if (!Number.isFinite(n)) return raw
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function EliminationJEsTable({ entries }: Props) {
  return (
    <section className="theme-card p-6">
      <h3 className="font-serif text-lg text-content-primary mb-4">
        Proposed Elimination Entries <span className="font-sans text-sm text-content-tertiary">({entries.length})</span>
      </h3>
      {entries.length === 0 ? (
        <p className="font-sans text-sm text-content-tertiary">
          No reciprocal intercompany pairs reconciled within tolerance — no elimination entries proposed.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-sans">
            <thead>
              <tr className="border-b border-theme text-left text-xs uppercase tracking-wider text-content-tertiary">
                <th className="py-2 pr-3">Description</th>
                <th className="py-2 px-3">Debit</th>
                <th className="py-2 px-3">Credit</th>
                <th className="py-2 pl-3 text-right">Amount</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((je, i) => (
                <tr key={`${je.description}-${i}`} className="border-b border-theme/40 last:border-0">
                  <td className="py-2 pr-3 font-sans">{je.description}</td>
                  <td className="py-2 px-3 font-sans">
                    <div className="text-content-primary">{je.debit_account}</div>
                    <div className="font-mono text-[11px] text-content-tertiary">{je.debit_entity}</div>
                  </td>
                  <td className="py-2 px-3 font-sans">
                    <div className="text-content-primary">{je.credit_account}</div>
                    <div className="font-mono text-[11px] text-content-tertiary">{je.credit_entity}</div>
                  </td>
                  <td className="py-2 pl-3 text-right font-mono">{formatAmount(je.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
