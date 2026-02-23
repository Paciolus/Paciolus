/**
 * Sprint 96.5: Journal Entry Testing page tests (10 tests)
 */
import { render, screen } from '@/test-utils'

// Mock hooks
const mockRunTests = jest.fn()
const mockReset = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()
const mockFileInputRef = { current: null }

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useJETesting', () => ({
  useJETesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })),
}))

jest.mock('@/hooks/useFileUpload', () => ({
  useFileUpload: jest.fn(() => ({
    isDragging: false, fileInputRef: mockFileInputRef,
    handleDrop: jest.fn(), handleDragOver: jest.fn(), handleDragLeave: jest.fn(), handleFileSelect: jest.fn(),
  })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, handleExportMemo: mockHandleExportMemo, handleExportCSV: mockHandleExportCSV })),
}))

jest.mock('@/components/jeTesting', () => ({
  JEScoreCard: ({ score }: { score: unknown }) => <div data-testid="je-score-card">ScoreCard</div>,
  TestResultGrid: () => <div data-testid="test-result-grid">Grid</div>,
  GLDataQualityBadge: () => <div data-testid="quality-badge">Quality</div>,
  BenfordChart: () => <div data-testid="benford-chart">Benford</div>,
  FlaggedEntryTable: () => <div data-testid="flagged-table">Flagged</div>,
  SamplingPanel: () => <div data-testid="sampling-panel">Sampling</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({
  useCanvasAccentSync: jest.fn(),
}))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractJEProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useJETesting } from '@/hooks/useJETesting'
import JournalEntryTestingPage from '@/app/tools/journal-entry-testing/page'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock
const mockUseJE = useJETesting as jest.Mock

describe('JournalEntryTestingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseJE.mockReturnValue({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<JournalEntryTestingPage />)
    expect(screen.getByText('Journal Entry Testing')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user in idle state', () => {
    render(<JournalEntryTestingPage />)
    expect(screen.getByText(/Upload General Ledger Extract/)).toBeInTheDocument()
    expect(screen.getByText(/CSV or Excel/)).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<JournalEntryTestingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows loading state with spinner text', () => {
    mockUseJE.mockReturnValue({ status: 'loading', result: null, error: null, runTests: mockRunTests, reset: mockReset })
    render(<JournalEntryTestingPage />)
    expect(screen.getByText(/Running 19-test battery/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseJE.mockReturnValue({ status: 'error', result: null, error: 'Parse failed', runTests: mockRunTests, reset: mockReset })
    render(<JournalEntryTestingPage />)
    expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
    expect(screen.getByText('Parse failed')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseJE.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, benford_result: { digits: [] }, multi_currency_warning: null },
    })
    render(<JournalEntryTestingPage />)
    expect(screen.getByTestId('je-score-card')).toBeInTheDocument()
    expect(screen.getByTestId('test-result-grid')).toBeInTheDocument()
    expect(screen.getByTestId('flagged-table')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUseJE.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, benford_result: null, multi_currency_warning: null },
    })
    render(<JournalEntryTestingPage />)
    expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
    expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
    expect(screen.getByText('New Test')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<JournalEntryTestingPage />)
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
    expect(screen.getByText('Advanced Tests')).toBeInTheDocument()
  })
})
