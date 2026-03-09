'use client'

/**
 * MaterialitySection — Materiality formula + weighted materiality editor
 * Sprint 519 Phase 4: Extracted from practice settings page.
 */

import { WeightedMaterialityEditor } from '@/components/sensitivity'
import { Reveal } from '@/components/ui/Reveal'
import type {
  MaterialityFormulaType,
  MaterialityPreview,
  WeightedMaterialityConfig,
} from '@/types/settings'
import { FORMULA_TYPE_LABELS } from '@/types/settings'

interface MaterialitySectionProps {
  formulaType: MaterialityFormulaType
  formulaValue: number
  minThreshold: string
  maxThreshold: string
  weightedMateriality: WeightedMaterialityConfig
  preview: MaterialityPreview | null
  sampleRevenue: number
  sampleAssets: number
  sampleEquity: number
  touched: Record<string, boolean>
  getInputClasses: (field: string, isValid?: boolean) => string
  onFormulaTypeChange: (type: MaterialityFormulaType) => void
  onFormulaValueChange: (value: number) => void
  onMinThresholdChange: (value: string) => void
  onMaxThresholdChange: (value: string) => void
  onWeightedMaterialityChange: (config: WeightedMaterialityConfig) => void
  onTouched: (field: string) => void
}

export function MaterialitySection({
  formulaType,
  formulaValue,
  minThreshold,
  maxThreshold,
  weightedMateriality,
  preview,
  sampleRevenue,
  sampleAssets,
  sampleEquity,
  touched,
  getInputClasses,
  onFormulaTypeChange,
  onFormulaValueChange,
  onMinThresholdChange,
  onMaxThresholdChange,
  onWeightedMaterialityChange,
  onTouched,
}: MaterialitySectionProps) {
  return (
    <>
      {/* Materiality Formula Section */}
      <Reveal className="theme-card p-6 mb-6">
        <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
          Default Materiality Formula
        </h2>
        <p className="text-content-tertiary text-sm font-sans mb-6">
          Define how materiality thresholds are calculated for diagnostics.
        </p>

        {/* Formula Type */}
        <div className="mb-6">
          <label htmlFor="formula-type" className="block text-content-secondary font-sans font-medium mb-2">
            Calculation Method
          </label>
          <select
            id="formula-type"
            value={formulaType}
            onChange={(e) => {
              onFormulaTypeChange(e.target.value as MaterialityFormulaType)
              onTouched('formulaType')
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
          <label htmlFor="formula-value" className="block text-content-secondary font-sans font-medium mb-2">
            {formulaType === 'fixed' ? 'Threshold Amount ($)' : 'Percentage (%)'}
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-content-tertiary">
              {formulaType === 'fixed' ? '$' : ''}
            </span>
            <input
              id="formula-value"
              type="number"
              value={formulaValue}
              onChange={(e) => {
                onFormulaValueChange(parseFloat(e.target.value) || 0)
                onTouched('formulaValue')
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
              <label htmlFor="min-threshold" className="block text-content-secondary font-sans font-medium mb-2">
                Minimum Floor ($)
              </label>
              <input
                id="min-threshold"
                type="number"
                value={minThreshold}
                onChange={(e) => onMinThresholdChange(e.target.value)}
                placeholder="Optional"
                min="0"
                step="100"
                className={`${getInputClasses('minThreshold')} font-mono`}
              />
            </div>
            <div>
              <label htmlFor="max-threshold" className="block text-content-secondary font-sans font-medium mb-2">
                Maximum Cap ($)
              </label>
              <input
                id="max-threshold"
                type="number"
                value={maxThreshold}
                onChange={(e) => onMaxThresholdChange(e.target.value)}
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
      </Reveal>

      {/* Weighted Materiality Section */}
      <Reveal delay={0.08} className="theme-card p-6 mb-6">
        <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
          Weighted Materiality by Account Type
        </h2>
        <p className="text-content-tertiary text-sm font-sans mb-6">
          Apply different scrutiny levels to different account categories. Higher weights mean lower thresholds (more scrutiny).
        </p>

        <WeightedMaterialityEditor
          config={weightedMateriality}
          baseThreshold={formulaType === 'fixed' ? formulaValue : (preview?.threshold || 500)}
          onChange={onWeightedMaterialityChange}
          disabled={false}
        />
      </Reveal>
    </>
  )
}
