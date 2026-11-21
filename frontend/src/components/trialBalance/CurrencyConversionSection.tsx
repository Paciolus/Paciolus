'use client'

/**
 * Sprint 890 (CEO brief 15D): the trial balance's convenience currency conversion.
 *
 * Every converted figure is shown with the rate, the rate's date and its source. The backend's
 * label says plainly that this is a single closing rate per currency, not translation under
 * ASC 830 or IAS 21.
 */
import type { TBCurrencyConversion } from '@/types/diagnostic'

const ISSUE_TEXT: Record<string, string> = {
  missing_rate: 'No rate for this currency in your table',
  no_currency: 'No currency given for this account',
  mixed_currency: 'More than one currency on this account',
}

function amount(value: number | null): string {
  if (value === null) return '—'
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function CurrencyConversionSection({ data }: { data: TBCurrencyConversion }) {
  return (
    <section className="theme-card p-6" data-testid="currency-conversion">
      <h3 className="font-serif text-lg text-content-primary mb-2">
        Convenience Conversion to {data.presentation_currency}
      </h3>
      <p className="font-sans text-sm text-content-secondary leading-relaxed mb-4">{data.label}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs font-sans uppercase tracking-wider text-content-tertiary">
              <th className="py-2 pr-4">Account</th>
              <th className="py-2 pr-4">Currency</th>
              <th className="py-2 pr-4 text-right">Amount</th>
              <th className="py-2 pr-4 text-right">Rate</th>
              <th className="py-2 pr-4">Rate date</th>
              <th className="py-2 pr-4">Rate source</th>
              <th className="py-2 text-right">{data.presentation_currency}</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map(row => (
              <tr key={row.account} className="border-t border-theme">
                <td className="py-2 pr-4 font-sans text-content-primary">{row.account}</td>
                <td className="py-2 pr-4 font-mono text-content-secondary">{row.currency ?? '—'}</td>
                <td className="py-2 pr-4 font-mono text-right">{amount(row.original_amount)}</td>
                <td className="py-2 pr-4 font-mono text-right">{row.rate ?? '—'}</td>
                <td className="py-2 pr-4 font-mono">{row.rate_date ?? '—'}</td>
                <td className="py-2 pr-4 font-sans text-content-secondary">
                  {row.issue ? <span className="text-clay-600">{ISSUE_TEXT[row.issue] ?? row.issue}</span> : row.rate_source}
                </td>
                <td className="py-2 font-mono text-right">{amount(row.converted_amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
