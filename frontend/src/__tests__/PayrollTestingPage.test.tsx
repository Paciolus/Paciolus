/**
 * Sprint 96.5 / Sprint 548: Payroll Testing page tests
 * Refactored to use shared toolPageScenarios harness.
 */
import PayrollTestingPage from '@/app/tools/payroll-testing/page'
import { usePayrollTesting } from '@/hooks/usePayrollTesting'
import { runStandardToolPageScenarios } from './helpers/toolPageScenarios'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/utils/telemetry', () => ({ trackEvent: jest.fn() }))

jest.mock('@/hooks/usePayrollTesting', () => ({
  usePayrollTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: jest.fn(), reset: jest.fn() })),
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

jest.mock('@/components/payrollTesting', () => ({
  PayrollScoreCard: () => <div data-testid="payroll-score-card">ScoreCard</div>,
  PayrollTestResultGrid: () => <div data-testid="payroll-test-grid">Grid</div>,
  PayrollDataQualityBadge: () => <div data-testid="payroll-quality-badge">Quality</div>,
  FlaggedEmployeeTable: () => <div data-testid="payroll-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({ useCanvasAccentSync: jest.fn() }))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractPayrollProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

runStandardToolPageScenarios({
  name: 'PayrollTestingPage',
  Component: PayrollTestingPage,
  getToolHookMock: () => usePayrollTesting as jest.Mock,
  heroText: 'Payroll & Employee Testing',
  uploadPromptPattern: /Upload Payroll Register/,
  loadingTextPattern: /Running 11-test battery/,
  successTestIds: ['payroll-score-card', 'payroll-test-grid', 'payroll-flagged-table'],
  infoCardLabels: ['Structural Tests', 'Statistical Tests', 'Fraud Indicators'],
  mockSuccessResult: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
  hasTierGating: true,
})
