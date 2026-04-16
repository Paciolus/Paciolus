'use client'

/**
 * Depreciation Calculator (Sprint 626)
 *
 * Form-input only — zero-storage compliant. Generates book and MACRS tax
 * depreciation schedules with a book/tax timing reconciliation.
 */

import { useState, useCallback, useMemo } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { Reveal } from '@/components/ui/Reveal'
import { apiPost } from '@/utils/apiClient'

type BookMethod = 'straight_line' | 'declining_balance' | 'sum_of_years_digits' | 'units_of_production'
type MacrsSystem = '' | 'gds_200db' | 'gds_150db' | 'gds_sl'
type MacrsConvention = 'half_year' | 'mid_quarter' | 'mid_month'

interface YearEntry {
  year_index: number
  calendar_year: number | null
  beginning_book_value: string
  depreciation: string
  accumulated_depreciation: string
  ending_book_value: string
}

interface ComparisonEntry {
  year_index: number
  book_depreciation: string
  tax_depreciation: string
  timing_difference: string
  deferred_tax_change: string
  cumulative_deferred_tax: string
}

interface DepreciationResponse {
  inputs: Record<string, unknown>
  book_schedule: YearEntry[]
  tax_schedule: YearEntry[]
  book_tax_comparison: ComparisonEntry[]
  total_book_depreciation: string
  total_tax_depreciation: string
  cumulative_deferred_tax: string
}

