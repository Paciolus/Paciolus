'use client'

import { useId, useState } from 'react'
import type { BankRecRunThresholds } from '@/hooks/useBankReconciliation'
import type { BankRecActiveThresholds } from '@/types/bankRec'
import { parseRunInput } from '@/utils/runSettingInput'

/**
 * Bank reconciliation run settings — Sprint 839.
 *
 * Optional materiality and performance materiality for one run. Empty fields
 * send nothing and the Paciolus default ($50,000) applies; the results say
 * which threshold came from where (`BankRecThresholdsApplied`).
 */

export interface BankRecThresholdInputs {
  materiality: string
  performanceMateriality: string
}

export interface ValidatedBankRecThresholds {
  thresholds: BankRecRunThresholds
  errors: { materiality: string | null; performanceMateriality: string | null }
  valid: boolean
}

export function validateBankRecThresholds(inputs: BankRecThresholdInputs): ValidatedBankRecThresholds {
  const m = parseRunInput(inputs.materiality, { label: 'Materiality', currency: true })
  const pm = parseRunInput(inputs.performanceMateriality, { label: 'Performance materiality', currency: true })
  let pmError = pm.error
  if (!pmError && m.value !== undefined && pm.value !== undefined && pm.value > m.value) {
    pmError = 'Performance materiality cannot exceed materiality.'
  }
  return {
    thresholds: {
      materiality: m.error ? undefined : m.value,
      performanceMateriality: pmError ? undefined : pm.value,
    },
    errors: { materiality: m.error, performanceMateriality: pmError },
    valid: !m.error && !pmError,
  }
}

interface BankRecRunSettingsProps {
  inputs: BankRecThresholdInputs
  onChange: (inputs: BankRecThresholdInputs) => void
  errors: ValidatedBankRecThresholds['errors']
}

function AmountField({ id, label, value, onChange, error, help }: {
  id: string
  label: string
  value: string
  onChange: (v: string) => void
  error: string | null
  help: string
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-sans font-medium text-content-primary mb-1">{label}</label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-sm text-content-tertiary" aria-hidden="true">$</span>
        <input
          id={id}
          type="text"
          inputMode="decimal"
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder="50,000 (default)"
          aria-invalid={error ? true : undefined}
          aria-describedby={`${id}-help`}
          className={`w-full pl-7 pr-3 py-2 bg-surface-input border rounded-lg font-mono text-sm text-content-primary focus:outline-hidden focus:border-sage-500/40 ${error ? 'border-clay-500' : 'border-theme'}`}
        />
      </div>
      <p id={`${id}-help`} className={`mt-1 text-xs font-sans ${error ? 'text-clay-600' : 'text-content-tertiary'}`}>
        {error ?? help}
      </p>
    </div>
  )
}

export function BankRecRunSettings({ inputs, onChange, errors }: BankRecRunSettingsProps) {
  const [open, setOpen] = useState(false)
  const baseId = useId()
  const panelId = `${baseId}-panel`
  const entered = [inputs.materiality, inputs.performanceMateriality].filter(v => v.trim() !== '').length

  return (
    <div className="border border-theme rounded-xl mb-6">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-controls={panelId}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <span className="font-serif text-sm text-content-primary">Run settings</span>
        <span className="font-sans text-xs text-content-tertiary">
          {entered > 0 ? `${entered} set for this run` : 'Paciolus defaults'}
          <span className="ml-2" aria-hidden="true">{open ? '−' : '+'}</span>
        </span>
      </button>
      {open && (
        <div id={panelId} className="px-4 pb-4 border-t border-theme pt-4">
          <p className="font-sans text-xs text-content-secondary mb-4">
            Optional, for this reconciliation only. Leave a field empty to use the Paciolus default of{' '}
            <span className="font-mono">$50,000</span>. Materiality sets the high-value transaction flag;
            performance materiality is compared with the reconciling difference in the diagnostic score.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AmountField
              id={`${baseId}-materiality`}
              label="Materiality"
              value={inputs.materiality}
              onChange={v => onChange({ ...inputs, materiality: v })}
              error={errors.materiality}
              help="Transactions at or above this amount are flagged."
            />
            <AmountField
              id={`${baseId}-pm`}
              label="Performance materiality"
              value={inputs.performanceMateriality}
              onChange={v => onChange({ ...inputs, performanceMateriality: v })}
              error={errors.performanceMateriality}
              help="Must not exceed materiality when both are entered."
            />
          </div>
        </div>
      )}
    </div>
  )
}

function formatDollars(value: string): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return value
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 })
}

/**
 * States the thresholds this run used and, for each, whether it was entered
 * for the run or is the Paciolus default.
 */
export function BankRecThresholdsApplied({ thresholds }: { thresholds: BankRecActiveThresholds }) {
  const sources = thresholds.threshold_sources ?? {
    materiality: thresholds.materiality_source,
    performance_materiality: thresholds.materiality_source,
  }
  const sourceLabel = (s: string) => (s === 'caller' ? 'entered for this run' : 'Paciolus default')
  return (
    <div className="theme-card p-4" data-testid="bank-rec-thresholds-applied">
      <h3 className="font-serif text-sm text-content-primary mb-2">Thresholds applied</h3>
      <ul className="space-y-1">
        <li className="font-sans text-xs text-content-secondary">
          Materiality: <span className="font-mono text-content-primary">{formatDollars(thresholds.materiality)}</span>{' '}
          <span className="text-content-tertiary">({sourceLabel(sources.materiality)})</span>
        </li>
        <li className="font-sans text-xs text-content-secondary">
          Performance materiality:{' '}
          <span className="font-mono text-content-primary">{formatDollars(thresholds.performance_materiality)}</span>{' '}
          <span className="text-content-tertiary">({sourceLabel(sources.performance_materiality)})</span>
        </li>
      </ul>
    </div>
  )
}
