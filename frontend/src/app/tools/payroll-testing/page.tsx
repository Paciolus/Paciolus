'use client'

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { PayrollScoreCard, PayrollTestResultGrid, PayrollDataQualityBadge, FlaggedEmployeeTable } from '@/components/payrollTesting'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox, ToolStatePresence, UpgradeGate } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractPayrollProof } from '@/components/shared/proof'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'
import { useFileUpload } from '@/hooks/useFileUpload'
import { usePayrollTesting } from '@/hooks/usePayrollTesting'
import { useTestingExport } from '@/hooks/useTestingExport'
import { isAcceptedFileType, ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

/**
 * Payroll & Employee Testing — Full Tool (Sprint 87)
 *
 * Standalone tool for automated payroll register analysis.
 * Upload -> Process -> Results with 11-test battery.
 * Sprint 88: Added export buttons (PDF memo + CSV).
 * Sprint 125: Migrated to semantic theme tokens (light theme).
 */
export default function PayrollTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { status, result, error, runTests, reset } = usePayrollTesting()
  useCanvasAccentSync(status)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/payroll-testing-memo', '/export/csv/payroll-testing',
    'PayrollTesting_Memo.pdf', 'PayrollTesting_Flagged.csv',
  )

  const exportBody = result ? {
    composite_score: result.composite_score,
    test_results: result.test_results,
    data_quality: result.data_quality,
    column_detection: result.column_detection,
    filename: selectedFile?.name.replace(/\.[^.]+$/, '') || 'payroll_testing',
  } : null

  const handleFileUpload = useCallback(async (file: File) => {
    if (!isAcceptedFileType(file)) return
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
      <div className="page-container">
        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-theme-success-bg border border-theme-success-border mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-theme-success-text text-sm font-sans font-medium">Automated Analysis</span>
          </div>
          <h1 className="type-tool-title mb-3">
            Payroll &amp; Employee Testing
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a Payroll Register for automated testing &mdash; 11-test battery
            for ghost employees, duplicate payments, and statistical anomalies.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Payroll &amp; Employee Testing requires a verified account. Sign in or create an account to analyze your payroll data." />
        )}

        {/* Tool State Blocks */}
        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="payroll_testing">
          <ToolStatePresence status={status}>
            {/* Upload Zone — Only for authenticated verified users */}
            {status === 'idle' && (
              <div>
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
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputRef.current?.click() } }}
                  role="button"
                  tabIndex={0}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_FILE_EXTENSIONS_STRING}
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-oatmeal-100 flex items-center justify-center">
                    <svg className="w-8 h-8 text-content-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                  </div>
                  <h3 className="type-tool-section mb-2">
                    Upload Payroll Register
                  </h3>
                  <p className="font-sans text-sm text-content-secondary mb-1">
                    Drop your payroll register here or click to browse
                  </p>
                  <p className="font-sans text-xs text-content-tertiary">
                    CSV, TSV, TXT, or Excel — up to 50MB
                  </p>
                </div>

                <ZeroStorageNotice className="mt-4" />
              </div>
            )}

            {/* Loading State */}
            {status === 'loading' && (
              <div className="text-center py-16" aria-live="polite">
                <div className="inline-flex items-center gap-3 px-6 py-4 theme-card">
                  <div className="w-5 h-5 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
                  <span className="font-sans text-content-primary">
                    Running 11-test battery on {selectedFile?.name}...
                  </span>
                </div>
              </div>
            )}

            {/* Error State */}
            {status === 'error' && (
              <div
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
              </div>
            )}

            {/* Results */}
            {status === 'success' && result && (
              <div className="space-y-6">
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

                {/* Evidence Summary */}
                <ProofSummaryBar proof={extractPayrollProof(result)} />
                <ProofPanel proof={extractPayrollProof(result)} />

                {/* Score Card */}
                <PayrollScoreCard score={result.composite_score} />

                {/* Data Quality — full width */}
                <PayrollDataQualityBadge quality={result.data_quality} />

                {/* Test Results Grid */}
                <div>
                  <h2 className="type-tool-section mb-4">Test Results</h2>
                  <PayrollTestResultGrid results={result.test_results} />
                </div>

                {/* Flagged Employee Table */}
                <div>
                  <h2 className="type-tool-section mb-4">Flagged Employees</h2>
                  <FlaggedEmployeeTable results={result.test_results} />
                </div>

                <DisclaimerBox>
                  This automated payroll testing
                  tool provides analytical procedures to assist professional auditors. Results should be interpreted in
                  the context of the specific engagement and are not a substitute for professional judgment. Ghost employee
                  indicators and fraud pattern tests use standard thresholds that may require adjustment for specific
                  industries or entity sizes.
                </DisclaimerBox>
              </div>
            )}
          </ToolStatePresence>
          </UpgradeGate>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">PR-T1 to T5</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Duplicate employees, missing fields, round amounts, post-termination payments, check number gaps
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">PR-T6 to T8</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Unusual pay amounts, pay frequency anomalies, Benford&apos;s Law analysis on gross pay
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">PR-T9 to T11</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Fraud Indicators</h3>
              <p className="font-sans text-content-secondary text-xs">
                Ghost employee patterns, duplicate bank accounts/addresses, duplicate tax IDs
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
