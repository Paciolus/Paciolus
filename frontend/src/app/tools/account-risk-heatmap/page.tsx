'use client'

/**
 * Account Risk Heatmap (Sprint 688)
 *
 * Aggregates per-account audit signals (audit anomalies, classification issues,
 * cutoff flags, accrual findings, composite risk profile) into a triage-density
 * view with priority tiers and weighted scores.
 *
 * Signals can be entered directly via the Raw Signal form, or pasted as JSON
 * from upstream diagnostic engines. CSV export downloads the same aggregation.
 */

import { useCallback, useMemo, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { DisclaimerBox, GuestCTA, UnverifiedCTA, CitationFooter } from '@/components/shared'
import { UpgradeGate } from '@/components/shared/UpgradeGate'
import { Reveal } from '@/components/ui/Reveal'
import { useAccountRiskHeatmap } from '@/hooks/useAccountRiskHeatmap'
import {
  PRIORITY_TIER_LABELS,
  PRIORITY_TIER_STYLES,
  type HeatmapRequest,
  type PriorityTier,
  type RawSignalInput,
  type Severity,
} from '@/types/accountRiskHeatmap'

const EMPTY_SIGNAL = (): RawSignalInput => ({
  account_number: '',
  account_name: '',
  source: '',
  severity: 'medium',
  issue: '',
  materiality: '0',
  confidence: 1.0,
})

const SEVERITIES: Severity[] = ['high', 'medium', 'low']

export default function AccountRiskHeatmapPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const { status, result, error, exporting, generate, downloadCsv, reset } = useAccountRiskHeatmap()

  const [signals, setSignals] = useState<RawSignalInput[]>([EMPTY_SIGNAL()])
  const [upstreamJson, setUpstreamJson] = useState('')
  const [jsonError, setJsonError] = useState<string | null>(null)

  const isVerified = user?.is_verified !== false

  const addSignal = useCallback(() => {
    setSignals(prev => [...prev, EMPTY_SIGNAL()])
  }, [])

  const removeSignal = useCallback((idx: number) => {
    setSignals(prev => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev))
  }, [])

  const updateSignal = useCallback(
    <K extends keyof RawSignalInput>(idx: number, field: K, value: RawSignalInput[K]) => {
      setSignals(prev => {
        const next = [...prev]
        next[idx] = { ...next[idx], [field]: value } as RawSignalInput
        return next
      })
    },
    [],
  )

  const buildPayload = useCallback((): HeatmapRequest | null => {
    const cleanSignals = signals
      .filter(s => s.account_name.trim() && s.source.trim() && s.issue.trim())
      .map(s => ({
        account_number: (s.account_number ?? '').trim(),
        account_name: s.account_name.trim(),
        source: s.source.trim(),
        severity: s.severity ?? 'medium',
        issue: s.issue.trim(),
        materiality: (s.materiality ?? '0').trim() || '0',
        confidence: s.confidence ?? 1.0,
      }))

    let upstream: Partial<HeatmapRequest> = {}
    if (upstreamJson.trim()) {
      try {
        const parsed = JSON.parse(upstreamJson)
        if (typeof parsed !== 'object' || Array.isArray(parsed) || parsed === null) {
          setJsonError('Upstream JSON must be an object with signal keys.')
          return null
        }
        upstream = parsed
        setJsonError(null)
      } catch (e) {
        setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
        return null
      }
    } else {
      setJsonError(null)
    }

    const payload: HeatmapRequest = {
      signals: cleanSignals,
      audit_anomalies: upstream.audit_anomalies ?? [],
      classification_issues: upstream.classification_issues ?? [],
      cutoff_flags: upstream.cutoff_flags ?? [],
      accrual_findings: upstream.accrual_findings ?? [],
      composite_risk_profile: upstream.composite_risk_profile ?? null,
    }
    return payload
  }, [signals, upstreamJson])

  const handleSubmit = useCallback(async () => {
    const payload = buildPayload()
    if (!payload) return
    await generate(payload)
  }, [buildPayload, generate])

  const handleExport = useCallback(async () => {
    const payload = buildPayload()
    if (!payload) return
    await downloadCsv(payload)
  }, [buildPayload, downloadCsv])

  const handleReset = useCallback(() => {
    reset()
    setSignals([EMPTY_SIGNAL()])
    setUpstreamJson('')
    setJsonError(null)
  }, [reset])

  const hasSomeInput = useMemo(
    () =>
      signals.some(s => s.account_name.trim() && s.source.trim() && s.issue.trim()) ||
      upstreamJson.trim().length > 0,
    [signals, upstreamJson],
  )

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="h-[2px] bg-gradient-to-r from-transparent via-sage-500/20 to-transparent" />
      <div className="max-w-6xl mx-auto px-6 pt-8 pb-16">
        <Reveal>
          <header className="mb-8">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-theme-success-bg border border-theme-success-border mb-4">
              <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
              <span className="text-theme-success-text text-xs font-sans font-medium">
                Cross-Engine Triage
              </span>
            </div>
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
              Account Risk Heatmap
            </h1>
            <p className="text-sm font-sans text-content-secondary mt-1.5 max-w-3xl">
              Aggregate per-account audit signals across diagnostic engines into a single
              triage-density view. Pre-normalized signals go in the raw signal form;
              upstream engine outputs can be pasted as JSON and translated automatically.
            </p>
          </header>
        </Reveal>

        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Account Risk Heatmap requires a verified account. Sign in or create an account to aggregate audit signals." />
        )}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="account_risk_heatmap">
            <Reveal delay={0.1}>
              <section className="theme-card p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-serif text-lg font-bold text-content-primary">
                    Raw Signals
                  </h2>
                  <button
                    type="button"
                    onClick={addSignal}
                    className="px-3 py-1.5 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm hover:bg-sage-700 transition-colors"
                  >
                    + Add Signal
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs font-sans text-content-tertiary uppercase tracking-wider border-b border-theme">
                        <th className="py-2 pr-3">Acct #</th>
                        <th className="py-2 pr-3">Account Name</th>
                        <th className="py-2 pr-3">Source</th>
                        <th className="py-2 pr-3">Severity</th>
                        <th className="py-2 pr-3">Issue</th>
                        <th className="py-2 pr-3">Materiality</th>
                        <th className="py-2 pr-3">Confidence</th>
                        <th className="py-2" />
                      </tr>
                    </thead>
                    <tbody>
                      {signals.map((s, idx) => (
                        <tr key={idx} className="border-b border-theme last:border-b-0">
                          <td className="py-2 pr-3">
                            <input
                              type="text"
                              value={s.account_number ?? ''}
                              onChange={e => updateSignal(idx, 'account_number', e.target.value)}
                              placeholder="4000"
                              className="w-24 px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-mono text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Account number signal ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <input
                              type="text"
                              value={s.account_name}
                              onChange={e => updateSignal(idx, 'account_name', e.target.value)}
                              placeholder="Revenue"
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Account name signal ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <input
                              type="text"
                              value={s.source}
                              onChange={e => updateSignal(idx, 'source', e.target.value)}
                              placeholder="audit_engine"
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Source signal ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <select
                              value={s.severity as Severity}
                              onChange={e => updateSignal(idx, 'severity', e.target.value as Severity)}
                              className="px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Severity signal ${idx + 1}`}
                            >
                              {SEVERITIES.map(sev => (
                                <option key={sev} value={sev}>
                                  {sev}
                                </option>
                              ))}
                            </select>
                          </td>
                          <td className="py-2 pr-3">
                            <input
                              type="text"
                              value={s.issue}
                              onChange={e => updateSignal(idx, 'issue', e.target.value)}
                              placeholder="Rounding anomaly"
                              className="w-full px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Issue signal ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <input
                              type="text"
                              value={s.materiality ?? '0'}
                              onChange={e => updateSignal(idx, 'materiality', e.target.value)}
                              placeholder="0"
                              className="w-28 px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-mono text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Materiality signal ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2 pr-3">
                            <input
                              type="number"
                              min="0"
                              max="1"
                              step="0.1"
                              value={s.confidence ?? 1.0}
                              onChange={e =>
                                updateSignal(idx, 'confidence', Number(e.target.value))
                              }
                              className="w-20 px-2 py-1.5 rounded-md bg-surface-input border border-theme text-content-primary font-mono text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                              aria-label={`Confidence signal ${idx + 1}`}
                            />
                          </td>
                          <td className="py-2">
                            <button
                              type="button"
                              onClick={() => removeSignal(idx)}
                              disabled={signals.length === 1}
                              className="px-2 py-1 text-xs text-clay-600 hover:text-clay-800 disabled:opacity-30 disabled:cursor-not-allowed"
                              aria-label={`Remove signal ${idx + 1}`}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="text-[11px] font-sans text-content-tertiary mt-3">
                  Empty rows (no account name / source / issue) are ignored on submit.
                </p>
              </section>
            </Reveal>

            <Reveal delay={0.15}>
              <section className="theme-card p-6 mb-6">
                <h2 className="font-serif text-lg font-bold text-content-primary mb-3">
                  Upstream Engine JSON (optional)
                </h2>
                <p className="text-xs font-sans text-content-secondary mb-3">
                  Paste a JSON object with any of:{' '}
                  <code className="font-mono text-xs bg-surface-card-secondary px-1 py-0.5 rounded">
                    audit_anomalies
                  </code>
                  ,{' '}
                  <code className="font-mono text-xs bg-surface-card-secondary px-1 py-0.5 rounded">
                    classification_issues
                  </code>
                  ,{' '}
                  <code className="font-mono text-xs bg-surface-card-secondary px-1 py-0.5 rounded">
                    cutoff_flags
                  </code>
                  ,{' '}
                  <code className="font-mono text-xs bg-surface-card-secondary px-1 py-0.5 rounded">
                    accrual_findings
                  </code>
                  ,{' '}
                  <code className="font-mono text-xs bg-surface-card-secondary px-1 py-0.5 rounded">
                    composite_risk_profile
                  </code>
                  . The backend adapter translates each into RiskSignals.
                </p>
                <textarea
                  value={upstreamJson}
                  onChange={e => setUpstreamJson(e.target.value)}
                  rows={6}
                  placeholder='{"audit_anomalies": [...], "classification_issues": [...]}'
                  className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono text-xs focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                />
                {jsonError && (
                  <p className="text-xs font-sans text-clay-700 mt-2" role="alert">
                    {jsonError}
                  </p>
                )}
              </section>
            </Reveal>

            <Reveal delay={0.2}>
              <div className="flex flex-wrap items-center gap-3 mb-6">
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={!hasSomeInput || status === 'loading'}
                  className="px-5 py-2.5 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {status === 'loading' ? 'Aggregating…' : 'Generate Heatmap'}
                </button>
                <button
                  type="button"
                  onClick={handleExport}
                  disabled={!hasSomeInput || exporting}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exporting ? 'Exporting…' : 'Export CSV'}
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                >
                  Reset
                </button>
              </div>
            </Reveal>

            {status === 'error' && (
              <div
                role="alert"
                className="bg-theme-error-bg border border-theme-error-border border-l-4 border-l-clay-500 rounded-xl p-6 mb-6"
              >
                <h3 className="font-serif text-sm text-theme-error-text mb-1">
                  Heatmap build failed
                </h3>
                <p className="font-sans text-sm text-content-secondary">{error}</p>
              </div>
            )}

            {status === 'success' && result && (
              <Reveal delay={0.1}>
                <HeatmapResults result={result} />
              </Reveal>
            )}
          </UpgradeGate>
        )}
      </div>
    </main>
  )
}

