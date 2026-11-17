'use client'

/**
 * Sprint 879b (DH-04) — proposed actuals from an analysis run.
 *
 * Running an analysis inside an engagement no longer writes account balances
 * into the expectation workpaper. The run proposes an actual for each open
 * expectation it matched; the auditor saves one, or all of them, here.
 */

import { useState } from 'react'
import type { CaptureActualsResponse, ProposedActual } from '@/types/analytical-expectations'
import { apiPost, formatCurrency } from '@/utils'

interface ProposedActualsPanelProps {
  engagementId: number
  proposals: ProposedActual[]
  token: string | null
  onCaptured?: () => void
}

export function ProposedActualsPanel({ engagementId, proposals, token, onCaptured }: ProposedActualsPanelProps) {
  const [captured, setCaptured] = useState<Record<number, 'captured' | 'skipped'>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (proposals.length === 0) return null

  const pending = proposals.filter(p => !captured[p.expectation_id])

  const capture = async (items: ProposedActual[]) => {
    if (!token || items.length === 0) return
    setBusy(true)
    setError(null)
    const { data, ok, error: apiError } = await apiPost<CaptureActualsResponse>(
      `/engagements/${engagementId}/analytical-expectations/capture-actuals`,
      token,
      { capture_tokens: items.map(p => p.capture_token) },
    )
    setBusy(false)
    if (!ok || !data) {
      setError(apiError || 'The actual values could not be saved.')
      return
    }
    setCaptured(prev => {
      const next = { ...prev }
      for (const r of data.results) next[r.expectation_id] = r.status
      return next
    })
    onCaptured?.()
  }

  return (
    <section
      aria-labelledby="proposed-actuals-heading"
      className="theme-card p-5 border border-theme rounded-lg"
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          <h3 id="proposed-actuals-heading" className="font-serif text-sm text-content-primary">
            Proposed actuals for your expectations
          </h3>
          <p className="text-xs font-sans text-content-secondary mt-1">
            Nothing from this run has been saved. Save an account&apos;s actual value to record it in the
            expectation workpaper.
          </p>
        </div>
        {pending.length > 1 && (
          <button
            type="button"
            onClick={() => capture(pending)}
            disabled={busy}
            className="shrink-0 px-3 py-1.5 text-xs font-sans bg-sage-500 text-white rounded hover:bg-sage-600 transition-colors disabled:opacity-40"
          >
            Save all {pending.length} actual values from this run
          </button>
        )}
      </div>
      {error && (
        <p role="alert" className="text-xs font-sans text-clay-600 mb-2">{error}</p>
      )}
      <ul className="divide-y divide-theme">
        {proposals.map(p => {
          const state = captured[p.expectation_id]
          return (
            <li key={p.expectation_id} className="flex items-center justify-between gap-3 py-2">
              <span className="text-sm font-sans text-content-primary">{p.target_label}</span>
              <span className="font-mono text-sm text-content-primary ml-auto">{formatCurrency(p.actual)}</span>
              {state === 'captured' ? (
                <span className="text-xs font-sans text-sage-700 w-48 text-right">Saved</span>
              ) : state === 'skipped' ? (
                <span className="text-xs font-sans text-content-tertiary w-48 text-right">Already captured</span>
              ) : (
                <button
                  type="button"
                  onClick={() => capture([p])}
                  disabled={busy}
                  className="w-48 px-3 py-1 text-xs font-sans border border-sage-500 text-sage-700 rounded hover:bg-sage-50 transition-colors disabled:opacity-40"
                >
                  Save actual value for {p.target_label}
                </button>
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}
