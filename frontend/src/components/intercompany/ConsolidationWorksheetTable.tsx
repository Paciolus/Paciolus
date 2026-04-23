'use client'

/**
 * Consolidation worksheet — Sprint 689c.
 *
 * Renders the standard consolidation layout: per-entity debit/credit
 * totals, then the eliminations row, then the consolidated total.
 * All numeric values arrive as Decimal-precise strings from the engine.
 */

import type { ConsolidationWorksheet } from '@/types/intercompany'

interface Props {
  worksheet: ConsolidationWorksheet
}

function formatAmount(raw: string): string {
  const n = Number.parseFloat(raw)
  if (!Number.isFinite(n)) return raw
  return n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function ConsolidationWorksheetTable({ worksheet }: Props) {
  const { columns, total_entity_debits, total_entity_credits, elimination_debits, elimination_credits, consolidated_debits, consolidated_credits } = worksheet

  return (
    <section className="theme-card p-6">
      <h3 className="font-serif text-lg text-content-primary mb-4">Consolidation Worksheet</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm font-sans">
          <thead>
            <tr className="border-b border-theme text-left text-xs uppercase tracking-wider text-content-tertiary">
              <th className="py-2 pr-3">Stage</th>
              {columns.map(c => (
                <th key={c.entity_id} className="py-2 px-3 text-right">
                  <div className="font-medium text-content-primary">{c.entity_name}</div>
                  <div className="font-mono text-[10px] text-content-tertiary">{c.entity_id}</div>
                </th>
              ))}
              <th className="py-2 pl-3 text-right">Total</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-theme/40">
              <td className="py-2 pr-3 font-medium">Entity debits</td>
              {columns.map(c => (
                <td key={c.entity_id} className="py-2 px-3 text-right font-mono">{formatAmount(c.debit_total)}</td>
              ))}
              <td className="py-2 pl-3 text-right font-mono font-medium">{formatAmount(total_entity_debits)}</td>
            </tr>
            <tr className="border-b border-theme/40">
              <td className="py-2 pr-3 font-medium">Entity credits</td>
              {columns.map(c => (
                <td key={c.entity_id} className="py-2 px-3 text-right font-mono">{formatAmount(c.credit_total)}</td>
              ))}
              <td className="py-2 pl-3 text-right font-mono font-medium">{formatAmount(total_entity_credits)}</td>
            </tr>
            <tr className="border-b border-theme/40">
              <td className="py-2 pr-3 font-medium text-content-tertiary">Intercompany gross</td>
              {columns.map(c => (
                <td key={c.entity_id} className="py-2 px-3 text-right font-mono text-content-tertiary">{formatAmount(c.intercompany_gross)}</td>
              ))}
              <td className="py-2 pl-3 text-right text-content-tertiary">—</td>
            </tr>
            <tr className="border-b border-theme/40 bg-clay-50/40">
              <td className="py-2 pr-3 font-medium text-clay-700">Eliminations</td>
              <td className="py-2 px-3 text-right font-mono text-clay-700" colSpan={Math.max(columns.length - 1, 0)}>
                Dr {formatAmount(elimination_debits)} / Cr {formatAmount(elimination_credits)}
              </td>
              {columns.length > 0 && <td className="py-2 px-3 text-right font-mono text-clay-700">{formatAmount(elimination_debits)}</td>}
              <td className="py-2 pl-3 text-right font-mono text-clay-700">{formatAmount(elimination_credits)}</td>
            </tr>
            <tr className="bg-sage-50/40">
              <td className="py-2 pr-3 font-serif text-sage-700">Consolidated</td>
              <td className="py-2 px-3 text-right font-mono font-medium" colSpan={Math.max(columns.length, 1)}>
                Dr {formatAmount(consolidated_debits)} / Cr {formatAmount(consolidated_credits)}
              </td>
              <td className="py-2 pl-3 text-right font-mono font-medium text-sage-700">
                {formatAmount(consolidated_credits)}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  )
}
