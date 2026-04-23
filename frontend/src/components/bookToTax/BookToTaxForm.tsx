'use client'

/**
 * Book-to-Tax input form — Sprint 689f.
 *
 * Pure form input (no file upload). Renders the top-level entity data
 * (tax year, pretax income, assets, rates), a dynamic adjustment table
 * with add/remove rows, and the deferred-tax rollforward inputs.
 */

import { useCallback, useMemo, useState } from 'react'
import type {
  AdjustmentDirection,
  AdjustmentRequest,
  BookToTaxRequest,
  DifferenceType,
  StandardAdjustment,
} from '@/types/bookToTax'

interface BookToTaxFormProps {
  onAnalyze: (payload: BookToTaxRequest) => void
  onExport: (payload: BookToTaxRequest) => void
  loading: boolean
  standardAdjustments: StandardAdjustment[]
}

interface AdjRow {
  id: string
  label: string
  amount: string
  difference_type: DifferenceType
  direction: AdjustmentDirection
  code?: string | null
}

function freshRow(): AdjRow {
  return {
    id: `adj-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    label: '',
    amount: '',
    difference_type: 'permanent',
    direction: 'add',
    code: null,
  }
}

export function BookToTaxForm({ onAnalyze, onExport, loading, standardAdjustments }: BookToTaxFormProps) {
  const [taxYear, setTaxYear] = useState<string>(String(new Date().getUTCFullYear() - 1))
  const [bookIncome, setBookIncome] = useState('')
  const [totalAssets, setTotalAssets] = useState('')
  const [federalRate, setFederalRate] = useState('0.21')
  const [stateRate, setStateRate] = useState('0')
  const [beginningDta, setBeginningDta] = useState('0')
  const [beginningDtl, setBeginningDtl] = useState('0')
  const [rows, setRows] = useState<AdjRow[]>([freshRow()])

  const addRow = useCallback(() => {
    setRows(prev => [...prev, freshRow()])
  }, [])

  const removeRow = useCallback((id: string) => {
    setRows(prev => (prev.length > 1 ? prev.filter(r => r.id !== id) : prev))
  }, [])

  const updateRow = useCallback((id: string, patch: Partial<AdjRow>) => {
    setRows(prev => prev.map(r => (r.id === id ? { ...r, ...patch } : r)))
  }, [])

  const applyStandardToRow = useCallback(
    (id: string, code: string) => {
      const std = standardAdjustments.find(s => s.code === code)
      if (!std) return
      updateRow(id, {
        label: std.description,
        code: std.code,
        difference_type: std.difference_type,
        direction: std.typical_direction,
      })
    },
    [standardAdjustments, updateRow],
  )

  const payload = useMemo<BookToTaxRequest | null>(() => {
    const year = Number.parseInt(taxYear, 10)
    if (!Number.isFinite(year) || year < 2000 || year > 2099) return null
    if (!bookIncome.trim() || !totalAssets.trim() || !federalRate.trim()) return null
    const adjustments: AdjustmentRequest[] = rows
      .filter(r => r.label.trim() && r.amount.trim())
      .map(r => ({
        label: r.label.trim(),
        amount: r.amount.trim(),
        difference_type: r.difference_type,
        direction: r.direction,
        code: r.code || null,
      }))
    return {
      tax_year: year,
      book_pretax_income: bookIncome.trim(),
      total_assets: totalAssets.trim(),
      federal_tax_rate: federalRate.trim(),
      state_tax_rate: stateRate.trim() || '0',
      adjustments,
      rollforward: {
        beginning_dta: beginningDta.trim() || '0',
        beginning_dtl: beginningDtl.trim() || '0',
      },
    }
  }, [taxYear, bookIncome, totalAssets, federalRate, stateRate, rows, beginningDta, beginningDtl])

  const canRun = payload !== null && !loading

  return (
    <div className="theme-card p-6">
      <h2 className="font-serif text-lg text-content-primary mb-2">Reconciliation Inputs</h2>
      <p className="font-sans text-sm text-content-secondary mb-5">
        Enter book pretax income and the entity&apos;s total assets; the engine applies the M-3 threshold
        ($10 million assets) to pick M-1 vs. M-3 presentation. Rates default to the 21% federal rate;
        override as needed.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
        <LabelledInput label="Tax year" value={taxYear} onChange={setTaxYear} disabled={loading} />
        <LabelledInput label="Book pretax income" value={bookIncome} onChange={setBookIncome} disabled={loading} placeholder="500000" />
        <LabelledInput label="Total assets" value={totalAssets} onChange={setTotalAssets} disabled={loading} placeholder="5000000" />
        <LabelledInput label="Federal rate" value={federalRate} onChange={setFederalRate} disabled={loading} placeholder="0.21" />
        <LabelledInput label="State rate" value={stateRate} onChange={setStateRate} disabled={loading} placeholder="0" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-2 gap-3 mb-5">
        <LabelledInput label="Beginning DTA" value={beginningDta} onChange={setBeginningDta} disabled={loading} placeholder="0" />
        <LabelledInput label="Beginning DTL" value={beginningDtl} onChange={setBeginningDtl} disabled={loading} placeholder="0" />
      </div>

      <h3 className="font-serif text-sm text-content-primary mb-2">Adjustments</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm font-sans">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wider text-content-tertiary border-b border-theme">
              <th className="py-2 pr-2 min-w-[160px]">Standard</th>
              <th className="py-2 pr-2 min-w-[200px]">Label</th>
              <th className="py-2 pr-2">Amount</th>
              <th className="py-2 pr-2">Type</th>
              <th className="py-2 pr-2">Direction</th>
              <th className="py-2 pl-2"></th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id} className="border-b border-theme/40 last:border-0">
                <td className="py-2 pr-2">
                  <select
                    value={r.code ?? ''}
                    onChange={e => applyStandardToRow(r.id, e.target.value)}
                    disabled={loading || standardAdjustments.length === 0}
                    className="w-full px-2 py-1 rounded border border-theme bg-surface-card font-sans text-xs text-content-primary"
                  >
                    <option value="">&mdash; custom &mdash;</option>
                    {standardAdjustments.map(s => (
                      <option key={s.code} value={s.code}>{s.description}</option>
                    ))}
                  </select>
                </td>
                <td className="py-2 pr-2">
                  <input
                    value={r.label}
                    onChange={e => updateRow(r.id, { label: e.target.value })}
                    disabled={loading}
                    className="w-full px-2 py-1 rounded border border-theme bg-surface-card font-sans text-xs text-content-primary"
                    placeholder="Adjustment label"
                  />
                </td>
                <td className="py-2 pr-2">
                  <input
                    value={r.amount}
                    onChange={e => updateRow(r.id, { amount: e.target.value })}
                    disabled={loading}
                    className="w-28 px-2 py-1 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary"
                    placeholder="0.00"
                  />
                </td>
                <td className="py-2 pr-2">
                  <select
                    value={r.difference_type}
                    onChange={e => updateRow(r.id, { difference_type: e.target.value as DifferenceType })}
                    disabled={loading}
                    className="px-2 py-1 rounded border border-theme bg-surface-card font-sans text-xs text-content-primary"
                  >
                    <option value="permanent">Permanent</option>
                    <option value="temporary">Temporary</option>
                  </select>
                </td>
                <td className="py-2 pr-2">
                  <select
                    value={r.direction}
                    onChange={e => updateRow(r.id, { direction: e.target.value as AdjustmentDirection })}
                    disabled={loading}
                    className="px-2 py-1 rounded border border-theme bg-surface-card font-sans text-xs text-content-primary"
                  >
                    <option value="add">Add</option>
                    <option value="subtract">Subtract</option>
                  </select>
                </td>
                <td className="py-2 pl-2 text-right">
                  <button
                    type="button"
                    onClick={() => removeRow(r.id)}
                    disabled={loading || rows.length === 1}
                    className="text-xs text-content-tertiary hover:text-clay-700 disabled:opacity-30 disabled:cursor-not-allowed"
                    aria-label="Remove adjustment"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-3 mb-5">
        <button
          type="button"
          onClick={addRow}
          disabled={loading}
          className="text-xs font-sans text-sage-700 hover:text-sage-800 disabled:opacity-50"
        >
          + Add adjustment row
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => payload && onAnalyze(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg bg-sage-600 text-oatmeal-50 font-sans font-medium hover:bg-sage-700 disabled:bg-obsidian-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Computing…' : 'Compute M-1 / M-3'}
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

function LabelledInput({
  label, value, onChange, disabled, placeholder,
}: { label: string; value: string; onChange: (v: string) => void; disabled?: boolean; placeholder?: string }) {
  return (
    <label className="flex flex-col gap-1 text-xs font-sans text-content-secondary">
      <span>{label}</span>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="px-2 py-1.5 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500"
      />
    </label>
  )
}
