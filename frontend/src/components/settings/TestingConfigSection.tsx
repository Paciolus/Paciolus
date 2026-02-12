'use client'

import { motion } from 'framer-motion'

// =============================================================================
// TYPES
// =============================================================================

interface ThresholdField {
  key: string
  label: string
  description: string
  prefix?: string
  suffix?: string
  step?: number | string
  min?: number
  max?: number
  /** Scale factor for display (e.g., 100 for percent). Value is divided by this for display and multiplied on change. */
  displayScale?: number
  /** Default fallback value on parse failure */
  fallback?: number
  /** Use parseInt instead of parseFloat */
  integer?: boolean
  /** Width class override (default: 'w-32') */
  widthClass?: string
}

interface ToggleField {
  key: string
  label: string
}

interface TestingConfigSectionProps<
  TPreset extends string,
  TConfig extends object,
> {
  title: string
  description: string
  delay: number
  /** Preset labels keyed by preset value */
  presetLabels: Record<TPreset, string>
  /** Preset descriptions keyed by preset value */
  presetDescriptions: Record<TPreset, string>
  /** Preset config overrides keyed by preset value */
  presetConfigs: Partial<Record<TPreset, Partial<TConfig>>>
  /** Default config to spread under presets */
  defaultConfig: TConfig
  /** Current preset value */
  currentPreset: TPreset
  /** Current config value */
  currentConfig: TConfig
  onPresetChange: (preset: TPreset) => void
  onConfigChange: (config: TConfig) => void
  thresholds: ThresholdField[]
  toggles: ToggleField[]
  /** Extra content to render after toggles (e.g., TWM fuzzy matching toggle) */
  children?: React.ReactNode
}

// =============================================================================
// COMPONENT
// =============================================================================

export function TestingConfigSection<
  TPreset extends string,
  TConfig extends object,
>({
  title,
  description,
  delay,
  presetLabels,
  presetDescriptions,
  presetConfigs,
  defaultConfig,
  currentPreset,
  currentConfig,
  onPresetChange,
  onConfigChange,
  thresholds,
  toggles,
  children,
}: TestingConfigSectionProps<TPreset, TConfig>) {

  const handlePresetClick = (preset: TPreset) => {
    onPresetChange(preset)
    if (preset !== 'custom') {
      onConfigChange({
        ...defaultConfig,
        ...presetConfigs[preset],
      })
    }
  }

  const handleThresholdChange = (field: ThresholdField, rawValue: string) => {
    const parse = field.integer ? parseInt : parseFloat
    let value = parse(rawValue) || (field.fallback ?? 0)
    if (field.displayScale) {
      value = value / field.displayScale
    }
    onConfigChange({ ...currentConfig, [field.key]: value })
    onPresetChange('custom' as TPreset)
  }

  const configRecord = currentConfig as Record<string, unknown>

  const getDisplayValue = (field: ThresholdField): string | number => {
    const raw = configRecord[field.key] as number
    if (field.displayScale) {
      return Math.round(raw * field.displayScale)
    }
    return raw
  }

  const handleToggleChange = (key: string, checked: boolean) => {
    onConfigChange({ ...currentConfig, [key]: checked })
    onPresetChange('custom' as TPreset)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="theme-card p-6 mb-6"
    >
      <h2 className="text-xl font-serif font-semibold text-content-primary mb-2">
        {title}
      </h2>
      <p className="text-content-tertiary text-sm font-sans mb-6">
        {description}
      </p>

      {/* Preset Selector */}
      <div className="mb-6">
        <label className="block text-content-secondary font-sans font-medium mb-3">
          Sensitivity Preset
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {(Object.keys(presetLabels) as TPreset[]).map((preset) => (
            <button
              key={preset}
              onClick={() => handlePresetClick(preset)}
              className={`px-3 py-2.5 rounded-lg border text-sm font-sans transition-all ${
                currentPreset === preset
                  ? 'bg-sage-50 border-sage-300 text-sage-700'
                  : 'bg-surface-card-secondary border-theme text-content-secondary hover:border-theme-hover'
              }`}
            >
              {presetLabels[preset]}
            </button>
          ))}
        </div>
        <p className="text-content-tertiary text-xs font-sans mt-2">
          {presetDescriptions[currentPreset]}
        </p>
      </div>

      {/* Key Threshold Overrides */}
      <div className="space-y-4 p-4 bg-surface-card-secondary rounded-lg border border-theme">
        <p className="text-content-secondary text-xs font-sans font-medium uppercase tracking-wide">
          Key Thresholds
        </p>

        {thresholds.map((field) => (
          <div key={field.key} className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <span className="text-content-secondary text-sm font-sans">{field.label}</span>
              <p className="text-content-tertiary text-xs">{field.description}</p>
            </div>
            <div className={`relative ${field.widthClass || 'w-32'}`}>
              {field.prefix && (
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-content-tertiary text-sm">
                  {field.prefix}
                </span>
              )}
              <input
                type="number"
                value={getDisplayValue(field)}
                onChange={(e) => handleThresholdChange(field, e.target.value)}
                step={field.step}
                min={field.min}
                max={field.max}
                className={`w-full ${field.prefix ? 'pl-7' : 'pl-3'} ${field.suffix ? 'pr-12' : 'pr-3'} py-2 bg-surface-input border border-theme rounded-lg text-content-primary font-mono text-sm ${field.prefix || field.suffix ? '' : 'text-center'} focus:outline-none focus:border-sage-500/40`}
              />
              {field.suffix && (
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-content-tertiary text-xs">
                  {field.suffix}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Toggle Tests */}
      {toggles.length > 0 && (
        <div className="mt-4 space-y-3">
          <p className="text-content-secondary text-xs font-sans font-medium uppercase tracking-wide">
            Enable / Disable Tests
          </p>
          {toggles.map(({ key, label }) => (
            <label key={key} className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={configRecord[key] as boolean}
                onChange={(e) => handleToggleChange(key, e.target.checked)}
                className="w-4 h-4 rounded border-theme bg-surface-input text-sage-500 focus:ring-sage-500/20"
              />
              <span className="text-content-secondary text-sm font-sans">{label}</span>
            </label>
          ))}
        </div>
      )}

      {children}
    </motion.div>
  )
}
