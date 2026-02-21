'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox } from '@/components/shared'
import { useAuth } from '@/contexts/AuthContext'
import { FileDropZone } from '@/components/shared'
import { MatchSummaryCard, MatchResultsTable, UnmatchedDocumentsPanel, VarianceDetailCard } from '@/components/threeWayMatch'
import { useThreeWayMatch } from '@/hooks/useThreeWayMatch'
import { useTestingExport } from '@/hooks/useTestingExport'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'

/**
 * Three-Way Match Validator — Tool 7 (Sprint 93)
 *
 * Upload PO, Invoice, and Receipt files for automated matching.
 * Validates AP completeness and detects procurement variances.
 */

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

// =============================================================================
// PAGE
// =============================================================================

export default function ThreeWayMatchPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { status, result, error, runMatch, reset } = useThreeWayMatch()
  useCanvasAccentSync(status)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/three-way-match-memo',
    '/export/csv/three-way-match',
    'three_way_match_memo.pdf',
    'three_way_match_results.csv',
  )
  const [poFile, setPoFile] = useState<File | null>(null)
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null)
  const [receiptFile, setReceiptFile] = useState<File | null>(null)

  const isVerified = user?.is_verified !== false
  const canRun = poFile && invoiceFile && receiptFile && status !== 'loading'

  const handleRunMatch = useCallback(async () => {
    if (!poFile || !invoiceFile || !receiptFile) return
    await runMatch(poFile, invoiceFile, receiptFile)
  }, [poFile, invoiceFile, receiptFile, runMatch])

  const handleNewMatch = useCallback(() => {
    reset()
    setPoFile(null)
    setInvoiceFile(null)
    setReceiptFile(null)
  }, [reset])

  return (
    <main className="min-h-screen bg-surface-page">
      <div className="page-container">
        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-600 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">Automated Matching</span>
          </div>
          <h1 className="font-serif text-4xl text-content-primary mb-3">
            Three-Way Match Validator
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Match purchase orders, invoices, and receipts to validate AP completeness
            and detect procurement variances.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Three-Way Match Validation requires a verified account. Sign in or create a free account to match your procurement documents." />
        )}

        {/* Upload Zone — Only for authenticated verified users */}
        {isAuthenticated && isVerified && status === 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* 3-File Dropzones */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <FileDropZone
                label="Purchase Orders"
                hint="Drop PO file here"
                icon={
                  <svg className="w-8 h-8 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                }
                file={poFile}
                onFileSelect={setPoFile}
                disabled={false}
              />
              <FileDropZone
                label="Invoices"
                hint="Drop invoice file here"
                icon={
                  <svg className="w-8 h-8 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                }
                file={invoiceFile}
                onFileSelect={setInvoiceFile}
                disabled={false}
              />
              <FileDropZone
                label="Receipts / GRN"
                hint="Drop receipt file here"
                icon={
                  <svg className="w-8 h-8 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                  </svg>
                }
                file={receiptFile}
                onFileSelect={setReceiptFile}
                disabled={false}
              />
            </div>

            {/* Run Match Button */}
            <div className="flex items-center justify-center gap-4 mt-6">
              <button
                onClick={handleRunMatch}
                disabled={!canRun}
                className="px-8 py-3 bg-sage-600 rounded-xl text-white font-sans text-sm font-medium hover:bg-sage-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Run Match
              </button>
            </div>

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
                <div className="w-5 h-5 border-2 border-sage-200 border-t-sage-600 rounded-full animate-spin" />
                <span className="font-sans text-content-primary">
                  Matching 3 files...
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
            className="bg-surface-card border border-l-4 border-theme border-l-clay-500 rounded-xl p-6 mb-6 shadow-theme-card"
            role="alert"
          >
            <h3 className="font-serif text-sm text-clay-600 mb-1">Matching Failed</h3>
            <p className="font-sans text-sm text-content-secondary">{error}</p>
            <button
              onClick={handleNewMatch}
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
                  Match results for <span className="text-content-primary">{poFile?.name}</span> + <span className="text-content-primary">{invoiceFile?.name}</span> + <span className="text-content-primary">{receiptFile?.name}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => result && handleExportMemo(result)}
                    disabled={!!exporting}
                    className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors disabled:opacity-40"
                  >
                    {exporting === 'pdf' ? 'Exporting...' : 'Download Memo'}
                  </button>
                  <button
                    onClick={() => result && handleExportCSV(result)}
                    disabled={!!exporting}
                    className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors disabled:opacity-40"
                  >
                    {exporting === 'csv' ? 'Exporting...' : 'Export CSV'}
                  </button>
                  <button
                    onClick={handleNewMatch}
                    className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                  >
                    New Match
                  </button>
                </div>
              </div>
            </div>

            {/* Summary Card */}
            <MatchSummaryCard summary={result.summary} />

            {/* Match Results Table */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Matched Documents</h2>
              <MatchResultsTable
                fullMatches={result.full_matches}
                partialMatches={result.partial_matches}
              />
            </div>

            {/* Variance Detail */}
            {result.variances.length > 0 && (
              <div>
                <h2 className="font-serif text-lg text-content-primary mb-4">Variance Analysis</h2>
                <VarianceDetailCard variances={result.variances} />
              </div>
            )}

            {/* Unmatched Documents */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Unmatched Documents</h2>
              <UnmatchedDocumentsPanel
                unmatchedPOs={result.unmatched_pos}
                unmatchedInvoices={result.unmatched_invoices}
                unmatchedReceipts={result.unmatched_receipts}
              />
            </div>

            <DisclaimerBox>
              This automated three-way match validator
              provides analytical procedures to assist professional auditors. Results should be interpreted in the context
              of the specific engagement and are not a substitute for professional judgment. Matching uses configurable
              thresholds that may require adjustment for specific industries or entity procurement processes.
            </DisclaimerBox>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">Phase 1</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Exact PO# Linkage</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Match invoices and receipts to purchase orders via PO number reference for high-confidence matches.
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">Phase 2</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Fuzzy Fallback</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Unmatched documents are compared using vendor name similarity, amount proximity, and date proximity scoring.
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">Analysis</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Variance Detection</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Quantity, price, amount, and date variances between matched documents with severity classification.
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
