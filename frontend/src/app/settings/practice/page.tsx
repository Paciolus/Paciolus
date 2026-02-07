'use client'

/**
 * Practice Settings Page - Sprint 48
 *
 * Business configuration: materiality formulas, weighted thresholds, export preferences.
 * Separate from Profile Settings (personal account info).
 */

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/context/AuthContext'
import { ProfileDropdown } from '@/components/auth/ProfileDropdown'
import { useSettings } from '@/hooks/useSettings'
import type {
  MaterialityFormula,
  MaterialityFormulaType,
  MaterialityPreview,
  WeightedMaterialityConfig,
  JETestingConfig,
  JETestingPreset,
  APTestingConfig,
  APTestingPreset,
} from '@/types/settings'
import {
  FORMULA_TYPE_LABELS,
  DEFAULT_MATERIALITY_FORMULA,
  DEFAULT_WEIGHTED_MATERIALITY,
  DEFAULT_JE_TESTING_CONFIG,
  JE_TESTING_PRESETS,
  JE_PRESET_LABELS,
  JE_PRESET_DESCRIPTIONS,
  DEFAULT_AP_TESTING_CONFIG,
  AP_TESTING_PRESETS,
  AP_PRESET_LABELS,
  AP_PRESET_DESCRIPTIONS,
} from '@/types/settings'
import { WeightedMaterialityEditor } from '@/components/sensitivity'

