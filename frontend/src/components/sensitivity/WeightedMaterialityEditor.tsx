'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type {
  WeightedMaterialityConfig,
  AccountCategory,
} from '@/types/settings'
import {
  DEFAULT_ACCOUNT_WEIGHTS,
  ACCOUNT_CATEGORY_LABELS,
  WEIGHT_DESCRIPTIONS,
} from '@/types/settings'

interface WeightedMaterialityEditorProps {
  config: WeightedMaterialityConfig
  baseThreshold: number
  onChange: (config: WeightedMaterialityConfig) => void
  disabled?: boolean
}

/**
 * Sprint 32: Weighted Materiality Editor
 *
 * Allows practitioners to configure per-account-category materiality weights.
 * Higher weights = more scrutiny (lower effective threshold).
 *
 * Design: Oat & Obsidian with Tier 1 animations
 */
export function WeightedMaterialityEditor({
  config,
  baseThreshold,
  onChange,
  disabled = false,
}: WeightedMaterialityEditorProps) {
  const [expandedCategory, setExpandedCategory] = useState<AccountCategory | null>(null)

  // Calculate effective threshold for a category
  const getEffectiveThreshold = useCallback((category: AccountCategory): number => {
    if (!config.enabled || baseThreshold <= 0) return baseThreshold

    const accountWeight = config.account_weights[category] || 1.0
    const isBalanceSheet = ['asset', 'liability', 'equity'].includes(category)
    const statementWeight = isBalanceSheet
      ? config.balance_sheet_weight
      : config.income_statement_weight

    return Math.round((baseThreshold / (accountWeight * statementWeight)) * 100) / 100
  }, [config, baseThreshold])

  // Handle toggle
  const handleToggle = useCallback(() => {
    onChange({ ...config, enabled: !config.enabled })
  }, [config, onChange])

  // Handle weight change
  const handleWeightChange = useCallback((category: AccountCategory, value: number) => {
    // Clamp between 0.1 and 5.0
    const clampedValue = Math.max(0.1, Math.min(5.0, value))
    onChange({
      ...config,
      account_weights: {
        ...config.account_weights,
        [category]: clampedValue,
      },
    })
  }, [config, onChange])

  // Handle statement weight change
  const handleStatementWeightChange = useCallback((
    type: 'balance_sheet' | 'income_statement',
    value: number
  ) => {
    const clampedValue = Math.max(0.1, Math.min(5.0, value))
    onChange({
      ...config,
      [type === 'balance_sheet' ? 'balance_sheet_weight' : 'income_statement_weight']: clampedValue,
    })
  }, [config, onChange])

  // Reset to defaults
  const handleReset = useCallback(() => {
    onChange({
      ...config,
      account_weights: { ...DEFAULT_ACCOUNT_WEIGHTS },
      balance_sheet_weight: 1.0,
      income_statement_weight: 0.9,
    })
  }, [config, onChange])

  const categories: AccountCategory[] = ['asset', 'liability', 'equity', 'revenue', 'expense', 'unknown']
  const balanceSheetCategories: AccountCategory[] = ['asset', 'liability', 'equity']
  const incomeStatementCategories: AccountCategory[] = ['revenue', 'expense']

  return (
    <div className="space-y-4">
      {/* Header with Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-oatmeal-200 font-sans font-medium">
            Weighted Materiality by Account Type
          </h3>
          <p className="text-oatmeal-500 text-xs font-sans mt-1">
            Apply different scrutiny levels to different account categories
          </p>
        </div>
        <button
          onClick={handleToggle}
          disabled={disabled}
          className={`relative w-14 h-8 rounded-full transition-colors ${
            config.enabled ? 'bg-sage-500' : 'bg-obsidian-600'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <div
            className={`absolute top-1 w-6 h-6 rounded-full bg-oatmeal-200 transition-all ${
              config.enabled ? 'left-7' : 'left-1'
            }`}
          />
        </button>
      </div>

      {/* Weighted Configuration (only visible when enabled) */}
      <AnimatePresence>
        {config.enabled && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="space-y-4 pt-4">
              {/* Explanation */}
              <div className="p-3 bg-obsidian-700/30 rounded-lg border border-obsidian-600/50">
                <div className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-sage-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-oatmeal-400 text-xs font-sans">
                    <span className="text-oatmeal-200 font-medium">Higher weights</span> = more scrutiny (lower effective threshold, more items flagged).
                    <span className="text-oatmeal-200 font-medium ml-1">Lower weights</span> = less scrutiny (higher effective threshold, fewer items flagged).
                  </p>
                </div>
              </div>

              {/* Statement Type Weights */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-obsidian-800/50 rounded-lg border border-obsidian-600/30">
                  <label className="block text-oatmeal-300 text-xs font-sans font-medium mb-2">
                    Balance Sheet Weight
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0.1"
                      max="2.0"
                      step="0.1"
                      value={config.balance_sheet_weight}
                      onChange={(e) => handleStatementWeightChange('balance_sheet', parseFloat(e.target.value))}
                      disabled={disabled}
                      className="flex-1 h-2 bg-obsidian-600 rounded-lg appearance-none cursor-pointer accent-sage-500"
                    />
                    <span className="w-12 text-right font-mono text-sm text-oatmeal-300">
                      {config.balance_sheet_weight.toFixed(1)}x
                    </span>
                  </div>
                  <p className="text-oatmeal-500 text-[10px] font-sans mt-1">
                    Assets, Liabilities, Equity
                  </p>
                </div>

                <div className="p-3 bg-obsidian-800/50 rounded-lg border border-obsidian-600/30">
                  <label className="block text-oatmeal-300 text-xs font-sans font-medium mb-2">
                    Income Statement Weight
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="0.1"
                      max="2.0"
                      step="0.1"
                      value={config.income_statement_weight}
                      onChange={(e) => handleStatementWeightChange('income_statement', parseFloat(e.target.value))}
                      disabled={disabled}
                      className="flex-1 h-2 bg-obsidian-600 rounded-lg appearance-none cursor-pointer accent-sage-500"
                    />
                    <span className="w-12 text-right font-mono text-sm text-oatmeal-300">
                      {config.income_statement_weight.toFixed(1)}x
                    </span>
                  </div>
                  <p className="text-oatmeal-500 text-[10px] font-sans mt-1">
                    Revenue, Expenses
                  </p>
                </div>
              </div>

              {/* Per-Category Weights */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="text-oatmeal-300 text-sm font-sans font-medium">
                    Account Category Weights
                  </label>
                  <button
                    onClick={handleReset}
                    disabled={disabled}
                    className="text-oatmeal-500 hover:text-oatmeal-300 text-xs font-sans transition-colors"
                  >
                    Reset to defaults
                  </button>
                </div>

                <div className="space-y-2">
                  {categories.filter(c => c !== 'unknown').map((category, index) => {
                    const weight = config.account_weights[category] || 1.0
                    const effectiveThreshold = getEffectiveThreshold(category)
                    const isExpanded = expandedCategory === category

                    return (
                      <motion.div
                        key={category}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className="bg-obsidian-800/30 rounded-lg border border-obsidian-600/30 overflow-hidden"
                      >
                        <button
                          onClick={() => setExpandedCategory(isExpanded ? null : category)}
                          disabled={disabled}
                          className="w-full p-3 flex items-center justify-between hover:bg-obsidian-700/30 transition-colors disabled:cursor-not-allowed"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-oatmeal-200 text-sm font-sans font-medium">
                              {ACCOUNT_CATEGORY_LABELS[category]}
                            </span>
                            <span className="text-oatmeal-500 text-xs font-mono">
                              {weight.toFixed(1)}x
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sage-400 font-mono text-sm">
                              ${effectiveThreshold.toLocaleString()}
                            </span>
                            <svg
                              className={`w-4 h-4 text-oatmeal-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                        </button>

                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0 }}
                              animate={{ height: 'auto' }}
                              exit={{ height: 0 }}
                              transition={{ duration: 0.15 }}
                              className="overflow-hidden"
                            >
                              <div className="px-3 pb-3 pt-1 border-t border-obsidian-600/30">
                                <p className="text-oatmeal-500 text-xs font-sans mb-3">
                                  {WEIGHT_DESCRIPTIONS[category]}
                                </p>
                                <div className="flex items-center gap-3">
                                  <span className="text-oatmeal-500 text-xs">Low</span>
                                  <input
                                    type="range"
                                    min="0.1"
                                    max="3.0"
                                    step="0.1"
                                    value={weight}
                                    onChange={(e) => handleWeightChange(category, parseFloat(e.target.value))}
                                    disabled={disabled}
                                    className="flex-1 h-2 bg-obsidian-600 rounded-lg appearance-none cursor-pointer accent-sage-500"
                                  />
                                  <span className="text-oatmeal-500 text-xs">High</span>
                                  <input
                                    type="number"
                                    min="0.1"
                                    max="5.0"
                                    step="0.1"
                                    value={weight}
                                    onChange={(e) => handleWeightChange(category, parseFloat(e.target.value) || 1.0)}
                                    disabled={disabled}
                                    className="w-16 px-2 py-1 bg-obsidian-700 border border-obsidian-500 rounded text-oatmeal-200 font-mono text-sm text-center"
                                  />
                                </div>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    )
                  })}
                </div>
              </div>

              {/* Effective Thresholds Preview */}
              <div className="p-4 bg-obsidian-700/50 rounded-lg border border-sage-500/20">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
                  <span className="text-sage-400 text-sm font-sans font-medium">
                    Effective Thresholds (Base: ${baseThreshold.toLocaleString()})
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {categories.filter(c => c !== 'unknown').map((category) => (
                    <div key={category} className="text-center">
                      <p className="text-oatmeal-500 text-xs font-sans">
                        {ACCOUNT_CATEGORY_LABELS[category]}
                      </p>
                      <p className="text-oatmeal-200 font-mono text-sm">
                        ${getEffectiveThreshold(category).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Disabled state explanation */}
      {!config.enabled && (
        <p className="text-oatmeal-500 text-xs font-sans">
          When disabled, a uniform threshold is applied to all accounts regardless of type.
        </p>
      )}
    </div>
  )
}

export default WeightedMaterialityEditor
