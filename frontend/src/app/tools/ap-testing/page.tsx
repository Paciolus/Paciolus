'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { VerificationBanner } from '@/components/auth'
import { ToolNav } from '@/components/shared'
import { APScoreCard, APTestResultGrid, APDataQualityBadge, FlaggedPaymentTable } from '@/components/apTesting'
import { useAPTesting } from '@/hooks/useAPTesting'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useTestingExport } from '@/hooks/useTestingExport'

/**
 * AP Payment Testing — Full Tool (Sprint 75)
 *
 * Standalone tool for automated AP payment analysis.
 * Upload → Process → Results with 13-test battery.
 */
export default function APTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()
  const { status, result, error, runTests, reset } = useAPTesting()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/ap-testing-memo', '/export/csv/ap-testing',
    'APTesting_Memo.pdf', 'APTesting_Flagged.csv',
  )

  const exportBody = {
    composite_score: result?.composite_score,
    test_results: result?.test_results,
    data_quality: result?.data_quality,
    column_detection: result?.column_detection,
    filename: selectedFile?.name?.replace(/\.[^.]+$/, '') || 'ap_testing',
  }

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
    <main className="min-h-screen bg-gradient-obsidian">
      <ToolNav currentTool="ap-testing" />

      <div className="pt-24 pb-16 px-6 max-w-5xl mx-auto">
        {/* Verification Banner */}
        {isAuthenticated && user && !isVerified && (
          <VerificationBanner />
        )}

        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-500/10 border border-sage-500/20 mb-6">
            <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
            <span className="text-sage-300 text-sm font-sans font-medium">Automated Analysis</span>
          </div>
          <h1 className="font-serif text-4xl text-oatmeal-100 mb-3">
            AP Payment Testing
          </h1>
          <p className="font-sans text-oatmeal-400 text-lg max-w-2xl mx-auto">
            Upload an AP Payment Register for automated testing &mdash; 13-test battery
            for duplicate payments, vendor anomalies, and fraud indicators.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-2xl p-8 text-center mb-10"
          >
            <h2 className="font-serif text-xl text-oatmeal-200 mb-2">Sign in to get started</h2>
            <p className="font-sans text-oatmeal-500 text-sm mb-6 max-w-md mx-auto">
              AP Payment Testing requires a verified account. Sign in or create a free account to analyze your payment data.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/login"
                className="px-6 py-3 bg-sage-500/20 border border-sage-500/40 rounded-lg text-sage-300 font-sans text-sm hover:bg-sage-500/30 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-6 py-3 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors"
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
                  ? 'border-sage-400 bg-sage-500/5'
                  : 'border-obsidian-600/50 bg-obsidian-800/30 hover:border-obsidian-500 hover:bg-obsidian-800/50'
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
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-obsidian-700/50 flex items-center justify-center">
                <svg className="w-8 h-8 text-oatmeal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="font-serif text-lg text-oatmeal-200 mb-2">
                Upload AP Payment Register
              </h3>
              <p className="font-sans text-sm text-oatmeal-500 mb-1">
                Drop your payment register here or click to browse
              </p>
              <p className="font-sans text-xs text-oatmeal-600">
                CSV or Excel (.xlsx) — up to 50MB
              </p>
            </div>

            {/* Zero-Storage notice */}
            <div className="flex items-center justify-center gap-2 mt-4">
              <svg className="w-4 h-4 text-sage-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span className="font-sans text-xs text-oatmeal-600">
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
              <div className="inline-flex items-center gap-3 px-6 py-4 bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl">
                <div className="w-5 h-5 border-2 border-sage-500/30 border-t-sage-400 rounded-full animate-spin" />
                <span className="font-sans text-oatmeal-300">
                  Running 13-test battery on {selectedFile?.name}...
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
            className="bg-obsidian-800/50 border border-l-4 border-clay-500/30 border-l-clay-500 rounded-xl p-6 mb-6"
          >
            <h3 className="font-serif text-sm text-clay-400 mb-1">Analysis Failed</h3>
            <p className="font-sans text-sm text-oatmeal-400">{error}</p>
            <button
              onClick={handleNewTest}
              className="mt-3 px-4 py-2 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors"
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
                <p className="font-sans text-sm text-oatmeal-500">
                  Results for <span className="text-oatmeal-300">{selectedFile?.name}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleExportMemo(exportBody)}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-sage-500/15 border border-sage-500/30 rounded-lg text-sage-300 font-sans text-sm hover:bg-sage-500/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exporting === 'pdf' ? 'Generating...' : 'Download Testing Memo'}
                </button>
                <button
                  onClick={() => handleExportCSV(exportBody)}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exporting === 'csv' ? 'Exporting...' : 'Export Flagged CSV'}
                </button>
                <button
                  onClick={handleNewTest}
                  className="px-4 py-2 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors"
                >
                  New Test
                </button>
              </div>
            </div>

            {/* Score Card */}
            <APScoreCard score={result.composite_score} />

            {/* Data Quality — full width */}
            <APDataQualityBadge quality={result.data_quality} />

            {/* Test Results Grid */}
            <div>
              <h2 className="font-serif text-lg text-oatmeal-200 mb-4">Test Results</h2>
              <APTestResultGrid results={result.test_results} />
            </div>

            {/* Flagged Payment Table */}
            <div>
              <h2 className="font-serif text-lg text-oatmeal-200 mb-4">Flagged Payments</h2>
              <FlaggedPaymentTable results={result.test_results} />
            </div>

            {/* Disclaimer */}
            <div className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl p-4 mt-8">
              <p className="font-sans text-xs text-oatmeal-600 leading-relaxed">
                <span className="text-oatmeal-500 font-medium">Disclaimer:</span> This automated AP payment testing
                tool provides analytical procedures to assist professional auditors. Results should be interpreted in
                the context of the specific engagement and are not a substitute for professional judgment. Duplicate
                detection and fraud indicator tests use standard thresholds that may require adjustment for specific
                industries or entity sizes.
              </p>
            </div>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">T1-T5</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Exact duplicates, near-duplicates, missing fields, round amounts, unusual payment amounts
              </p>
            </div>
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">T6-T10</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Vendor concentration, payment timing, amount clustering, invoice sequence gaps, payment splitting
              </p>
            </div>
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">T11-T13</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Fraud Indicators</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Ghost vendor patterns, rush payments, approval threshold circumvention
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
