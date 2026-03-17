/**
 * Sprint 129 / Sprint 548: AR Aging page tests
 * Refactored to use shared toolPageScenarios harness.
 */
import ARAgingPage from '@/app/tools/ar-aging/page'
import { useARAging } from '@/hooks/useARAging'
import { runStandardToolPageScenarios } from './helpers/toolPageScenarios'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'enterprise' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/utils/telemetry', () => ({ trackEvent: jest.fn() }))

jest.mock('@/hooks/useARAging', () => ({
  useARAging: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: jest.fn(), reset: jest.fn() })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, handleExportMemo: jest.fn(), handleExportCSV: jest.fn() })),
}))

jest.mock('@/components/arAging', () => ({
  ARScoreCard: () => <div data-testid="ar-score-card">ScoreCard</div>,
  ARTestResultGrid: () => <div data-testid="ar-test-grid">Grid</div>,
  ARDataQualityBadge: () => <div data-testid="ar-quality-badge">Quality</div>,
  FlaggedARTable: () => <div data-testid="ar-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

runStandardToolPageScenarios({
  name: 'ARAgingPage',
  Component: ARAgingPage,
  getToolHookMock: () => useARAging as jest.Mock,
  heroText: 'AR Aging Analysis',
  uploadPromptPattern: /Trial Balance/,
  loadingTextPattern: /Running.*AR aging battery/,
  successTestIds: ['ar-score-card', 'ar-test-grid', 'ar-flagged-table'],
  infoCardLabels: ['Structural Tests', 'Statistical Tests', 'Advanced Tests'],
  mockSuccessResult: { composite_score: {}, test_results: [], data_quality: {}, tb_column_detection: {}, sl_column_detection: {}, ar_summary: {} },
  hasTierGating: true,
})
