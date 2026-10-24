'use client'

import { useId, useState } from 'react'
import type { TWMRunOverrides } from '@/hooks/useThreeWayMatch'
import { DEFAULT_THREE_WAY_MATCH_CONFIG, TWM_RUN_OVERRIDE_KEYS, type ThreeWayMatchConfig } from '@/types/settings'
import { parseRunInput } from '@/utils/runSettingInput'

/**
 * Three-Way Match run settings — Sprint 839.
 *
 * The seven matching tolerances for one run, prefilled from the user's saved
 * settings (Sprint 836) or the Paciolus defaults. Only a field the user
 * changes is sent; the result and memo list it as "set for this run only".
 * Bounds mirror the backend's TWM_CONFIG_BOUNDS.
 */

type NumericKey = Exclude<(typeof TWM_RUN_OVERRIDE_KEYS)[number], 'enable_fuzzy_matching'>

interface NumericFieldDef {
  key: NumericKey
  label: string
  help: string
  prefix?: string
  suffix?: string
  /** Display = engine value x scale (fractions shown as %). */
  scale: number
  min: number
  max: number
  integer?: boolean
}

export const TWM_RUN_FIELDS: NumericFieldDef[] = [
  { key: 'amount_tolerance', label: 'Amount tolerance', help: 'PO-to-invoice difference allowed before a variance is flagged.', prefix: '$', scale: 1, min: 0, max: 10000 },
  { key: 'quantity_tolerance', label: 'Quantity tolerance', help: 'Units of difference allowed; 0 means exact.', suffix: 'units', scale: 1, min: 0, max: 10000 },
  { key: 'date_window_days', label: 'Date window', help: 'Days a receipt may fall from the expected delivery date.', suffix: 'days', scale: 1, min: 0, max: 365, integer: true },
  { key: 'price_variance_threshold', label: 'Price variance threshold', help: 'Unit-price difference, as % of the PO price, before flagging.', suffix: '%', scale: 100, min: 0, max: 100 },
  { key: 'fuzzy_vendor_threshold', label: 'Vendor match sensitivity', help: 'Minimum vendor-name similarity for a fuzzy match.', suffix: '%', scale: 100, min: 0, max: 100 },
  { key: 'fuzzy_composite_threshold', label: 'Fuzzy match minimum score', help: 'Minimum combined vendor / amount / date score for a fuzzy match.', suffix: '%', scale: 100, min: 0, max: 100 },
]

/** User edits, as typed. A key is present only once the user touches it. */
export type TWMRunEdits = Partial<Record<NumericKey, string>> & { enable_fuzzy_matching?: boolean }

export interface ValidatedTWMRunSettings {
  overrides: TWMRunOverrides
  errors: Partial<Record<NumericKey, string>>
  valid: boolean
}

function toDisplay(value: number, scale: number): string {
  return String(Math.round(value * scale * 10000) / 10000)
}

/**
 * The saved settings merged over the engine defaults, keeping only values of
 * the right type (the backend ignores and reports anything else).
 */
export function twmBaseline(saved?: Partial<ThreeWayMatchConfig> | null): ThreeWayMatchConfig {
  const base: ThreeWayMatchConfig = { ...DEFAULT_THREE_WAY_MATCH_CONFIG }
  if (!saved) return base
  for (const key of TWM_RUN_OVERRIDE_KEYS) {
    const value = (saved as Record<string, unknown>)[key]
    if (typeof value === typeof base[key] && (typeof value !== 'number' || Number.isFinite(value))) {
      (base as unknown as Record<string, unknown>)[key] = value
    }
  }
  return base
}

/**
 * Per-run values to send. A value the user entered is always sent, even when
 * it equals the baseline, so what the panel shows is what runs (PR #230
 * review). With `sendAll` (saved settings could not be loaded), every
 * displayed value is sent, so the backend cannot silently apply a saved value
 * the panel never showed.
 */
export function computeTWMRunOverrides(
  edits: TWMRunEdits,
  baseline: ThreeWayMatchConfig,
  options: { sendAll?: boolean } = {},
): ValidatedTWMRunSettings {
  const overrides: TWMRunOverrides = {}
  const errors: Partial<Record<NumericKey, string>> = {}
  for (const field of TWM_RUN_FIELDS) {
    const raw = edits[field.key]
    if (raw === undefined) {
      if (options.sendAll) overrides[field.key] = baseline[field.key]
      continue
    }
    if (raw.trim() === '') {
      errors[field.key] = `Enter a value for ${field.label.toLowerCase()}, or reset to use the saved value.`
      continue
    }
    const parsed = parseRunInput(raw, {
      label: field.label,
      min: field.min,
      max: field.max,
      integer: field.integer,
      currency: field.prefix === '$',
    })
    if (parsed.error || parsed.value === undefined) {
      errors[field.key] = parsed.error ?? `${field.label} must be a number.`
      continue
    }
    const engineValue = field.scale === 1 ? parsed.value : Number((parsed.value / field.scale).toFixed(6))
    overrides[field.key] = engineValue
  }
  if (edits.enable_fuzzy_matching !== undefined) {
    overrides.enable_fuzzy_matching = edits.enable_fuzzy_matching
  } else if (options.sendAll) {
    overrides.enable_fuzzy_matching = baseline.enable_fuzzy_matching
  }
  return { overrides, errors, valid: Object.keys(errors).length === 0 }
}

