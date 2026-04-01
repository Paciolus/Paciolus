'use client'

/**
 * Practice Settings Page - Sprint 48
 *
 * Business configuration: materiality formulas, weighted thresholds, export preferences.
 * Separate from Profile Settings (personal account info).
 *
 * Sprint 519 Phase 4: Decomposed into MaterialitySection, ExportPreferencesSection,
 * and testingConfigFields. Testing config sections were already extracted (TestingConfigSection).
 */

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { ExportPreferencesSection } from '@/components/settings/ExportPreferencesSection'
import { MaterialitySection } from '@/components/settings/MaterialitySection'
import {
  JE_THRESHOLDS, JE_TOGGLES,
  AP_THRESHOLDS, AP_TOGGLES,
  PAYROLL_THRESHOLDS, PAYROLL_TOGGLES,
  TWM_THRESHOLDS,
} from '@/components/settings/testingConfigFields'
import { TestingConfigSection } from '@/components/settings/TestingConfigSection'
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
  PayrollTestingConfig,
  PayrollTestingPreset,
  ThreeWayMatchConfig,
  ThreeWayMatchPreset,
} from '@/types/settings'
import {
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

// =============================================================================
// PAGE COMPONENT
// =============================================================================

export default function PracticeSettingsPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
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
    const baseClasses = 'w-full px-4 py-3 bg-surface-input border-2 rounded-lg text-content-primary font-sans transition-all duration-200 outline-hidden'

    if (touched[field] && !isValid) {
      return `${baseClasses} border-clay-500 focus:border-clay-400 focus:ring-2 focus:ring-clay-500/20`
    }

    if (touched[field] && isValid) {
      return `${baseClasses} border-sage-500/50 focus:border-sage-400 focus:ring-2 focus:ring-sage-500/20`
    }

    return `${baseClasses} border-theme focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20`
  }

  const handleTouched = (field: string) => {
    setTouched({ ...touched, [field]: true })
  }

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex flex-col items-center justify-center gap-4">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
        <span className="text-content-secondary font-sans text-sm">Loading settings...</span>
      </div>
    )
  }

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      {/* Main Content */}
      <div className="pt-8 pb-16 px-6">
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
            <div className="mb-6 p-4 bg-theme-error-bg border border-theme-error-border rounded-lg" role="alert">
              <p className="text-theme-error-text font-sans text-sm">{error}</p>
            </div>
          )}

          {/* Materiality Formula + Weighted Materiality */}
          <MaterialitySection
            formulaType={formulaType}
            formulaValue={formulaValue}
            minThreshold={minThreshold}
            maxThreshold={maxThreshold}
            weightedMateriality={weightedMateriality}
            preview={preview}
            sampleRevenue={sampleRevenue}
            sampleAssets={sampleAssets}
            sampleEquity={sampleEquity}
            touched={touched}
            getInputClasses={getInputClasses}
            onFormulaTypeChange={setFormulaType}
            onFormulaValueChange={setFormulaValue}
            onMinThresholdChange={setMinThreshold}
            onMaxThresholdChange={setMaxThreshold}
            onWeightedMaterialityChange={setWeightedMateriality}
            onTouched={handleTouched}
          />

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
                  className="w-4 h-4 rounded-sm border-theme bg-surface-input text-sage-500 focus:ring-sage-500/20"
                />
                <span className="text-content-secondary text-sm font-sans">Enable Fuzzy Vendor Matching</span>
              </label>
              <p className="text-content-tertiary text-xs mt-1 ml-7">
                When enabled, unmatched documents are matched by vendor name similarity + amount + date proximity
              </p>
            </div>
          </TestingConfigSection>

          {/* Display + Export Preferences */}
          <ExportPreferencesSection
            showImmaterial={showImmaterial}
            autoSaveSummaries={autoSaveSummaries}
            defaultExportFormat={defaultExportFormat}
            defaultFYE={defaultFYE}
            getInputClasses={getInputClasses}
            onShowImmaterialChange={setShowImmaterial}
            onAutoSaveSummariesChange={setAutoSaveSummaries}
            onExportFormatChange={setDefaultExportFormat}
            onFYEChange={setDefaultFYE}
          />

          {/* Save Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-8 py-3 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-semibold hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
