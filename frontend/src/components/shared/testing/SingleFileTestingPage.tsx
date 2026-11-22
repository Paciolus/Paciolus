'use client'

/**
 * Shared shell for single-file testing tool pages — Sprint 892 (CEO brief 17C, review ST-13).
 *
 * The testing pages each repeated the selected-file state, export request building, file-type
 * check, drag and drop, reset, sign-in and verification branches, plan gating, and the upload,
 * loading and export controls. This component holds that shell once; each page supplies its
 * labels, endpoints, accepted formats text and the result sections as slots. Pages with extra
 * inputs (journal-entry sampling, revenue contract data) pass them in `beforeUpload` /
 * `extraFormFields` style extensions rather than forking the shell; AR aging's two-file flow
 * stays outside it.
 */
import { useCallback, useState, type ReactNode } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { GuestCTA, UnverifiedCTA, UploadHandlingNotice, ToolStatePresence, UpgradeGate, ToolSettingsDrawer, type ToolSettingsKey } from '@/components/shared'
import { Button } from '@/components/ui/Button'
import { useCanvasAccentSync } from '@/hooks/useCanvasAccentSync'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useTestingExport } from '@/hooks/useTestingExport'
import { useUploadCapabilities } from '@/hooks/useUploadCapabilities'
import { isAcceptedFileType } from '@/utils/fileFormats'

/** The parts of a testing hook's result the shell needs for the export request. */
export interface TestingResultCore {
  composite_score: unknown
  test_results: unknown
  data_quality?: unknown
  column_detection?: unknown
}

export interface TestingToolState<R> {
  status: 'idle' | 'loading' | 'success' | 'error'
  result: R | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

export interface SingleFileTestingPageProps<R extends TestingResultCore> {
  /** Registry slug, for plan gating. */
  toolName: string
  tool: TestingToolState<R>
  hero: { badge: ReactNode; title: ReactNode; subtitle: ReactNode }
  guestDescription: string
  upload: {
    title: ReactNode
    prompt: ReactNode
    iconClassName: string
    /** SVG path for the upload icon; defaults to the cloud-upload arrow. */
    iconPath?: string
  }
  /** e.g. `Running 11-test fixed asset battery on ${name}...` */
  loadingText: (fileName: string | undefined) => ReactNode
  spinnerClassName: string
  exports: {
    memoEndpoint: string
    csvEndpoint: string
    memoFilename: string
    csvFilename: string
    /** filename stem when no file is selected */
    defaultStem: string
  }
  /** Result sections below the action bar. */
  renderResult: (result: R) => ReactNode
  /** Info cards shown in the idle state. */
  infoCards: ReactNode
  /** Result fields the memo needs beyond the common four (placed before `filename`). */
  extraExportFields?: (result: R) => Record<string, unknown>
  /** Tools with saved thresholds: a settings button in the hero and the settings drawer. */
  settingsToolKey?: ToolSettingsKey
}

const UPLOAD_ICON_PATH = 'M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12'

export function SingleFileTestingPage<R extends TestingResultCore>(props: SingleFileTestingPageProps<R>) {
  const { toolName, tool, hero, guestDescription, upload: uploadText, loadingText, spinnerClassName } = props
  const upload = useUploadCapabilities()
  const { user, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const { status, result, error, runTests, reset } = tool
  useCanvasAccentSync(status)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    props.exports.memoEndpoint,
    props.exports.csvEndpoint,
    props.exports.memoFilename,
    props.exports.csvFilename,
  )

  const exportBody = result
    ? {
        composite_score: result.composite_score,
        test_results: result.test_results,
        data_quality: result.data_quality,
        column_detection: result.column_detection,
        ...(props.extraExportFields ? props.extraExportFields(result) : {}),
        filename: selectedFile?.name.replace(/\.[^.]+$/, '') || props.exports.defaultStem,
      }
    : null

  const handleFileUpload = useCallback(
    async (file: File) => {
      if (!isAcceptedFileType(file)) return
      setSelectedFile(file)
      await runTests(file)
    },
    [runTests],
  )

  const { isDragging, fileInputRef, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } =
    useFileUpload(handleFileUpload)

  const handleNewTest = useCallback(() => {
    reset()
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [reset, fileInputRef])

  const isVerified = user?.is_verified !== false

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="page-container">
        {/* Hero Header */}
        <div className={props.settingsToolKey ? 'text-center mb-10 relative' : 'text-center mb-10'}>
          {props.settingsToolKey && isAuthenticated && isVerified && (
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
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-theme-success-bg border border-theme-success-border mb-6">
            <div className="w-2 h-2 bg-sage-500 rounded-full animate-pulse" />
            <span className="text-theme-success-text text-sm font-sans font-medium">{hero.badge}</span>
          </div>
          <h1 className="type-tool-title mb-3">{hero.title}</h1>
          <p className="font-sans text-content-secondary text-lg max-w-2xl mx-auto">{hero.subtitle}</p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && <GuestCTA description={guestDescription} />}

        {!authLoading && isAuthenticated && !isVerified && <UnverifiedCTA />}

        {/* Tool State Blocks */}
        {isAuthenticated && isVerified && (
          <UpgradeGate toolName={toolName}>
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
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault()
                        fileInputRef.current?.click()
                      }
                    }}
                    role="button"
                    tabIndex={0}
                  >
                    <input ref={fileInputRef} type="file" accept={upload.accept} onChange={handleFileSelect} className="hidden" />
                    <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-oatmeal-100 flex items-center justify-center">
                      <svg className={uploadText.iconClassName} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={uploadText.iconPath ?? UPLOAD_ICON_PATH} />
                      </svg>
                    </div>
                    <h3 className="type-tool-section mb-2">{uploadText.title}</h3>
                    <p className="font-sans text-sm text-content-secondary mb-1">{uploadText.prompt}</p>
                    <p className="font-sans text-xs text-content-tertiary">
                      CSV, TSV, TXT, or Excel &mdash; up to {upload.sizeLabel}
                    </p>
                  </div>

                  <UploadHandlingNotice className="mt-4" />
                </div>
              )}

              {/* Loading State */}
              {status === 'loading' && (
                <div className="text-center py-16" aria-live="polite">
                  <div className="inline-flex items-center gap-3 px-6 py-4 theme-card">
                    <div className={spinnerClassName} />
                    <span className="font-sans text-content-primary">{loadingText(selectedFile?.name)}</span>
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
                  <Button variant="secondary" onClick={handleNewTest} className="mt-3">
                    Try Again
                  </Button>
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
                      <Button
                        variant="primary"
                        onClick={() => exportBody && handleExportMemo(exportBody)}
                        disabled={exporting !== null || !result}
                      >
                        {exporting === 'pdf' ? 'Generating...' : 'Download Testing Memo'}
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => exportBody && handleExportCSV(exportBody)}
                        disabled={exporting !== null || !result}
                      >
                        {exporting === 'csv' ? 'Exporting...' : 'Export Flagged CSV'}
                      </Button>
                      <Button variant="secondary" onClick={handleNewTest}>
                        New Test
                      </Button>
                    </div>
                  </div>

                  {props.renderResult(result)}
                </div>
              )}
            </ToolStatePresence>
          </UpgradeGate>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">{props.infoCards}</div>
        )}
      </div>

      {props.settingsToolKey && (
        <ToolSettingsDrawer toolKey={props.settingsToolKey} open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      )}
    </main>
  )
}
