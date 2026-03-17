/**
 * Sprint 96.5 / Sprint 548: Journal Entry Testing page tests
 * Refactored to use shared toolPageScenarios harness.
 */
import JournalEntryTestingPage from '@/app/tools/journal-entry-testing/page'
import { useJETesting } from '@/hooks/useJETesting'
import { runStandardToolPageScenarios } from './helpers/toolPageScenarios'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useJETesting', () => ({
  useJETesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: jest.fn(), reset: jest.fn() })),
}))

jest.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: jest.fn(() => ({
    isDragging: false, fileInputRef: { current: null },
    handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: jest.fn(),
  })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, handleExportMemo: jest.fn(), handleExportCSV: jest.fn() })),
}))

jest.mock('@/components/jeTesting', () => ({
  JEScoreCard: ({ score }: { score: unknown }) => <div data-testid="je-score-card">ScoreCard</div>,
  TestResultGrid: () => <div data-testid="test-result-grid">Grid</div>,
  GLDataQualityBadge: () => <div data-testid="quality-badge">Quality</div>,
  BenfordChart: () => <div data-testid="benford-chart">Benford</div>,
  FlaggedEntryTable: () => <div data-testid="flagged-table">Flagged</div>,
  SamplingPanel: () => <div data-testid="sampling-panel">Sampling</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractJEProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

runStandardToolPageScenarios({
  name: 'JournalEntryTestingPage',
  Component: JournalEntryTestingPage,
  getToolHookMock: () => useJETesting as jest.Mock,
  heroText: 'Journal Entry Testing',
  uploadPromptPattern: /Upload General Ledger Extract/,
  loadingTextPattern: /Running 19-test battery/,
  successTestIds: ['je-score-card', 'test-result-grid', 'flagged-table'],
  infoCardLabels: ['Structural Tests', 'Statistical Tests', 'Advanced Tests'],
  mockSuccessResult: { composite_score: {}, test_results: [], data_quality: {}, benford_result: { digits: [] }, multi_currency_warning: null },
})
