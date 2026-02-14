'use client'

import { MappingProvider } from '@/contexts/MappingContext'
import { ColumnMappingModal } from '@/components/mapping'
import { WorkbookInspector } from '@/components/workbook'
import { WorkspaceHeader, QuickActionsBar, RecentHistoryMini } from '@/components/workspace'
import { MaterialityControl } from '@/components/diagnostic'
import { useTrialBalanceAudit } from '@/hooks/useTrialBalanceAudit'
import { GuestMarketingView } from '@/components/trialBalance/GuestMarketingView'
import { AuditResultsPanel } from '@/components/trialBalance/AuditResultsPanel'

function HomeContent() {
  const {
    // Auth
    user, isAuthenticated, token, isVerified,
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
    // Benchmarks
    selectedIndustry, availableIndustries, comparisonResults, isLoadingComparison, handleIndustryChange,
    // File upload
    isDragging, handleDrop, handleDragOver, handleDragLeave, handleFileSelect,
    // Actions
    resetAudit, handleRerunAudit,
  } = useTrialBalanceAudit()

  return (
    <main className="min-h-screen bg-surface-page">
      {!isAuthenticated ? (
        <GuestMarketingView />
      ) : (
        <>
          <WorkspaceHeader user={user!} token={token || undefined} />
          <QuickActionsBar />

          {!isVerified ? (
            <section className="py-16 px-6">
              <div className="max-w-lg mx-auto theme-card rounded-2xl p-10 text-center">
                <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-clay-50 border border-clay-200 flex items-center justify-center">
                  <svg className="w-8 h-8 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-serif font-bold text-content-primary mb-3">Verify Your Email</h2>
                <p className="text-content-secondary font-sans mb-2">
                  Trial Balance Diagnostics requires a verified account.
                </p>
                <p className="text-content-tertiary font-sans text-sm">
                  Check your inbox for a verification link, or use the banner above to resend.
                </p>
              </div>
            </section>
          ) : (
            <>
              {/* Diagnostic Zone */}
              <section className="py-16 px-6 bg-surface-card-secondary">
                <div className="max-w-3xl mx-auto">
                  <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 bg-sage-50 border border-sage-200 rounded-full px-4 py-1.5 mb-4">
                      <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                      </svg>
                      <span className="text-sage-700 text-sm font-sans font-medium">Zero-Storage Processing</span>
                    </div>
                    <h2 className="text-3xl font-serif font-bold text-content-primary mb-2">Diagnostic Intelligence Zone</h2>
                    <p className="text-content-secondary font-sans">Upload your trial balance for instant analysis. Your data never leaves your browser's memory.</p>
                  </div>

                  <MaterialityControl
                    idPrefix="workspace"
                    value={materialityThreshold}
                    onChange={setMaterialityThreshold}
                    showLiveIndicator={!!selectedFile && auditStatus === 'success'}
                    filename={selectedFile?.name}
                  />

                  {/* Drop Zone */}
                  <div
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    className={`drop-zone ${auditStatus === 'idle' ? 'cursor-pointer' : ''} ${isDragging ? 'dragging' : ''}`}
                  >
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={handleFileSelect}
                      className={`absolute inset-0 w-full h-full opacity-0 ${auditStatus === 'idle' ? 'cursor-pointer' : 'pointer-events-none'}`}
                      tabIndex={auditStatus === 'idle' ? 0 : -1}
                    />

                    {auditStatus === 'idle' && (
                      <>
                        <svg className="w-12 h-12 text-content-tertiary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                        </svg>
                        <p className="text-content-secondary text-lg font-sans mb-2">Drag and drop your trial balance</p>
                        <p className="text-content-tertiary text-sm font-sans">or click to browse. Supports CSV and Excel files.</p>
                      </>
                    )}

                    {auditStatus === 'loading' && (
                      <div className="flex flex-col items-center" aria-live="polite">
                        <div className="w-12 h-12 border-4 border-sage-200 border-t-sage-500 rounded-full animate-spin mb-4"></div>
                        <p className="text-content-secondary font-sans mb-2">Streaming analysis in progress...</p>
                        <div className="w-full max-w-xs">
                          <div className="h-2 bg-oatmeal-200 rounded-full overflow-hidden mb-2">
                            <div className="h-full bg-sage-500 rounded-full animate-pulse" style={{ width: '100%' }}></div>
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
                </div>
              </section>

              <RecentHistoryMini token={token || undefined} />

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
            </>
          )}
        </>
      )}
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
