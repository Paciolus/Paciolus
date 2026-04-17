'use client'

/**
 * Loan Amortization Generator (Sprint 625)
 *
 * Form-input only — zero-storage compliant. Generates a period-by-period
 * amortization schedule with annual roll-ups and book journal entry templates.
 */

import { useState, useCallback, useMemo } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { Reveal } from '@/components/ui/Reveal'
import { apiPost } from '@/utils/apiClient'

type Frequency = 'monthly' | 'quarterly' | 'semi-annual' | 'annual'
type Method = 'standard' | 'interest_only' | 'balloon'

interface PeriodEntry {
  period_number: number
  payment_date: string | null
  beginning_balance: string
  scheduled_payment: string
  interest: string
  principal: string
  extra_principal: string
  ending_balance: string
}

interface AnnualSummaryEntry {
  year_index: number
  calendar_year: number | null
  total_payments: string
  total_interest: string
  total_principal: string
  ending_balance: string
}

interface JournalEntryTemplate {
  description: string
  debits: { account: string; amount: string }[]
  credits: { account: string; amount: string }[]
}

interface ScheduleResponse {
  schedule: PeriodEntry[]
  annual_summary: AnnualSummaryEntry[]
  inputs: Record<string, unknown>
  total_interest: string
  total_payments: string
  payoff_date: string | null
  journal_entry_templates: JournalEntryTemplate[]
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

export default function LoanAmortizationPage() {
  const { token } = useAuthSession()
  const [principal, setPrincipal] = useState('200000')
  const [annualRatePct, setAnnualRatePct] = useState('6.0')
  const [termPeriods, setTermPeriods] = useState('360')
  const [frequency, setFrequency] = useState<Frequency>('monthly')
  const [method, setMethod] = useState<Method>('standard')
  const [startDate, setStartDate] = useState('')
  const [balloonAmount, setBalloonAmount] = useState('')
  const [extraPaymentPeriod, setExtraPaymentPeriod] = useState('')
  const [extraPaymentAmount, setExtraPaymentAmount] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ScheduleResponse | null>(null)

  const buildPayload = useCallback(() => {
    const annualRateDecimal = (Number(annualRatePct) / 100).toString()
    const extras: { period_number: number; amount: string }[] = []
    const extraPeriod = Number(extraPaymentPeriod)
    const extraAmount = Number(extraPaymentAmount)
    if (extraPeriod > 0 && extraAmount > 0) {
      extras.push({ period_number: extraPeriod, amount: extraAmount.toString() })
    }
    return {
      principal: principal.trim(),
      annual_rate: annualRateDecimal,
      term_periods: Number(termPeriods),
      frequency,
      method,
      start_date: startDate || null,
      balloon_amount: method === 'balloon' && balloonAmount ? balloonAmount.trim() : null,
      extra_payments: extras,
      rate_changes: [],
    }
  }, [
    principal,
    annualRatePct,
    termPeriods,
    frequency,
    method,
    startDate,
    balloonAmount,
    extraPaymentPeriod,
    extraPaymentAmount,
  ])

  const submit = useCallback(async () => {
    setError(null)
    setResult(null)
    setSubmitting(true)
    try {
      const response = await apiPost<ScheduleResponse>(
        '/audit/loan-amortization',
        token,
        buildPayload()
      )
      if (response.ok && response.data) {
        setResult(response.data)
      } else {
        setError(response.error || 'Calculation failed')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Calculation failed')
    } finally {
      setSubmitting(false)
    }
  }, [token, buildPayload])

  const downloadExport = useCallback(
    async (format: 'csv' | 'xlsx' | 'pdf') => {
      if (!token) return
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || ''}/audit/loan-amortization/export.${format}`,
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
      if (!response.ok) {
        setError(`${format.toUpperCase()} export failed`)
        return
      }
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `loan_amortization_schedule.${format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
    },
    [token, buildPayload]
  )

  const monthlyPayment = useMemo(() => {
    const first = result?.schedule[0]
    return first ? first.scheduled_payment : null
  }, [result])

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="h-[2px] bg-gradient-to-r from-transparent via-sage-500/20 to-transparent" />
      <div className="max-w-5xl mx-auto px-6 pt-8 pb-16">
        <Reveal>
          <header className="mb-8">
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
              Loan Amortization
            </h1>
            <p className="text-sm font-sans text-content-secondary mt-1.5">
              Generate a period-by-period schedule with annual roll-ups and book journal entry templates.
              Form input only — no file upload, no data persisted.
            </p>
          </header>
        </Reveal>

        <Reveal delay={0.1}>
          <section className="theme-card p-6 mb-6">
            <h2 className="font-serif text-lg font-bold text-content-primary mb-4">Loan Inputs</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Principal ($)</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={principal}
                  onChange={e => setPrincipal(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                />
              </label>
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Annual Rate (%)</span>
                <input
                  type="number"
                  min="0"
                  step="0.001"
                  value={annualRatePct}
                  onChange={e => setAnnualRatePct(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                />
              </label>
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Term (periods)</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={termPeriods}
                  onChange={e => setTermPeriods(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                />
              </label>
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Payment Frequency</span>
                <select
                  value={frequency}
                  onChange={e => setFrequency(e.target.value as Frequency)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                >
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly</option>
                  <option value="semi-annual">Semi-Annual</option>
                  <option value="annual">Annual</option>
                </select>
              </label>
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Amortization Method</span>
                <select
                  value={method}
                  onChange={e => setMethod(e.target.value as Method)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                >
                  <option value="standard">Standard (level payment)</option>
                  <option value="interest_only">Interest Only</option>
                  <option value="balloon">Balloon</option>
                </select>
              </label>
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Start Date (optional)</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={e => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                />
              </label>
              {method === 'balloon' && (
                <label className="block md:col-span-2">
                  <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Balloon Amount ($)</span>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={balloonAmount}
                    onChange={e => setBalloonAmount(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                  />
                </label>
              )}
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Extra Payment — Period</span>
                <input
                  type="number"
                  min="0"
                  step="1"
                  placeholder="e.g. 12"
                  value={extraPaymentPeriod}
                  onChange={e => setExtraPaymentPeriod(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                />
              </label>
              <label className="block">
                <span className="block text-xs font-sans font-medium text-content-secondary mb-1">Extra Payment — Amount ($)</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="e.g. 5000"
                  value={extraPaymentAmount}
                  onChange={e => setExtraPaymentAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500 transition"
                />
              </label>
            </div>

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={submit}
                disabled={submitting || !token}
                className="px-5 py-2.5 rounded-xl bg-obsidian-900 text-oatmeal-50 font-sans font-bold hover:bg-obsidian-800 disabled:opacity-50 transition-colors"
              >
                {submitting ? 'Calculating…' : 'Generate Schedule'}
              </button>
              {result && (
                <>
                  <button
                    type="button"
                    onClick={() => downloadExport('csv')}
                    className="px-5 py-2.5 rounded-xl bg-sage-600 text-oatmeal-50 font-sans font-bold hover:bg-sage-700 transition-colors"
                  >
                    Download CSV
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadExport('xlsx')}
                    className="px-5 py-2.5 rounded-xl bg-sage-600 text-oatmeal-50 font-sans font-bold hover:bg-sage-700 transition-colors"
                  >
                    Download XLSX
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadExport('pdf')}
                    className="px-5 py-2.5 rounded-xl bg-obsidian-700 text-oatmeal-50 font-sans font-bold hover:bg-obsidian-600 transition-colors"
                  >
                    Download PDF
                  </button>
                </>
              )}
            </div>

            {error && (
              <p className="mt-4 text-sm font-sans text-clay-600" role="alert">
                {error}
              </p>
            )}
          </section>
        </Reveal>

        {result && (
          <Reveal delay={0.15}>
            <section className="theme-card p-6 mb-6">
              <h2 className="font-serif text-lg font-bold text-content-primary mb-4">Summary</h2>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Period Payment</p>
                  <p className="font-mono text-2xl text-content-primary mt-1">
                    {monthlyPayment ? formatCurrency(monthlyPayment) : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Total Interest</p>
                  <p className="font-mono text-2xl text-clay-600 mt-1">{formatCurrency(result.total_interest)}</p>
                </div>
                <div>
                  <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Payoff</p>
                  <p className="font-mono text-2xl text-content-primary mt-1">
                    {result.payoff_date || `${result.schedule.length} periods`}
                  </p>
                </div>
              </div>
            </section>

            <section className="theme-card p-6 mb-6">
              <h2 className="font-serif text-lg font-bold text-content-primary mb-4">Annual Summary</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left border-b border-theme">
                      <th className="py-2 pr-4 font-sans font-medium text-content-secondary">Year</th>
                      <th className="py-2 pr-4 font-sans font-medium text-content-secondary text-right">Payments</th>
                      <th className="py-2 pr-4 font-sans font-medium text-content-secondary text-right">Interest</th>
                      <th className="py-2 pr-4 font-sans font-medium text-content-secondary text-right">Principal</th>
                      <th className="py-2 font-sans font-medium text-content-secondary text-right">Ending Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.annual_summary.map(row => (
                      <tr key={row.year_index} className="border-b border-theme/50">
                        <td className="py-2 pr-4 font-mono text-content-primary">
                          {row.calendar_year ?? `Year ${row.year_index}`}
                        </td>
                        <td className="py-2 pr-4 font-mono text-content-primary text-right">{formatCurrency(row.total_payments)}</td>
                        <td className="py-2 pr-4 font-mono text-clay-600 text-right">{formatCurrency(row.total_interest)}</td>
                        <td className="py-2 pr-4 font-mono text-sage-600 text-right">{formatCurrency(row.total_principal)}</td>
                        <td className="py-2 font-mono text-content-primary text-right">{formatCurrency(row.ending_balance)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="theme-card p-6 mb-6">
              <h2 className="font-serif text-lg font-bold text-content-primary mb-4">
                Period-by-Period Schedule ({result.schedule.length} entries)
              </h2>
              <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                <table className="min-w-full text-xs">
                  <thead className="bg-surface-card-secondary sticky top-0">
                    <tr className="text-left border-b border-theme">
                      <th className="py-2 px-2 font-sans font-medium text-content-secondary">#</th>
                      <th className="py-2 px-2 font-sans font-medium text-content-secondary">Date</th>
                      <th className="py-2 px-2 font-sans font-medium text-content-secondary text-right">Payment</th>
                      <th className="py-2 px-2 font-sans font-medium text-content-secondary text-right">Interest</th>
                      <th className="py-2 px-2 font-sans font-medium text-content-secondary text-right">Principal</th>
                      <th className="py-2 px-2 font-sans font-medium text-content-secondary text-right">Extra</th>
                      <th className="py-2 px-2 font-sans font-medium text-content-secondary text-right">Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.schedule.map(row => (
                      <tr key={row.period_number} className="border-b border-theme/30">
                        <td className="py-1.5 px-2 font-mono text-content-primary">{row.period_number}</td>
                        <td className="py-1.5 px-2 font-mono text-content-tertiary">{row.payment_date || '—'}</td>
                        <td className="py-1.5 px-2 font-mono text-content-primary text-right">{formatCurrency(row.scheduled_payment)}</td>
                        <td className="py-1.5 px-2 font-mono text-clay-600 text-right">{formatCurrency(row.interest)}</td>
                        <td className="py-1.5 px-2 font-mono text-sage-600 text-right">{formatCurrency(row.principal)}</td>
                        <td className="py-1.5 px-2 font-mono text-sage-700 text-right">
                          {row.extra_principal !== '0.00' ? formatCurrency(row.extra_principal) : '—'}
                        </td>
                        <td className="py-1.5 px-2 font-mono text-content-primary text-right">{formatCurrency(row.ending_balance)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="theme-card p-6">
              <h2 className="font-serif text-lg font-bold text-content-primary mb-4">Suggested Journal Entries</h2>
              <div className="space-y-4">
                {result.journal_entry_templates.map((tmpl, idx) => (
                  <div key={idx} className="border border-theme rounded-lg p-4">
                    <p className="font-sans font-medium text-content-primary mb-2">{tmpl.description}</p>
                    <table className="w-full text-sm">
                      <tbody>
                        {tmpl.debits.map((d, i) => (
                          <tr key={`dr-${i}`}>
                            <td className="py-1 pr-3 font-sans text-content-secondary w-24">DR</td>
                            <td className="py-1 pr-3 font-sans text-content-primary">{d.account}</td>
                            <td className="py-1 font-mono text-content-primary text-right">{formatCurrency(d.amount)}</td>
                          </tr>
                        ))}
                        {tmpl.credits.map((c, i) => (
                          <tr key={`cr-${i}`}>
                            <td className="py-1 pr-3 font-sans text-content-secondary w-24 pl-6">CR</td>
                            <td className="py-1 pr-3 font-sans text-content-primary pl-6">{c.account}</td>
                            <td className="py-1 font-mono text-content-primary text-right">{formatCurrency(c.amount)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            </section>
          </Reveal>
        )}
      </div>
    </main>
  )
}
