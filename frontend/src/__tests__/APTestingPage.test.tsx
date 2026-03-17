/**
 * Sprint 96.5 / Sprint 548: AP Testing page tests
 * Refactored to use shared toolPageScenarios harness.
 */
import APTestingPage from '@/app/tools/ap-testing/page'
import { useAPTesting } from '@/hooks/useAPTesting'
import { runStandardToolPageScenarios } from './helpers/toolPageScenarios'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useAPTesting', () => ({
  useAPTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: jest.fn(), reset: jest.fn() })),
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

jest.mock('@/components/apTesting', () => ({
  APScoreCard: () => <div data-testid="ap-score-card">ScoreCard</div>,
  APTestResultGrid: () => <div data-testid="ap-test-grid">Grid</div>,
  APDataQualityBadge: () => <div data-testid="ap-quality-badge">Quality</div>,
  FlaggedPaymentTable: () => <div data-testid="ap-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractAPProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

runStandardToolPageScenarios({
  name: 'APTestingPage',
  Component: APTestingPage,
  getToolHookMock: () => useAPTesting as jest.Mock,
  heroText: 'AP Payment Testing',
  uploadPromptPattern: /Upload AP Payment Register/,
  loadingTextPattern: /Running 13-test battery/,
  successTestIds: ['ap-score-card', 'ap-test-grid', 'ap-flagged-table'],
  infoCardLabels: ['Structural Tests', 'Statistical Tests', 'Fraud Indicators'],
  mockSuccessResult: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
})
