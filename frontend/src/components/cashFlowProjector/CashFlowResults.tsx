'use client'

/**
 * Cash Flow Projector results — Sprint 689g.
 *
 * Renders a per-scenario summary grid (base / stress / best) with
 * 30 / 60 / 90 horizon summaries. Daily detail lives in the CSV export.
 */

import type { CashFlowForecastResponse, ScenarioResult } from '@/types/cashFlowProjector'

function formatAmount(raw: string): string {
  const n = Number.parseFloat(raw)
  if (!Number.isFinite(n)) return raw
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

interface Props {
  result: CashFlowForecastResponse
}

export function CashFlowResults({ result }: Props) {
  const scenarioEntries = Object.entries(result.scenarios)

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scenarioEntries.map(([name, s]) => (
          <ScenarioCard key={name} name={name} scenario={s} />
        ))}
      </div>

      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Horizon Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-sans">
            <thead>
              <tr className="border-b border-theme text-left text-xs uppercase tracking-wider text-content-tertiary">
                <th className="py-2 pr-3">Scenario</th>
                <th className="py-2 px-3">Horizon</th>
                <th className="py-2 px-3 text-right">Inflow</th>
                <th className="py-2 px-3 text-right">Outflow</th>
                <th className="py-2 px-3 text-right">Ending</th>
                <th className="py-2 px-3 text-right">Lowest</th>
                <th className="py-2 pl-3 text-right">Lowest day</th>
              </tr>
            </thead>
            <tbody>
              {scenarioEntries.flatMap(([name, s]) =>
                Object.entries(s.horizon).map(([horizonDay, h]) => (
                  <tr key={`${name}-${horizonDay}`} className="border-b border-theme/40 last:border-0">
                    <td className="py-2 pr-3 font-medium capitalize">{name}</td>
                    <td className="py-2 px-3 font-mono text-xs">{h.day}d</td>
                    <td className="py-2 px-3 text-right font-mono">{formatAmount(h.cumulative_inflow)}</td>
                    <td className="py-2 px-3 text-right font-mono">{formatAmount(h.cumulative_outflow)}</td>
                    <td className="py-2 px-3 text-right font-mono">{formatAmount(h.ending_balance)}</td>
                    <td className="py-2 px-3 text-right font-mono">{formatAmount(h.lowest_balance)}</td>
                    <td className="py-2 pl-3 text-right font-mono text-content-tertiary">{h.lowest_balance_day}</td>
                  </tr>
                )),
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function ScenarioCard({ name, scenario }: { name: string; scenario: ScenarioResult }) {
  const tone = scenario.goes_negative
    ? 'border-clay-200 bg-clay-50/40'
    : scenario.breach_min_safe_cash
      ? 'border-obsidian-200 bg-oatmeal-100/40'
      : 'border-sage-200 bg-sage-50/40'

  return (
    <div className={`theme-card p-5 border ${tone}`}>
      <div className="font-serif text-content-primary capitalize mb-2">{name}</div>
      <dl className="text-xs font-sans space-y-1">
        <dt className="text-content-tertiary">Goes negative</dt>
        <dd className={`font-mono ${scenario.goes_negative ? 'text-clay-700' : 'text-sage-700'}`}>
          {scenario.goes_negative ? `Yes (day ${scenario.first_negative_day ?? '—'})` : 'No'}
        </dd>
        <dt className="text-content-tertiary pt-1">Min-safe-cash breach</dt>
        <dd className={`font-mono ${scenario.breach_min_safe_cash ? 'text-obsidian-700' : 'text-sage-700'}`}>
          {scenario.breach_min_safe_cash ? 'Yes' : 'No'}
        </dd>
        <dt className="text-content-tertiary pt-1">Collection priorities</dt>
        <dd className="font-mono">{scenario.collection_priorities.length}</dd>
        <dt className="text-content-tertiary pt-1">AP deferral candidates</dt>
        <dd className="font-mono">{scenario.ap_deferral_candidates.length}</dd>
      </dl>
    </div>
  )
}
