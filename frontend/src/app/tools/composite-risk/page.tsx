'use client'

/**
 * Composite Risk Scoring (Sprint 688)
 *
 * ISA 315 (Revised 2019): Auditor-input workflow for inherent/control/fraud
 * risk per account/assertion. Combines auditor inputs via the RMM matrix and
 * optionally integrates automated diagnostic data (TB anomaly score, tool
 * scores, going concern indicators).
 *
 * Form input only — no file upload, no data persisted (Zero-Storage).
 */

import { useCallback, useMemo, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { DisclaimerBox, GuestCTA, UnverifiedCTA, CitationFooter } from '@/components/shared'
import { UpgradeGate } from '@/components/shared/UpgradeGate'
import { Reveal } from '@/components/ui/Reveal'
import { useCompositeRisk } from '@/hooks/useCompositeRisk'
import {
  ASSERTIONS,
  ASSERTION_LABELS,
  RISK_BADGE_STYLES,
  RISK_LEVELS,
  RISK_LEVEL_LABELS,
  type AccountRiskAssessmentInput,
  type Assertion,
  type RiskLevel,
} from '@/types/compositeRisk'

const EMPTY_ROW = (): AccountRiskAssessmentInput => ({
  account_name: '',
  assertion: 'existence',
  inherent_risk: 'moderate',
  control_risk: 'moderate',
  fraud_risk_factor: false,
  auditor_notes: '',
})

export default function CompositeRiskPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const { status, result, error, buildProfile, reset } = useCompositeRisk()

  const [rows, setRows] = useState<AccountRiskAssessmentInput[]>([EMPTY_ROW()])
  const [tbScore, setTbScore] = useState('')
  const [tbTier, setTbTier] = useState('')
  const [gcCount, setGcCount] = useState('0')

  const isVerified = user?.is_verified !== false

  const addRow = useCallback(() => {
    setRows(prev => [...prev, EMPTY_ROW()])
  }, [])

  const removeRow = useCallback((idx: number) => {
    setRows(prev => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev))
  }, [])

  const updateRow = useCallback(
    <K extends keyof AccountRiskAssessmentInput>(
      idx: number,
      field: K,
      value: AccountRiskAssessmentInput[K],
    ) => {
      setRows(prev => {
        const next = [...prev]
        next[idx] = { ...next[idx], [field]: value } as AccountRiskAssessmentInput
        return next
      })
    },
    [],
  )

  const canSubmit = useMemo(
    () => rows.every(r => r.account_name.trim().length > 0),
    [rows],
  )

  const handleSubmit = useCallback(async () => {
    const payload = {
      account_assessments: rows.map(r => ({
        ...r,
        account_name: r.account_name.trim(),
        auditor_notes: r.auditor_notes.trim(),
      })),
      tb_diagnostic_score: tbScore ? Number(tbScore) : null,
      tb_diagnostic_tier: tbTier.trim() || null,
      going_concern_indicators_triggered: Number(gcCount) || 0,
    }
    await buildProfile(payload)
  }, [rows, tbScore, tbTier, gcCount, buildProfile])

  const handleReset = useCallback(() => {
    reset()
    setRows([EMPTY_ROW()])
    setTbScore('')
    setTbTier('')
    setGcCount('0')
  }, [reset])

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="h-[2px] bg-gradient-to-r from-transparent via-sage-500/20 to-transparent" />
      <div className="max-w-6xl mx-auto px-6 pt-8 pb-16">
        <Reveal>
          <header className="mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-theme-success-bg border border-theme-success-border mb-4">
              <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
              <span className="text-theme-success-text text-xs font-sans font-medium">
                ISA 315 (Revised 2019) — Risks of Material Misstatement
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
              Composite Risk Scoring
            </h1>
            <p className="text-sm font-sans text-content-secondary mt-1.5 max-w-3xl">
              Record auditor-assessed inherent and control risk per account/assertion pair.
              The composite profile combines your judgments via the ISA 315 RMM matrix and
              optionally integrates automated diagnostic data. Auditor inputs drive the
              overall risk tier — this tool structures your judgments, it does not replace them.
            </p>
          </header>
        </Reveal>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Composite Risk Scoring requires a verified account. Sign in or create an account to record risk assessments." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="composite_risk">
            <Reveal delay={0.1}>
              <section className="theme-card p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-serif text-lg font-bold text-content-primary">
                    Account / Assertion Risk Assessments
                  </h2>
                  <button
                    type="button"
                    onClick={addRow}
                    className="px-3 py-1.5 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm hover:bg-sage-700 transition-colors"
                  >
                    + Add Row
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs font-sans text-content-tertiary uppercase tracking-wider border-b border-theme">
                        <th className="py-2 pr-3">Account</th>
                        <th className="py-2 pr-3">Assertion</th>
                        <th className="py-2 pr-3">Inherent</th>
                        <th className="py-2 pr-3">Control</th>
                        <th className="py-2 pr-3">Fraud</th>
                        <th className="py-2 pr-3">Notes</th>
                        <th className="py-2" />
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row, idx) => (
                        <tr key={idx} className="border-b border-theme last:border-b-0">
                          <td className="py-2 pr-3">
                            <input
                              type="text"
                              value={row.account_name}
                              onChange={e => updateRow(idx, 'account_name', e.target.value)}
                              placeholder="e.g. Revenue"
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Account name row ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <select
                              value={row.assertion}
                              onChange={e => updateRow(idx, 'assertion', e.target.value as Assertion)}
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Assertion row ${idx + 1}`}
                            >
                              {ASSERTIONS.map(a => (
                                <option key={a} value={a}>
                                  {ASSERTION_LABELS[a]}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="py-2 pr-3">
                            <select
                              value={row.inherent_risk}
                              onChange={e => updateRow(idx, 'inherent_risk', e.target.value as RiskLevel)}
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Inherent risk row ${idx + 1}`}
                            >
                              {RISK_LEVELS.map(r => (
                                <option key={r} value={r}>
                                  {RISK_LEVEL_LABELS[r]}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="py-2 pr-3">
                            <select
                              value={row.control_risk}
                              onChange={e => updateRow(idx, 'control_risk', e.target.value as RiskLevel)}
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Control risk row ${idx + 1}`}
                            >
                              {RISK_LEVELS.map(r => (
                                <option key={r} value={r}>
                                  {RISK_LEVEL_LABELS[r]}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="py-2 pr-3 text-center">
                            <input
                              type="checkbox"
                              checked={row.fraud_risk_factor}
                              onChange={e => updateRow(idx, 'fraud_risk_factor', e.target.checked)}
                              className="w-4 h-4 text-sage-600 focus:ring-sage-500 rounded"
                              aria-label={`Fraud risk factor row ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <input
                              type="text"
                              value={row.auditor_notes}
                              onChange={e => updateRow(idx, 'auditor_notes', e.target.value)}
                              placeholder="Optional"
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Auditor notes row ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2">
                            <button
                              type="button"
                              onClick={() => removeRow(idx)}
                              disabled={rows.length === 1}
                              className="px-2 py-1 text-xs text-clay-600 hover:text-clay-800 disabled:opacity-30 disabled:cursor-not-allowed"
                              aria-label={`Remove row ${idx + 1}`}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </Reveal>

            <Reveal delay={0.15}>
              <section className="theme-card p-6 mb-6">
                <h2 className="font-serif text-lg font-bold text-content-primary mb-4">
                  Optional Diagnostic Integration
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <label className="block">
                    <span className="block text-xs font-sans font-medium text-content-secondary mb-1">
                      TB Anomaly Score (0–100)
                    </span>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={tbScore}
                      onChange={e => setTbScore(e.target.value)}
                      placeholder="e.g. 42"
                      className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                    />
                  </label>
                  <label className="block">
                    <span className="block text-xs font-sans font-medium text-content-secondary mb-1">
                      TB Diagnostic Tier
                    </span>
                    <input
                      type="text"
                      value={tbTier}
                      onChange={e => setTbTier(e.target.value)}
                      placeholder="e.g. elevated"
                      maxLength={50}
                      className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                    />
                  </label>
                  <label className="block">
                    <span className="block text-xs font-sans font-medium text-content-secondary mb-1">
                      Going Concern Indicators
                    </span>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      value={gcCount}
                      onChange={e => setGcCount(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                    />
                  </label>
                </div>
              </section>
            </Reveal>

            <Reveal delay={0.2}>
              <div className="flex flex-wrap items-center gap-3 mb-6">
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={!canSubmit || status === 'loading'}
                  className="px-5 py-2.5 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {status === 'loading' ? 'Building Profile…' : 'Build Composite Profile'}
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                >
                  Reset
                </button>
                {!canSubmit && (
                  <span className="text-xs font-sans text-content-tertiary">
                    Every row needs an account name.
                  </span>
                )}
              </div>
            </Reveal>

            {status === 'error' && (
              <div
                role="alert"
                className="bg-theme-error-bg border border-theme-error-border border-l-4 border-l-clay-500 rounded-xl p-6 mb-6"
              >
                <h3 className="font-serif text-sm text-theme-error-text mb-1">
                  Profile build failed
                </h3>
                <p className="font-sans text-sm text-content-secondary">{error}</p>
              </div>
            )}

            {status === 'success' && result && (
              <Reveal delay={0.1}>
                <CompositeRiskResults data={result} />
              </Reveal>
            )}
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}

/* ─── Results sub-component ───────────────────────────────────────── */

function CompositeRiskResults({ data }: { data: import('@/types/compositeRisk').CompositeRiskProfileResponse }) {
  const overall = data.overall_risk_tier ?? 'low'
  return (
    <div className="space-y-6">
      <section className="theme-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="font-serif text-lg font-bold text-content-primary">
            Composite Risk Profile
          </h2>
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full border text-xs font-sans font-semibold uppercase tracking-wider ${RISK_BADGE_STYLES[overall as RiskLevel]}`}
          >
            Overall Tier: {RISK_LEVEL_LABELS[overall as RiskLevel]}
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <Stat label="Total Assessments" value={data.total_assessments} />
          <Stat label="High-Risk Accounts" value={data.high_risk_accounts} tone="clay" />
          <Stat label="Fraud Risk Factors" value={data.fraud_risk_accounts} tone="clay" />
          <Stat label="Going Concern Flags" value={data.going_concern_indicators_triggered} />
        </div>
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-base font-bold text-content-primary mb-3">
          Risk Distribution (combined inherent × control)
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {RISK_LEVELS.map(level => (
            <div
              key={level}
              className={`border rounded-lg p-3 text-center ${RISK_BADGE_STYLES[level]}`}
            >
              <div className="font-mono text-2xl font-bold">
                {data.risk_distribution[level] ?? 0}
              </div>
              <div className="text-xs font-sans uppercase tracking-wider mt-1">
                {RISK_LEVEL_LABELS[level]}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-base font-bold text-content-primary mb-3">
          Account / Assertion Matrix
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs font-sans text-content-tertiary uppercase tracking-wider border-b border-theme">
                <th className="py-2 pr-3">Account</th>
                <th className="py-2 pr-3">Assertion</th>
                <th className="py-2 pr-3">Inherent</th>
                <th className="py-2 pr-3">Control</th>
                <th className="py-2 pr-3">Combined (RMM)</th>
                <th className="py-2 pr-3">Fraud</th>
                <th className="py-2 pr-3">Notes</th>
              </tr>
            </thead>
            <tbody>
              {data.account_assessments.map((a, idx) => (
                <tr key={idx} className="border-b border-theme last:border-b-0">
                  <td className="py-2 pr-3 font-sans text-content-primary">{a.account_name}</td>
                  <td className="py-2 pr-3 font-sans text-content-secondary capitalize">
                    {ASSERTION_LABELS[a.assertion]}
                  </td>
                  <td className="py-2 pr-3">
                    <RiskPill level={a.inherent_risk} />
                  </td>
                  <td className="py-2 pr-3">
                    <RiskPill level={a.control_risk} />
                  </td>
                  <td className="py-2 pr-3">
                    <RiskPill level={a.combined_risk} />
                  </td>
                  <td className="py-2 pr-3 text-center font-mono">
                    {a.fraud_risk_factor ? 'Yes' : '—'}
                  </td>
                  <td className="py-2 pr-3 font-sans text-xs text-content-tertiary">
                    {a.auditor_notes || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <DisclaimerBox>
        {data.disclaimer}
      </DisclaimerBox>
      <CitationFooter standards={['ISA 315', 'ISA 330']} />
    </div>
  )
}

function RiskPill({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md border text-xs font-sans font-medium ${RISK_BADGE_STYLES[level]}`}
    >
      {RISK_LEVEL_LABELS[level]}
    </span>
  )
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone?: 'clay' | 'sage'
}) {
  const color =
    tone === 'clay'
      ? 'text-clay-700'
      : tone === 'sage'
        ? 'text-sage-700'
        : 'text-content-primary'
  return (
    <div className="p-3 rounded-lg border border-theme bg-surface-card-secondary">
      <div className={`font-mono text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs font-sans text-content-tertiary uppercase tracking-wider mt-1">
        {label}
      </div>
    </div>
  )
}
