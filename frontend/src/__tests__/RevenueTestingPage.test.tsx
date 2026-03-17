/**
 * Sprint 129 / Sprint 548: Revenue Testing page tests
 * Refactored to use shared toolPageScenarios harness.
 */
import RevenueTestingPage from '@/app/tools/revenue-testing/page'
import { useRevenueTesting } from '@/hooks/useRevenueTesting'
import { runStandardToolPageScenarios } from './helpers/toolPageScenarios'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useRevenueTesting', () => ({
  useRevenueTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: jest.fn(), reset: jest.fn() })),
}))

jest.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: jest.fn(() => ({
    isDragging: false, fileInputRef: { current: null },
    handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: jest.fn(),
  })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, lastExportSuccess: null, handleExportMemo: jest.fn(), handleExportCSV: jest.fn() })),
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))

jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => <div data-testid="proof-panel">Panel</div>,
  extractRevenueProof: () => ({}),
}))

jest.mock('@/components/revenueTesting', () => ({
  RevenueScoreCard: () => <div data-testid="revenue-score-card">ScoreCard</div>,
  RevenueTestResultGrid: () => <div data-testid="revenue-test-grid">Grid</div>,
  RevenueDataQualityBadge: () => <div data-testid="revenue-quality-badge">Quality</div>,
  FlaggedRevenueTable: () => <div data-testid="revenue-flagged-table">Flagged</div>,
}))

jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

runStandardToolPageScenarios({
  name: 'RevenueTestingPage',
  Component: RevenueTestingPage,
  getToolHookMock: () => useRevenueTesting as jest.Mock,
  heroText: 'Revenue Testing',
  uploadPromptPattern: /Upload Revenue GL Extract/,
  loadingTextPattern: /Running revenue test battery/,
  successTestIds: ['revenue-score-card', 'revenue-test-grid', 'revenue-flagged-table'],
  infoCardLabels: ['Structural Tests', 'Statistical Tests', 'Advanced Tests'],
  mockSuccessResult: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
})