const formatCurrency = (raw: string) => {
  const num = Number(raw)
  if (Number.isNaN(num)) return raw
  return num.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export default function DepreciationPage() {
  const { token } = useAuthSession()
  const [assetName, setAssetName] = useState('Office Equipment')
  const [cost, setCost] = useState('10000')
  const [salvageValue, setSalvageValue] = useState('0')
  const [usefulLifeYears, setUsefulLifeYears] = useState('5')
  const [placedInServiceYear, setPlacedInServiceYear] = useState(String(new Date().getFullYear()))
  const [placedInServiceQuarter, setPlacedInServiceQuarter] = useState<1 | 2 | 3 | 4>(1)
  const [bookMethod, setBookMethod] = useState<BookMethod>('straight_line')
  const [dbFactor, setDbFactor] = useState('2')
  const [macrsSystem, setMacrsSystem] = useState<MacrsSystem>('gds_200db')
  const [macrsPropertyClass, setMacrsPropertyClass] = useState('5')
  const [macrsConvention, setMacrsConvention] = useState<MacrsConvention>('half_year')
  const [taxRatePct, setTaxRatePct] = useState('21')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DepreciationResponse | null>(null)

  const buildPayload = useCallback(() => {
    return {
      asset_name: assetName.trim(),
      cost: cost.trim(),
      salvage_value: salvageValue.trim() || '0',
      useful_life_years: Number(usefulLifeYears),
      placed_in_service_year: placedInServiceYear ? Number(placedInServiceYear) : null,
      placed_in_service_quarter: placedInServiceQuarter,
      placed_in_service_month: 1,
      book_method: bookMethod,
      db_factor: dbFactor || '2',
      units_total: null,
      units_per_year: [],
      macrs_system: macrsSystem || null,
      macrs_property_class: macrsSystem ? Number(macrsPropertyClass) : null,
      macrs_convention: macrsConvention,
      tax_rate: (Number(taxRatePct) / 100).toString(),
    }
  }, [
    assetName,
    cost,
    salvageValue,
    usefulLifeYears,
    placedInServiceYear,
    placedInServiceQuarter,
    bookMethod,
    dbFactor,
    macrsSystem,
    macrsPropertyClass,
    macrsConvention,
    taxRatePct,
  ])

  const onSubmit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault()
      setSubmitting(true)
      setError(null)
      setResult(null)
      try {
        const response = await apiPost<DepreciationResponse>(
          '/audit/depreciation',
          token,
          buildPayload()
        )
        if (response.ok && response.data) {
          setResult(response.data)
        } else {
          setError(response.error || 'Calculation failed')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to compute schedule.')
      } finally {
        setSubmitting(false)
      }
    },
    [buildPayload, token]
  )

  const onDownloadCsv = useCallback(async () => {
    if (!token) return
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ''}/audit/depreciation/export.csv`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: JSON.stringify(buildPayload()),
        }
      )
      if (!res.ok) throw new Error('Failed to download CSV.')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `depreciation_${assetName.replace(/\W+/g, '_')}.csv`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to download CSV.')
    }
  }, [assetName, buildPayload, token])

  const summaryCards = useMemo(() => {
    if (!result) return null
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="rounded-lg border border-obsidian-200 bg-oatmeal-50 p-4">
          <div className="text-xs font-sans text-obsidian-600 uppercase tracking-wide">Total Book Depreciation</div>
          <div className="font-mono text-2xl text-obsidian-900 mt-1">{formatCurrency(result.total_book_depreciation)}</div>
        </div>
        <div className="rounded-lg border border-obsidian-200 bg-oatmeal-50 p-4">
          <div className="text-xs font-sans text-obsidian-600 uppercase tracking-wide">Total Tax (MACRS) Depreciation</div>
          <div className="font-mono text-2xl text-obsidian-900 mt-1">
            {result.tax_schedule.length ? formatCurrency(result.total_tax_depreciation) : '—'}
          </div>
        </div>
        <div className="rounded-lg border border-obsidian-200 bg-oatmeal-50 p-4">
          <div className="text-xs font-sans text-obsidian-600 uppercase tracking-wide">Cumulative Deferred Tax</div>
          <div className="font-mono text-2xl text-obsidian-900 mt-1">
            {result.book_tax_comparison.length ? formatCurrency(result.cumulative_deferred_tax) : '—'}
          </div>
        </div>
      </div>
    )
  }, [result])

  return (
    <div className="min-h-screen bg-oatmeal-100">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <Reveal>
          <h1 className="font-serif text-4xl text-obsidian-900 mb-2">Depreciation Calculator</h1>
          <p className="font-sans text-obsidian-700 mb-8">
            Book methods (straight-line, declining balance, SYD, units of production) and MACRS tax depreciation
            with a book-vs-tax timing reconciliation. Form input — zero-storage.
          </p>
        </Reveal>

        <form onSubmit={onSubmit} className="bg-white rounded-lg border border-obsidian-200 p-6 mb-8 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Asset Name</span>
              <input
                type="text"
                value={assetName}
                onChange={(e) => setAssetName(e.target.value)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-sans"
                required
              />
            </label>
            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Cost ($)</span>
              <input
                type="number"
                step="0.01"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-mono"
                required
              />
            </label>
            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Salvage Value ($)</span>
              <input
                type="number"
                step="0.01"
                value={salvageValue}
                onChange={(e) => setSalvageValue(e.target.value)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-mono"
              />
            </label>
            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Useful Life (years)</span>
              <input
                type="number"
                min="1"
                max="50"
                value={usefulLifeYears}
                onChange={(e) => setUsefulLifeYears(e.target.value)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-mono"
                required
              />
            </label>
            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Placed-in-Service Year</span>
              <input
                type="number"
                min="1900"
                max="2100"
                value={placedInServiceYear}
                onChange={(e) => setPlacedInServiceYear(e.target.value)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-mono"
              />
            </label>
            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Quarter (mid-quarter)</span>
              <select
                value={placedInServiceQuarter}
                onChange={(e) => setPlacedInServiceQuarter(Number(e.target.value) as 1 | 2 | 3 | 4)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-sans"
              >
                <option value={1}>Q1</option>
                <option value={2}>Q2</option>
                <option value={3}>Q3</option>
                <option value={4}>Q4</option>
              </select>
            </label>

            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Book Method</span>
              <select
                value={bookMethod}
                onChange={(e) => setBookMethod(e.target.value as BookMethod)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-sans"
              >
                <option value="straight_line">Straight-Line</option>
                <option value="declining_balance">Declining Balance</option>
                <option value="sum_of_years_digits">Sum-of-Years-Digits</option>
              </select>
            </label>
            {bookMethod === 'declining_balance' && (
              <label className="block">
                <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">DB Factor (e.g. 2 = DDB)</span>
                <input
                  type="number"
                  step="0.1"
                  value={dbFactor}
                  onChange={(e) => setDbFactor(e.target.value)}
                  className="w-full border border-obsidian-300 rounded px-3 py-2 font-mono"
                />
              </label>
            )}

            <label className="block">
              <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">MACRS System</span>
              <select
                value={macrsSystem}
                onChange={(e) => setMacrsSystem(e.target.value as MacrsSystem)}
                className="w-full border border-obsidian-300 rounded px-3 py-2 font-sans"
              >
                <option value="">No MACRS (book only)</option>
                <option value="gds_200db">GDS 200% DB</option>
                <option value="gds_150db">GDS 150% DB</option>
                <option value="gds_sl">GDS Straight-Line</option>
              </select>
            </label>
            {macrsSystem && (
              <>
                <label className="block">
                  <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">MACRS Property Class</span>
                  <select
                    value={macrsPropertyClass}
                    onChange={(e) => setMacrsPropertyClass(e.target.value)}
                    className="w-full border border-obsidian-300 rounded px-3 py-2 font-sans"
                  >
                    <option value="3">3-year (rents, tractors)</option>
                    <option value="5">5-year (computers, autos)</option>
                    <option value="7">7-year (office furniture)</option>
                    <option value="10">10-year (vessels, fruit trees)</option>
                    <option value="15">15-year (land improvements)</option>
                    <option value="20">20-year (farm buildings)</option>
                  </select>
                </label>
                <label className="block">
                  <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">MACRS Convention</span>
                  <select
                    value={macrsConvention}
                    onChange={(e) => setMacrsConvention(e.target.value as MacrsConvention)}
                    className="w-full border border-obsidian-300 rounded px-3 py-2 font-sans"
                  >
                    <option value="half_year">Half-Year</option>
                    <option value="mid_quarter">Mid-Quarter (5-yr only)</option>
                  </select>
                </label>
                <label className="block">
                  <span className="block text-xs font-sans text-obsidian-700 uppercase tracking-wide mb-1">Tax Rate (%)</span>
                  <input
                    type="number"
                    step="0.1"
                    value={taxRatePct}
                    onChange={(e) => setTaxRatePct(e.target.value)}
                    className="w-full border border-obsidian-300 rounded px-3 py-2 font-mono"
                  />
                </label>
              </>
            )}
          </div>

          <div className="flex items-center gap-3 mt-6">
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 bg-obsidian-900 text-oatmeal-50 rounded font-sans hover:bg-obsidian-800 disabled:opacity-50"
            >
              {submitting ? 'Computing…' : 'Calculate Schedule'}
            </button>
            {result && (
              <button
                type="button"
                onClick={onDownloadCsv}
                className="px-5 py-2 border border-obsidian-300 text-obsidian-900 rounded font-sans hover:bg-oatmeal-100"
              >
                Download CSV
              </button>
            )}
            {error && <span className="font-sans text-clay-700">{error}</span>}
          </div>
        </form>

        {result && (
          <Reveal>
            {summaryCards}
            <h2 className="font-serif text-2xl text-obsidian-900 mb-3">Book Schedule</h2>
            <div className="overflow-x-auto bg-white rounded-lg border border-obsidian-200 mb-8">
              <table className="min-w-full text-sm">
                <thead className="bg-oatmeal-100">
                  <tr>
                    <th className="px-3 py-2 text-left font-sans text-obsidian-700">Year</th>
                    <th className="px-3 py-2 text-left font-sans text-obsidian-700">Calendar Year</th>
                    <th className="px-3 py-2 text-right font-sans text-obsidian-700">Beginning BV</th>
                    <th className="px-3 py-2 text-right font-sans text-obsidian-700">Depreciation</th>
                    <th className="px-3 py-2 text-right font-sans text-obsidian-700">Accumulated</th>
                    <th className="px-3 py-2 text-right font-sans text-obsidian-700">Ending BV</th>
                  </tr>
                </thead>
                <tbody>
                  {result.book_schedule.map((entry) => (
                    <tr key={entry.year_index} className="border-t border-obsidian-100">
                      <td className="px-3 py-2 font-mono">{entry.year_index}</td>
                      <td className="px-3 py-2 font-mono">{entry.calendar_year ?? '—'}</td>
                      <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.beginning_book_value)}</td>
                      <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.depreciation)}</td>
                      <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.accumulated_depreciation)}</td>
                      <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.ending_book_value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {result.tax_schedule.length > 0 && (
              <>
                <h2 className="font-serif text-2xl text-obsidian-900 mb-3">Tax (MACRS) Schedule</h2>
                <div className="overflow-x-auto bg-white rounded-lg border border-obsidian-200 mb-8">
                  <table className="min-w-full text-sm">
                    <thead className="bg-oatmeal-100">
                      <tr>
                        <th className="px-3 py-2 text-left font-sans text-obsidian-700">Year</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Beginning Basis</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Depreciation</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Accumulated</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Ending Basis</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.tax_schedule.map((entry) => (
                        <tr key={entry.year_index} className="border-t border-obsidian-100">
                          <td className="px-3 py-2 font-mono">{entry.year_index}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.beginning_book_value)}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.depreciation)}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.accumulated_depreciation)}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(entry.ending_book_value)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <h2 className="font-serif text-2xl text-obsidian-900 mb-3">Book vs Tax Timing</h2>
                <div className="overflow-x-auto bg-white rounded-lg border border-obsidian-200 mb-8">
                  <table className="min-w-full text-sm">
                    <thead className="bg-oatmeal-100">
                      <tr>
                        <th className="px-3 py-2 text-left font-sans text-obsidian-700">Year</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Book</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Tax</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Timing Diff</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Deferred Tax Δ</th>
                        <th className="px-3 py-2 text-right font-sans text-obsidian-700">Cumulative DTL/DTA</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.book_tax_comparison.map((row) => (
                        <tr key={row.year_index} className="border-t border-obsidian-100">
                          <td className="px-3 py-2 font-mono">{row.year_index}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(row.book_depreciation)}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(row.tax_depreciation)}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(row.timing_difference)}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(row.deferred_tax_change)}</td>
                          <td className="px-3 py-2 font-mono text-right">{formatCurrency(row.cumulative_deferred_tax)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </Reveal>
        )}
      </div>
    </div>
  )
}
