'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { RevenueScoreCard, RevenueTestResultGrid, RevenueDataQualityBadge, FlaggedRevenueTable } from '@/components/revenueTesting'
import { useRevenueTesting } from '@/hooks/useRevenueTesting'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useTestingExport } from '@/hooks/useTestingExport'

/**
 * Revenue Testing — Tool 8 (Sprint 106)
 *
 * ISA 240: Presumed fraud risk in revenue recognition.
 * Upload a revenue GL extract for automated testing — 12-test battery
 * for revenue anomaly indicators across structural, statistical, and advanced tiers.
 */
export default function RevenueTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { status, result, error, runTests, reset } = useRevenueTesting()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/revenue-testing-memo', '/export/csv/revenue-testing',
    'RevenueTesting_Memo.pdf', 'RevenueTesting_Flagged.csv',
  )

  const exportBody = result ? {
    composite_score: result.composite_score,
    test_results: result.test_results,
    data_quality: result.data_quality,
    column_detection: result.column_detection,
    filename: selectedFile?.name.replace(/\.[^.]+$/, '') || 'revenue_testing',
  } : null

  const handleFileUpload = useCallback(async (file: File) => {
    const validTypes = [
      'text/csv',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ]
    const ext = file.name.toLowerCase().split('.').pop()
    if (!validTypes.includes(file.type) && !['csv', 'xlsx', 'xls'].includes(ext || '')) {
      return
    }
    setSelectedFile(file)
    await runTests(file)
  }, [runTests])

  const { isDragging, fileInputRef, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } = useFileUpload(handleFileUpload)

  const handleNewTest = useCallback(() => {
    reset()
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [reset, fileInputRef])

  const isVerified = user?.is_verified !== false

  return (
    <main className="min-h-screen bg-surface-page">
      <div className="pt-24 pb-16 px-6 max-w-5xl mx-auto">
        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-theme-success-bg border border-theme-success-border mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-theme-success-text text-sm font-sans font-medium">ISA 240 Revenue Analysis</span>
          </div>
          <h1 className="font-serif text-4xl text-content-primary mb-3">
            Revenue Testing
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a revenue GL extract for automated testing &mdash; 12-test battery
            for revenue recognition anomaly indicators per ISA 240.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
 className="theme-card rounded-2xl p-8 text-center mb-10"
          >
            <h2 className="font-serif text-xl text-content-primary mb-2">Sign in to get started</h2>
            <p className="font-sans text-content-secondary text-sm mb-6 max-w-md mx-auto">
              Revenue Testing requires a verified account. Sign in or create a free account to analyze your revenue data.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/login"
                className="px-6 py-3 bg-sage-600 border border-sage-600 rounded-lg text-white font-sans text-sm hover:bg-sage-700 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-6 py-3 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
              >
                Create Account
              </Link>
            </div>
          </motion.div>
        )}

        {/* Upload Zone */}
        {isAuthenticated && isVerified && status === 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer
                ${isDragging
                  ? 'border-sage-500 bg-theme-success-bg'
                  : 'border-theme bg-surface-card-secondary hover:border-theme-hover hover:bg-surface-card'
                }`}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
              />
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-oatmeal-100 flex items-center justify-center">
                <svg className="w-8 h-8 text-content-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="font-serif text-lg text-content-primary mb-2">
                Upload Revenue GL Extract
              </h3>
              <p className="font-sans text-sm text-content-secondary mb-1">
                Drop your revenue general ledger extract here or click to browse
              </p>
              <p className="font-sans text-xs text-content-tertiary">
                CSV or Excel (.xlsx) &mdash; up to 50MB
              </p>
            </div>

            {/* Zero-Storage notice */}
            <div className="flex items-center justify-center gap-2 mt-4">
              <svg className="w-4 h-4 text-theme-success-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span className="font-sans text-xs text-content-tertiary">
                Zero-Storage: Your data is processed in-memory and never saved.
              </span>
            </div>
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
                  Running 12-test revenue battery on {selectedFile?.name}...
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
                  Results for <span className="text-content-primary">{selectedFile?.name}</span>
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

            {/* Score Card */}
            <RevenueScoreCard score={result.composite_score} />

            {/* Data Quality */}
            <RevenueDataQualityBadge quality={result.data_quality} />

            {/* Test Results Grid */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Test Results</h2>
              <RevenueTestResultGrid results={result.test_results} />
            </div>

            {/* Flagged Revenue Table */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Flagged Revenue Entries</h2>
              <FlaggedRevenueTable results={result.test_results} />
            </div>

            {/* Disclaimer */}
            <div className="bg-surface-card-secondary border border-theme rounded-xl p-4 mt-8">
              <p className="font-sans text-xs text-content-tertiary leading-relaxed">
                <span className="text-content-secondary font-medium">Disclaimer:</span> This automated revenue testing
                tool provides analytical procedures to assist professional auditors in evaluating revenue recognition
                anomaly indicators per ISA 240 (presumed fraud risk in revenue recognition). Results are not fraud
                detection conclusions and should be interpreted in the context of the specific engagement. They are
                not a substitute for professional judgment or sufficient audit evidence per ISA 500.
              </p>
            </div>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">RT-01 to RT-05</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Large manual entries, year-end concentration, round amounts, sign anomalies, unclassified entries
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">RT-06 to RT-09</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Z-score outliers, trend variance, concentration risk, cut-off risk indicators
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">RT-10 to RT-12</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Advanced Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Benford&apos;s Law analysis, duplicate entry detection, contra-revenue anomalies
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
