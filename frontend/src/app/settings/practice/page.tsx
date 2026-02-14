'use client'

// NOTE: Decomposition candidate (665 LOC) — extract MaterialitySection, ExportPreferencesSection

/**
 * Practice Settings Page - Sprint 48
 *
 * Business configuration: materiality formulas, weighted thresholds, export preferences.
 * Separate from Profile Settings (personal account info).
 */

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { ProfileDropdown } from '@/components/auth/ProfileDropdown'
import { useSettings } from '@/hooks/useSettings'
import { TestingConfigSection } from '@/components/settings/TestingConfigSection'
import type {
  MaterialityFormula,
  MaterialityFormulaType,
  MaterialityPreview,
  WeightedMaterialityConfig,
  JETestingConfig,
  JETestingPreset,
  APTestingConfig,
  APTestingPreset,
  PayrollTestingConfig,
  PayrollTestingPreset,
  ThreeWayMatchConfig,
  ThreeWayMatchPreset,
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
  DEFAULT_PAYROLL_TESTING_CONFIG,
  PAYROLL_TESTING_PRESETS,
  PAYROLL_PRESET_LABELS,
  PAYROLL_PRESET_DESCRIPTIONS,
  DEFAULT_THREE_WAY_MATCH_CONFIG,
  THREE_WAY_MATCH_PRESETS,
  TWM_PRESET_LABELS,
  TWM_PRESET_DESCRIPTIONS,
} from '@/types/settings'
import { WeightedMaterialityEditor } from '@/components/sensitivity'

// =============================================================================
// TESTING CONFIG FIELD DEFINITIONS
// =============================================================================

const JE_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'T4: Only flag amounts above this', prefix: '$' },
  { key: 'unusual_amount_stddev', label: 'Unusual Amount Sensitivity', description: 'T5: Standard deviations from mean', step: 0.5, min: 1, max: 5 },
  { key: 'single_user_volume_pct', label: 'User Volume Threshold', description: 'T9: Flag users posting more than this % of entries', suffix: '%', displayScale: 100, fallback: 25, min: 5, max: 80 },
  { key: 'backdate_days_threshold', label: 'Backdating Threshold', description: 'T12: Days between posting and entry date', suffix: 'days', integer: true, fallback: 30, min: 7, max: 180 },
  { key: 'suspicious_keyword_threshold', label: 'Keyword Sensitivity', description: 'T13: Minimum confidence for suspicious keywords', suffix: '%', displayScale: 100, fallback: 60, min: 30, max: 95 },
]

const JE_TOGGLES = [
  { key: 'weekend_posting_enabled', label: 'T7: Weekend Postings' },
  { key: 'after_hours_enabled', label: 'T10: After-Hours Postings' },
  { key: 'numbering_gap_enabled', label: 'T11: Numbering Gaps' },
  { key: 'backdate_enabled', label: 'T12: Backdated Entries' },
  { key: 'suspicious_keyword_enabled', label: 'T13: Suspicious Keywords' },
]

const AP_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'T4: Only flag amounts above this', prefix: '$' },
  { key: 'duplicate_days_window', label: 'Duplicate Date Window', description: 'T6: Days to check for fuzzy duplicates', suffix: 'days', integer: true, fallback: 30, min: 7, max: 90 },
  { key: 'unusual_amount_stddev', label: 'Unusual Amount Sensitivity', description: 'T8: Standard deviations from vendor mean', step: 0.5, min: 1, max: 5 },
  { key: 'suspicious_keyword_threshold', label: 'Keyword Sensitivity', description: 'T13: Minimum confidence for suspicious keywords', suffix: '%', displayScale: 100, fallback: 60, min: 30, max: 95 },
]

const AP_TOGGLES = [
  { key: 'check_number_gap_enabled', label: 'T3: Check Number Gaps' },
  { key: 'payment_before_invoice_enabled', label: 'T5: Payment Before Invoice' },
  { key: 'invoice_reuse_check', label: 'T7: Invoice Reuse' },
  { key: 'weekend_payment_enabled', label: 'T9: Weekend Payments' },
  { key: 'high_frequency_vendor_enabled', label: 'T10: High-Frequency Vendors' },
  { key: 'vendor_variation_enabled', label: 'T11: Vendor Variations' },
  { key: 'threshold_proximity_enabled', label: 'T12: Just-Below-Threshold' },
]

