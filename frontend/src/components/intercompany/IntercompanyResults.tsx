'use client'

/**
 * Composite results view — Sprint 689c.
 *
 * Aggregates the three result sections + headline counters.
 */

import { ConsolidationWorksheetTable } from '@/components/intercompany/ConsolidationWorksheetTable'
import { EliminationJEsTable } from '@/components/intercompany/EliminationJEsTable'
import { MismatchList } from '@/components/intercompany/MismatchList'
import type { IntercompanyEliminationResponse } from '@/types/intercompany'

interface CounterProps {
  label: string
  value: number | string
  tone?: 'ok' | 'warn' | 'bad'
}

function Counter({ label, value, tone = 'ok' }: CounterProps) {
  const toneClass =
    tone === 'bad'
      ? 'text-clay-700'
      : tone === 'warn'
        ? 'text-obsidian-700'
        : 'text-sage-700'
  return (
    <div className="theme-card p-4">
      <div className="text-xs font-sans uppercase tracking-wider text-content-tertiary mb-1">{label}</div>
      <div className={`font-mono text-2xl ${toneClass}`}>{value}</div>
    </div>
  )
}

interface Props {
  result: IntercompanyEliminationResponse
}

export function IntercompanyResults({ result }: Props) {
  const { summary, worksheet, elimination_journal_entries, mismatches } = result
  const entityCount = summary.entity_count ?? worksheet.columns.length
  const matched = summary.matched_pair_count ?? 0
  const reconciling = summary.reconciling_pair_count ?? 0
  const mismatchCount = summary.mismatch_count ?? mismatches.length

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Counter label="Entities" value={entityCount} />
        <Counter label="Matched Pairs" value={matched} />
        <Counter
          label="Reconciled"
          value={reconciling}
          tone={reconciling === matched && matched > 0 ? 'ok' : 'warn'}
        />
        <Counter label="Mismatches" value={mismatchCount} tone={mismatchCount > 0 ? 'bad' : 'ok'} />
      </div>

      <ConsolidationWorksheetTable worksheet={worksheet} />
      <EliminationJEsTable entries={elimination_journal_entries} />
      <MismatchList mismatches={mismatches} />
    </div>
  )
}
