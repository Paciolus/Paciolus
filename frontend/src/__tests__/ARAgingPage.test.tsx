/**
 * Sprint 129: AR Aging page tests (10 tests)
 */
import { render, screen } from '@/test-utils'

const mockRunTests = jest.fn()
const mockReset = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useARAging', () => ({
  useARAging: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, handleExportMemo: mockHandleExportMemo, handleExportCSV: mockHandleExportCSV })),
}))

jest.mock('@/components/arAging', () => ({
  ARScoreCard: () => <div data-testid="ar-score-card">ScoreCard</div>,
  ARTestResultGrid: () => <div data-testid="ar-test-grid">Grid</div>,
  ARDataQualityBadge: () => <div data-testid="ar-quality-badge">Quality</div>,
  FlaggedARTable: () => <div data-testid="ar-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({
  useCanvasAccentSync: jest.fn(),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useAuth } from '@/contexts/AuthContext'
import { useARAging } from '@/hooks/useARAging'
import ARAgingPage from '@/app/tools/ar-aging/page'

const mockUseAuth = useAuth as jest.Mock
const mockUseARAging = useARAging as jest.Mock

describe('ARAgingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseARAging.mockReturnValue({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<ARAgingPage />)
    expect(screen.getByText('AR Aging Analysis')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user', () => {
    render(<ARAgingPage />)
    expect(screen.getByText(/Trial Balance/)).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<ARAgingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseARAging.mockReturnValue({ status: 'loading', result: null, error: null, runTests: mockRunTests, reset: mockReset })
    render(<ARAgingPage />)
    expect(screen.getByText(/Running.*AR aging battery/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseARAging.mockReturnValue({ status: 'error', result: null, error: 'Column detection failed', runTests: mockRunTests, reset: mockReset })
    render(<ARAgingPage />)
    expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
    expect(screen.getByText('Column detection failed')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseARAging.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, tb_column_detection: {}, sl_column_detection: {}, ar_summary: {} },
    })
    render(<ARAgingPage />)
    expect(screen.getByTestId('ar-score-card')).toBeInTheDocument()
    expect(screen.getByTestId('ar-test-grid')).toBeInTheDocument()
    expect(screen.getByTestId('ar-flagged-table')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUseARAging.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, tb_column_detection: {}, sl_column_detection: {}, ar_summary: {} },
    })
    render(<ARAgingPage />)
    expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
    expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
    expect(screen.getByText('New Test')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<ARAgingPage />)
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
    expect(screen.getByText('Advanced Tests')).toBeInTheDocument()
  })
})
