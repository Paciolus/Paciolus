'use client'

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { InventoryScoreCard, InventoryTestResultGrid, InventoryDataQualityBadge, FlaggedInventoryTable } from '@/components/inventoryTesting'
import { GuestCTA, ZeroStorageNotice, DisclaimerBox, ToolStatePresence } from '@/components/shared'
import { ProofSummaryBar, ProofPanel, extractInventoryProof } from '@/components/shared/proof'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useInventoryTesting } from '@/hooks/useInventoryTesting'
import { useTestingExport } from '@/hooks/useTestingExport'
import { isAcceptedFileType, ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

/**
 * Inventory Testing — Tool 11 (Sprint 119)
 *
 * IAS 2 / ISA 501 / ISA 540: Inventory existence, completeness, and valuation.
 * Upload an inventory register for automated testing — 9-test battery
 * for inventory anomaly indicators across structural, statistical, and advanced tiers.
 */
export default function InventoryTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { status, result, error, runTests, reset } = useInventoryTesting()
  useCanvasAccentSync(status)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/inventory-memo', '/export/csv/inventory',
    'InventoryTesting_Memo.pdf', 'InventoryTesting_Flagged.csv',
  )

  const exportBody = result ? {
    composite_score: result.composite_score,
    test_results: result.test_results,
    data_quality: result.data_quality,
    column_detection: result.column_detection,
    filename: selectedFile?.name.replace(/\.[^.]+$/, '') || 'inventory_testing',
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
            <span className="text-theme-success-text text-sm font-sans font-medium">IAS 2 / ISA 501 Inventory Analysis</span>
          </div>
          <h1 className="type-tool-title mb-3">
            Inventory Testing
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload an inventory register for automated testing &mdash; 9-test battery
            for inventory anomaly indicators per IAS 2 and ISA 501.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <GuestCTA description="Inventory Testing requires a verified account. Sign in or create a free account to analyze your inventory register." />
        )}

        {/* State blocks */}
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
                    Upload Inventory Register
                  </h3>
                  <p className="font-sans text-sm text-content-secondary mb-1">
                    Drop your inventory register here or click to browse
                  </p>
                  <p className="font-sans text-xs text-content-tertiary">
                    CSV or Excel (.xlsx) &mdash; up to 50MB
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
                    Running 9-test inventory battery on {selectedFile?.name}...
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
                <ProofSummaryBar proof={extractInventoryProof(result)} />
                <ProofPanel proof={extractInventoryProof(result)} />

                {/* Score Card */}
                <InventoryScoreCard score={result.composite_score} />

                {/* Data Quality */}
                <InventoryDataQualityBadge quality={result.data_quality} />

                {/* Test Results Grid */}
                <div>
                  <h2 className="type-tool-section mb-4">Test Results</h2>
                  <InventoryTestResultGrid results={result.test_results} />
                </div>

                {/* Flagged Inventory Table */}
                <div>
                  <h2 className="type-tool-section mb-4">Flagged Inventory Items</h2>
                  <FlaggedInventoryTable results={result.test_results} />
                </div>

                <DisclaimerBox>
                  This automated inventory testing
                  tool provides analytical procedures to assist professional auditors in evaluating inventory register
                  anomaly indicators per IAS 2 (Inventories), ISA 501 (Audit Evidence &mdash; Specific Considerations),
                  and ISA 540 (Auditing Accounting Estimates).
                  Results are not NRV adequacy conclusions or obsolescence determinations and should be interpreted
                  in the context of the specific engagement. They are not a substitute for professional judgment or
                  sufficient audit evidence per ISA 500.
                </DisclaimerBox>
              </div>
            )}
          </ToolStatePresence>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">IN-01 to IN-03</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Missing fields, negative values, extended value mismatch
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">IN-04 to IN-07</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Unit cost outliers, quantity outliers, slow-moving inventory, category concentration
              </p>
            </div>
 <div className="theme-card p-6">
              <div className="text-2xl mb-3">IN-08 to IN-09</div>
              <h3 className="font-serif text-content-primary text-sm mb-2">Advanced Tests</h3>
              <p className="font-sans text-content-secondary text-xs">
                Duplicate items, zero-value items
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
