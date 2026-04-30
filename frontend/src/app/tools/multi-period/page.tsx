'use client'

import { useCallback, useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useCanvasAccent } from '@/contexts/CanvasAccentContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import {
  AccountMovementTable,
  BudgetSummaryCards,
  CategoryMovementSection,
  fadeIn,
  MOVEMENT_TYPE_LABELS,
  MovementSummaryCards,
  PeriodFileDropZone,
  stagger,
} from '@/components/multiPeriod'
import { DisclaimerBox, GuestCTA, ZeroStorageNotice } from '@/components/shared'
import { Reveal } from '@/components/ui/Reveal'
import {
  type MovementSummaryResponse,
  useMultiPeriodComparison,
  useMultiPeriodMemoExport,
  usePeriodUploads,
} from '@/hooks'

export default function MultiPeriodPage() {
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuthSession()
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId ?? null
  const { comparison, isComparing, isExporting, error: compareError, compareResults, exportCsv, clear } = useMultiPeriodComparison(engagementId)

  const { setAccentState } = useCanvasAccent()
  useEffect(() => {
    if (isComparing) setAccentState('analyze')
    else if (comparison) setAccentState('validate')
    else if (isExporting) setAccentState('export')
    else setAccentState('idle')
  }, [isComparing, isExporting, comparison, setAccentState])

  const isVerified = user?.is_verified !== false

  // Period labels + materiality
  const [priorLabel, setPriorLabel] = useState('Prior Period')
  const [currentLabel, setCurrentLabel] = useState('Current Period')
  const [budgetLabel, setBudgetLabel] = useState('Budget')
  const [materialityThreshold, setMaterialityThreshold] = useState(500)

  // Engagement metadata for PDF memo
  const [clientName, setClientName] = useState('')
  const [fiscalYearEnd, setFiscalYearEnd] = useState('')
  const [practitioner, setPractitioner] = useState('')
  const [reviewer, setReviewer] = useState('')

  // Filters
  const [filterType, setFilterType] = useState('all')
  const [filterSignificance, setFilterSignificance] = useState('all')
  const [filterSearch, setFilterSearch] = useState('')

  const uploads = usePeriodUploads({
    token,
    materialityThreshold,
    engagementId,
    onBeforeUpload: clear,
  })
  const { prior, current, budget, showBudget, anyLoading: anyZoneLoading, canCompare } = uploads

  const { exporting: exportingMemo, exportMemo } = useMultiPeriodMemoExport(token)

  const isProcessing = anyZoneLoading || isComparing
  const hasBudgetData = !!comparison?.budget_label

  const handleCompare = useCallback(async () => {
    if (!prior.result || !current.result) return
    const success = await compareResults(
      prior.result,
      current.result,
      priorLabel,
      currentLabel,
      materialityThreshold,
      token,
      showBudget && budget.result ? budget.result : null,
      budgetLabel,
    )

    if (success && engagement?.engagementId) {
      engagement.refreshToolRuns()
      engagement.triggerLinkToast('Multi-Period Comparison')
    }
  }, [prior.result, current.result, budget.result, priorLabel, currentLabel, budgetLabel, materialityThreshold, token, showBudget, compareResults, engagement])

  const handleExportCsv = useCallback(async () => {
    if (!prior.result || !current.result) return
    await exportCsv(
      prior.result,
      current.result,
      priorLabel,
      currentLabel,
      materialityThreshold,
      token,
      showBudget && budget.result ? budget.result : null,
      budgetLabel,
    )
  }, [prior.result, current.result, budget.result, priorLabel, currentLabel, budgetLabel, materialityThreshold, token, showBudget, exportCsv])

  const handleExportMemo = useCallback(async () => {
    if (!comparison) return
    await exportMemo(comparison, { clientName, fiscalYearEnd, practitioner, reviewer })
  }, [comparison, exportMemo, clientName, fiscalYearEnd, practitioner, reviewer])

  const handleReset = useCallback(() => {
    uploads.reset()
    clear()
    setFilterType('all')
    setFilterSignificance('all')
    setFilterSearch('')
  }, [uploads, clear])

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="pt-24 pb-16 px-6 max-w-6xl mx-auto">
        {/* Hero */}
        <motion.div className="text-center mb-10" initial="hidden" animate="visible" variants={stagger}>
          <motion.div
            className="inline-flex items-center gap-2 bg-sage-50 border border-sage-500/20 rounded-full px-4 py-1.5 mb-6"
            variants={fadeIn}
          >
            <span className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">Multi-Period Comparison</span>
          </motion.div>
          <motion.h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary mb-3" variants={fadeIn}>
            Period-Over-Period Analysis
          </motion.h1>
          <motion.p className="text-content-secondary font-sans max-w-xl mx-auto" variants={fadeIn}>
            Upload two or three trial balance files to compare account movements, detect variances, and analyze budget performance.
          </motion.p>
        </motion.div>

        {!isAuthenticated ? (
          <GuestCTA description="Multi-Period Comparison requires a verified account. Sign in or create an account for Zero-Storage processing." />
        ) : !isVerified ? (
          <div className="max-w-lg mx-auto theme-card rounded-2xl p-10 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-clay-50 border border-clay-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h2 className="text-2xl font-serif font-bold text-content-primary mb-3">Verify Your Email</h2>
            <p className="text-content-secondary font-sans mb-2">
              Multi-Period Comparison requires a verified account.
            </p>
            <p className="text-content-tertiary font-sans text-sm">
              Check your inbox for a verification link, or use the banner above to resend.
            </p>
          </div>
        ) : (
          <>
            {/* Upload Section */}
            <Reveal>
            <section
              className="theme-card p-6 mb-6"
            >
              {/* Period Labels */}
              <div className={`grid gap-4 mb-4 ${showBudget ? 'grid-cols-3' : 'grid-cols-2'}`}>
                <div>
                  <label htmlFor="prior-label" className="block text-xs font-sans text-content-tertiary mb-1">Prior Period Label</label>
                  <input
                    id="prior-label"
                    type="text"
                    value={priorLabel}
                    onChange={(e) => setPriorLabel(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                    placeholder="e.g. FY2024"
                  />
                </div>
                <div>
                  <label htmlFor="current-label" className="block text-xs font-sans text-content-tertiary mb-1">Current Period Label</label>
                  <input
                    id="current-label"
                    type="text"
                    value={currentLabel}
                    onChange={(e) => setCurrentLabel(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                    placeholder="e.g. FY2025"
                  />
                </div>
                {showBudget && (
                  <div>
                    <label htmlFor="budget-label" className="block text-xs font-sans text-content-tertiary mb-1">Budget/Forecast Label</label>
                    <input
                      id="budget-label"
                      type="text"
                      value={budgetLabel}
                      onChange={(e) => setBudgetLabel(e.target.value)}
                      className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                      placeholder="e.g. Budget 2025"
                    />
                  </div>
                )}
              </div>

              {/* Engagement Metadata */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <label htmlFor="client-name" className="block text-xs font-sans text-content-tertiary mb-1">Client Name</label>
                  <input
                    id="client-name"
                    type="text"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                    placeholder="e.g. Meridian Capital Group"
                  />
                </div>
                <div>
                  <label htmlFor="fiscal-year-end" className="block text-xs font-sans text-content-tertiary mb-1">Fiscal Year End</label>
                  <input
                    id="fiscal-year-end"
                    type="text"
                    value={fiscalYearEnd}
                    onChange={(e) => setFiscalYearEnd(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                    placeholder="e.g. December 31, 2025"
                  />
                </div>
                <div>
                  <label htmlFor="practitioner" className="block text-xs font-sans text-content-tertiary mb-1">Engagement Practitioner</label>
                  <input
                    id="practitioner"
                    type="text"
                    value={practitioner}
                    onChange={(e) => setPractitioner(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                    placeholder="Preparer name"
                  />
                </div>
                <div>
                  <label htmlFor="reviewer" className="block text-xs font-sans text-content-tertiary mb-1">Engagement Reviewer</label>
                  <input
                    id="reviewer"
                    type="text"
                    value={reviewer}
                    onChange={(e) => setReviewer(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                    placeholder="Reviewer name"
                  />
                </div>
              </div>

              {/* File Upload — each zone operates independently */}
              <div className={`grid gap-4 mb-4 ${showBudget ? 'grid-cols-3' : 'grid-cols-2'}`}>
                <PeriodFileDropZone label="Prior Period" period={prior} onFileSelect={uploads.handlePriorFile} disabled={isComparing || prior.status === 'loading'} />
                <PeriodFileDropZone label="Current Period" period={current} onFileSelect={uploads.handleCurrentFile} disabled={isComparing || current.status === 'loading'} />
                {showBudget && (
                  <PeriodFileDropZone label="Budget / Forecast" period={budget} onFileSelect={uploads.handleBudgetFile} disabled={isComparing || budget.status === 'loading'} />
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <label htmlFor="materiality-threshold" className="text-xs font-sans text-content-tertiary">Materiality $</label>
                    <input
                      id="materiality-threshold"
                      type="number"
                      value={materialityThreshold}
                      onChange={(e) => setMaterialityThreshold(Number(e.target.value) || 0)}
                      className="w-24 px-2 py-1.5 bg-surface-input border border-theme rounded-lg text-sm font-mono text-content-primary focus:outline-hidden focus:border-sage-500"
                      min={0}
                    />
                  </div>
                  <button
                    onClick={uploads.toggleBudget}
                    className={`px-3 py-1.5 text-xs font-sans rounded-xl border transition-colors ${
                      showBudget
                        ? 'bg-sage-50 border-sage-500/30 text-sage-600'
                        : 'bg-surface-card border-oatmeal-300 text-content-secondary hover:text-content-primary'
                    }`}
                  >
                    {showBudget ? 'Remove Budget' : '+ Add Budget/Forecast'}
                  </button>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 text-sm font-sans text-content-secondary hover:text-content-primary transition-colors"
                  >
                    Reset
                  </button>
                  <button
                    onClick={handleCompare}
                    disabled={!canCompare || isProcessing}
                    className={`px-6 py-2 rounded-xl text-sm font-sans font-medium transition-colors ${
                      canCompare && !isProcessing
                        ? 'bg-sage-600 text-oatmeal-50 hover:bg-sage-700'
                        : 'bg-surface-card-secondary border border-theme text-content-tertiary cursor-not-allowed'
                    }`}
                  >
                    <span aria-live="polite">
                      {isComparing ? 'Comparing...' : showBudget ? 'Compare 3 Periods' : 'Compare Periods'}
                    </span>
                  </button>
                </div>
              </div>

              {compareError && (
                <div className="mt-3 px-4 py-2 border-l-4 border-l-clay-500 bg-clay-50 rounded-sm" role="alert">
                  <span className="text-sm font-sans text-clay-600">{compareError}</span>
                </div>
              )}
            </section>
            </Reveal>

            {/* Results */}
            <AnimatePresence>
              {comparison && (
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  {/* Summary Header + Export */}
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                      <h2 className="font-serif text-xl text-content-primary">
                        {comparison.prior_label} vs {comparison.current_label}
                        {comparison.budget_label && ` vs ${comparison.budget_label}`}
                      </h2>
                      <p className="text-sm font-sans text-content-tertiary">
                        {comparison.total_accounts} accounts analyzed
                        {comparison.dormant_accounts.length > 0 && ` \u00B7 ${comparison.dormant_accounts.length} dormant`}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-sans text-content-tertiary">
                        {comparison.movements_by_significance.material || 0} material · {comparison.movements_by_significance.significant || 0} significant
                      </span>
                      <button
                        onClick={handleExportMemo}
                        disabled={exportingMemo}
                        className="px-4 py-1.5 text-xs font-sans font-medium bg-sage-600 text-oatmeal-50 rounded-xl hover:bg-sage-700 transition-colors disabled:opacity-50"
                      >
                        {exportingMemo ? 'Generating...' : 'Download Memo'}
                      </button>
                      <button
                        onClick={handleExportCsv}
                        disabled={isExporting}
                        className="px-4 py-1.5 text-xs font-sans font-medium bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary hover:bg-surface-card-secondary transition-colors disabled:opacity-50"
                      >
                        {isExporting ? 'Exporting...' : 'Export CSV'}
                      </button>
                    </div>
                  </div>

                  <MovementSummaryCards comparison={comparison} />
                  <BudgetSummaryCards comparison={comparison} />

                  {/* Filters + Movement Table */}
                  <section className="theme-card overflow-hidden">
                    <div className="px-4 py-3 border-b border-theme-divider flex flex-wrap items-center gap-3">
                      <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-xs font-sans text-content-primary focus:outline-hidden focus:border-sage-500"
                      >
                        <option value="all">All Types</option>
                        {Object.entries(MOVEMENT_TYPE_LABELS).map(([k, v]) => (
                          <option key={k} value={k}>{v}</option>
                        ))}
                      </select>
                      <select
                        value={filterSignificance}
                        onChange={(e) => setFilterSignificance(e.target.value)}
                        className="px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-xs font-sans text-content-primary focus:outline-hidden focus:border-sage-500"
                      >
                        <option value="all">All Significance</option>
                        <option value="material">Material</option>
                        <option value="significant">Significant</option>
                        <option value="minor">Minor</option>
                      </select>
                      <input
                        type="text"
                        value={filterSearch}
                        onChange={(e) => setFilterSearch(e.target.value)}
                        placeholder="Search accounts..."
                        className="flex-1 min-w-[150px] px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-xs font-sans text-content-primary placeholder-content-tertiary focus:outline-hidden focus:border-sage-500"
                      />
                    </div>
                    <AccountMovementTable
                      movements={comparison.all_movements}
                      filter={{ type: filterType, significance: filterSignificance, search: filterSearch }}
                      hasBudget={hasBudgetData}
                    />
                  </section>

                  {/* Lead Sheet Grouping */}
                  <section>
                    <h3 className="type-tool-section mb-3">By Lead Sheet</h3>
                    <CategoryMovementSection comparison={comparison} hasBudget={hasBudgetData} />
                  </section>

                  {/* Disclaimer */}
                  <DisclaimerBox>
                    This automated multi-period
                    comparison tool provides analytical procedures to assist professional auditors. Period-over-period
                    movements should be interpreted in the context of the specific engagement and are not a substitute
                    for professional judgment or substantive audit procedures per ISA 520.
                  </DisclaimerBox>

                  {/* Zero-Storage Notice */}
                  <ZeroStorageNotice className="mt-4" />
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </div>
    </main>
  )
}
