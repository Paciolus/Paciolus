'use client'

/**
 * W-2 / W-3 reconciliation results — Sprint 689d.
 */

import type {
  DiscrepancySeverity,
  W2ReconciliationResponse,
} from '@/types/w2Reconciliation'

const SEVERITY_STYLES: Record<DiscrepancySeverity, string> = {
  high: 'bg-clay-100 text-clay-700 border-clay-200',
  medium: 'bg-oatmeal-200 text-obsidian-700 border-obsidian-200',
  low: 'bg-sage-50 text-sage-700 border-sage-200',
}

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
  result: W2ReconciliationResponse
}

export function W2Results({ result }: Props) {
  const { employee_discrepancies, form_941_mismatches, w3_totals, tax_year } = result

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Counter label="Tax year" value={tax_year} />
        <Counter label="Employees" value={w3_totals.employee_count} />
        <Counter
          label="Employee discrepancies"
          value={employee_discrepancies.length}
          tone={employee_discrepancies.length > 0 ? 'bad' : 'ok'}
        />
        <Counter
          label="Form 941 mismatches"
          value={form_941_mismatches.length}
          tone={form_941_mismatches.length > 0 ? 'bad' : 'ok'}
        />
      </div>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">W-3 Totals</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm font-sans">
          <Stat label="Federal wages" value={formatAmount(w3_totals.total_federal_wages)} />
          <Stat label="Federal withholding" value={formatAmount(w3_totals.total_federal_withholding)} />
          <Stat label="SS wages" value={formatAmount(w3_totals.total_ss_wages)} />
          <Stat label="SS tax withheld" value={formatAmount(w3_totals.total_ss_tax_withheld)} />
          <Stat label="Medicare wages" value={formatAmount(w3_totals.total_medicare_wages)} />
          <Stat label="Medicare tax withheld" value={formatAmount(w3_totals.total_medicare_tax_withheld)} />
        </div>
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">
          Employee Discrepancies{' '}
          <span className="font-sans text-sm text-content-tertiary">({employee_discrepancies.length})</span>
        </h3>
        {employee_discrepancies.length === 0 ? (
          <p className="font-sans text-sm text-content-tertiary">No employee-level discrepancies.</p>
        ) : (
          <ul className="space-y-3">
            {employee_discrepancies.map((d, i) => (
              <li key={`${d.employee_id}-${d.kind}-${i}`} className="border border-theme rounded-lg p-4">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="font-serif text-content-primary">
                      {d.employee_name} <span className="font-mono text-xs text-content-tertiary">({d.employee_id})</span>
                    </div>
                    <div className="font-sans text-xs text-content-tertiary mt-1">{d.kind}</div>
                  </div>
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-sans font-medium border ${SEVERITY_STYLES[d.severity]}`}>
                    {d.severity}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs font-sans text-content-secondary mb-1">
                  <div>Expected: <span className="font-mono">{formatAmount(d.expected)}</span></div>
                  <div>Actual: <span className="font-mono">{formatAmount(d.actual)}</span></div>
                  <div>Delta: <span className="font-mono">{formatAmount(d.difference)}</span></div>
                </div>
                <p className="text-xs font-sans text-content-secondary">{d.message}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">
          Form 941 Mismatches{' '}
          <span className="font-sans text-sm text-content-tertiary">({form_941_mismatches.length})</span>
        </h3>
        {form_941_mismatches.length === 0 ? (
          <p className="font-sans text-sm text-content-tertiary">
            No quarterly or YTD mismatches against Form 941 totals.
          </p>
        ) : (
          <ul className="space-y-3">
            {form_941_mismatches.map((m, i) => (
              <li key={`${m.quarter ?? 'ytd'}-${m.kind}-${i}`} className="border border-theme rounded-lg p-4">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="font-serif text-content-primary">
                      {m.quarter === null ? 'YTD' : `Q${m.quarter}`} &mdash; {m.kind}
                    </div>
                  </div>
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-sans font-medium border ${SEVERITY_STYLES[m.severity]}`}>
                    {m.severity}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs font-sans text-content-secondary mb-1">
                  <div>Expected: <span className="font-mono">{formatAmount(m.expected)}</span></div>
                  <div>Actual: <span className="font-mono">{formatAmount(m.actual)}</span></div>
                  <div>Delta: <span className="font-mono">{formatAmount(m.difference)}</span></div>
                </div>
                <p className="text-xs font-sans text-content-secondary">{m.message}</p>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-l-2 border-theme pl-3">
      <div className="text-xs font-sans uppercase tracking-wider text-content-tertiary">{label}</div>
      <div className="font-mono text-content-primary">{value}</div>
    </div>
  )
}
