'use client'

import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox } from '@/components/shared'
import { ARScoreCard, ARTestResultGrid, ARDataQualityBadge, FlaggedARTable } from '@/components/arAging'
import { useARAging } from '@/hooks/useARAging'
import { useTestingExport } from '@/hooks/useTestingExport'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'
import { ProofSummaryBar, ProofPanel, extractARProof } from '@/components/shared/proof'

const VALID_EXTENSIONS = ['csv', 'xlsx', 'xls']
const VALID_TYPES = [
  'text/csv',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
]

function isValidFile(file: File): boolean {
  const ext = file.name.toLowerCase().split('.').pop()
  return VALID_TYPES.includes(file.type) || VALID_EXTENSIONS.includes(ext || '')
}

/**
 * AR Aging Analysis — Tool 9 (Sprint 109)
 *
 * ISA 500/540: Audit Evidence + Auditing Accounting Estimates.
 * Upload a trial balance (required) and optional AR sub-ledger for
 * automated receivables testing — 11-test battery across structural,
 * statistical, and advanced tiers.
 */
export default function ARAgingPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { status, result, error, runTests, reset } = useARAging()
  useCanvasAccentSync(status)
  const [tbFile, setTbFile] = useState<File | null>(null)
  const [slFile, setSlFile] = useState<File | null>(null)
  const [tbDragging, setTbDragging] = useState(false)
  const [slDragging, setSlDragging] = useState(false)
  const tbInputRef = useRef<HTMLInputElement>(null)
  const slInputRef = useRef<HTMLInputElement>(null)

  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/ar-aging-memo', '/export/csv/ar-aging',
    'ARAging_Memo.pdf', 'ARAging_Flagged.csv',
  )

  const exportBody = result ? {
    composite_score: result.composite_score,
    test_results: result.test_results,
    data_quality: result.data_quality,
    tb_column_detection: result.tb_column_detection,
    sl_column_detection: result.sl_column_detection,
    ar_summary: result.ar_summary,
    filename: tbFile?.name.replace(/\.[^.]+$/, '') || 'ar_aging',
  } : null

  const handleTbFile = useCallback((file: File) => {
    if (!isValidFile(file)) return
    setTbFile(file)
  }, [])

  const handleSlFile = useCallback((file: File) => {
    if (!isValidFile(file)) return
    setSlFile(file)
  }, [])

  const handleRunTests = useCallback(async () => {
    if (!tbFile) return
    await runTests(tbFile, slFile || undefined)
  }, [tbFile, slFile, runTests])

  const handleNewTest = useCallback(() => {
    reset()
    setTbFile(null)
    setSlFile(null)
    if (tbInputRef.current) tbInputRef.current.value = ''
    if (slInputRef.current) slInputRef.current.value = ''
  }, [reset])

  const isVerified = user?.is_verified !== false
  const hasFiles = tbFile !== null
  const skippedTests = result ? result.test_results.filter(t => t.skipped) : []

  return (
    <main className="min-h-screen bg-surface-page">
      <div className="page-container">
        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-theme-success-bg border border-theme-success-border mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-theme-success-text text-sm font-sans font-medium">ISA 500/540 Receivables Analysis</span>
          </div>
          <h1 className="font-serif text-4xl text-content-primary mb-3">
            AR Aging Analysis
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a trial balance and optional AR sub-ledger for automated receivables
            testing &mdash; 11-test battery for aging, allowance, and concentration anomaly indicators.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <GuestCTA description="AR Aging Analysis requires a verified account. Sign in or create a free account to analyze your receivables data." />
        )}

        {/* Dual Upload Zones */}
        {isAuthenticated && isVerified && status === 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* TB Dropzone (Required) */}
              <div
                onDrop={e => { e.preventDefault(); setTbDragging(false); if (e.dataTransfer.files[0]) handleTbFile(e.dataTransfer.files[0]) }}
                onDragOver={e => { e.preventDefault(); setTbDragging(true) }}
                onDragLeave={() => setTbDragging(false)}
                onClick={() => tbInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-200 cursor-pointer
                  ${tbDragging
                    ? 'border-sage-500 bg-theme-success-bg'
                    : tbFile
                      ? 'border-sage-500 bg-theme-success-bg'
                      : 'border-theme bg-surface-card-secondary hover:border-theme-hover hover:bg-surface-card'
                  }`}
              >
                <input
                  ref={tbInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={e => { if (e.target.files?.[0]) handleTbFile(e.target.files[0]) }}
                  className="hidden"
                />
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-oatmeal-100 flex items-center justify-center">
                  {tbFile ? (
                    <svg className="w-6 h-6 text-sage-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-content-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  )}
                </div>
                <h3 className="font-serif text-lg text-content-primary mb-1">
                  Trial Balance <span className="text-clay-600 text-sm">(Required)</span>
                </h3>
                {tbFile ? (
                  <p className="font-sans text-sm text-sage-600">{tbFile.name}</p>
                ) : (
                  <>
                    <p className="font-sans text-sm text-content-secondary mb-1">
                      Drop your trial balance file here
                    </p>
                    <p className="font-sans text-xs text-content-tertiary">CSV or Excel &mdash; up to 50MB</p>
                  </>
                )}
              </div>

              {/* Sub-ledger Dropzone (Optional) */}
              <div
                onDrop={e => { e.preventDefault(); setSlDragging(false); if (e.dataTransfer.files[0]) handleSlFile(e.dataTransfer.files[0]) }}
                onDragOver={e => { e.preventDefault(); setSlDragging(true) }}
                onDragLeave={() => setSlDragging(false)}
                onClick={() => slInputRef.current?.click()}
                className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-200 cursor-pointer
                  ${slDragging
                    ? 'border-sage-500 bg-theme-success-bg'
                    : slFile
                      ? 'border-sage-500 bg-theme-success-bg'
                      : 'border-theme bg-surface-card-secondary hover:border-theme-hover hover:bg-surface-card'
                  }`}
              >
                <input
                  ref={slInputRef}
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={e => { if (e.target.files?.[0]) handleSlFile(e.target.files[0]) }}
                  className="hidden"
                />
                <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-oatmeal-100 flex items-center justify-center">
                  {slFile ? (
                    <svg className="w-6 h-6 text-sage-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-6 h-6 text-content-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  )}
                </div>
                <h3 className="font-serif text-lg text-content-primary mb-1">
                  AR Sub-Ledger <span className="text-content-tertiary text-sm">(Optional)</span>
                </h3>
                {slFile ? (
                  <p className="font-sans text-sm text-sage-600">{slFile.name}</p>
                ) : (
                  <>
                    <p className="font-sans text-sm text-content-secondary mb-1">
                      Add a sub-ledger for full 11-test analysis
                    </p>
                    <p className="font-sans text-xs text-content-tertiary">Customer aging detail with invoice dates</p>
                  </>
                )}
              </div>
            </div>

            {/* Run button */}
            {hasFiles && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-6"
              >
                <button
                  onClick={handleRunTests}
                  className="px-8 py-3 bg-sage-600 border border-sage-600 rounded-xl text-white font-sans text-sm hover:bg-sage-700 transition-colors"
                >
                  Run AR Aging Analysis{slFile ? ' (Full Mode)' : ' (TB-Only)'}
                </button>
                <p className="font-sans text-xs text-content-tertiary mt-2">
                  {slFile ? '11 tests: structural + statistical + advanced' : '4 structural tests (add sub-ledger for full coverage)'}
                </p>
              </motion.div>
            )}

            {/* Zero-Storage notice */}
            <ZeroStorageNotice className="mt-4" />
          </motion.div>
        )}

        {/* Loading State */}
        <AnimatePresence>
          {status === 'loading' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-16"
              aria-live="polite"
            >
 <div className="inline-flex items-center gap-3 px-6 py-4 theme-card">
                <div className="w-5 h-5 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
                <span className="font-sans text-content-primary">
                  Running {slFile ? '11-test' : '4-test'} AR aging battery on {tbFile?.name}...
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error State */}
        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-theme-error-bg border border-theme-error-border border-l-4 border-l-clay-500 rounded-xl p-6 mb-6"
            role="alert"
          >
            <h3 className="font-serif text-sm text-theme-error-text mb-1">Analysis Failed</h3>
            <p className="font-sans text-sm text-content-secondary">{error}</p>
            <button
              onClick={handleNewTest}
              className="mt-3 px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
            >
              Try Again
            </button>
          </motion.div>
        )}

        {/* Results */}
        {status === 'success' && result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {/* Action bar */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="font-sans text-sm text-content-secondary">
                  Results for <span className="text-content-primary">{tbFile?.name}</span>
                  {slFile && (
                    <span className="text-content-secondary"> + <span className="text-content-primary">{slFile.name}</span></span>
                  )}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => exportBody && handleExportMemo(exportBody)}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-sage-600 border border-sage-600 rounded-lg text-white font-sans text-sm hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exporting === 'pdf' ? 'Generating...' : 'Download Testing Memo'}
                </button>
                <button
                  onClick={() => exportBody && handleExportCSV(exportBody)}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exporting === 'csv' ? 'Exporting...' : 'Export Flagged CSV'}
                </button>
                <button
                  onClick={handleNewTest}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                >
                  New Test
                </button>
              </div>
            </div>

            {/* Evidence Summary */}
            <ProofSummaryBar proof={extractARProof(result)} />
            <ProofPanel proof={extractARProof(result)} />

            {/* Score Card */}
            <ARScoreCard score={result.composite_score} />

            {/* Data Quality */}
            <ARDataQualityBadge quality={result.data_quality} />

            {/* Skipped tests notice */}
            {skippedTests.length > 0 && (
              <div className="bg-surface-card-secondary border border-theme rounded-xl p-4">
                <p className="font-sans text-xs text-content-secondary">
                  <span className="text-content-secondary font-medium">{skippedTests.length} tests skipped</span> &mdash; upload
                  an AR sub-ledger to enable full 11-test coverage including aging bucket analysis, customer
                  concentration, and credit limit checks.
                </p>
              </div>
            )}

            {/* Test Results Grid */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Test Results</h2>
              <ARTestResultGrid results={result.test_results} />
            </div>

            {/* Flagged AR Table */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Flagged AR Items</h2>
              <FlaggedARTable results={result.test_results} />
            </div>

            {/* Disclaimer */}
            <DisclaimerBox>
              This automated AR aging analysis
              tool provides analytical procedures to assist professional auditors in evaluating receivables
              anomaly indicators per ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates).
              Results represent data anomalies and are not determinations of allowance sufficiency, net
              realizable value, or expected credit losses. They are not a substitute for professional judgment
              or sufficient audit evidence.
            </DisclaimerBox>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && !hasFiles && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">AR-01 to AR-04</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Sign anomalies, missing allowance, negative aging, unreconciled detail
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">AR-05 to AR-09</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Bucket concentration, past-due, allowance adequacy, customer concentration, DSO trend
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">AR-10 to AR-11</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Advanced Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Roll-forward reconciliation, credit limit breaches
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
