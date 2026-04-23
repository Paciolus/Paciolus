'use client'

/**
 * Cash Flow Projector input form — Sprint 689g.
 */

import { useCallback, useMemo, useState } from 'react'
import type {
  AgingBucketsRequest,
  CashFlowProjectionRequest,
  ForecastFrequency,
  RecurringFlowRequest,
} from '@/types/cashFlowProjector'

interface Props {
  onProject: (payload: CashFlowProjectionRequest) => void
  onExport: (payload: CashFlowProjectionRequest) => void
  loading: boolean
}

interface FlowRow {
  id: string
  label: string
  amount: string
  frequency: ForecastFrequency
  first_date: string
}

function freshFlow(startDate: string): FlowRow {
  return {
    id: `flow-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    label: '',
    amount: '',
    frequency: 'monthly',
    first_date: startDate,
  }
}

function emptyAging(): AgingBucketsRequest {
  return { current: '0', days_1_30: '0', days_31_60: '0', days_61_90: '0', days_over_90: '0' }
}

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export function CashFlowForm({ onProject, onExport, loading }: Props) {
  const today = isoDate(new Date())
  const [openingBalance, setOpeningBalance] = useState('')
  const [startDate, setStartDate] = useState(today)
  const [minSafeCash, setMinSafeCash] = useState('')
  const [arAging, setArAging] = useState<AgingBucketsRequest>(emptyAging())
  const [apAging, setApAging] = useState<AgingBucketsRequest>(emptyAging())
  const [flows, setFlows] = useState<FlowRow[]>([])

  const addFlow = useCallback(() => {
    setFlows(prev => [...prev, freshFlow(startDate)])
  }, [startDate])

  const removeFlow = useCallback((id: string) => {
    setFlows(prev => prev.filter(f => f.id !== id))
  }, [])

  const updateFlow = useCallback((id: string, patch: Partial<FlowRow>) => {
    setFlows(prev => prev.map(f => (f.id === id ? { ...f, ...patch } : f)))
  }, [])

  const payload = useMemo<CashFlowProjectionRequest | null>(() => {
    if (!openingBalance.trim() || !startDate) return null
    const recurring_flows: RecurringFlowRequest[] = flows
      .filter(f => f.label.trim() && f.amount.trim() && f.first_date)
      .map(f => ({
        label: f.label.trim(),
        amount: f.amount.trim(),
        frequency: f.frequency,
        first_date: f.first_date,
      }))
    return {
      opening_balance: openingBalance.trim(),
      start_date: startDate,
      ar_aging: arAging,
      ap_aging: apAging,
      recurring_flows,
      min_safe_cash: minSafeCash.trim() || null,
    }
  }, [openingBalance, startDate, minSafeCash, arAging, apAging, flows])

  const canRun = payload !== null && !loading

  return (
    <div className="theme-card p-6">
      <h2 className="font-serif text-lg text-content-primary mb-2">Forecast Inputs</h2>
      <p className="font-sans text-sm text-content-secondary mb-5">
        Project 90 days of cash flow across base / stress / best scenarios. AR and AP aging buckets drive
        the collection and disbursement curves; recurring flows land on their frequency cadence starting
        from the specified first date.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <LabelledInput label="Opening cash" value={openingBalance} onChange={setOpeningBalance} disabled={loading} placeholder="100000" />
        <LabelledInput label="Start date" value={startDate} onChange={setStartDate} disabled={loading} type="date" />
        <LabelledInput label="Min safe cash" value={minSafeCash} onChange={setMinSafeCash} disabled={loading} placeholder="optional" />
      </div>

      <AgingGrid label="AR aging" buckets={arAging} onChange={setArAging} disabled={loading} />
      <AgingGrid label="AP aging" buckets={apAging} onChange={setApAging} disabled={loading} />

      <h3 className="font-serif text-sm text-content-primary mt-5 mb-2">Recurring Flows</h3>
      <p className="font-sans text-xs text-content-tertiary mb-3">
        Positive amounts are inflows (e.g. subscription revenue); negative amounts are outflows
        (e.g. payroll, rent).
      </p>
      {flows.length === 0 ? (
        <p className="font-sans text-xs text-content-tertiary mb-3">No recurring flows yet.</p>
      ) : (
        <div className="overflow-x-auto mb-3">
          <table className="w-full text-sm font-sans">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-content-tertiary border-b border-theme">
                <th className="py-2 pr-2 min-w-[160px]">Label</th>
                <th className="py-2 pr-2">Amount</th>
                <th className="py-2 pr-2">Frequency</th>
                <th className="py-2 pr-2">First date</th>
                <th className="py-2 pl-2"></th>
              </tr>
            </thead>
            <tbody>
              {flows.map(f => (
                <tr key={f.id} className="border-b border-theme/40 last:border-0">
                  <td className="py-2 pr-2">
                    <input
                      value={f.label}
                      onChange={e => updateFlow(f.id, { label: e.target.value })}
                      disabled={loading}
                      className="w-full px-2 py-1 rounded border border-theme bg-surface-card font-sans text-xs text-content-primary"
                      placeholder="Payroll"
                    />
                  </td>
                  <td className="py-2 pr-2">
                    <input
                      value={f.amount}
                      onChange={e => updateFlow(f.id, { amount: e.target.value })}
                      disabled={loading}
                      className="w-28 px-2 py-1 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary"
                      placeholder="-30000"
                    />
                  </td>
                  <td className="py-2 pr-2">
                    <select
                      value={f.frequency}
                      onChange={e => updateFlow(f.id, { frequency: e.target.value as ForecastFrequency })}
                      disabled={loading}
                      className="px-2 py-1 rounded border border-theme bg-surface-card font-sans text-xs text-content-primary"
                    >
                      <option value="weekly">Weekly</option>
                      <option value="biweekly">Bi-weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="quarterly">Quarterly</option>
                    </select>
                  </td>
                  <td className="py-2 pr-2">
                    <input
                      type="date"
                      value={f.first_date}
                      onChange={e => updateFlow(f.id, { first_date: e.target.value })}
                      disabled={loading}
                      className="px-2 py-1 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary"
                    />
                  </td>
                  <td className="py-2 pl-2 text-right">
                    <button
                      type="button"
                      onClick={() => removeFlow(f.id)}
                      disabled={loading}
                      className="text-xs text-content-tertiary hover:text-clay-700 disabled:opacity-30"
                      aria-label="Remove recurring flow"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mb-5">
        <button
          type="button"
          onClick={addFlow}
          disabled={loading}
          className="text-xs font-sans text-sage-700 hover:text-sage-800 disabled:opacity-50"
        >
          + Add recurring flow
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => payload && onProject(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg bg-sage-600 text-oatmeal-50 font-sans font-medium hover:bg-sage-700 disabled:bg-obsidian-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Projecting…' : 'Run Projection'}
        </button>
        <button
          type="button"
          onClick={() => payload && onExport(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg border border-theme bg-surface-card text-content-primary font-sans font-medium hover:bg-oatmeal-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Download CSV
        </button>
      </div>
    </div>
  )
}

function AgingGrid({
  label, buckets, onChange, disabled,
}: { label: string; buckets: AgingBucketsRequest; onChange: (b: AgingBucketsRequest) => void; disabled?: boolean }) {
  const set = (key: keyof AgingBucketsRequest, value: string) => onChange({ ...buckets, [key]: value })
  return (
    <div className="mb-4">
      <h3 className="font-serif text-sm text-content-primary mb-2">{label}</h3>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <LabelledInput label="Current" value={buckets.current} onChange={v => set('current', v)} disabled={disabled} />
        <LabelledInput label="1–30" value={buckets.days_1_30} onChange={v => set('days_1_30', v)} disabled={disabled} />
        <LabelledInput label="31–60" value={buckets.days_31_60} onChange={v => set('days_31_60', v)} disabled={disabled} />
        <LabelledInput label="61–90" value={buckets.days_61_90} onChange={v => set('days_61_90', v)} disabled={disabled} />
        <LabelledInput label="Over 90" value={buckets.days_over_90} onChange={v => set('days_over_90', v)} disabled={disabled} />
      </div>
    </div>
  )
}

function LabelledInput({
  label, value, onChange, disabled, placeholder, type = 'text',
}: { label: string; value: string; onChange: (v: string) => void; disabled?: boolean; placeholder?: string; type?: string }) {
  return (
    <label className="flex flex-col gap-1 text-xs font-sans text-content-secondary">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="px-2 py-1.5 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500"
      />
    </label>
  )
}
