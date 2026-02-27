'use client'

import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { useCanvasAccent } from '@/contexts/CanvasAccentContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import {
  PeriodFileDropZone,
  type PeriodState,
  MovementSummaryCards,
  BudgetSummaryCards,
  AccountMovementTable,
  CategoryMovementSection,
  MOVEMENT_TYPE_LABELS,
  fadeIn,
  stagger,
} from '@/components/multiPeriod'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox } from '@/components/shared'
import { useMultiPeriodComparison, type MovementSummaryResponse } from '@/hooks'
import { apiPost } from '@/utils/apiClient'
import { apiDownload, downloadBlob } from '@/utils'

type AuditResultCast = { lead_sheet_grouping?: { summaries: Array<{ accounts: Array<{ account: string; debit: number; credit: number; type: string }> }> } }

export default function MultiPeriodPage() {
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuth()
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

  const [exportingMemo, setExportingMemo] = useState(false)

  const isVerified = user?.is_verified !== false

  // Period state
  const [priorLabel, setPriorLabel] = useState('Prior Period')
  const [currentLabel, setCurrentLabel] = useState('Current Period')
  const [budgetLabel, setBudgetLabel] = useState('Budget')
  const [materialityThreshold, setMaterialityThreshold] = useState(500)
  const [showBudget, setShowBudget] = useState(false)

  const [prior, setPrior] = useState<PeriodState>({ file: null, status: 'idle', result: null, error: null })
  const [current, setCurrent] = useState<PeriodState>({ file: null, status: 'idle', result: null, error: null })
  const [budget, setBudget] = useState<PeriodState>({ file: null, status: 'idle', result: null, error: null })

  // Filters
  const [filterType, setFilterType] = useState('all')
  const [filterSignificance, setFilterSignificance] = useState('all')
  const [filterSearch, setFilterSearch] = useState('')

  const auditFile = useCallback(async (file: File, setPeriod: React.Dispatch<React.SetStateAction<PeriodState>>) => {
    setPeriod(prev => ({ ...prev, file, status: 'loading', result: null, error: null }))

    const formData = new FormData()
    formData.append('file', file)
    formData.append('materiality_threshold', materialityThreshold.toString())

    if (engagementId) {
      formData.append('engagement_id', engagementId.toString())
    }

    try {
      const response = await apiPost('/audit/trial-balance', token, formData)

      if (!response.ok) {
        setPeriod(prev => ({ ...prev, status: 'error', error: response.error || `Audit failed (${response.status})` }))
        return
      }

      setPeriod(prev => ({ ...prev, status: 'success', result: response.data as Record<string, unknown> }))
    } catch {
      setPeriod(prev => ({ ...prev, status: 'error', error: 'Network error during audit' }))
    }
  }, [token, materialityThreshold, engagementId])

  const handlePriorFile = useCallback((file: File) => {
    clear()
    auditFile(file, setPrior)
  }, [auditFile, clear])

  const handleCurrentFile = useCallback((file: File) => {
    clear()
    auditFile(file, setCurrent)
  }, [auditFile, clear])

  const handleBudgetFile = useCallback((file: File) => {
    clear()
    auditFile(file, setBudget)
  }, [auditFile, clear])

  const canCompare = prior.status === 'success' && current.status === 'success' && prior.result && current.result
    && (!showBudget || (budget.status === 'success' && budget.result))
  const isProcessing = prior.status === 'loading' || current.status === 'loading' || budget.status === 'loading' || isComparing

  const hasBudgetData = !!comparison?.budget_label

  const handleCompare = useCallback(async () => {
    if (!prior.result || !current.result) return
    const success = await compareResults(
      prior.result as AuditResultCast,
      current.result as AuditResultCast,
      priorLabel,
      currentLabel,
      materialityThreshold,
      token,
      showBudget && budget.result ? budget.result as AuditResultCast : null,
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
      prior.result as AuditResultCast,
      current.result as AuditResultCast,
      priorLabel,
      currentLabel,
      materialityThreshold,
      token,
      showBudget && budget.result ? budget.result as AuditResultCast : null,
      budgetLabel,
    )
  }, [prior.result, current.result, budget.result, priorLabel, currentLabel, budgetLabel, materialityThreshold, token, showBudget, exportCsv])

  const handleExportMemo = useCallback(async () => {
    if (!comparison || !token) return
    setExportingMemo(true)
    try {
      const strippedSummaries = comparison.lead_sheet_summaries.map(ls => ({
        lead_sheet: ls.lead_sheet,
        lead_sheet_name: ls.lead_sheet_name,
        account_count: ls.account_count,
        prior_total: ls.prior_total,
        current_total: ls.current_total,
        net_change: ls.net_change,
      }))

      const { blob, filename, ok } = await apiDownload(
        '/export/multi-period-memo',
        token,
        {
          method: 'POST',
          body: {
            prior_label: comparison.prior_label,
            current_label: comparison.current_label,
            budget_label: comparison.budget_label || null,
            total_accounts: comparison.total_accounts,
            movements_by_type: comparison.movements_by_type,
            movements_by_significance: comparison.movements_by_significance,
            significant_movements: comparison.significant_movements,
            lead_sheet_summaries: strippedSummaries,
            dormant_account_count: comparison.dormant_accounts.length,
          },
        },
      )
      if (ok && blob) {
        downloadBlob(blob, filename || 'MultiPeriod_Memo.pdf')
      }
    } catch {
      // Silent failure — user sees button reset
    } finally {
      setExportingMemo(false)
    }
  }, [comparison, token])

  const handleReset = useCallback(() => {
    setPrior({ file: null, status: 'idle', result: null, error: null })
    setCurrent({ file: null, status: 'idle', result: null, error: null })
    setBudget({ file: null, status: 'idle', result: null, error: null })
    clear()
    setFilterType('all')
    setFilterSignificance('all')
    setFilterSearch('')
  }, [clear])

  return (
    <main className="min-h-screen bg-surface-page">
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
            <motion.section
              className="theme-card p-6 mb-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
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

              {/* File Upload */}
              <div className={`grid gap-4 mb-4 ${showBudget ? 'grid-cols-3' : 'grid-cols-2'}`}>
                <PeriodFileDropZone label="Prior Period" period={prior} onFileSelect={handlePriorFile} disabled={isProcessing} />
                <PeriodFileDropZone label="Current Period" period={current} onFileSelect={handleCurrentFile} disabled={isProcessing} />
                {showBudget && (
                  <PeriodFileDropZone label="Budget / Forecast" period={budget} onFileSelect={handleBudgetFile} disabled={isProcessing} />
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
                    onClick={() => {
                      setShowBudget(!showBudget)
                      if (showBudget) setBudget({ file: null, status: 'idle', result: null, error: null })
                    }}
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
                        ? 'bg-sage-600 text-white hover:bg-sage-700'
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
            </motion.section>

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
                        {comparison.movements_by_significance.material || 0} material \u00B7 {comparison.movements_by_significance.significant || 0} significant
                      </span>
                      <button
                        onClick={handleExportMemo}
                        disabled={exportingMemo}
                        className="px-4 py-1.5 text-xs font-sans font-medium bg-sage-600 text-white rounded-xl hover:bg-sage-700 transition-colors disabled:opacity-50"
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
