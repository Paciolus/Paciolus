'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/context/AuthContext'
import { useSettings } from '@/hooks/useSettings'
import type {
  MaterialityFormula,
  MaterialityFormulaType,
  MaterialityPreview,
} from '@/types/settings'
import { FORMULA_TYPE_LABELS, DEFAULT_MATERIALITY_FORMULA } from '@/types/settings'

export default function SettingsPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
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

  // UI state
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [preview, setPreview] = useState<MaterialityPreview | null>(null)
  const [touched, setTouched] = useState<Record<string, boolean>>({})

  // Sample data for preview (user can override)
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
    })

    setIsSaving(false)

    if (success) {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
    }
  }

  // Input styling with Tier 2 validation
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
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-obsidian-900/80 backdrop-blur-md border-b border-obsidian-600/50 z-50">
        <div className="max-w-4xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
            />
            <span className="text-xl font-bold font-serif text-oatmeal-200 tracking-tight">
              Paciolus
            </span>
          </Link>
          <div className="text-oatmeal-400 text-sm font-sans">
            Practice Settings
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-8">
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

            {/* Preview Section */}
            {preview && (
              <div className="p-4 bg-obsidian-700/50 rounded-lg border border-obsidian-600">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
                  <span className="text-sage-400 text-sm font-sans font-medium">Preview</span>
                </div>
                <p className="text-oatmeal-200 font-mono text-2xl mb-1">
                  ${preview.threshold.toLocaleString()}
                </p>
                <p className="text-oatmeal-500 text-sm font-sans">
                  {preview.explanation}
                </p>
              </div>
            )}

            {/* Sample Data for Preview (only for percentage formulas) */}
            {formulaType !== 'fixed' && (
              <div className="mt-6 pt-6 border-t border-obsidian-600">
                <h3 className="text-oatmeal-300 font-sans font-medium mb-4">
                  Sample Data for Preview
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-oatmeal-500 text-xs font-sans mb-1">
                      Revenue
                    </label>
                    <input
                      type="number"
                      value={sampleRevenue}
                      onChange={(e) => setSampleRevenue(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-obsidian-800 border border-obsidian-500 rounded text-oatmeal-200 font-mono text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-oatmeal-500 text-xs font-sans mb-1">
                      Total Assets
                    </label>
                    <input
                      type="number"
                      value={sampleAssets}
                      onChange={(e) => setSampleAssets(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-obsidian-800 border border-obsidian-500 rounded text-oatmeal-200 font-mono text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-oatmeal-500 text-xs font-sans mb-1">
                      Total Equity
                    </label>
                    <input
                      type="number"
                      value={sampleEquity}
                      onChange={(e) => setSampleEquity(parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 bg-obsidian-800 border border-obsidian-500 rounded text-oatmeal-200 font-mono text-sm"
                    />
                  </div>
                </div>
              </div>
            )}
          </motion.div>

          {/* Display Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card mb-6"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-4">
              Display Preferences
            </h2>

            {/* Show Immaterial Toggle */}
            <div className="flex items-center justify-between py-3 border-b border-obsidian-700">
              <div>
                <p className="text-oatmeal-200 font-sans font-medium">
                  Show Indistinct Items by Default
                </p>
                <p className="text-oatmeal-500 text-sm font-sans">
                  Display items below materiality threshold in results
                </p>
              </div>
              <button
                onClick={() => setShowImmaterial(!showImmaterial)}
                className={`relative w-14 h-8 rounded-full transition-colors ${
                  showImmaterial ? 'bg-sage-500' : 'bg-obsidian-600'
                }`}
              >
                <div
                  className={`absolute top-1 w-6 h-6 rounded-full bg-oatmeal-200 transition-all ${
                    showImmaterial ? 'left-7' : 'left-1'
                  }`}
                />
              </button>
            </div>

            {/* Default Export Format */}
            <div className="py-3 border-b border-obsidian-700">
              <label className="block text-oatmeal-200 font-sans font-medium mb-2">
                Default Export Format
              </label>
              <div className="flex gap-4">
                <button
                  onClick={() => setDefaultExportFormat('pdf')}
                  className={`px-4 py-2 rounded-lg font-sans text-sm transition-all ${
                    defaultExportFormat === 'pdf'
                      ? 'bg-sage-500/20 border-2 border-sage-500 text-sage-400'
                      : 'bg-obsidian-700 border-2 border-obsidian-600 text-oatmeal-400 hover:border-obsidian-500'
                  }`}
                >
                  PDF Report
                </button>
                <button
                  onClick={() => setDefaultExportFormat('excel')}
                  className={`px-4 py-2 rounded-lg font-sans text-sm transition-all ${
                    defaultExportFormat === 'excel'
                      ? 'bg-sage-500/20 border-2 border-sage-500 text-sage-400'
                      : 'bg-obsidian-700 border-2 border-obsidian-600 text-oatmeal-400 hover:border-obsidian-500'
                  }`}
                >
                  Excel Workpaper
                </button>
              </div>
            </div>

            {/* Auto-save Summaries */}
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-oatmeal-200 font-sans font-medium">
                  Auto-Save Diagnostic Summaries
                </p>
                <p className="text-oatmeal-500 text-sm font-sans">
                  Automatically save summaries for variance tracking
                </p>
              </div>
              <button
                onClick={() => setAutoSaveSummaries(!autoSaveSummaries)}
                className={`relative w-14 h-8 rounded-full transition-colors ${
                  autoSaveSummaries ? 'bg-sage-500' : 'bg-obsidian-600'
                }`}
              >
                <div
                  className={`absolute top-1 w-6 h-6 rounded-full bg-oatmeal-200 transition-all ${
                    autoSaveSummaries ? 'left-7' : 'left-1'
                  }`}
                />
              </button>
            </div>
          </motion.div>

          {/* Client Defaults */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card mb-8"
          >
            <h2 className="text-xl font-serif font-semibold text-oatmeal-200 mb-4">
              Client Defaults
            </h2>

            {/* Default Fiscal Year End */}
            <div className="mb-4">
              <label className="block text-oatmeal-200 font-sans font-medium mb-2">
                Default Fiscal Year End
              </label>
              <select
                value={defaultFYE}
                onChange={(e) => setDefaultFYE(e.target.value)}
                className={getInputClasses('defaultFYE')}
              >
                <option value="12-31" className="bg-obsidian-800">December 31 (Calendar Year)</option>
                <option value="03-31" className="bg-obsidian-800">March 31</option>
                <option value="06-30" className="bg-obsidian-800">June 30</option>
                <option value="09-30" className="bg-obsidian-800">September 30</option>
              </select>
            </div>
          </motion.div>

          {/* Save Button */}
          <div className="flex items-center justify-between">
            <Link
              href="/"
              className="text-oatmeal-400 hover:text-oatmeal-200 font-sans font-medium transition-colors"
            >
              Cancel
            </Link>

            <motion.button
              onClick={handleSave}
              disabled={isSaving}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`px-8 py-3 rounded-lg font-sans font-semibold transition-all ${
                saveSuccess
                  ? 'bg-sage-500 text-oatmeal-100'
                  : 'bg-sage-500/20 border-2 border-sage-500 text-sage-400 hover:bg-sage-500/30'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isSaving ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-sage-400/30 border-t-sage-400 rounded-full animate-spin" />
                  Saving...
                </span>
              ) : saveSuccess ? (
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Saved
                </span>
              ) : (
                'Save Settings'
              )}
            </motion.button>
          </div>

          {/* Zero-Storage Notice */}
          <div className="mt-8 text-center">
            <div className="inline-flex items-center gap-2 text-oatmeal-600 text-xs font-sans">
              <div className="w-2 h-2 bg-sage-500/50 rounded-full" />
              Zero-Storage: Only formulas are stored, never financial data
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
