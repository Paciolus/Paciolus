'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { TestingConfigSection } from '@/components/settings/TestingConfigSection'
import { useSettings } from '@/hooks/useSettings'
import type {
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
// TOOL CONFIG DEFINITIONS
// =============================================================================

const JE_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'Only flag amounts above this', prefix: '$' },
  { key: 'unusual_amount_stddev', label: 'Unusual Amount Sensitivity', description: 'Standard deviations from mean', step: 0.5, min: 1, max: 5 },
  { key: 'single_user_volume_pct', label: 'User Volume Threshold', description: 'Flag users posting more than this % of entries', suffix: '%', displayScale: 100, fallback: 25, min: 5, max: 80 },
  { key: 'backdate_days_threshold', label: 'Backdating Threshold', description: 'Days between posting and entry date', suffix: 'days', integer: true, fallback: 30, min: 7, max: 180 },
  { key: 'suspicious_keyword_threshold', label: 'Keyword Sensitivity', description: 'Minimum confidence for suspicious keywords', suffix: '%', displayScale: 100, fallback: 60, min: 30, max: 95 },
]

const JE_TOGGLES = [
  { key: 'weekend_posting_enabled', label: 'Weekend Postings' },
  { key: 'after_hours_enabled', label: 'After-Hours Postings' },
  { key: 'numbering_gap_enabled', label: 'Numbering Gaps' },
  { key: 'backdate_enabled', label: 'Backdated Entries' },
  { key: 'suspicious_keyword_enabled', label: 'Suspicious Keywords' },
]

const AP_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'Only flag amounts above this', prefix: '$' },
  { key: 'duplicate_days_window', label: 'Duplicate Date Window', description: 'Days to check for fuzzy duplicates', suffix: 'days', integer: true, fallback: 30, min: 7, max: 90 },
  { key: 'unusual_amount_stddev', label: 'Unusual Amount Sensitivity', description: 'Standard deviations from vendor mean', step: 0.5, min: 1, max: 5 },
  { key: 'suspicious_keyword_threshold', label: 'Keyword Sensitivity', description: 'Minimum confidence for suspicious keywords', suffix: '%', displayScale: 100, fallback: 60, min: 30, max: 95 },
]

const AP_TOGGLES = [
  { key: 'check_number_gap_enabled', label: 'Check Number Gaps' },
  { key: 'payment_before_invoice_enabled', label: 'Payment Before Invoice' },
  { key: 'invoice_reuse_check', label: 'Invoice Reuse' },
  { key: 'weekend_payment_enabled', label: 'Weekend Payments' },
  { key: 'high_frequency_vendor_enabled', label: 'High-Frequency Vendors' },
  { key: 'vendor_variation_enabled', label: 'Vendor Variations' },
  { key: 'threshold_proximity_enabled', label: 'Just-Below-Threshold' },
]

const PAYROLL_THRESHOLDS = [
  { key: 'round_amount_threshold', label: 'Round Amount Minimum', description: 'Only flag salary amounts above this', prefix: '$' },
  { key: 'unusual_pay_stddev', label: 'Unusual Pay Sensitivity', description: 'Standard deviations from department mean', step: 0.5, min: 1, max: 5 },
  { key: 'benford_min_entries', label: 'Benford Minimum Entries', description: 'Minimum entries for Benford analysis', integer: true, fallback: 500, min: 100, max: 5000, step: 100 },
  { key: 'ghost_min_indicators', label: 'Ghost Employee Min Indicators', description: 'Indicators needed to flag as ghost', integer: true, fallback: 2, min: 1, max: 4 },
]

const PAYROLL_TOGGLES = [
  { key: 'check_gap_enabled', label: 'Check Number Gaps' },
  { key: 'frequency_enabled', label: 'Pay Frequency Anomalies' },
  { key: 'benford_enabled', label: "Benford's Law Analysis" },
  { key: 'ghost_enabled', label: 'Ghost Employee Indicators' },
  { key: 'duplicate_bank_enabled', label: 'Duplicate Bank/Address' },
  { key: 'duplicate_tax_enabled', label: 'Duplicate Tax IDs' },
]

const TWM_THRESHOLDS = [
  { key: 'amount_tolerance', label: 'Amount Tolerance', description: 'Maximum difference before flagging a variance', prefix: '$', step: '0.01', min: 0 },
  { key: 'price_variance_threshold', label: 'Price Variance Threshold', description: '% difference in unit price before flagging', suffix: '%', displayScale: 100, fallback: 5, step: 1, min: 1, max: 50 },
  { key: 'date_window_days', label: 'Date Window', description: 'Days between PO and receipt before flagging', suffix: 'd', integer: true, fallback: 30, min: 7, max: 180 },
  { key: 'fuzzy_vendor_threshold', label: 'Vendor Match Sensitivity', description: 'Minimum name similarity for fuzzy matching (0-100%)', suffix: '%', displayScale: 100, fallback: 85, step: 5, min: 50, max: 100 },
]

// =============================================================================
// COMPONENT
// =============================================================================

export type ToolSettingsKey = 'je' | 'ap' | 'payroll' | 'three_way_match'

interface ToolSettingsDrawerProps {
  toolKey: ToolSettingsKey
  open: boolean
  onClose: () => void
}

const TOOL_TITLES: Record<ToolSettingsKey, string> = {
  je: 'Journal Entry Testing',
  ap: 'AP Testing',
  payroll: 'Payroll Testing',
  three_way_match: 'Three-Way Match',
}