/* ─── Results ──────────────────────────────────────────────────────── */

function HeatmapResults({ result }: { result: import('@/types/accountRiskHeatmap').HeatmapResponse }) {
  return (
    <div className="space-y-6">
      <section className="theme-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className="font-serif text-lg font-bold text-content-primary">
            Heatmap Summary
          </h2>
          <div className="flex flex-wrap gap-2 text-[11px] font-sans text-content-tertiary">
            Sources active:{' '}
            {result.sources_active.length > 0
              ? result.sources_active.map(src => (
                  <span
                    key={src}
                    className="font-mono bg-surface-card-secondary border border-theme rounded px-1.5 py-0.5"
                  >
                    {src}
                  </span>
                ))
              : '—'}
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatBox label="Accounts Flagged" value={result.total_accounts_with_signals} />
          <StatBox label="Total Signals" value={result.total_signals} />
          <StatBox
            label="High Priority"
            value={result.high_priority_count}
            tier="high"
          />
          <StatBox
            label="Moderate"
            value={result.moderate_priority_count}
            tier="moderate"
          />
          <StatBox label="Low" value={result.low_priority_count} tier="low" />
        </div>
      </section>

      <section className="theme-card p-6">
        <h3 className="font-serif text-base font-bold text-content-primary mb-3">
          Ranked Accounts
        </h3>
        {result.rows.length === 0 ? (
          <p className="font-sans text-sm text-content-tertiary italic">
            No accounts flagged by the supplied signals.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs font-sans text-content-tertiary uppercase tracking-wider border-b border-theme">
                  <th className="py-2 pr-3">Rank</th>
                  <th className="py-2 pr-3">Account</th>
                  <th className="py-2 pr-3">Tier</th>
                  <th className="py-2 pr-3">Signals</th>
                  <th className="py-2 pr-3">Severities</th>
                  <th className="py-2 pr-3">Sources</th>
                  <th className="py-2 pr-3">Materiality</th>
                  <th className="py-2 pr-3 text-right">Weighted</th>
                </tr>
              </thead>
              <tbody>
                {result.rows.map(row => (
                  <tr key={`${row.rank}-${row.account_name}`} className="border-b border-theme last:border-b-0 align-top">
                    <td className="py-2 pr-3 font-mono text-content-secondary">{row.rank}</td>
                    <td className="py-2 pr-3">
                      <div className="font-sans text-content-primary">{row.account_name}</div>
                      {row.account_number && (
                        <div className="font-mono text-xs text-content-tertiary">
                          {row.account_number}
                        </div>
                      )}
                      <ul className="mt-1 space-y-0.5">
                        {row.issues.slice(0, 3).map((issue, i) => (
                          <li key={i} className="text-[11px] font-sans text-content-tertiary">
                            • {issue}
                          </li>
                        ))}
                        {row.issues.length > 3 && (
                          <li className="text-[11px] font-sans text-content-tertiary italic">
                            … +{row.issues.length - 3} more
                          </li>
                        )}
                      </ul>
                    </td>
                    <td className="py-2 pr-3">
                      <TierPill tier={row.priority_tier} />
                    </td>
                    <td className="py-2 pr-3 font-mono">{row.signal_count}</td>
                    <td className="py-2 pr-3 text-xs font-sans">
                      {Object.entries(row.severities).map(([sev, n]) => (
                        <span
                          key={sev}
                          className="inline-block mr-1 px-1.5 py-0.5 rounded border border-theme bg-surface-card-secondary font-mono"
                        >
                          {sev}: {n}
                        </span>
                      ))}
                    </td>
                    <td className="py-2 pr-3 text-xs font-sans">
                      {row.sources.map(src => (
                        <span
                          key={src}
                          className="inline-block mr-1 px-1.5 py-0.5 rounded border border-theme bg-surface-card-secondary font-mono"
                        >
                          {src}
                        </span>
                      ))}
                    </td>
                    <td className="py-2 pr-3 font-mono text-content-secondary">
                      {row.total_materiality}
                    </td>
                    <td className="py-2 pr-3 font-mono text-right text-content-primary">
                      {row.weighted_score.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <DisclaimerBox>
        The heatmap is an analytical triage aid, not a substitute for professional
        judgment. Priority tiers reflect the distribution of the supplied signals —
        high-priority accounts warrant earlier substantive procedures, but all
        signals should be evaluated on their merits within the engagement context.
      </DisclaimerBox>
      <CitationFooter standards={['ISA 315', 'ISA 520']} />
    </div>
  )
}

function TierPill({ tier }: { tier: PriorityTier }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md border text-xs font-sans font-medium ${PRIORITY_TIER_STYLES[tier]}`}
    >
      {PRIORITY_TIER_LABELS[tier]}
    </span>
  )
}

function StatBox({
  label,
  value,
  tier,
}: {
  label: string
  value: number
  tier?: PriorityTier
}) {
  const classes = tier
    ? `${PRIORITY_TIER_STYLES[tier]} border rounded-lg p-3 text-center`
    : 'border border-theme bg-surface-card-secondary rounded-lg p-3 text-center'
  return (
    <div className={classes}>
      <div className="font-mono text-2xl font-bold">{value}</div>
      <div className="text-xs font-sans uppercase tracking-wider mt-1">{label}</div>
    </div>
  )
}