interface TWMRunSettingsProps {
  baseline: ThreeWayMatchConfig
  /** True when the baseline came from the user's saved settings. */
  fromSavedSettings: boolean
  edits: TWMRunEdits
  onEditsChange: (edits: TWMRunEdits) => void
  validated: ValidatedTWMRunSettings
}

export function TWMRunSettings({ baseline, fromSavedSettings, edits, onEditsChange, validated }: TWMRunSettingsProps) {
  const [open, setOpen] = useState(false)
  const baseId = useId()
  const panelId = `${baseId}-panel`
  const changed = Object.keys(validated.overrides).length
  const fuzzyOn = edits.enable_fuzzy_matching ?? baseline.enable_fuzzy_matching
  const sourceText = fromSavedSettings ? 'your saved settings' : 'the Paciolus defaults'

  return (
    <div className="border border-theme rounded-xl mb-4">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        aria-controls={panelId}
        className="w-full flex items-center justify-between px-4 py-3 text-left"
      >
        <span className="font-serif text-sm text-content-primary">Run settings</span>
        <span className="font-sans text-xs text-content-tertiary">
          {changed > 0 ? `${changed} changed for this run` : fromSavedSettings ? 'Saved settings' : 'Paciolus defaults'}
          <span className="ml-2" aria-hidden="true">{open ? '−' : '+'}</span>
        </span>
      </button>
      {open && (
        <div id={panelId} className="px-4 pb-4 border-t border-theme pt-4">
          <p className="font-sans text-xs text-content-secondary mb-4">
            Prefilled from {sourceText}. A value you change applies to this run only and is listed in the
            results and the memo; to change it for every run, use the settings button above.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {TWM_RUN_FIELDS.map(field => {
              const id = `${baseId}-${field.key}`
              const error = validated.errors[field.key]
              const value = edits[field.key] ?? toDisplay(baseline[field.key], field.scale)
              const isChanged = field.key in validated.overrides
              return (
                <div key={field.key}>
                  <label htmlFor={id} className="block text-xs font-sans font-medium text-content-primary mb-1">
                    {field.label}
                    {isChanged && <span className="ml-2 text-sage-700 font-normal">changed for this run</span>}
                  </label>
                  <div className="relative">
                    {field.prefix && (
                      <span className="absolute left-3 top-1/2 -translate-y-1/2 font-mono text-sm text-content-tertiary" aria-hidden="true">{field.prefix}</span>
                    )}
                    <input
                      id={id}
                      type="text"
                      inputMode="decimal"
                      value={value}
                      onChange={e => onEditsChange({ ...edits, [field.key]: e.target.value })}
                      aria-invalid={error ? true : undefined}
                      aria-describedby={`${id}-help`}
                      className={`w-full ${field.prefix ? 'pl-7' : 'pl-3'} ${field.suffix ? 'pr-14' : 'pr-3'} py-2 bg-surface-input border rounded-lg font-mono text-sm text-content-primary focus:outline-hidden focus:border-sage-500/40 ${error ? 'border-clay-500' : 'border-theme'}`}
                    />
                    {field.suffix && (
                      <span className="absolute right-3 top-1/2 -translate-y-1/2 font-sans text-xs text-content-tertiary" aria-hidden="true">{field.suffix}</span>
                    )}
                  </div>
                  <p id={`${id}-help`} className={`mt-1 text-xs font-sans ${error ? 'text-clay-600' : 'text-content-tertiary'}`}>
                    {error ?? field.help}
                  </p>
                </div>
              )
            })}
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 mt-4">
            <label className="flex items-center gap-2 font-sans text-xs text-content-primary">
              <input
                type="checkbox"
                checked={fuzzyOn}
                onChange={e => onEditsChange({ ...edits, enable_fuzzy_matching: e.target.checked })}
                className="accent-sage-600"
              />
              Fuzzy fallback matching (vendor, amount and date) for documents without a PO-number link
              {'enable_fuzzy_matching' in validated.overrides && (
                <span className="text-sage-700">changed for this run</span>
              )}
            </label>
            <button
              type="button"
              onClick={() => onEditsChange({})}
              disabled={Object.keys(edits).length === 0}
              className="px-3 py-1.5 rounded-lg border border-theme bg-surface-card font-sans text-xs text-content-primary hover:bg-surface-card-secondary transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Reset to {fromSavedSettings ? 'saved settings' : 'defaults'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
