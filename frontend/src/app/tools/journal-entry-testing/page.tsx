'use client'

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { JEScoreCard, TestResultGrid, GLDataQualityBadge, BenfordChart, FlaggedEntryTable, SamplingPanel } from '@/components/jeTesting'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox, ToolStatePresence, ToolSettingsDrawer, Citation, CitationFooter } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractJEProof } from '@/components/shared/proof'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useJETesting } from '@/hooks/useJETesting'
import { useTestingExport } from '@/hooks/useTestingExport'
import { isAcceptedFileType, ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

/**
 * Journal Entry Testing — Full Tool (Sprint 66)
 *
 * Standalone tool for automated journal entry analysis.
 * Upload → Process → Results with Benford's Law visualization.
 */
export default function JournalEntryTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuthSession()
  const { status, result, error, runTests, reset } = useJETesting()
  useCanvasAccentSync(status)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/je-testing-memo', '/export/csv/je-testing',
    'JE_Testing_Memo.pdf', 'JE_Flagged_Entries.csv',
  )

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

  const jeExportBody = result ? {
    composite_score: result.composite_score,
    test_results: result.test_results,
    data_quality: result.data_quality,
    column_detection: result.column_detection ?? null,
    multi_currency_warning: result.multi_currency_warning ?? null,
    benford_result: result.benford_result ?? null,
    filename: selectedFile?.name || 'je_testing',
  } : null

  const isVerified = user?.is_verified !== false
  const [settingsOpen, setSettingsOpen] = useState(false)

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        {/* Hero Header */}
        <div className="text-center mb-10 relative">
          {isAuthenticated && isVerified && (
            <button
              onClick={() => setSettingsOpen(true)}
              className="absolute right-0 top-0 p-2 rounded-lg text-content-tertiary hover:text-content-primary hover:bg-surface-card-secondary transition-colors"
              aria-label="Open testing settings"
              title="Testing settings"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          )}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-50 border border-sage-200 mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-sage-700 text-sm font-sans font-medium">ISA 240 / PCAOB AS 2401</span>
          </div>
          <h1 className="type-tool-title mb-3">
            Journal Entry Testing
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a General Ledger extract for automated testing — Benford&apos;s Law,
            structural validation, and statistical anomaly detection.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Journal Entry Testing requires a verified account. Sign in or create an account to analyze your GL data." />
        )}

        {/* State Choreography — Upload/Loading/Error/Results */}
        {isAuthenticated && isVerified && (
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
                      ? 'border-sage-500 bg-sage-50'
                      : 'bg-surface-card-secondary border-theme hover:border-theme-hover hover:bg-surface-card'
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
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-surface-card-secondary flex items-center justify-center">
                    <svg className="w-8 h-8 text-content-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                  </div>
                  <h3 className="type-tool-section mb-2">
                    Upload General Ledger Extract
                  </h3>
                  <p className="font-sans text-sm text-content-tertiary mb-1">
                    Drop your GL file here or click to browse
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
                  <div className="w-5 h-5 border-2 border-sage-200 border-t-sage-500 rounded-full animate-spin" />
                  <span className="font-sans text-content-primary">
                    Running 19-test battery on {selectedFile?.name}...
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
                <h3 className="font-serif text-sm text-clay-700 mb-1">Analysis Failed</h3>
                <p className="font-sans text-sm text-content-secondary">{error}</p>
                <button
                  onClick={handleNewTest}
                  className="mt-3 px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
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
                <p className="font-sans text-sm text-content-tertiary">
                  Results for <span className="text-content-primary">{selectedFile?.name}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => jeExportBody && handleExportMemo({ ...jeExportBody, client_name: null, period_tested: null, prepared_by: null, reviewed_by: null, workpaper_date: null })}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-sage-600 text-white rounded-xl font-sans text-sm hover:bg-sage-700 transition-colors disabled:opacity-50"
                >
                  {exporting === 'pdf' ? 'Generating...' : 'Download Testing Memo'}
                </button>
                <button
                  onClick={() => jeExportBody && handleExportCSV(jeExportBody)}
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

            {/* Evidence Summary */}
            <ProofSummaryBar proof={extractJEProof(result)} />
            <ProofPanel proof={extractJEProof(result)} />

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
              <h2 className="type-tool-section mb-4">Test Results</h2>
              <TestResultGrid results={result.test_results} />
            </div>

            {/* Flagged Entry Table */}
            <div>
              <h2 className="type-tool-section mb-4">Flagged Entries</h2>
              <FlaggedEntryTable results={result.test_results} />
            </div>

            {/* Stratified Sampling */}
            <div>
              <h2 className="type-tool-section mb-4">Stratified Sampling</h2>
              <SamplingPanel file={selectedFile} token={token} />
            </div>

            {/* Disclaimer */}
            <DisclaimerBox>
              This automated journal entry testing
              tool provides analytical procedures to assist professional auditors per <Citation code="ISA 240" /> and <Citation code="ISA 530" />.
              Results should be interpreted in the context of the specific engagement and are not a substitute for
              professional judgment or sufficient audit evidence per <Citation code="ISA 500" />.
            </DisclaimerBox>
            <CitationFooter standards={['ISA 240', 'ISA 500', 'ISA 530']} />
              </div>
            )}
          </ToolStatePresence>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">5 Tests</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Unbalanced entries, missing fields, duplicates, round amounts, unusual amounts
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">3 Tests</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-content-tertiary text-xs">
                Benford&apos;s Law analysis, weekend postings, month-end clustering
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">10 Tests</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Advanced Tests</h3>
              <p className="font-sans text-content-tertiary text-xs">
                User analysis, after-hours, backdating, reciprocal entries, threshold splitting, frequency anomalies
              </p>
            </div>
          </div>
        )}
      </div>

      <ToolSettingsDrawer toolKey="je" open={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </main>
  )
}
