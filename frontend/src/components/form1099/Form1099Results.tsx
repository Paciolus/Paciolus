'use client'

/**
 * Form 1099 results — Sprint 689e.
 */

import type { Form1099Response } from '@/types/form1099'

function formatAmount(raw: string): string {
  const n = Number.parseFloat(raw)
  if (!Number.isFinite(n)) return raw
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

interface CounterProps {
  label: string
  value: number | string
  tone?: 'ok' | 'warn' | 'bad'
}

function Counter({ label, value, tone = 'ok' }: CounterProps) {
  const toneClass =
    tone === 'bad' ? 'text-clay-700' : tone === 'warn' ? 'text-obsidian-700' : 'text-sage-700'
  return (
    <div className="theme-card p-4">
      <div className="text-xs font-sans uppercase tracking-wider text-content-tertiary mb-1">{label}</div>
      <div className={`font-mono text-2xl ${toneClass}`}>{value}</div>
    </div>
  )
}

interface Props {
  result: Form1099Response
}

export function Form1099Results({ result }: Props) {
  const { candidates, data_quality, w9_collection_list, tax_year } = result
  const flagged = candidates.filter(c => c.flagged_for_review).length
  const qualityIssues = data_quality.filter(dq => dq.has_issue).length

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Counter label="Tax year" value={tax_year} />
        <Counter label="Filing candidates" value={candidates.length} />
        <Counter label="Review required" value={flagged} tone={flagged > 0 ? 'warn' : 'ok'} />
        <Counter label="W-9 to collect" value={w9_collection_list.length} tone={w9_collection_list.length > 0 ? 'bad' : 'ok'} />
      </div>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">
          Filing Candidates <span className="font-sans text-sm text-content-tertiary">({candidates.length})</span>
        </h3>
        {candidates.length === 0 ? (
          <p className="font-sans text-sm text-content-tertiary">No vendors met the 1099 reporting threshold.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-theme text-left text-xs uppercase tracking-wider text-content-tertiary">
                  <th className="py-2 pr-3">Vendor</th>
                  <th className="py-2 px-3">Form</th>
                  <th className="py-2 px-3 text-right">Total reportable</th>
                  <th className="py-2 px-3 text-right">Payments</th>
                  <th className="py-2 px-3 text-right">Excluded</th>
                  <th className="py-2 pl-3">Review</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map(c => (
                  <tr key={c.vendor_id} className="border-b border-theme/40 last:border-0">
                    <td className="py-2 pr-3">
                      <div className="font-medium text-content-primary">{c.vendor_name}</div>
                      <div className="font-mono text-xs text-content-tertiary">{c.vendor_id}</div>
                    </td>
                    <td className="py-2 px-3 font-mono text-xs">{c.form_type}</td>
                    <td className="py-2 px-3 text-right font-mono">{formatAmount(c.total_reportable)}</td>
                    <td className="py-2 px-3 text-right font-mono">{c.payment_count}</td>
                    <td className="py-2 px-3 text-right font-mono text-content-tertiary">{formatAmount(c.excluded_amount)}</td>
                    <td className="py-2 pl-3">
                      {c.flagged_for_review ? (
                        <span className="inline-block px-2 py-0.5 rounded-full text-xs font-sans font-medium bg-clay-100 text-clay-700 border border-clay-200">
                          {c.review_reasons.join(', ') || 'Review'}
                        </span>
                      ) : (
                        <span className="text-content-tertiary text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">
          W-9 Collection Queue{' '}
          <span className="font-sans text-sm text-content-tertiary">({w9_collection_list.length})</span>
        </h3>
        {w9_collection_list.length === 0 ? (
          <p className="font-sans text-sm text-content-tertiary">All filing candidates have valid TINs on file.</p>
        ) : (
          <ul className="space-y-2">
            {w9_collection_list.map(w => (
              <li key={w.vendor_id} className="flex items-start justify-between gap-4 text-sm font-sans">
                <div>
                  <div className="font-medium text-content-primary">{w.vendor_name}</div>
                  <div className="font-mono text-xs text-content-tertiary">{w.vendor_id}</div>
                </div>
                <span className="text-xs text-clay-700">{w.reason}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">
          Data Quality <span className="font-sans text-sm text-content-tertiary">({qualityIssues} with issues)</span>
        </h3>
        {qualityIssues === 0 ? (
          <p className="font-sans text-sm text-content-tertiary">All vendor records are complete and well-formed.</p>
        ) : (
          <ul className="space-y-2">
            {data_quality.filter(dq => dq.has_issue).map(dq => (
              <li key={dq.vendor_id} className="text-sm font-sans">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-medium text-content-primary">{dq.vendor_name}</div>
                    <div className="font-mono text-xs text-content-tertiary">{dq.vendor_id}</div>
                  </div>
                  <span className="text-xs text-clay-700">{dq.notes.join('; ')}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
