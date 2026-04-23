'use client'

/**
 * Book-to-Tax results — Sprint 689f.
 */

import type {
  AdjustmentLine,
  BookToTaxResponse,
} from '@/types/bookToTax'

function formatAmount(raw: string): string {
  const n = Number.parseFloat(raw)
  if (!Number.isFinite(n)) return raw
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatRate(raw: string): string {
  const n = Number.parseFloat(raw)
  if (!Number.isFinite(n)) return raw
  return `${(n * 100).toFixed(2)}%`
}

interface Props {
  result: BookToTaxResponse
}

export function BookToTaxResults({ result }: Props) {
  const { schedule_m1, deferred_tax, tax_provision, entity_size, tax_year } = result

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Counter label="Tax year" value={tax_year} />
        <Counter label="Presentation" value={entity_size === 'large' ? 'Schedule M-3' : 'Schedule M-1'} />
        <Counter label="Taxable income" value={formatAmount(schedule_m1.taxable_income)} />
        <Counter label="Effective rate" value={formatRate(tax_provision.effective_rate)} />
      </div>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Schedule M-1</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-sans">
            <tbody>
              <Row label="Net income per books" value={schedule_m1.net_income_per_books} />
              <Row label="Federal income tax per books" value={schedule_m1.federal_income_tax_per_books} />
              <AdjSection title="Permanent additions" entries={schedule_m1.permanent_additions} />
              <AdjSection title="Temporary additions" entries={schedule_m1.temporary_additions} />
              <AdjSection title="Permanent subtractions" entries={schedule_m1.permanent_subtractions} negative />
              <AdjSection title="Temporary subtractions" entries={schedule_m1.temporary_subtractions} negative />
              <tr className="bg-sage-50/40">
                <td className="py-2 pr-3 font-serif text-sage-700">Taxable income</td>
                <td className="py-2 pl-3 text-right font-mono font-medium text-sage-700">
                  {formatAmount(schedule_m1.taxable_income)}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Deferred Tax Rollforward</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm font-sans">
          <Stat label="Beginning DTA" value={formatAmount(deferred_tax.beginning_dta)} />
          <Stat label="Beginning DTL" value={formatAmount(deferred_tax.beginning_dtl)} />
          <Stat label="Temporary net" value={formatAmount(deferred_tax.current_year_temporary_adjustments)} />
          <Stat label="Movement" value={formatAmount(deferred_tax.current_year_movement)} />
          <Stat label="Ending DTA" value={formatAmount(deferred_tax.ending_dta)} />
          <Stat label="Ending DTL" value={formatAmount(deferred_tax.ending_dtl)} />
          <Stat label="Applied rate" value={formatRate(deferred_tax.tax_rate)} />
        </div>
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Tax Provision</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm font-sans">
          <Stat label="Current federal" value={formatAmount(tax_provision.current_federal_tax)} />
          <Stat label="Current state" value={formatAmount(tax_provision.current_state_tax)} />
          <Stat label="Deferred expense" value={formatAmount(tax_provision.deferred_tax_expense)} />
          <Stat label="Total tax expense" value={formatAmount(tax_provision.total_tax_expense)} />
          <Stat label="Effective rate" value={formatRate(tax_provision.effective_rate)} />
        </div>
      </section>
    </div>
  )
}

function Counter({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="theme-card p-4">
      <div className="text-xs font-sans uppercase tracking-wider text-content-tertiary mb-1">{label}</div>
      <div className="font-mono text-xl text-content-primary">{value}</div>
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

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-b border-theme/40">
      <td className="py-2 pr-3 font-medium">{label}</td>
      <td className="py-2 pl-3 text-right font-mono">{formatAmount(value)}</td>
    </tr>
  )
}

function AdjSection({ title, entries, negative }: { title: string; entries: AdjustmentLine[]; negative?: boolean }) {
  if (entries.length === 0) return null
  return (
    <>
      <tr>
        <td colSpan={2} className="pt-4 pb-1 text-xs font-sans uppercase tracking-wider text-content-tertiary">{title}</td>
      </tr>
      {entries.map((a, i) => (
        <tr key={`${title}-${i}`} className="border-b border-theme/40">
          <td className="py-1.5 pr-3 pl-4 text-content-secondary">{a.label}</td>
          <td className={`py-1.5 pl-3 text-right font-mono ${negative ? 'text-clay-700' : ''}`}>
            {negative ? '(' : ''}{formatAmount(a.amount)}{negative ? ')' : ''}
          </td>
        </tr>
      ))}
    </>
  )
}
