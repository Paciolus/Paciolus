'use client'

import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { VerificationBanner } from '@/components/auth'
import { ToolNav, FileDropZone } from '@/components/shared'
import { MatchSummaryCards, BankRecMatchTable, ReconciliationBridge } from '@/components/bankRec'
import { useBankReconciliation } from '@/hooks/useBankReconciliation'
import { downloadBlob } from '@/lib/downloadBlob'
import type { BankColumnDetectionData } from '@/types/bankRec'

/**
 * Bank Statement Reconciliation — Full Tool (Sprint 78)
 *
 * Dual-file upload (bank statement + GL cash detail),
 * reconciliation via backend API, results display with export.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

function ColumnDetectionWarning({ label, detection }: {
  label: string
  detection: BankColumnDetectionData
}) {
  if (!detection.requires_mapping && detection.detection_notes.length === 0) return null

  return (
    <div className={`border rounded-xl p-4 ${
      detection.requires_mapping
        ? 'bg-clay-50 border-clay-200'
        : 'bg-oatmeal-100 border-theme'
    }`}>
      <div className="flex items-start gap-2">
        <svg className={`w-4 h-4 mt-0.5 flex-shrink-0 ${detection.requires_mapping ? 'text-clay-600' : 'text-content-secondary'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
        <div>
          <p className={`text-sm font-sans font-medium ${detection.requires_mapping ? 'text-clay-600' : 'text-content-primary'}`}>
            {label}: Column detection confidence {(detection.overall_confidence * 100).toFixed(0)}%
          </p>
          {detection.detection_notes.map((note, i) => (
            <p key={i} className="text-xs font-sans text-content-tertiary mt-1">{note}</p>
          ))}
          <p className="text-xs font-sans text-content-tertiary mt-1">
            Detected: date={detection.date_column || 'none'}, amount={detection.amount_column || 'none'},
            description={detection.description_column || 'none'}
          </p>
        </div>
      </div>
    </div>
  )
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function BankRecPage() {
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuth()
  const { status, result, error, reconcile, reset } = useBankReconciliation()
  const [bankFile, setBankFile] = useState<File | null>(null)
  const [ledgerFile, setLedgerFile] = useState<File | null>(null)
  const [exporting, setExporting] = useState(false)
  const [exportingMemo, setExportingMemo] = useState(false)
  const fileResetRef = useRef(0)

  const isVerified = user?.is_verified !== false

  const handleReconcile = useCallback(async () => {
    if (!bankFile || !ledgerFile) return
    await reconcile(bankFile, ledgerFile)
  }, [bankFile, ledgerFile, reconcile])

  const handleNewReconciliation = useCallback(() => {
    reset()
    setBankFile(null)
    setLedgerFile(null)
    fileResetRef.current += 1
  }, [reset])

  const handleExportCSV = useCallback(async () => {
    if (!result || !token) return
    setExporting(true)
    try {
      await downloadBlob({
        url: `${API_URL}/export/csv/bank-rec`,
        body: {
          summary: result.summary,
          matches: result.summary.matches,
          filename: bankFile?.name?.replace(/\.[^.]+$/, '') || 'bank_reconciliation',
        },
        token,
        fallbackFilename: 'BankRec_Export.csv',
      })
    } catch {
      // Silent failure — user sees button reset
    } finally {
      setExporting(false)
    }
  }, [result, token, bankFile, API_URL])

  const handleExportMemo = useCallback(async () => {
    if (!result || !token) return
    setExportingMemo(true)
    try {
      await downloadBlob({
        url: `${API_URL}/export/bank-rec-memo`,
        body: {
          summary: result.summary,
          bank_column_detection: result.bank_column_detection,
          ledger_column_detection: result.ledger_column_detection,
          filename: bankFile?.name?.replace(/\.[^.]+$/, '') || 'bank_reconciliation',
        },
        token,
        fallbackFilename: 'BankRec_Memo.pdf',
      })
    } catch {
      // Silent failure — user sees button reset
    } finally {
      setExportingMemo(false)
    }
  }, [result, token, bankFile, API_URL])

  return (
    <main className="min-h-screen bg-surface-page">
      <ToolNav currentTool="bank-rec" />

      <div className="pt-24 pb-16 px-6 max-w-5xl mx-auto">
        {/* Verification Banner */}
        {isAuthenticated && user && !isVerified && (
          <VerificationBanner />
        )}

        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">Reconciliation Tool</span>
          </div>
          <h1 className="font-serif text-4xl text-content-primary mb-3">
            Bank Statement Reconciliation
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a bank statement and GL cash detail for automated matching &mdash;
            identify outstanding deposits, checks, and reconciling differences.
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
            <p className="font-sans text-content-tertiary text-sm mb-6 max-w-md mx-auto">
              Bank Reconciliation requires a verified account. Sign in or create a free account to reconcile your data.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/login"
                className="px-6 py-3 bg-sage-600 text-white rounded-xl font-sans text-sm font-medium hover:bg-sage-700 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-6 py-3 bg-surface-card border border-oatmeal-300 text-content-primary rounded-xl font-sans text-sm hover:bg-surface-card-secondary transition-colors"
              >
                Create Account
              </Link>
            </div>
          </motion.div>
        )}

        {/* Upload Zone — Only for authenticated verified users */}
        {isAuthenticated && isVerified && status === 'idle' && (
          <motion.div
            key={fileResetRef.current}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
 <div className="theme-card p-6 mb-6">
              <div className="grid grid-cols-2 gap-4 mb-6">
                <FileDropZone
                  label="Bank Statement"
                  hint="Drop bank statement here"
                  file={bankFile}
                  onFileSelect={setBankFile}
                  disabled={false}
                />
                <FileDropZone
                  label="GL Cash Detail"
                  hint="Drop GL cash detail here"
                  file={ledgerFile}
                  onFileSelect={setLedgerFile}
                  disabled={false}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <svg className="w-4 h-4 text-sage-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span className="font-sans text-xs text-content-tertiary">
                    Zero-Storage: Your data is processed in-memory and never saved.
                  </span>
                </div>
                <button
                  onClick={handleReconcile}
                  disabled={!bankFile || !ledgerFile}
                  className={`px-6 py-2.5 rounded-xl text-sm font-sans font-medium transition-colors ${
                    bankFile && ledgerFile
                      ? 'bg-sage-600 text-white hover:bg-sage-700'
                      : 'bg-surface-card-secondary border border-theme text-content-tertiary cursor-not-allowed'
                  }`}
                >
                  Reconcile
                </button>
              </div>
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
                <div className="w-5 h-5 border-2 border-sage-200 border-t-sage-600 rounded-full animate-spin" />
                <span className="font-sans text-content-primary">
                  Reconciling {bankFile?.name} + {ledgerFile?.name}...
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
            className="bg-clay-50 border border-l-4 border-clay-200 border-l-clay-500 rounded-xl p-6 mb-6"
            role="alert"
          >
            <h3 className="font-serif text-sm text-clay-600 mb-1">Reconciliation Failed</h3>
            <p className="font-sans text-sm text-content-secondary">{error}</p>
            <button
              onClick={handleNewReconciliation}
              className="mt-3 px-4 py-2 bg-surface-card border border-oatmeal-300 text-content-primary rounded-xl font-sans text-sm hover:bg-surface-card-secondary transition-colors"
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
                  Results for <span className="text-content-primary">{bankFile?.name}</span>
                  {' '}+ <span className="text-content-primary">{ledgerFile?.name}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleExportMemo}
                  disabled={exportingMemo}
                  className="px-4 py-2 bg-sage-600 text-white rounded-xl font-sans text-sm font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exportingMemo ? 'Generating...' : 'Download Memo'}
                </button>
                <button
                  onClick={handleExportCSV}
                  disabled={exporting}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 text-content-primary rounded-xl font-sans text-sm font-medium hover:bg-surface-card-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exporting ? 'Exporting...' : 'Export CSV'}
                </button>
                <button
                  onClick={handleNewReconciliation}
                  className="px-4 py-2 bg-surface-card border border-oatmeal-300 text-content-primary rounded-xl font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                >
                  New Reconciliation
                </button>
              </div>
            </div>

            {/* Summary Cards */}
            <MatchSummaryCards summary={result.summary} />

            {/* Reconciliation Bridge */}
            <ReconciliationBridge summary={result.summary} />

            {/* Column Detection Warnings */}
            {(result.bank_column_detection.requires_mapping || result.bank_column_detection.detection_notes.length > 0) && (
              <ColumnDetectionWarning label="Bank Statement" detection={result.bank_column_detection} />
            )}
            {(result.ledger_column_detection.requires_mapping || result.ledger_column_detection.detection_notes.length > 0) && (
              <ColumnDetectionWarning label="GL Cash Detail" detection={result.ledger_column_detection} />
            )}

            {/* Match Table */}
            <div>
              <h2 className="font-serif text-lg text-content-primary mb-4">Reconciliation Items</h2>
              <BankRecMatchTable matches={result.summary.matches} />
            </div>

            {/* Disclaimer */}
            <div className="bg-surface-card-secondary border border-theme rounded-xl p-4 mt-8">
              <p className="font-sans text-xs text-content-tertiary leading-relaxed">
                <span className="text-content-secondary font-medium">Disclaimer:</span> This automated bank reconciliation
                tool assists professional auditors by matching bank statement transactions against general ledger entries.
                Results should be reviewed in the context of the specific engagement. Column auto-detection may require
                manual verification for non-standard file formats. Outstanding items should be investigated per ISA 500 /
                PCAOB AS 2301 requirements.
              </p>
            </div>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
 <div className="theme-card p-6">
              <div className="w-10 h-10 bg-sage-50 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Exact Matching</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Matches transactions by amount and date with configurable tolerance. Greedy algorithm processes largest amounts first.
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="w-10 h-10 bg-sage-50 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Auto-Detection</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Intelligent column detection for date, amount, description, and reference fields. Works with most bank statement formats.
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="w-10 h-10 bg-sage-50 rounded-lg flex items-center justify-center mb-3">
                <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="font-serif text-content-primary text-sm mb-2">CSV Export</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Export matched items, outstanding deposits, outstanding checks, and reconciliation summary to workpaper-ready CSV.
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
