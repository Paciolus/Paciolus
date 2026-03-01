'use client'

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { RevenueScoreCard, RevenueTestResultGrid, RevenueDataQualityBadge, FlaggedRevenueTable } from '@/components/revenueTesting'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox, ToolStatePresence, UpgradeGate } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractRevenueProof } from '@/components/shared/proof'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useRevenueTesting } from '@/hooks/useRevenueTesting'
import { useTestingExport } from '@/hooks/useTestingExport'
import type { ContractEvidenceLevel } from '@/types/revenueTesting'
import { isAcceptedFileType, ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

const EVIDENCE_LEVEL_CONFIG: Record<string, { label: string; color: string }> = {
  full: { label: 'Full Contract Data', color: 'bg-sage-50 border-sage-200 text-sage-700' },
  partial: { label: 'Partial Contract Data', color: 'bg-oatmeal-100 border-oatmeal-300 text-oatmeal-700' },
  minimal: { label: 'Minimal Contract Data', color: 'bg-clay-50 border-clay-200 text-clay-700' },
}

function ContractEvidenceBadge({ evidence }: { evidence: ContractEvidenceLevel }) {
  const config = EVIDENCE_LEVEL_CONFIG[evidence.level]
  if (!config) return null

  return (
    <div className={`border rounded-xl p-4 ${config.color}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-serif text-sm font-medium">{config.label}</span>
          <span className="font-mono text-xs opacity-75">
            ({evidence.detected_count}/{evidence.total_contract_fields} fields)
          </span>
        </div>
        <span className="font-mono text-xs">
          ASC 606 / IFRS 15
        </span>
      </div>
      {evidence.detected_fields.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {evidence.detected_fields.map((field) => (
            <span key={field} className="px-2 py-0.5 rounded-sm text-[10px] font-sans bg-surface-card border border-theme">
              {field.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

/**
 * Revenue Testing — Tool 8 (Sprint 106)
 *
 * ISA 240: Presumed fraud risk in revenue recognition.
 * Upload a revenue GL extract for automated testing — up to 16-test battery
 * for revenue anomaly indicators across structural, statistical, advanced, and contract tiers.
 */
export default function RevenueTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { status, result, error, runTests, reset } = useRevenueTesting()
  useCanvasAccentSync(status)
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
            <span className="text-theme-success-text text-sm font-sans font-medium">ISA 240 Revenue Analysis</span>
          </div>
          <h1 className="type-tool-title mb-3">
            Revenue Testing
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a revenue GL extract for automated testing &mdash; up to 16-test battery
            for revenue recognition anomaly indicators per ISA 240 and ASC 606 / IFRS 15.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Revenue Testing requires a verified account. Sign in or create an account to analyze your revenue data." />
        )}

        {/* Tool State Blocks */}
        {isAuthenticated && isVerified && (
          <UpgradeGate toolName="revenue_testing">
          <ToolStatePresence status={status}>
            {/* Upload Zone */}
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
                    <svg className="w-8 h-8 text-content-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <h3 className="type-tool-section mb-2">
                    Upload Revenue GL Extract
                  </h3>
                  <p className="font-sans text-sm text-content-secondary mb-1">
                    Drop your revenue general ledger extract here or click to browse
                  </p>
                  <p className="font-sans text-xs text-content-tertiary">
                    CSV, TSV, TXT, or Excel &mdash; up to 50MB
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
                    Running revenue test battery on {selectedFile?.name}...
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
                <ProofSummaryBar proof={extractRevenueProof(result)} />
                <ProofPanel proof={extractRevenueProof(result)} />

                {/* Score Card */}
                <RevenueScoreCard score={result.composite_score} />

                {/* Contract Evidence Badge */}
                {result.contract_evidence && result.contract_evidence.level !== 'none' && (
                  <ContractEvidenceBadge evidence={result.contract_evidence} />
                )}

                {/* Data Quality */}
                <RevenueDataQualityBadge quality={result.data_quality} />

                {/* Test Results Grid */}
                <div>
                  <h2 className="type-tool-section mb-4">Test Results</h2>
                  <RevenueTestResultGrid results={result.test_results} />
                </div>

                {/* Flagged Revenue Table */}
                <div>
                  <h2 className="type-tool-section mb-4">Flagged Revenue Entries</h2>
                  <FlaggedRevenueTable results={result.test_results} />
                </div>

                {/* Disclaimer */}
                <DisclaimerBox>
                  This automated revenue testing
                  tool provides analytical procedures to assist professional auditors in evaluating revenue recognition
                  anomaly indicators per ISA 240 (presumed fraud risk in revenue recognition). Results are not fraud
                  detection conclusions and should be interpreted in the context of the specific engagement. They are
                  not a substitute for professional judgment or sufficient audit evidence per ISA 500.
                </DisclaimerBox>
              </div>
            )}
          </ToolStatePresence>
          </UpgradeGate>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
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
            <div className="theme-card p-6">
              <div className="text-2xl mb-3">RT-13 to RT-16</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Contract-Aware Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                ASC 606 / IFRS 15: recognition timing, obligation linkage, modification treatment, SSP allocation
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