const PAYROLL_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'T3: Only flag salary amounts above this', prefix: '$' },
  { key: 'unusual_pay_stddev', label: 'Unusual Pay Sensitivity', description: 'T6: Standard deviations from department mean', step: 0.5, min: 1, max: 5 },
  { key: 'benford_min_entries', label: 'Benford Minimum Entries', description: 'T8: Minimum entries for Benford analysis', integer: true, fallback: 500, min: 100, max: 5000, step: 100 },
  { key: 'ghost_min_indicators', label: 'Ghost Employee Min Indicators', description: 'T9: Indicators needed to flag as ghost', integer: true, fallback: 2, min: 1, max: 4 },
]

const PAYROLL_TOGGLES = [
  { key: 'check_gap_enabled', label: 'T5: Check Number Gaps' },
  { key: 'frequency_enabled', label: 'T7: Pay Frequency Anomalies' },
  { key: 'benford_enabled', label: "T8: Benford's Law Analysis" },
  { key: 'ghost_enabled', label: 'T9: Ghost Employee Indicators' },
  { key: 'duplicate_bank_enabled', label: 'T10: Duplicate Bank/Address' },
  { key: 'duplicate_tax_enabled', label: 'T11: Duplicate Tax IDs' },
]

const TWM_THRESHOLDS = [
  { key: 'amount_tolerance', label: 'Amount Tolerance', description: 'Maximum difference before flagging a variance', prefix: '$', step: '0.01', min: 0 },
  { key: 'price_variance_threshold', label: 'Price Variance Threshold', description: '% difference in unit price before flagging', suffix: '%', displayScale: 100, fallback: 5, step: 1, min: 1, max: 50 },
  { key: 'date_window_days', label: 'Date Window', description: 'Days between PO and receipt before flagging', suffix: 'd', integer: true, fallback: 30, min: 7, max: 180 },
  { key: 'fuzzy_vendor_threshold', label: 'Vendor Match Sensitivity', description: 'Minimum name similarity for fuzzy matching (0-100%)', suffix: '%', displayScale: 100, fallback: 85, step: 5, min: 50, max: 100 },
]

