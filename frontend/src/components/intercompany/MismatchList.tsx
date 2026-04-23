'use client'

/**
 * Intercompany mismatch list — Sprint 689c.
 *
 * Renders the three mismatch kinds the engine emits:
 *  - no_reciprocal: only one side booked the intercompany balance
 *  - amount_mismatch: both sides booked, amounts diverge beyond tolerance
 *  - direction_mismatch: both sides booked the same direction
 */

import type { IntercompanyMismatch, MismatchKind } from '@/types/intercompany'

const KIND_STYLES: Record<MismatchKind, string> = {
  no_reciprocal: 'bg-clay-100 text-clay-700 border-clay-200',
  amount_mismatch: 'bg-oatmeal-200 text-obsidian-700 border-obsidian-200',
  direction_mismatch: 'bg-clay-50 text-clay-700 border-clay-200',
}

const KIND_LABELS: Record<MismatchKind, string> = {
  no_reciprocal: 'No Reciprocal',
  amount_mismatch: 'Amount Mismatch',
  direction_mismatch: 'Direction Mismatch',
}

interface Props {
  mismatches: IntercompanyMismatch[]
}

function formatAmount(raw: string): string {
  const n = Number.parseFloat(raw)
  if (!Number.isFinite(n)) return raw
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function MismatchList({ mismatches }: Props) {
  return (
    <section className="theme-card p-6">
      <h3 className="font-serif text-lg text-content-primary mb-4">
        Mismatches <span className="font-sans text-sm text-content-tertiary">({mismatches.length})</span>
      </h3>
      {mismatches.length === 0 ? (
        <p className="font-sans text-sm text-content-tertiary">
          Every intercompany pair reconciled within tolerance.
        </p>
      ) : (
        <ul className="space-y-3">
          {mismatches.map((m, i) => (
            <li key={`${m.entity}-${m.account}-${i}`} className="border border-theme rounded-lg p-4">
              <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                <div>
                  <div className="font-serif text-content-primary">
                    {m.entity} <span className="text-content-tertiary">&middot;</span> {m.account}
                  </div>
                  <div className="font-sans text-xs text-content-tertiary mt-1">
                    Counterparty: <span className="font-mono">{m.counterparty || '—'}</span>
                    {' '}&middot; Direction: <span className="font-mono">{m.direction}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-sans font-medium border ${KIND_STYLES[m.kind]}`}>
                    {KIND_LABELS[m.kind]}
                  </span>
                  <span className="font-mono text-sm text-content-primary">{formatAmount(m.amount)}</span>
                </div>
              </div>
              <p className="text-xs font-sans text-content-secondary">{m.message}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
