'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { VerificationBanner } from '@/components/auth'
import { ToolNav } from '@/components/shared'
import { JEScoreCard, TestResultGrid, GLDataQualityBadge, BenfordChart, FlaggedEntryTable, SamplingPanel } from '@/components/jeTesting'
import { useJETesting } from '@/hooks/useJETesting'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useTestingExport } from '@/hooks/useTestingExport'

/**
 * Journal Entry Testing — Full Tool (Sprint 66)
 *
 * Standalone tool for automated journal entry analysis.
 * Upload → Process → Results with Benford's Law visualization.
 */
export default function JournalEntryTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuth()
  const { status, result, error, runTests, reset } = useJETesting()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/je-testing-memo', '/export/csv/je-testing',
    'JE_Testing_Memo.pdf', 'JE_Flagged_Entries.csv',
  )

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

  const jeExportBody = {
    composite_score: result?.composite_score,
    test_results: result?.test_results,
    data_quality: result?.data_quality,
    column_detection: result?.column_detection ?? null,
    multi_currency_warning: result?.multi_currency_warning ?? null,
    benford_result: result?.benford_result ?? null,
    filename: selectedFile?.name || 'je_testing',
  }

  const isVerified = user?.is_verified !== false

  return (
    <main className="min-h-screen bg-surface-page">
      <ToolNav currentTool="je-testing" />

      <div className="pt-24 pb-16 px-6 max-w-5xl mx-auto">
        {/* Verification Banner */}
        {isAuthenticated && user && !isVerified && (
          <VerificationBanner />
        )}

        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">Automated Analysis</span>
          </div>
          <h1 className="font-serif text-4xl text-content-primary mb-3">
            Journal Entry Testing
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a General Ledger extract for automated testing — Benford&apos;s Law,
            structural validation, and statistical anomaly detection.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-surface-card border border-theme rounded-2xl p-8 text-center mb-10 shadow-theme-card"
          >
            <h2 className="font-serif text-xl text-content-primary mb-2">Sign in to get started</h2>
            <p className="font-sans text-content-tertiary text-sm mb-6 max-w-md mx-auto">
              Journal Entry Testing requires a verified account. Sign in or create a free account to analyze your GL data.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/login"
                className="px-6 py-3 bg-sage-600 border border-sage-600 rounded-xl text-white font-sans text-sm hover:bg-sage-700 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-6 py-3 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
              >
                Create Account
              </Link>
            </div>
          </motion.div>
        )}

        {/* Upload Zone — Only for authenticated verified users */}
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
                  ? 'border-sage-500 bg-sage-50'
                  : 'bg-surface-card-secondary border-theme hover:border-theme-hover hover:bg-surface-card'
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
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-surface-card-secondary flex items-center justify-center">
                <svg className="w-8 h-8 text-content-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="font-serif text-lg text-content-primary mb-2">
                Upload General Ledger Extract
              </h3>
              <p className="font-sans text-sm text-content-tertiary mb-1">
                Drop your GL file here or click to browse
              </p>
              <p className="font-sans text-xs text-content-tertiary">
                CSV or Excel (.xlsx) — up to 50MB
              </p>
            </div>

            {/* Zero-Storage notice */}
            <div className="flex items-center justify-center gap-2 mt-4">
              <svg className="w-4 h-4 text-sage-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
            >
              <div className="inline-flex items-center gap-3 px-6 py-4 bg-surface-card border border-theme rounded-xl shadow-theme-card">
                <div className="w-5 h-5 border-2 border-sage-200 border-t-sage-500 rounded-full animate-spin" />
                <span className="font-sans text-content-primary">
                  Running 18-test battery on {selectedFile?.name}...
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
          >
            <h3 className="font-serif text-sm text-clay-700 mb-1">Analysis Failed</h3>
            <p className="font-sans text-sm text-content-secondary">{error}</p>
            <button
              onClick={handleNewTest}
              className="mt-3 px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
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
                <p className="font-sans text-sm text-content-tertiary">
                  Results for <span className="text-content-primary">{selectedFile?.name}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleExportMemo({ ...jeExportBody, client_name: null, period_tested: null, prepared_by: null, reviewed_by: null, workpaper_date: null })}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-sage-600 text-white rounded-xl font-sans text-sm hover:bg-sage-700 transition-colors disabled:opacity-50"
                >
                  {exporting === 'pdf' ? 'Generating...' : 'Download Testing Memo'}
                </button>
                <button
                  onClick={() => handleExportCSV(jeExportBody)}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors disabled:opacity-50"
                >
                  {exporting === 'csv' ? 'Exporting...' : 'Export Flagged CSV'}
                </button>
                <button
                  onClick={handleNewTest}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                >
                  New Test
                </button>
              </div>
            </div>

            {/* Multi-currency warning */}
            {result.multi_currency_warning && (
              <div className="bg-surface-card border border-theme border-l-4 border-l-oatmeal-400 rounded-xl p-4 shadow-theme-card">
                <p className="font-sans text-sm text-content-primary">
                  {result.multi_currency_warning.warning_message}
                </p>
              </div>
            )}

            {/* Score Card */}
            <JEScoreCard score={result.composite_score} />

            {/* Data Quality + Benford side by side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GLDataQualityBadge quality={result.data_quality} />
              {result.benford_result && (
                <BenfordChart benford={result.benford_result} />
              )}
            </div>

            {/* Test Results Grid */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Test Results</h2>
              <TestResultGrid results={result.test_results} />
            </div>

            {/* Flagged Entry Table */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Flagged Entries</h2>
              <FlaggedEntryTable results={result.test_results} />
            </div>

            {/* Stratified Sampling */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Stratified Sampling</h2>
              <SamplingPanel file={selectedFile} token={token} />
            </div>

            {/* Disclaimer */}
            <div className="bg-surface-card-secondary border border-theme rounded-xl p-4 mt-8">
              <p className="font-sans text-xs text-content-tertiary leading-relaxed">
                <span className="text-content-secondary font-medium">Disclaimer:</span> This automated journal entry testing
                tool provides analytical procedures to assist professional auditors. Results should be interpreted in
                the context of the specific engagement and are not a substitute for professional judgment. Statistical
                tests use standard thresholds that may require adjustment for specific industries or entity sizes.
              </p>
            </div>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="bg-surface-card border border-theme rounded-xl p-6 shadow-theme-card">
              <div className="text-2xl mb-3">T1-T5</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Unbalanced entries, missing fields, duplicates, round amounts, unusual amounts
              </p>
            </div>
            <div className="bg-surface-card border border-theme rounded-xl p-6 shadow-theme-card">
              <div className="text-2xl mb-3">T6-T8</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Benford&apos;s Law analysis, weekend postings, month-end clustering
              </p>
            </div>
            <div className="bg-surface-card border border-theme rounded-xl p-6 shadow-theme-card">
              <div className="text-2xl mb-3">T9-T18</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Advanced Tests</h3>
              <p className="font-sans text-content-tertiary text-xs">
                User analysis, after-hours, backdating, reciprocal entries, threshold splitting, frequency anomalies
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