export default function PracticeSettingsPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()
  const {
    practiceSettings,
    isLoading,
    error,
    updatePracticeSettings,
    previewMateriality,
  } = useSettings()

  // Form state
  const [formulaType, setFormulaType] = useState<MaterialityFormulaType>('fixed')
  const [formulaValue, setFormulaValue] = useState<number>(500)
  const [minThreshold, setMinThreshold] = useState<string>('')
  const [maxThreshold, setMaxThreshold] = useState<string>('')
  const [showImmaterial, setShowImmaterial] = useState(false)
  const [defaultFYE, setDefaultFYE] = useState('12-31')
  const [autoSaveSummaries, setAutoSaveSummaries] = useState(true)
  const [defaultExportFormat, setDefaultExportFormat] = useState('pdf')

  // Weighted materiality state
  const [weightedMateriality, setWeightedMateriality] = useState<WeightedMaterialityConfig>(
    DEFAULT_WEIGHTED_MATERIALITY
  )

  // JE Testing config state (Sprint 68)
  const [jeTestingPreset, setJeTestingPreset] = useState<JETestingPreset>('standard')
  const [jeTestingConfig, setJeTestingConfig] = useState<JETestingConfig>(DEFAULT_JE_TESTING_CONFIG)

  // AP Testing config state (Sprint 76)
  const [apTestingPreset, setApTestingPreset] = useState<APTestingPreset>('standard')
  const [apTestingConfig, setApTestingConfig] = useState<APTestingConfig>(DEFAULT_AP_TESTING_CONFIG)

  // UI state
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [preview, setPreview] = useState<MaterialityPreview | null>(null)
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  // Sample data for preview
  const [sampleRevenue, setSampleRevenue] = useState<number>(1000000)
  const [sampleAssets, setSampleAssets] = useState<number>(500000)
  const [sampleEquity, setSampleEquity] = useState<number>(200000)

  // Load current settings into form
  useEffect(() => {
    if (practiceSettings) {
      const formula = practiceSettings.default_materiality
      setFormulaType(formula.type)
      setFormulaValue(formula.value)
      setMinThreshold(formula.min_threshold?.toString() || '')
      setMaxThreshold(formula.max_threshold?.toString() || '')
      setShowImmaterial(practiceSettings.show_immaterial_by_default)
      setDefaultFYE(practiceSettings.default_fiscal_year_end)
      setAutoSaveSummaries(practiceSettings.auto_save_summaries)
      setDefaultExportFormat(practiceSettings.default_export_format)
      if (practiceSettings.weighted_materiality) {
        setWeightedMateriality(practiceSettings.weighted_materiality)
      }
      if (practiceSettings.je_testing_config) {
        setJeTestingConfig({ ...DEFAULT_JE_TESTING_CONFIG, ...practiceSettings.je_testing_config })
        setJeTestingPreset('custom')
      }
      if (practiceSettings.ap_testing_config) {
        setApTestingConfig({ ...DEFAULT_AP_TESTING_CONFIG, ...practiceSettings.ap_testing_config })
        setApTestingPreset('custom')
      }
    }
  }, [practiceSettings])

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  // Update preview when formula changes
  useEffect(() => {
    const updatePreview = async () => {
      const formula: MaterialityFormula = {
        type: formulaType,
        value: formulaValue,
        min_threshold: minThreshold ? parseFloat(minThreshold) : null,
        max_threshold: maxThreshold ? parseFloat(maxThreshold) : null,
      }

      const result = await previewMateriality(
        formula,
        sampleRevenue,
        sampleAssets,
        sampleEquity
      )

      if (result) {
        setPreview(result)
      }
    }

    if (isAuthenticated) {
      updatePreview()
    }
  }, [formulaType, formulaValue, minThreshold, maxThreshold, sampleRevenue, sampleAssets, sampleEquity, previewMateriality, isAuthenticated])

  // Handle save
  const handleSave = async () => {
    setIsSaving(true)
    setSaveSuccess(false)

    const formula: MaterialityFormula = {
      type: formulaType,
      value: formulaValue,
      min_threshold: minThreshold ? parseFloat(minThreshold) : null,
      max_threshold: maxThreshold ? parseFloat(maxThreshold) : null,
    }

    const success = await updatePracticeSettings({
      default_materiality: formula,
      show_immaterial_by_default: showImmaterial,
      default_fiscal_year_end: defaultFYE,
      auto_save_summaries: autoSaveSummaries,
      default_export_format: defaultExportFormat,
      weighted_materiality: weightedMateriality,
      je_testing_config: jeTestingConfig,
      ap_testing_config: apTestingConfig,
    })

    setIsSaving(false)

    if (success) {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  }

  // Input styling
  const getInputClasses = (field: string, isValid: boolean = true) => {
    const baseClasses = 'w-full px-4 py-3 bg-obsidian-800 border-2 rounded-lg text-oatmeal-200 font-sans transition-all duration-200 outline-none'

    if (touched[field] && !isValid) {
      return `${baseClasses} border-clay-500 focus:border-clay-400 focus:ring-2 focus:ring-clay-500/20`
    }

    if (touched[field] && isValid) {
      return `${baseClasses} border-sage-500/50 focus:border-sage-400 focus:ring-2 focus:ring-sage-500/20`
    }

    return `${baseClasses} border-obsidian-500 focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20`
  }

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gradient-obsidian flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      {/* Navigation - Sprint 56: Unified nav with ProfileDropdown */}
      <nav className="fixed top-0 w-full bg-obsidian-900/80 backdrop-blur-md border-b border-obsidian-600/50 z-50">
        <div className="max-w-6xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
              style={{ imageRendering: 'crisp-edges' }}
            />
            <span className="text-xl font-bold font-serif text-oatmeal-200 tracking-tight">
              Paciolus
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-oatmeal-400 font-sans hidden sm:block">
              Practice Settings
            </span>
            {user && <ProfileDropdown user={user} onLogout={logout} />}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 text-oatmeal-500 text-sm font-sans mb-4">
              <Link href="/" className="hover:text-oatmeal-300 transition-colors">Home</Link>
              <span>/</span>
              <span className="text-oatmeal-300">Practice Settings</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-oatmeal-200 mb-2">
              Practice Configuration
            </h1>
            <p className="text-oatmeal-400 font-sans">
              Configure your default diagnostic settings. These will apply to all new diagnostics unless overridden at the client level.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-clay-500/10 border border-clay-500/30 rounded-lg">
              <p className="text-clay-400 font-sans">{error}</p>
            </div>
          )}

          {/* Materiality Formula Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-4">
              Default Materiality Formula
            </h2>
            <p className="text-oatmeal-500 text-sm font-sans mb-6">
              Define how materiality thresholds are calculated for diagnostics.
            </p>

            {/* Formula Type */}
            <div className="mb-6">
              <label className="block text-oatmeal-300 font-sans font-medium mb-2">
                Calculation Method
              </label>
              <select
                value={formulaType}
                onChange={(e) => {
                  setFormulaType(e.target.value as MaterialityFormulaType)
                  setTouched({ ...touched, formulaType: true })
                }}
                className={getInputClasses('formulaType')}
              >
                {Object.entries(FORMULA_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value} className="bg-obsidian-800">
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Formula Value */}
            <div className="mb-6">
              <label className="block text-oatmeal-300 font-sans font-medium mb-2">
                {formulaType === 'fixed' ? 'Threshold Amount ($)' : 'Percentage (%)'}
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-oatmeal-500">
                  {formulaType === 'fixed' ? '$' : ''}
                </span>
                <input
                  type="number"
                  value={formulaValue}
                  onChange={(e) => {
                    setFormulaValue(parseFloat(e.target.value) || 0)
                    setTouched({ ...touched, formulaValue: true })
                  }}
                  min="0"
                  step={formulaType === 'fixed' ? '100' : '0.1'}
                  className={`${getInputClasses('formulaValue')} ${formulaType === 'fixed' ? 'pl-8' : ''} font-mono`}
                />
                {formulaType !== 'fixed' && (
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-oatmeal-500">
                    %
                  </span>
                )}
              </div>
            </div>

            {/* Min/Max Thresholds (for percentage-based) */}
            {formulaType !== 'fixed' && (
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-oatmeal-300 font-sans font-medium mb-2">
                    Minimum Floor ($)
                  </label>
                  <input
                    type="number"
                    value={minThreshold}
                    onChange={(e) => setMinThreshold(e.target.value)}
                    placeholder="Optional"
                    min="0"
                    step="100"
                    className={`${getInputClasses('minThreshold')} font-mono`}
                  />
                </div>
                <div>
                  <label className="block text-oatmeal-300 font-sans font-medium mb-2">
                    Maximum Cap ($)
                  </label>
                  <input
                    type="number"
                    value={maxThreshold}
                    onChange={(e) => setMaxThreshold(e.target.value)}
                    placeholder="Optional"
                    min="0"
                    step="100"
                    className={`${getInputClasses('maxThreshold')} font-mono`}
                  />
                </div>
              </div>
            )}

            {/* Preview */}
            {preview && (
              <div className="p-4 bg-obsidian-700/50 rounded-lg border border-obsidian-600">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-oatmeal-400 text-sm font-sans">Calculated Threshold</span>
                  <span className="text-sage-400 font-mono text-lg font-semibold">
                    ${preview.threshold.toLocaleString()}
                  </span>
                </div>
                <p className="text-oatmeal-500 text-xs font-sans">
                  Based on sample: ${sampleRevenue.toLocaleString()} revenue, ${sampleAssets.toLocaleString()} assets, ${sampleEquity.toLocaleString()} equity
                </p>
              </div>
            )}
          </motion.div>

          {/* Weighted Materiality Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-4">
              Weighted Materiality by Account Type
            </h2>
            <p className="text-oatmeal-500 text-sm font-sans mb-6">
              Apply different scrutiny levels to different account categories. Higher weights mean lower thresholds (more scrutiny).
            </p>

            <WeightedMaterialityEditor
              config={weightedMateriality}
              baseThreshold={formulaType === 'fixed' ? formulaValue : (preview?.threshold || 500)}
              onChange={setWeightedMateriality}
              disabled={false}
            />
          </motion.div>

          {/* JE Testing Thresholds — Sprint 68 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="card mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-2">
              Journal Entry Testing
            </h2>
            <p className="text-oatmeal-500 text-sm font-sans mb-6">
              Configure sensitivity thresholds for the 13-test JE testing battery. Presets provide quick configuration for common engagement profiles.
            </p>

            {/* Preset Selector */}
            <div className="mb-6">
              <label className="block text-oatmeal-300 font-sans font-medium mb-3">
                Sensitivity Preset
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {(Object.keys(JE_PRESET_LABELS) as JETestingPreset[]).map((preset) => (
                  <button
                    key={preset}
                    onClick={() => {
                      setJeTestingPreset(preset)
                      if (preset !== 'custom') {
                        setJeTestingConfig({
                          ...DEFAULT_JE_TESTING_CONFIG,
                          ...JE_TESTING_PRESETS[preset],
                        })
                      }
                    }}
                    className={`px-3 py-2.5 rounded-lg border text-sm font-sans transition-all ${
                      jeTestingPreset === preset
                        ? 'bg-sage-500/15 border-sage-500/40 text-sage-300'
                        : 'bg-obsidian-800 border-obsidian-500/30 text-oatmeal-400 hover:border-obsidian-400'
                    }`}
                  >
                    {JE_PRESET_LABELS[preset]}
                  </button>
                ))}
              </div>
              <p className="text-oatmeal-600 text-xs font-sans mt-2">
                {JE_PRESET_DESCRIPTIONS[jeTestingPreset]}
              </p>
            </div>

            {/* Key Threshold Overrides */}
            <div className="space-y-4 p-4 bg-obsidian-900/40 rounded-lg border border-obsidian-600/20">
              <p className="text-oatmeal-400 text-xs font-sans font-medium uppercase tracking-wide">
                Key Thresholds
              </p>

              {/* T4: Round Amount Threshold */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Round Amount Minimum</span>
                  <p className="text-oatmeal-600 text-xs">T4: Only flag amounts above this</p>
                </div>
                <div className="relative w-32">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-oatmeal-600 text-sm">$</span>
                  <input
                    type="number"
                    value={jeTestingConfig.round_amount_threshold}
                    onChange={(e) => {
                      setJeTestingConfig({ ...jeTestingConfig, round_amount_threshold: parseFloat(e.target.value) || 0 })
                      setJeTestingPreset('custom')
                    }}
                    className="w-full pl-7 pr-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm focus:outline-none focus:border-sage-500/40"
                  />
                </div>
              </div>

              {/* T5: Unusual Amount Std Dev */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Unusual Amount Sensitivity</span>
                  <p className="text-oatmeal-600 text-xs">T5: Standard deviations from mean</p>
                </div>
                <input
                  type="number"
                  value={jeTestingConfig.unusual_amount_stddev}
                  onChange={(e) => {
                    setJeTestingConfig({ ...jeTestingConfig, unusual_amount_stddev: parseFloat(e.target.value) || 3 })
                    setJeTestingPreset('custom')
                  }}
                  step="0.5"
                  min="1"
                  max="5"
                  className="w-32 px-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm text-center focus:outline-none focus:border-sage-500/40"
                />
              </div>

              {/* T9: Single-User Volume % */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">User Volume Threshold</span>
                  <p className="text-oatmeal-600 text-xs">T9: Flag users posting more than this % of entries</p>
                </div>
                <div className="relative w-32">
                  <input
                    type="number"
                    value={Math.round(jeTestingConfig.single_user_volume_pct * 100)}
                    onChange={(e) => {
                      setJeTestingConfig({ ...jeTestingConfig, single_user_volume_pct: (parseFloat(e.target.value) || 25) / 100 })
                      setJeTestingPreset('custom')
                    }}
                    min="5"
                    max="80"
                    className="w-full pr-7 pl-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm text-center focus:outline-none focus:border-sage-500/40"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-oatmeal-600 text-sm">%</span>
                </div>
              </div>

              {/* T12: Backdate Days */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Backdating Threshold</span>
                  <p className="text-oatmeal-600 text-xs">T12: Days between posting and entry date</p>
                </div>
                <div className="relative w-32">
                  <input
                    type="number"
                    value={jeTestingConfig.backdate_days_threshold}
                    onChange={(e) => {
                      setJeTestingConfig({ ...jeTestingConfig, backdate_days_threshold: parseInt(e.target.value) || 30 })
                      setJeTestingPreset('custom')
                    }}
                    min="7"
                    max="180"
                    className="w-full pr-12 pl-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm text-center focus:outline-none focus:border-sage-500/40"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-oatmeal-600 text-xs">days</span>
                </div>
              </div>

              {/* T13: Keyword Confidence */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Keyword Sensitivity</span>
                  <p className="text-oatmeal-600 text-xs">T13: Minimum confidence for suspicious keywords</p>
                </div>
                <div className="relative w-32">
                  <input
                    type="number"
                    value={Math.round(jeTestingConfig.suspicious_keyword_threshold * 100)}
                    onChange={(e) => {
                      setJeTestingConfig({ ...jeTestingConfig, suspicious_keyword_threshold: (parseFloat(e.target.value) || 60) / 100 })
                      setJeTestingPreset('custom')
                    }}
                    min="30"
                    max="95"
                    className="w-full pr-7 pl-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm text-center focus:outline-none focus:border-sage-500/40"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-oatmeal-600 text-sm">%</span>
                </div>
              </div>
            </div>

            {/* Toggle Tests */}
            <div className="mt-4 space-y-3">
              <p className="text-oatmeal-400 text-xs font-sans font-medium uppercase tracking-wide">
                Enable / Disable Tests
              </p>
              {[
                { key: 'weekend_posting_enabled' as const, label: 'T7: Weekend Postings' },
                { key: 'after_hours_enabled' as const, label: 'T10: After-Hours Postings' },
                { key: 'numbering_gap_enabled' as const, label: 'T11: Numbering Gaps' },
                { key: 'backdate_enabled' as const, label: 'T12: Backdated Entries' },
                { key: 'suspicious_keyword_enabled' as const, label: 'T13: Suspicious Keywords' },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={jeTestingConfig[key]}
                    onChange={(e) => {
                      setJeTestingConfig({ ...jeTestingConfig, [key]: e.target.checked })
                      setJeTestingPreset('custom')
                    }}
                    className="w-4 h-4 rounded border-obsidian-500 bg-obsidian-800 text-sage-500 focus:ring-sage-500/20"
                  />
                  <span className="text-oatmeal-300 text-sm font-sans">{label}</span>
                </label>
              ))}
            </div>
          </motion.div>

          {/* AP Testing Thresholds — Sprint 76 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 as const }}
            className="card mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-2">
              AP Payment Testing
            </h2>
            <p className="text-oatmeal-500 text-sm font-sans mb-6">
              Configure sensitivity thresholds for the 13-test AP payment testing battery. Presets provide quick configuration for common engagement profiles.
            </p>

            {/* Preset Selector */}
            <div className="mb-6">
              <label className="block text-oatmeal-300 font-sans font-medium mb-3">
                Sensitivity Preset
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {(Object.keys(AP_PRESET_LABELS) as APTestingPreset[]).map((preset) => (
                  <button
                    key={preset}
                    onClick={() => {
                      setApTestingPreset(preset)
                      if (preset !== 'custom') {
                        setApTestingConfig({
                          ...DEFAULT_AP_TESTING_CONFIG,
                          ...AP_TESTING_PRESETS[preset],
                        })
                      }
                    }}
                    className={`px-3 py-2.5 rounded-lg border text-sm font-sans transition-all ${
                      apTestingPreset === preset
                        ? 'bg-sage-500/15 border-sage-500/40 text-sage-300'
                        : 'bg-obsidian-800 border-obsidian-500/30 text-oatmeal-400 hover:border-obsidian-400'
                    }`}
                  >
                    {AP_PRESET_LABELS[preset]}
                  </button>
                ))}
              </div>
              <p className="text-oatmeal-600 text-xs font-sans mt-2">
                {AP_PRESET_DESCRIPTIONS[apTestingPreset]}
              </p>
            </div>

            {/* Key Threshold Overrides */}
            <div className="space-y-4 p-4 bg-obsidian-900/40 rounded-lg border border-obsidian-600/20">
              <p className="text-oatmeal-400 text-xs font-sans font-medium uppercase tracking-wide">
                Key Thresholds
              </p>

              {/* AP-T4: Round Amount Threshold */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Round Amount Minimum</span>
                  <p className="text-oatmeal-600 text-xs">T4: Only flag amounts above this</p>
                </div>
                <div className="relative w-32">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-oatmeal-600 text-sm">$</span>
                  <input
                    type="number"
                    value={apTestingConfig.round_amount_threshold}
                    onChange={(e) => {
                      setApTestingConfig({ ...apTestingConfig, round_amount_threshold: parseFloat(e.target.value) || 0 })
                      setApTestingPreset('custom')
                    }}
                    className="w-full pl-7 pr-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm focus:outline-none focus:border-sage-500/40"
                  />
                </div>
              </div>

              {/* AP-T6: Duplicate Date Window */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Duplicate Date Window</span>
                  <p className="text-oatmeal-600 text-xs">T6: Days to check for fuzzy duplicates</p>
                </div>
                <div className="relative w-32">
                  <input
                    type="number"
                    value={apTestingConfig.duplicate_days_window}
                    onChange={(e) => {
                      setApTestingConfig({ ...apTestingConfig, duplicate_days_window: parseInt(e.target.value) || 30 })
                      setApTestingPreset('custom')
                    }}
                    min="7"
                    max="90"
                    className="w-full pr-12 pl-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm text-center focus:outline-none focus:border-sage-500/40"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-oatmeal-600 text-xs">days</span>
                </div>
              </div>

              {/* AP-T8: Unusual Amount Std Dev */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Unusual Amount Sensitivity</span>
                  <p className="text-oatmeal-600 text-xs">T8: Standard deviations from vendor mean</p>
                </div>
                <input
                  type="number"
                  value={apTestingConfig.unusual_amount_stddev}
                  onChange={(e) => {
                    setApTestingConfig({ ...apTestingConfig, unusual_amount_stddev: parseFloat(e.target.value) || 3 })
                    setApTestingPreset('custom')
                  }}
                  step="0.5"
                  min="1"
                  max="5"
                  className="w-32 px-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm text-center focus:outline-none focus:border-sage-500/40"
                />
              </div>

              {/* AP-T13: Keyword Confidence */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <span className="text-oatmeal-300 text-sm font-sans">Keyword Sensitivity</span>
                  <p className="text-oatmeal-600 text-xs">T13: Minimum confidence for suspicious keywords</p>
                </div>
                <div className="relative w-32">
                  <input
                    type="number"
                    value={Math.round(apTestingConfig.suspicious_keyword_threshold * 100)}
                    onChange={(e) => {
                      setApTestingConfig({ ...apTestingConfig, suspicious_keyword_threshold: (parseFloat(e.target.value) || 60) / 100 })
                      setApTestingPreset('custom')
                    }}
                    min="30"
                    max="95"
                    className="w-full pr-7 pl-3 py-2 bg-obsidian-800 border border-obsidian-500/30 rounded-lg text-oatmeal-200 font-mono text-sm text-center focus:outline-none focus:border-sage-500/40"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-oatmeal-600 text-sm">%</span>
                </div>
              </div>
            </div>

            {/* Toggle Tests */}
            <div className="mt-4 space-y-3">
              <p className="text-oatmeal-400 text-xs font-sans font-medium uppercase tracking-wide">
                Enable / Disable Tests
              </p>
              {[
                { key: 'check_number_gap_enabled' as const, label: 'T3: Check Number Gaps' },
                { key: 'payment_before_invoice_enabled' as const, label: 'T5: Payment Before Invoice' },
                { key: 'invoice_reuse_check' as const, label: 'T7: Invoice Reuse' },
                { key: 'weekend_payment_enabled' as const, label: 'T9: Weekend Payments' },
                { key: 'high_frequency_vendor_enabled' as const, label: 'T10: High-Frequency Vendors' },
                { key: 'vendor_variation_enabled' as const, label: 'T11: Vendor Variations' },
                { key: 'threshold_proximity_enabled' as const, label: 'T12: Just-Below-Threshold' },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={apTestingConfig[key]}
                    onChange={(e) => {
                      setApTestingConfig({ ...apTestingConfig, [key]: e.target.checked })
                      setApTestingPreset('custom')
                    }}
                    className="w-4 h-4 rounded border-obsidian-500 bg-obsidian-800 text-sage-500 focus:ring-sage-500/20"
                  />
                  <span className="text-oatmeal-300 text-sm font-sans">{label}</span>
                </label>
              ))}
            </div>
          </motion.div>

          {/* Display Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="card mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-4">
              Display Preferences
            </h2>

            <div className="space-y-4">
              {/* Show Immaterial */}
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showImmaterial}
                  onChange={(e) => setShowImmaterial(e.target.checked)}
                  className="w-5 h-5 rounded border-obsidian-500 bg-obsidian-800 text-sage-500 focus:ring-sage-500/20"
                />
                <div>
                  <span className="text-oatmeal-200 font-sans font-medium">Show immaterial items by default</span>
                  <p className="text-oatmeal-500 text-xs">Display all anomalies, including those below materiality threshold</p>
                </div>
              </label>

              {/* Auto-save Summaries */}
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoSaveSummaries}
                  onChange={(e) => setAutoSaveSummaries(e.target.checked)}
                  className="w-5 h-5 rounded border-obsidian-500 bg-obsidian-800 text-sage-500 focus:ring-sage-500/20"
                />
                <div>
                  <span className="text-oatmeal-200 font-sans font-medium">Auto-save diagnostic summaries</span>
                  <p className="text-oatmeal-500 text-xs">Automatically store aggregate totals for trend analysis (Zero-Storage compliant)</p>
                </div>
              </label>
            </div>
          </motion.div>

          {/* Export Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="card mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-4">
              Export Settings
            </h2>

            <div className="mb-4">
              <label className="block text-oatmeal-300 font-sans font-medium mb-2">
                Default Export Format
              </label>
              <select
                value={defaultExportFormat}
                onChange={(e) => setDefaultExportFormat(e.target.value)}
                className={getInputClasses('exportFormat')}
              >
                <option value="pdf" className="bg-obsidian-800">PDF Report</option>
                <option value="excel" className="bg-obsidian-800">Excel Workpaper</option>
              </select>
            </div>

            <div>
              <label className="block text-oatmeal-300 font-sans font-medium mb-2">
                Default Fiscal Year End
              </label>
              <input
                type="text"
                value={defaultFYE}
                onChange={(e) => setDefaultFYE(e.target.value)}
                placeholder="MM-DD"
                className={getInputClasses('fye')}
              />
              <p className="text-oatmeal-500 text-xs mt-1">Format: MM-DD (e.g., 12-31 for December 31)</p>
            </div>
          </motion.div>

          {/* Save Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-8 py-3 bg-sage-500 text-obsidian-900 rounded-lg font-sans font-semibold hover:bg-sage-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving...' : 'Save All Settings'}
            </button>

            {saveSuccess && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-sage-400 font-sans"
              >
                Settings saved successfully!
              </motion.span>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
