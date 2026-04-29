/**
 * Period file uploads hook (Sprint 750 — Phase 4 tool-page template).
 *
 * Owns the upload state machine for the multi-period comparison tool:
 * three independent `PeriodState` slots (prior / current / optional budget),
 * the `auditFile` upload pipeline that feeds them, the `showBudget` toggle,
 * and the `reset` action. Returns a flat API the page composition root
 * destructures.
 *
 * Pattern (per ADR-016 follow-up — tool-page template):
 *   - useToolWorkflow concern: data + process orchestration (this file).
 *   - useToolUIState concern: filter/tab/view state (separate hook).
 *   - Page is a composition root — no inline state machines.
 */
'use client'

import { useCallback, useState } from 'react'
import { type PeriodState } from '@/components/multiPeriod'
import { uploadTrialBalance } from '@/utils/trialBalanceUpload'

const INITIAL_PERIOD: PeriodState = {
  file: null,
  status: 'idle',
  result: null,
  error: null,
}

export interface UsePeriodUploadsOptions {
  token: string | null
  materialityThreshold: number
  engagementId: number | null
  /** Called once before each upload starts so the consumer can clear any
   *  comparison results that a fresh file invalidates. */
  onBeforeUpload?: () => void
}

export interface UsePeriodUploadsReturn {
  prior: PeriodState
  current: PeriodState
  budget: PeriodState
  showBudget: boolean
  /** True while any of the three zones is loading. */
  anyLoading: boolean
  /** True iff prior + current (and budget if `showBudget`) are all `success`. */
  canCompare: boolean
  handlePriorFile: (file: File) => void
  handleCurrentFile: (file: File) => void
  handleBudgetFile: (file: File) => void
  toggleBudget: () => void
  reset: () => void
}

export function usePeriodUploads(options: UsePeriodUploadsOptions): UsePeriodUploadsReturn {
  const { token, materialityThreshold, engagementId, onBeforeUpload } = options

  const [prior, setPrior] = useState<PeriodState>(INITIAL_PERIOD)
  const [current, setCurrent] = useState<PeriodState>(INITIAL_PERIOD)
  const [budget, setBudget] = useState<PeriodState>(INITIAL_PERIOD)
  const [showBudget, setShowBudget] = useState(false)

  const auditFile = useCallback(
    async (file: File, setPeriod: React.Dispatch<React.SetStateAction<PeriodState>>) => {
      setPeriod(prev => ({ ...prev, file, status: 'loading', result: null, error: null }))

      const outcome = await uploadTrialBalance(
        { file, materialityThreshold, engagementId },
        token,
      )

      if (outcome.kind === 'success') {
        setPeriod(prev => ({ ...prev, status: 'success', result: outcome.result }))
        return
      }
      setPeriod(prev => ({ ...prev, status: 'error', error: outcome.message }))
    },
    [token, materialityThreshold, engagementId],
  )

  const handlePriorFile = useCallback(
    (file: File) => {
      onBeforeUpload?.()
      void auditFile(file, setPrior)
    },
    [auditFile, onBeforeUpload],
  )

  const handleCurrentFile = useCallback(
    (file: File) => {
      onBeforeUpload?.()
      void auditFile(file, setCurrent)
    },
    [auditFile, onBeforeUpload],
  )

  const handleBudgetFile = useCallback(
    (file: File) => {
      onBeforeUpload?.()
      void auditFile(file, setBudget)
    },
    [auditFile, onBeforeUpload],
  )

  const toggleBudget = useCallback(() => {
    setShowBudget(prev => {
      // Toggling OFF clears any in-flight or successful budget upload so the
      // comparison snapshot doesn't carry stale 3rd-period data.
      if (prev) setBudget(INITIAL_PERIOD)
      return !prev
    })
  }, [])

  const reset = useCallback(() => {
    setPrior(INITIAL_PERIOD)
    setCurrent(INITIAL_PERIOD)
    setBudget(INITIAL_PERIOD)
  }, [])

  const anyLoading =
    prior.status === 'loading' || current.status === 'loading' || budget.status === 'loading'

  const canCompare = Boolean(
    prior.status === 'success' &&
      current.status === 'success' &&
      prior.result &&
      current.result &&
      (!showBudget || (budget.status === 'success' && budget.result)),
  )

  return {
    prior,
    current,
    budget,
    showBudget,
    anyLoading,
    canCompare,
    handlePriorFile,
    handleCurrentFile,
    handleBudgetFile,
    toggleBudget,
    reset,
  }
}