export function ToolSettingsDrawer({ toolKey, open, onClose }: ToolSettingsDrawerProps) {
  const { practiceSettings, updatePracticeSettings } = useSettings()
  const drawerRef = useRef<HTMLDivElement>(null)

  // Local state for each tool config
  const [jePreset, setJePreset] = useState<JETestingPreset>('standard')
  const [jeConfig, setJeConfig] = useState<JETestingConfig>(DEFAULT_JE_TESTING_CONFIG)
  const [apPreset, setApPreset] = useState<APTestingPreset>('standard')
  const [apConfig, setApConfig] = useState<APTestingConfig>(DEFAULT_AP_TESTING_CONFIG)
  const [payrollPreset, setPayrollPreset] = useState<PayrollTestingPreset>('standard')
  const [payrollConfig, setPayrollConfig] = useState<PayrollTestingConfig>(DEFAULT_PAYROLL_TESTING_CONFIG)
  const [twmPreset, setTwmPreset] = useState<ThreeWayMatchPreset>('standard')
  const [twmConfig, setTwmConfig] = useState<ThreeWayMatchConfig>(DEFAULT_THREE_WAY_MATCH_CONFIG)

  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)

  // Sync from practice settings on mount / when settings load
  useEffect(() => {
    if (!practiceSettings) return
    if (practiceSettings.je_testing_config) setJeConfig(practiceSettings.je_testing_config)
    if (practiceSettings.ap_testing_config) setApConfig(practiceSettings.ap_testing_config)
    if (practiceSettings.payroll_testing_config) setPayrollConfig(practiceSettings.payroll_testing_config)
    if (practiceSettings.three_way_match_config) setTwmConfig(practiceSettings.three_way_match_config)
  }, [practiceSettings])

  // Escape key closes drawer
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  const handleSave = useCallback(async () => {
    setIsSaving(true)
    setSaveSuccess(false)
    const updates: Record<string, unknown> = {}
    if (toolKey === 'je') updates.je_testing_config = jeConfig
    if (toolKey === 'ap') updates.ap_testing_config = apConfig
    if (toolKey === 'payroll') updates.payroll_testing_config = payrollConfig
    if (toolKey === 'three_way_match') updates.three_way_match_config = twmConfig
    const ok = await updatePracticeSettings(updates)
    setIsSaving(false)
    if (ok) {
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    }
  }, [toolKey, jeConfig, apConfig, payrollConfig, twmConfig, updatePracticeSettings])

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-obsidian-900/20 backdrop-blur-sm z-40"
            onClick={onClose}
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.div
            ref={drawerRef}
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 bottom-0 w-[400px] max-w-[90vw] bg-surface-page border-l border-theme shadow-theme-elevated z-50 flex flex-col"
            role="dialog"
            aria-modal="true"
            aria-label={`${TOOL_TITLES[toolKey]} Settings`}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-theme bg-surface-card">
              <div>
                <h2 className="font-serif text-content-primary text-base">{TOOL_TITLES[toolKey]} Settings</h2>
                <p className="font-sans text-content-tertiary text-xs mt-0.5">Adjust thresholds for this tool</p>
              </div>
              <button
                onClick={onClose}
                className="p-2 rounded-lg text-content-tertiary hover:text-content-primary hover:bg-surface-card-secondary transition-colors"
                aria-label="Close settings"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto px-6 py-6">
              {toolKey === 'je' && (
                <TestingConfigSection
                  title="Thresholds & Toggles"
                  description="Configure sensitivity levels for journal entry anomaly detection"
                  delay={0}
                  presetLabels={JE_PRESET_LABELS}
                  presetDescriptions={JE_PRESET_DESCRIPTIONS}
                  presetConfigs={JE_TESTING_PRESETS}
                  defaultConfig={DEFAULT_JE_TESTING_CONFIG}
                  currentPreset={jePreset}
                  currentConfig={jeConfig}
                  onPresetChange={setJePreset}
                  onConfigChange={setJeConfig}
                  thresholds={JE_THRESHOLDS}
                  toggles={JE_TOGGLES}
                />
              )}

              {toolKey === 'ap' && (
                <TestingConfigSection
                  title="Thresholds & Toggles"
                  description="Configure sensitivity levels for AP anomaly detection"
                  delay={0}
                  presetLabels={AP_PRESET_LABELS}
                  presetDescriptions={AP_PRESET_DESCRIPTIONS}
                  presetConfigs={AP_TESTING_PRESETS}
                  defaultConfig={DEFAULT_AP_TESTING_CONFIG}
                  currentPreset={apPreset}
                  currentConfig={apConfig}
                  onPresetChange={setApPreset}
                  onConfigChange={setApConfig}
                  thresholds={AP_THRESHOLDS}
                  toggles={AP_TOGGLES}
                />
              )}

              {toolKey === 'payroll' && (
                <TestingConfigSection
                  title="Thresholds & Toggles"
                  description="Configure sensitivity levels for payroll anomaly detection"
                  delay={0}
                  presetLabels={PAYROLL_PRESET_LABELS}
                  presetDescriptions={PAYROLL_PRESET_DESCRIPTIONS}
                  presetConfigs={PAYROLL_TESTING_PRESETS}
                  defaultConfig={DEFAULT_PAYROLL_TESTING_CONFIG}
                  currentPreset={payrollPreset}
                  currentConfig={payrollConfig}
                  onPresetChange={setPayrollPreset}
                  onConfigChange={setPayrollConfig}
                  thresholds={PAYROLL_THRESHOLDS}
                  toggles={PAYROLL_TOGGLES}
                />
              )}

              {toolKey === 'three_way_match' && (
                <TestingConfigSection
                  title="Thresholds"
                  description="Configure matching tolerances and sensitivity"
                  delay={0}
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
                />
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-theme bg-surface-card">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="w-full px-4 py-2.5 bg-sage-600 border border-sage-600 rounded-lg text-white font-sans text-sm font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : saveSuccess ? 'Saved' : 'Save Settings'}
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
