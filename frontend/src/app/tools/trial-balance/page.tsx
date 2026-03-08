'use client'

import { MappingProvider } from '@/contexts/MappingContext'
import { CurrencyRatePanel } from '@/components/currencyRates/CurrencyRatePanel'
import { MaterialityControl } from '@/components/diagnostic'
import { ColumnMappingModal } from '@/components/mapping'
import { PreFlightSummary } from '@/components/preflight/PreFlightSummary'
import { GuestCTA, DisclaimerBox, Citation, CitationFooter } from '@/components/shared'
import { PdfExtractionPreview } from '@/components/shared/PdfExtractionPreview'
import { AuditResultsPanel } from '@/components/trialBalance/AuditResultsPanel'
import { WorkbookInspector } from '@/components/workbook'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'
import { useTrialBalanceAudit } from '@/hooks/useTrialBalanceAudit'
import { ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

function HomeContent() {
  const {
    // Auth
    user, isAuthenticated, token, isVerified,
    // Pre-flight (Sprint 283)
    preflightStatus, preflightReport, preflightError,
    showPreflight,
    handlePreflightProceed, handlePreflightExportPDF, handlePreflightExportCSV,
    // Population Profile (Sprint 287)
    handlePopulationProfileExportPDF, handlePopulationProfileExportCSV,
    // Expense Category (Sprint 289)
    handleExpenseCategoryExportPDF, handleExpenseCategoryExportCSV,
    // Accrual Completeness (Sprint 290)
    handleAccrualCompletenessExportPDF, handleAccrualCompletenessExportCSV,
    // Audit state
    auditStatus, auditResult, auditError,
    selectedFile, isRecalculating, scanningRows,
    // Materiality
    materialityThreshold, setMaterialityThreshold,
    displayMode, handleDisplayModeChange,
    // Column mapping modal
    showColumnMappingModal, pendingColumnDetection,
    handleColumnMappingConfirm, handleColumnMappingClose,
    // Workbook inspector
    showWorkbookInspector, pendingWorkbookInfo,
    handleWorkbookInspectorConfirm, handleWorkbookInspectorClose,
    // PDF preview (Sprint 427)
    showPdfPreview, pendingPdfPreview,
    handlePdfPreviewConfirm, handlePdfPreviewClose,
    // Benchmarks
    selectedIndustry, availableIndustries, comparisonResults, isLoadingComparison, handleIndustryChange,
    // File upload
    isDragging, handleDrop, handleDragOver, handleDragLeave, handleFileSelect,
    // Actions
    resetAudit, handleRerunAudit,
  } = useTrialBalanceAudit()

  useCanvasAccentSync(auditStatus)

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-theme-success-bg border border-theme-success-border mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-theme-success-text text-sm font-sans font-medium">ISA 520 Analytical Procedures</span>
          </div>
          <h1 className="type-tool-title mb-3">
            Trial Balance Diagnostics
          </h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">
            Upload a trial balance for streaming diagnostic analysis &mdash; ratio analysis,
            anomaly detection, benchmarks, and lead sheet generation.
          </p>
        </div>

        {/* Guest CTA */}
        {!isAuthenticated && (
          <GuestCTA description="Trial Balance Diagnostics requires a verified account. Sign in or create an account to analyze your trial balance." />
        )}

        {isAuthenticated && isVerified && (
          <>
            {/* Diagnostic Zone */}
            <section className="max-w-3xl mx-auto">
              <div className="space-y-4 mb-6">
                <MaterialityControl
                  idPrefix="workspace"
                  value={materialityThreshold}
                  onChange={setMaterialityThreshold}
                  showLiveIndicator={!!selectedFile && auditStatus === 'success'}
                  filename={selectedFile?.name}
                />

                <CurrencyRatePanel />
              </div>

              {/* Drop Zone */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`drop-zone ${auditStatus === 'idle' ? 'cursor-pointer' : ''} ${isDragging ? 'dragging' : ''}`}
              >
                <input
                  type="file"
                  accept={ACCEPTED_FILE_EXTENSIONS_STRING}
                  onChange={handleFileSelect}
                  className={`absolute inset-0 w-full h-full opacity-0 ${auditStatus === 'idle' ? 'cursor-pointer' : 'pointer-events-none'}`}
                  tabIndex={auditStatus === 'idle' ? 0 : -1}
                />

                {auditStatus === 'idle' && !showPreflight && preflightStatus !== 'loading' && (
                  <>
                    <svg className="w-12 h-12 text-content-tertiary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p className="text-content-secondary text-lg font-sans mb-2">Drag and drop your trial balance</p>
                    <p className="text-content-tertiary text-sm font-sans">or click to browse. CSV, TSV, TXT, or Excel &mdash; up to 50MB</p>
                  </>
                )}

                {preflightStatus === 'loading' && (
                  <div className="flex flex-col items-center py-4" aria-live="polite">
                    <div className="w-10 h-10 border-3 border-oatmeal-200 border-t-sage-500 rounded-full animate-spin mb-3"></div>
                    <p className="text-content-secondary font-sans text-sm">Running data quality pre-flight check...</p>
                  </div>
                )}

                {showPreflight && preflightStatus === 'success' && preflightReport && (
                  <PreFlightSummary
                    report={preflightReport}
                    onProceed={handlePreflightProceed}
                    onExportPDF={handlePreflightExportPDF}
                    onExportCSV={handlePreflightExportCSV}
                  />
                )}

                {preflightStatus === 'error' && showPreflight && (
                  <div className="space-y-2" role="alert">
                    <p className="text-content-secondary font-sans text-sm">Pre-flight check failed: {preflightError}</p>
                    <button
                      onClick={resetAudit}
                      className="text-sage-600 hover:text-sage-700 text-sm font-sans font-medium"
                    >
                      Try again
                    </button>
                  </div>
                )}

                {auditStatus === 'loading' && (
                  <div className="flex flex-col items-center" aria-live="polite">
                    <div className="w-12 h-12 border-4 border-sage-200 border-t-sage-500 rounded-full animate-spin mb-4"></div>
                    <p className="text-content-secondary font-sans mb-2">Streaming analysis in progress...</p>
                    <div className="w-full max-w-xs">
                      <div className="h-2 bg-oatmeal-200 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-sage-500 rounded-full animate-progress-smooth"></div>
                      </div>
                      <div className="flex items-center justify-center gap-2 text-sm font-sans">
                        <svg className="w-4 h-4 text-sage-600 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <span className="text-sage-700 font-mono">
                          Scanning rows: <span className="text-content-primary">{scanningRows.toLocaleString()}</span>...
                        </span>
                      </div>
                    </div>
                    <p className="text-content-tertiary text-xs font-sans mt-3">Processing in memory-efficient chunks</p>
                  </div>
                )}

                {auditStatus === 'success' && auditResult && (
                  <AuditResultsPanel
                    result={auditResult}
                    isRecalculating={isRecalculating}
                    filename={selectedFile?.name || 'diagnostic'}
                    token={token}
                    materialityThreshold={materialityThreshold}
                    setMaterialityThreshold={setMaterialityThreshold}
                    displayMode={displayMode}
                    onDisplayModeChange={handleDisplayModeChange}
                    selectedIndustry={selectedIndustry}
                    availableIndustries={availableIndustries}
                    comparisonResults={comparisonResults}
                    isLoadingComparison={isLoadingComparison}
                    onIndustryChange={handleIndustryChange}
                    onRerunAudit={handleRerunAudit}
                    onReset={resetAudit}
                    onExportPopulationProfilePDF={handlePopulationProfileExportPDF}
                    onExportPopulationProfileCSV={handlePopulationProfileExportCSV}
                    onExportExpenseCategoryPDF={handleExpenseCategoryExportPDF}
                    onExportExpenseCategoryCSV={handleExpenseCategoryExportCSV}
                    onExportAccrualCompletenessPDF={handleAccrualCompletenessExportPDF}
                    onExportAccrualCompletenessCSV={handleAccrualCompletenessExportCSV}
                  />
                )}

                {auditStatus === 'error' && (
                  <div className="space-y-4" role="alert">
                    <div className="w-16 h-16 bg-theme-error-bg rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-theme-error-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                    <p className="text-theme-error-text font-sans font-medium">{auditError}</p>
                    <button
                      onClick={resetAudit}
                      className="text-sage-600 hover:text-sage-700 text-sm font-sans font-medium"
                    >
                      Try again
                    </button>
                  </div>
                )}
              </div>

              <p className="text-center text-content-tertiary text-xs font-sans mt-4">
                Your file is processed entirely in-memory and is never saved to any disk or server.
              </p>
            </section>

            {/* Disclaimer — shown after results */}
            {auditStatus === 'success' && auditResult && (
              <div className="max-w-3xl mx-auto mt-8 space-y-0">
                <DisclaimerBox>
                  This automated trial balance diagnostic tool provides analytical procedures to assist
                  professional auditors per <Citation code="ISA 520" />. Results represent data anomalies
                  and ratio analysis and are not audit conclusions. They are not a substitute for professional
                  judgment or sufficient audit evidence per <Citation code="ISA 500" />.
                </DisclaimerBox>
                <CitationFooter standards={['ISA 520', 'ISA 500', 'ISA 315']} />
              </div>
            )}

            {pendingColumnDetection && (
              <ColumnMappingModal
                isOpen={showColumnMappingModal}
                onClose={handleColumnMappingClose}
                onConfirm={handleColumnMappingConfirm}
                columnDetection={pendingColumnDetection}
                filename={selectedFile?.name || 'uploaded file'}
              />
            )}

            {pendingWorkbookInfo && (
              <WorkbookInspector
                isOpen={showWorkbookInspector}
                onClose={handleWorkbookInspectorClose}
                onConfirm={handleWorkbookInspectorConfirm}
                workbookInfo={pendingWorkbookInfo}
              />
            )}

            {pendingPdfPreview && (
              <PdfExtractionPreview
                isOpen={showPdfPreview}
                onClose={handlePdfPreviewClose}
                onConfirm={handlePdfPreviewConfirm}
                previewResult={pendingPdfPreview}
              />
            )}
          </>
        )}
      </div>
    </main>
  )
}

export default function Home() {
  return (
    <MappingProvider>
      <HomeContent />
    </MappingProvider>
  )
}
