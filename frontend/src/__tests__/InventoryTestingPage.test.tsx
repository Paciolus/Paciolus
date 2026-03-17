/**
 * Sprint 129 / Sprint 548: Inventory Testing page tests
 * Refactored to use shared toolPageScenarios harness.
 */
import InventoryTestingPage from '@/app/tools/inventory-testing/page'
import { useInventoryTesting } from '@/hooks/useInventoryTesting'
import { runStandardToolPageScenarios } from './helpers/toolPageScenarios'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'enterprise' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/utils/telemetry', () => ({ trackEvent: jest.fn() }))

jest.mock('@/hooks/useInventoryTesting', () => ({
  useInventoryTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: jest.fn(), reset: jest.fn() })),
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

jest.mock('@/components/inventoryTesting', () => ({
  InventoryScoreCard: () => <div data-testid="inv-score-card">ScoreCard</div>,
  InventoryTestResultGrid: () => <div data-testid="inv-test-grid">Grid</div>,
  InventoryDataQualityBadge: () => <div data-testid="inv-quality-badge">Quality</div>,
  FlaggedInventoryTable: () => <div data-testid="inv-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractInventoryProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

runStandardToolPageScenarios({
  name: 'InventoryTestingPage',
  Component: InventoryTestingPage,
  getToolHookMock: () => useInventoryTesting as jest.Mock,
  heroText: 'Inventory Testing',
  uploadPromptPattern: /Upload Inventory Register/,
  loadingTextPattern: /Running 9-test inventory battery/,
  successTestIds: ['inv-score-card', 'inv-test-grid', 'inv-flagged-table'],
  infoCardLabels: ['Structural Tests', 'Statistical Tests', 'Advanced Tests'],
  mockSuccessResult: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
  hasTierGating: true,
})