// =============================================================================
// PAGE COMPONENT
// =============================================================================

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

  // Testing config states
  const [jeTestingPreset, setJeTestingPreset] = useState<JETestingPreset>('standard')
  const [jeTestingConfig, setJeTestingConfig] = useState<JETestingConfig>(DEFAULT_JE_TESTING_CONFIG)
  const [apTestingPreset, setApTestingPreset] = useState<APTestingPreset>('standard')
  const [apTestingConfig, setApTestingConfig] = useState<APTestingConfig>(DEFAULT_AP_TESTING_CONFIG)
  const [payrollTestingPreset, setPayrollTestingPreset] = useState<PayrollTestingPreset>('standard')
  const [payrollTestingConfig, setPayrollTestingConfig] = useState<PayrollTestingConfig>(DEFAULT_PAYROLL_TESTING_CONFIG)
  const [twmPreset, setTwmPreset] = useState<ThreeWayMatchPreset>('standard')
  const [twmConfig, setTwmConfig] = useState<ThreeWayMatchConfig>(DEFAULT_THREE_WAY_MATCH_CONFIG)

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
      if (practiceSettings.payroll_testing_config) {
        setPayrollTestingConfig({ ...DEFAULT_PAYROLL_TESTING_CONFIG, ...practiceSettings.payroll_testing_config })
        setPayrollTestingPreset('custom')
      }
      if (practiceSettings.three_way_match_config) {
        setTwmConfig({ ...DEFAULT_THREE_WAY_MATCH_CONFIG, ...practiceSettings.three_way_match_config })
        setTwmPreset('custom')
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
      payroll_testing_config: payrollTestingConfig,
      three_way_match_config: twmConfig,
    })

    setIsSaving(false)

    if (success) {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  }

  // Input styling
  const getInputClasses = (field: string, isValid: boolean = true) => {
    const baseClasses = 'w-full px-4 py-3 bg-surface-input border-2 rounded-lg text-content-primary font-sans transition-all duration-200 outline-none'

    if (touched[field] && !isValid) {
      return `${baseClasses} border-clay-500 focus:border-clay-400 focus:ring-2 focus:ring-clay-500/20`
    }

    if (touched[field] && isValid) {
      return `${baseClasses} border-sage-500/50 focus:border-sage-400 focus:ring-2 focus:ring-sage-500/20`
    }

    return `${baseClasses} border-theme focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20`
  }

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-surface-page">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-surface-card backdrop-blur-md border-b border-theme z-50">
        <div className="max-w-6xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
              style={{ imageRendering: 'crisp-edges' }}
            />
            <span className="text-xl font-bold font-serif text-content-primary tracking-tight">
              Paciolus
            </span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-sm text-content-secondary font-sans hidden sm:block">
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
            <div className="flex items-center gap-2 text-content-tertiary text-sm font-sans mb-4">
              <Link href="/" className="hover:text-content-secondary transition-colors">Home</Link>
              <span>/</span>
              <span className="text-content-secondary">Practice Settings</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
              Practice Configuration
            </h1>
            <p className="text-content-secondary font-sans">
              Configure your default diagnostic settings. These will apply to all new diagnostics unless overridden at the client level.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-clay-50 border border-clay-200 rounded-lg">
              <p className="text-clay-600 font-sans">{error}</p>
            </div>
          )}

          {/* Materiality Formula Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="theme-card p-6 mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Default Materiality Formula
            </h2>
            <p className="text-content-tertiary text-sm font-sans mb-6">
              Define how materiality thresholds are calculated for diagnostics.
            </p>

            {/* Formula Type */}
            <div className="mb-6">
              <label className="block text-content-secondary font-sans font-medium mb-2">
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
                  <option key={value} value={value} className="bg-surface-input">
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Formula Value */}
            <div className="mb-6">
              <label className="block text-content-secondary font-sans font-medium mb-2">
                {formulaType === 'fixed' ? 'Threshold Amount ($)' : 'Percentage (%)'}
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-content-tertiary">
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
                  <span className="absolute right-4 top-1/2 -translate-y-1/2 text-content-tertiary">
                    %
                  </span>
                )}
              </div>
            </div>

            {/* Min/Max Thresholds (for percentage-based) */}
            {formulaType !== 'fixed' && (
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-content-secondary font-sans font-medium mb-2">
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
                  <label className="block text-content-secondary font-sans font-medium mb-2">
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
              <div className="p-4 bg-surface-card-secondary rounded-lg border border-theme">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-content-secondary text-sm font-sans">Calculated Threshold</span>
                  <span className="text-sage-600 font-mono text-lg font-semibold">
                    ${preview.threshold.toLocaleString()}
                  </span>
                </div>
                <p className="text-content-tertiary text-xs font-sans">
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
            className="theme-card p-6 mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Weighted Materiality by Account Type
            </h2>
            <p className="text-content-tertiary text-sm font-sans mb-6">
              Apply different scrutiny levels to different account categories. Higher weights mean lower thresholds (more scrutiny).
            </p>

            <WeightedMaterialityEditor
              config={weightedMateriality}
              baseThreshold={formulaType === 'fixed' ? formulaValue : (preview?.threshold || 500)}
              onChange={setWeightedMateriality}
              disabled={false}
            />
          </motion.div>

          {/* JE Testing Thresholds */}
          <TestingConfigSection
            title="Journal Entry Testing"
            description="Configure sensitivity thresholds for the 13-test JE testing battery. Presets provide quick configuration for common engagement profiles."
            delay={0.15}
            presetLabels={JE_PRESET_LABELS}
            presetDescriptions={JE_PRESET_DESCRIPTIONS}
            presetConfigs={JE_TESTING_PRESETS}
            defaultConfig={DEFAULT_JE_TESTING_CONFIG}
            currentPreset={jeTestingPreset}
            currentConfig={jeTestingConfig}
            onPresetChange={setJeTestingPreset}
            onConfigChange={setJeTestingConfig}
            thresholds={JE_THRESHOLDS}
            toggles={JE_TOGGLES}
          />

          {/* AP Testing Thresholds */}
          <TestingConfigSection
            title="AP Payment Testing"
            description="Configure sensitivity thresholds for the 13-test AP payment testing battery. Presets provide quick configuration for common engagement profiles."
            delay={0.2}
            presetLabels={AP_PRESET_LABELS}
            presetDescriptions={AP_PRESET_DESCRIPTIONS}
            presetConfigs={AP_TESTING_PRESETS}
            defaultConfig={DEFAULT_AP_TESTING_CONFIG}
            currentPreset={apTestingPreset}
            currentConfig={apTestingConfig}
            onPresetChange={setApTestingPreset}
            onConfigChange={setApTestingConfig}
            thresholds={AP_THRESHOLDS}
            toggles={AP_TOGGLES}
          />

          {/* Payroll Testing Thresholds */}
          <TestingConfigSection
            title="Payroll &amp; Employee Testing"
            description="Configure sensitivity thresholds for the 11-test payroll testing battery. Presets provide quick configuration for common engagement profiles."
            delay={0.25}
            presetLabels={PAYROLL_PRESET_LABELS}
            presetDescriptions={PAYROLL_PRESET_DESCRIPTIONS}
            presetConfigs={PAYROLL_TESTING_PRESETS}
            defaultConfig={DEFAULT_PAYROLL_TESTING_CONFIG}
            currentPreset={payrollTestingPreset}
            currentConfig={payrollTestingConfig}
            onPresetChange={setPayrollTestingPreset}
            onConfigChange={setPayrollTestingConfig}
            thresholds={PAYROLL_THRESHOLDS}
            toggles={PAYROLL_TOGGLES}
          />

          {/* Three-Way Match Thresholds */}
          <TestingConfigSection
            title="Three-Way Match"
            description="Configure matching tolerances for PO → Invoice → Receipt validation. Presets provide quick configuration for common procurement environments."
            delay={0.28}
            presetLabels={TWM_PRESET_LABELS}
            presetDescriptions={TWM_PRESET_DESCRIPTIONS}
            presetConfigs={THREE_WAY_MATCH_PRESETS}
            defaultConfig={DEFAULT_THREE_WAY_MATCH_CONFIG}
            currentPreset={twmPreset}
            currentConfig={twmConfig}
            onPresetChange={setTwmPreset}
            onConfigChange={setTwmConfig}
            thresholds={TWM_THRESHOLDS}
            toggles={[]}
          >
            {/* TWM-specific: Fuzzy Matching Toggle */}
            <div className="mt-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={twmConfig.enable_fuzzy_matching}
                  onChange={(e) => {
                    setTwmConfig({ ...twmConfig, enable_fuzzy_matching: e.target.checked })
                    setTwmPreset('custom')
                  }}
                  className="w-4 h-4 rounded border-theme bg-surface-input text-sage-500 focus:ring-sage-500/20"
                />
                <span className="text-content-secondary text-sm font-sans">Enable Fuzzy Vendor Matching</span>
              </label>
              <p className="text-content-tertiary text-xs mt-1 ml-7">
                When enabled, unmatched documents are matched by vendor name similarity + amount + date proximity
              </p>
            </div>
          </TestingConfigSection>

          {/* Display Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="theme-card p-6 mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Display Preferences
            </h2>

            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showImmaterial}
                  onChange={(e) => setShowImmaterial(e.target.checked)}
                  className="w-5 h-5 rounded border-theme bg-surface-input text-sage-500 focus:ring-sage-500/20"
                />
                <div>
                  <span className="text-content-primary font-sans font-medium">Show immaterial items by default</span>
                  <p className="text-content-tertiary text-xs">Display all anomalies, including those below materiality threshold</p>
                </div>
              </label>

              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoSaveSummaries}
                  onChange={(e) => setAutoSaveSummaries(e.target.checked)}
                  className="w-5 h-5 rounded border-theme bg-surface-input text-sage-500 focus:ring-sage-500/20"
                />
                <div>
                  <span className="text-content-primary font-sans font-medium">Auto-save diagnostic summaries</span>
                  <p className="text-content-tertiary text-xs">Automatically store aggregate totals for trend analysis (Zero-Storage compliant)</p>
                </div>
              </label>
            </div>
          </motion.div>

          {/* Export Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="theme-card p-6 mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
              Export Settings
            </h2>

            <div className="mb-4">
              <label className="block text-content-secondary font-sans font-medium mb-2">
                Default Export Format
              </label>
              <select
                value={defaultExportFormat}
                onChange={(e) => setDefaultExportFormat(e.target.value)}
                className={getInputClasses('exportFormat')}
              >
                <option value="pdf" className="bg-surface-input">PDF Report</option>
                <option value="excel" className="bg-surface-input">Excel Workpaper</option>
              </select>
            </div>

            <div>
              <label className="block text-content-secondary font-sans font-medium mb-2">
                Default Fiscal Year End
              </label>
              <input
                type="text"
                value={defaultFYE}
                onChange={(e) => setDefaultFYE(e.target.value)}
                placeholder="MM-DD"
                className={getInputClasses('fye')}
              />
              <p className="text-content-tertiary text-xs mt-1">Format: MM-DD (e.g., 12-31 for December 31)</p>
            </div>
          </motion.div>

          {/* Save Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-8 py-3 bg-sage-600 text-white rounded-lg font-sans font-semibold hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? 'Saving...' : 'Save All Settings'}
            </button>

            {saveSuccess && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-sage-600 font-sans"
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
