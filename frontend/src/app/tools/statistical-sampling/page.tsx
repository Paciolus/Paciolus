'use client'

import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { useCanvasAccent } from '@/contexts/CanvasAccentContext'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox } from '@/components/shared'
import {
  SamplingDesignPanel,
  SampleSelectionTable,
  SamplingEvaluationPanel,
  SamplingResultCard,
} from '@/components/statisticalSampling'
import { useStatisticalSampling } from '@/hooks/useStatisticalSampling'
import { useTestingExport } from '@/hooks/useTestingExport'

/**
 * Statistical Sampling — Tool 12 (Sprint 270)
 *
 * ISA 530 / PCAOB AS 2315: Two-phase sampling workflow.
 * Phase 1 (Design): Upload population + configure parameters -> select sample items
 * Phase 2 (Evaluate): Upload completed sample with audited amounts -> Pass/Fail
 */

type SamplingTab = 'design' | 'evaluate'

export default function StatisticalSamplingPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const {
    designStatus, designResult, designError, runDesign, resetDesign,
    evalStatus, evalResult, evalError, runEvaluation, resetEvaluation,
  } = useStatisticalSampling()

  const { setAccentState } = useCanvasAccent()
  useEffect(() => {
    if (designStatus === 'loading' || evalStatus === 'loading') setAccentState('analyze')
    else if (designStatus === 'success' || evalStatus === 'success') setAccentState('validate')
    else setAccentState('idle')
  }, [designStatus, evalStatus, setAccentState])

  const [activeTab, setActiveTab] = useState<SamplingTab>('design')

  const isVerified = user?.is_verified !== false

  // Export hooks — design memo, evaluation memo, selection CSV
  const {
    exporting: designExporting,
    handleExportMemo: handleDesignMemo,
    handleExportCSV: handleDesignCSV,
  } = useTestingExport(
    '/export/sampling-design-memo',
    '/export/csv/sampling-selection',
    'SamplingDesign_Memo.pdf',
    'SamplingSelection.csv',
  )

  const {
    exporting: evalExporting,
    handleExportMemo: handleEvalMemo,
  } = useTestingExport(
    '/export/sampling-evaluation-memo',
    '/export/csv/sampling-selection', // unused for eval but required by hook
    'SamplingEvaluation_Memo.pdf',
    'SamplingSelection.csv',
  )

  // Build export body for design memo
  const handleExportDesignMemo = useCallback(() => {
    if (!designResult) return
    handleDesignMemo({
      method: designResult.method,
      confidence_level: designResult.confidence_level,
      confidence_factor: designResult.confidence_factor,
      tolerable_misstatement: designResult.tolerable_misstatement,
      expected_misstatement: designResult.expected_misstatement,
      population_size: designResult.population_size,
      population_value: designResult.population_value,
      sampling_interval: designResult.sampling_interval,
      calculated_sample_size: designResult.calculated_sample_size,
      actual_sample_size: designResult.actual_sample_size,
      high_value_count: designResult.high_value_count,
      high_value_total: designResult.high_value_total,
      remainder_count: designResult.remainder_count,
      remainder_sample_size: designResult.remainder_sample_size,
      strata_summary: designResult.strata_summary,
      filename: 'sampling_design',
    })
  }, [designResult, handleDesignMemo])

  // Build export body for selection CSV
  const handleExportSelectionCSV = useCallback(() => {
    if (!designResult) return
    handleDesignCSV({
      selected_items: designResult.selected_items,
      method: designResult.method,
      population_size: designResult.population_size,
      population_value: designResult.population_value,
      filename: 'sampling_selection',
    })
  }, [designResult, handleDesignCSV])

  // Build export body for evaluation memo
  const handleExportEvalMemo = useCallback(() => {
    if (!evalResult) return
    handleEvalMemo({
      method: evalResult.method,
      confidence_level: evalResult.confidence_level,
      tolerable_misstatement: evalResult.tolerable_misstatement,
      expected_misstatement: evalResult.expected_misstatement,
      population_value: evalResult.population_value,
      sample_size: evalResult.sample_size,
      sample_value: evalResult.sample_value,
      errors_found: evalResult.errors_found,
      total_misstatement: evalResult.total_misstatement,
      projected_misstatement: evalResult.projected_misstatement,
      basic_precision: evalResult.basic_precision,
      incremental_allowance: evalResult.incremental_allowance,
      upper_error_limit: evalResult.upper_error_limit,
      conclusion: evalResult.conclusion,
      conclusion_detail: evalResult.conclusion_detail,
      errors: evalResult.errors,
      taintings_ranked: evalResult.taintings_ranked,
      design_result: designResult ? {
        method: designResult.method,
        population_size: designResult.population_size,
        population_value: designResult.population_value,
        actual_sample_size: designResult.actual_sample_size,
        sampling_interval: designResult.sampling_interval,
        strata_summary: designResult.strata_summary,
      } : null,
      filename: 'sampling_evaluation',
    })
  }, [evalResult, designResult, handleEvalMemo])

  // Switch to evaluate tab (auto-navigate after design)
  const handleSwitchToEvaluate = useCallback(() => {
    setActiveTab('evaluate')
  }, [])

  // Reset handlers
  const handleNewDesign = useCallback(() => {
    resetDesign()
  }, [resetDesign])

  const handleNewEvaluation = useCallback(() => {
    resetEvaluation()
  }, [resetEvaluation])

  return (
    <main className="min-h-screen bg-surface-page">
      <div className="page-container">
        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-theme-success-bg border border-theme-success-border mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-theme-success-text text-sm font-sans font-medium">ISA 530 / PCAOB AS 2315</span>
          </div>
          <h1 className="type-tool-title mb-3">
            Statistical Sampling
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Design statistically valid audit samples and evaluate results &mdash;
            Monetary Unit Sampling (MUS) and simple random selection with Stringer bound evaluation.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Statistical Sampling requires a verified account. Sign in or create a free account to design and evaluate audit samples." />
        )}

        {/* Authenticated Content */}
        {isAuthenticated && (
          <>
            {/* Tab Navigation */}
            <div className="flex gap-1 p-1 rounded-xl bg-surface-card-secondary mb-8 max-w-md mx-auto">
              <button
                onClick={() => setActiveTab('design')}
                className={`flex-1 px-4 py-2.5 rounded-lg font-sans text-sm font-medium transition-all duration-200 ${
                  activeTab === 'design'
                    ? 'bg-surface-card text-content-primary shadow-sm'
                    : 'text-content-tertiary hover:text-content-secondary'
                }`}
              >
                1. Design Sample
                {designStatus === 'success' && (
                  <span className="ml-2 inline-block w-2 h-2 bg-sage-500 rounded-full" />
                )}
              </button>
              <button
                onClick={() => setActiveTab('evaluate')}
                className={`flex-1 px-4 py-2.5 rounded-lg font-sans text-sm font-medium transition-all duration-200 ${
                  activeTab === 'evaluate'
                    ? 'bg-surface-card text-content-primary shadow-sm'
                    : 'text-content-tertiary hover:text-content-secondary'
                }`}
              >
                2. Evaluate Results
                {evalStatus === 'success' && (
                  <span className="ml-2 inline-block w-2 h-2 bg-sage-500 rounded-full" />
                )}
              </button>
            </div>

            {/* Tab Content */}
            <AnimatePresence mode="wait">
              {activeTab === 'design' && (
                <motion.div
                  key="design"
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.15 }}
                >
                  {/* Design: Idle or Loading → show design panel */}
                  {(designStatus === 'idle' || designStatus === 'loading' || designStatus === 'error') && (
                    <SamplingDesignPanel
                      status={designStatus}
                      error={designError}
                      onRun={runDesign}
                      isVerified={isVerified}
                    />
                  )}

                  {/* Design: Success → show results */}
                  {designStatus === 'success' && designResult && (
                    <div className="space-y-6">
                      {/* Action bar */}
                      <div className="flex items-center justify-between flex-wrap gap-3">
                        <p className="font-sans text-sm text-content-secondary">
                          Sample designed: <span className="font-mono text-content-primary">{designResult.actual_sample_size} items</span> selected from population of {designResult.population_size.toLocaleString()}
                        </p>
                        <div className="flex items-center gap-3">
                          <button
                            onClick={handleSwitchToEvaluate}
                            className="px-4 py-2 bg-sage-600 border border-sage-600 rounded-lg text-white font-sans text-sm hover:bg-sage-700 transition-colors"
                          >
                            Proceed to Evaluation
                          </button>
                          <button
                            onClick={handleNewDesign}
                            className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                          >
                            New Design
                          </button>
                        </div>
                      </div>

                      <SampleSelectionTable
                        result={designResult}
                        onExportCSV={handleExportSelectionCSV}
                        onExportMemo={handleExportDesignMemo}
                        exporting={designExporting !== null}
                      />
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === 'evaluate' && (
                <motion.div
                  key="evaluate"
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 12 }}
                  transition={{ duration: 0.15 }}
                >
                  {/* Evaluate: Idle or Loading → show evaluation panel */}
                  {(evalStatus === 'idle' || evalStatus === 'loading' || evalStatus === 'error') && (
                    <SamplingEvaluationPanel
                      status={evalStatus}
                      error={evalError}
                      designResult={designResult}
                      onRun={runEvaluation}
                      isVerified={isVerified}
                    />
                  )}

                  {/* Evaluate: Success → show results */}
                  {evalStatus === 'success' && evalResult && (
                    <div className="space-y-6">
                      {/* Action bar */}
                      <div className="flex items-center justify-end gap-3">
                        <button
                          onClick={handleNewEvaluation}
                          className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                        >
                          New Evaluation
                        </button>
                      </div>

                      <SamplingResultCard
                        result={evalResult}
                        onExportMemo={handleExportEvalMemo}
                        exporting={evalExporting !== null}
                      />
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Disclaimer */}
            <div className="mt-12">
              <DisclaimerBox>
                This statistical sampling tool provides sample design and evaluation
                calculations to assist professional auditors in substantive testing per ISA 530 (Audit Sampling)
                and PCAOB AS 2315 (Audit Sampling). Monetary Unit Sampling uses Poisson-based confidence factors
                and Stringer bound evaluation. Results should be interpreted in the context of the specific
                engagement and are not a substitute for professional judgment or sufficient audit evidence per ISA 500.
              </DisclaimerBox>
            </div>

            {/* Info cards for idle design state */}
            {designStatus === 'idle' && activeTab === 'design' && isVerified && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                <div className="theme-card p-6">
                  <div className="text-2xl mb-3 font-serif text-sage-500">MUS</div>
                  <h3 className="font-serif text-content-primary text-sm mb-2">Monetary Unit Sampling</h3>
                  <p className="font-sans text-content-secondary text-xs">
                    Probability-proportional-to-size selection. Each dollar is a sampling unit.
                    Optimal for overstatement testing.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <div className="text-2xl mb-3 font-serif text-sage-500">SRS</div>
                  <h3 className="font-serif text-content-primary text-sm mb-2">Simple Random Sampling</h3>
                  <p className="font-sans text-content-secondary text-xs">
                    Equal probability selection using CSPRNG. Optional sample size override
                    for non-statistical sampling plans.
                  </p>
                </div>
                <div className="theme-card p-6">
                  <div className="text-2xl mb-3 font-serif text-sage-500">Eval</div>
                  <h3 className="font-serif text-content-primary text-sm mb-2">Stringer Bound Evaluation</h3>
                  <p className="font-sans text-content-secondary text-xs">
                    Upper Error Limit calculation: basic precision + projected misstatement +
                    incremental allowance vs tolerable misstatement.
                  </p>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}
