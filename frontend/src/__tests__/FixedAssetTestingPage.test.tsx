/**
 * Sprint 129 / Sprint 548: Fixed Asset Testing page tests
 * Refactored to use shared toolPageScenarios harness.
 */
import FixedAssetTestingPage from '@/app/tools/fixed-assets/page'
import { useFixedAssetTesting } from '@/hooks/useFixedAssetTesting'
import { runStandardToolPageScenarios } from './helpers/toolPageScenarios'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'enterprise' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/utils/telemetry', () => ({ trackEvent: jest.fn() }))

jest.mock('@/hooks/useFixedAssetTesting', () => ({
  useFixedAssetTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: jest.fn(), reset: jest.fn() })),
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

jest.mock('@/components/fixedAssetTesting', () => ({
  FixedAssetScoreCard: () => <div data-testid="fa-score-card">ScoreCard</div>,
  FixedAssetTestResultGrid: () => <div data-testid="fa-test-grid">Grid</div>,
  FixedAssetDataQualityBadge: () => <div data-testid="fa-quality-badge">Quality</div>,
  FlaggedFixedAssetTable: () => <div data-testid="fa-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractFAProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

runStandardToolPageScenarios({
  name: 'FixedAssetTestingPage',
  Component: FixedAssetTestingPage,
  getToolHookMock: () => useFixedAssetTesting as jest.Mock,
  heroText: 'Fixed Asset Testing',
  uploadPromptPattern: /Upload Fixed Asset Register/,
  loadingTextPattern: /Running 9-test fixed asset battery/,
  successTestIds: ['fa-score-card', 'fa-test-grid', 'fa-flagged-table'],
  infoCardLabels: ['Structural Tests', 'Statistical Tests', 'Advanced Tests'],
  mockSuccessResult: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
  hasTierGating: true,
})
