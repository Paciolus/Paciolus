import {
  JE_THRESHOLDS,
  JE_TOGGLES,
  AP_THRESHOLDS,
  AP_TOGGLES,
  PAYROLL_THRESHOLDS,
  PAYROLL_TOGGLES,
  TWM_THRESHOLDS,
  TWM_RUN_ONLY_FIELDS,
} from '@/components/settings/testingConfigFields'
import type { ToolSettingsKey } from '@/components/shared/ToolSettingsDrawer'
import {
  DEFAULT_JE_TESTING_CONFIG,
  DEFAULT_AP_TESTING_CONFIG,
  DEFAULT_PAYROLL_TESTING_CONFIG,
  DEFAULT_THREE_WAY_MATCH_CONFIG,
} from '@/types/settings'
import type { SavedSettingIgnored, SavedSettingValue } from '@/types/testingShared'

interface FieldDef {
  key: string
  label: string
  prefix?: string
  suffix?: string
  displayScale?: number
}

const FIELDS: Record<ToolSettingsKey, FieldDef[]> = {
  je: [...JE_THRESHOLDS, ...JE_TOGGLES],
  ap: [...AP_THRESHOLDS, ...AP_TOGGLES],
  payroll: [...PAYROLL_THRESHOLDS, ...PAYROLL_TOGGLES],
  three_way_match: [...TWM_THRESHOLDS, ...TWM_RUN_ONLY_FIELDS],
}

const DEFAULTS: Record<ToolSettingsKey, Record<string, unknown>> = {
  je: { ...DEFAULT_JE_TESTING_CONFIG },
  ap: { ...DEFAULT_AP_TESTING_CONFIG },
  payroll: { ...DEFAULT_PAYROLL_TESTING_CONFIG },
  three_way_match: { ...DEFAULT_THREE_WAY_MATCH_CONFIG },
}

function humanize(key: string): string {
  const words = key.replace(/_/g, ' ').trim()
  return words.charAt(0).toUpperCase() + words.slice(1)
}

export function formatSettingValue(value: unknown, field?: FieldDef): string {
  if (typeof value === 'boolean') return value ? 'On' : 'Off'
  if (Array.isArray(value)) return value.map(v => formatSettingValue(v, field)).join(', ')
  if (typeof value === 'number') {
    const scaled = field?.displayScale ? value * field.displayScale : value
    const rounded = Math.round(scaled * 10000) / 10000
    const text = rounded.toLocaleString('en-US', { maximumFractionDigits: 4 })
    const prefix = field?.prefix ?? ''
    const suffix = field?.suffix ? (field.suffix === '%' ? '%' : ` ${field.suffix}`) : ''
    return `${prefix}${text}${suffix}`
  }
  return String(value)
}

interface SavedSettingsNoticeProps {
  tool: ToolSettingsKey
  applied?: Record<string, SavedSettingValue>
  ignored?: SavedSettingIgnored[]
  /** Sprint 839: values set for this run only (Three-Way Match run settings). */
  runOverrides?: Record<string, SavedSettingValue>
  className?: string
}

/**
 * SavedSettingsNotice — Sprint 836.
 *
 * Says, on the results view, which of the user's saved settings changed a
 * threshold from the Paciolus default on this run, and which saved settings
 * were not applied (clay accent). Renders nothing when every threshold was a
 * Paciolus default and nothing was ignored. Sprint 839: values set for this
 * run only are listed first, in their own block.
 */
export function SavedSettingsNotice({ tool, applied, ignored, runOverrides, className = 'mb-6' }: SavedSettingsNoticeProps) {
  const appliedEntries = Object.entries(applied ?? {})
  const ignoredEntries = ignored ?? []
  const runEntries = Object.entries(runOverrides ?? {})
  if (appliedEntries.length === 0 && ignoredEntries.length === 0 && runEntries.length === 0) return null

  const fields = FIELDS[tool]
  const defaults = DEFAULTS[tool]
  const fieldFor = (key: string) => fields.find(f => f.key === key)
  const count = appliedEntries.length

  return (
    <div className={`space-y-3 ${className}`} data-testid="saved-settings-notice">
      {runEntries.length > 0 && (
        <div className="bg-surface-card border border-theme border-l-4 border-l-obsidian-500 rounded-xl p-4" role="status" data-testid="run-overrides-notice">
          <h3 className="font-serif text-sm text-content-primary">
            {runEntries.length === 1 ? '1 threshold was' : `${runEntries.length} thresholds were`} set for this run only
          </h3>
          <ul className="mt-2 space-y-1">
            {runEntries.map(([key, value]) => {
              const field = fieldFor(key)
              const hasDefault = key in defaults
              return (
                <li key={key} className="font-sans text-xs text-content-secondary">
                  {field?.label ?? humanize(key)}:{' '}
                  <span className="font-mono text-content-primary">{formatSettingValue(value, field)}</span>
                  {hasDefault && (
                    <span className="text-content-tertiary">
                      {' '}(default <span className="font-mono">{formatSettingValue(defaults[key], field)}</span>)
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
          <p className="mt-2 font-sans text-xs text-content-tertiary">
            These values replace your saved settings and the Paciolus defaults for this run; the memo states them.
          </p>
        </div>
      )}
      {count > 0 && (
        <div className="bg-surface-card border border-theme border-l-4 border-l-sage-500 rounded-xl p-4" role="status">
          <h3 className="font-serif text-sm text-content-primary">
            Your saved settings changed {count} {count === 1 ? 'threshold' : 'thresholds'} from Paciolus defaults
          </h3>
          <ul className="mt-2 space-y-1">
            {appliedEntries.map(([key, value]) => {
              const field = fieldFor(key)
              const hasDefault = key in defaults
              return (
                <li key={key} className="font-sans text-xs text-content-secondary">
                  {field?.label ?? humanize(key)}:{' '}
                  <span className="font-mono text-content-primary">{formatSettingValue(value, field)}</span>
                  {hasDefault && (
                    <span className="text-content-tertiary">
                      {' '}(default <span className="font-mono">{formatSettingValue(defaults[key], field)}</span>)
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
          <p className="mt-2 font-sans text-xs text-content-tertiary">
            These results, and the memo, reflect your values. Change them in this tool&apos;s settings.
          </p>
        </div>
      )}
      {ignoredEntries.length > 0 && (
        <div className="bg-clay-500/5 border border-clay-500/30 border-l-4 border-l-clay-500 rounded-xl p-4" role="alert">
          <h3 className="font-serif text-sm text-clay-700 dark:text-clay-400">
            {ignoredEntries.length === 1
              ? '1 saved setting was not applied'
              : `${ignoredEntries.length} saved settings were not applied`}
          </h3>
          <ul className="mt-2 space-y-1">
            {ignoredEntries.map(item => (
              <li key={item.key} className="font-sans text-xs text-content-secondary">
                <span className="font-mono text-content-primary">{item.key}</span>: {item.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
