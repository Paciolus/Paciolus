/**
 * Sprint 129: Revenue Testing page tests (10 tests)
 */
import { render, screen } from '@/test-utils'

const mockRunTests = jest.fn()
const mockReset = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()
const mockFileInputRef = { current: null }

jest.mock('@/context/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useRevenueTesting', () => ({
  useRevenueTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })),
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

jest.mock('@/components/revenueTesting', () => ({
  RevenueScoreCard: () => <div data-testid="revenue-score-card">ScoreCard</div>,
  RevenueTestResultGrid: () => <div data-testid="revenue-test-grid">Grid</div>,
  RevenueDataQualityBadge: () => <div data-testid="revenue-quality-badge">Quality</div>,
  FlaggedRevenueTable: () => <div data-testid="revenue-flagged-table">Flagged</div>,
}))

jest.mock('@/components/auth', () => ({ VerificationBanner: () => <div data-testid="verification-banner">Verify</div> }))
jest.mock('@/components/shared', () => ({ ToolNav: () => <nav data-testid="tool-nav">Nav</nav> }))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useAuth } from '@/context/AuthContext'
import { useRevenueTesting } from '@/hooks/useRevenueTesting'
import RevenueTestingPage from '@/app/tools/revenue-testing/page'

const mockUseAuth = useAuth as jest.Mock
const mockUseRevenue = useRevenueTesting as jest.Mock

describe('RevenueTestingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseRevenue.mockReturnValue({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<RevenueTestingPage />)
    expect(screen.getByText('Revenue Testing')).toBeInTheDocument()
  })

  it('renders tool navigation', () => {
    render(<RevenueTestingPage />)
    expect(screen.getByTestId('tool-nav')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user', () => {
    render(<RevenueTestingPage />)
    expect(screen.getByText(/Upload Revenue GL Extract/)).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<RevenueTestingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows verification banner for unverified user', () => {
    mockUseAuth.mockReturnValue({ user: { is_verified: false }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'tk' })
    render(<RevenueTestingPage />)
    expect(screen.getByTestId('verification-banner')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseRevenue.mockReturnValue({ status: 'loading', result: null, error: null, runTests: mockRunTests, reset: mockReset })
    render(<RevenueTestingPage />)
    expect(screen.getByText(/Running 12-test revenue battery/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseRevenue.mockReturnValue({ status: 'error', result: null, error: 'Column detection failed', runTests: mockRunTests, reset: mockReset })
    render(<RevenueTestingPage />)
    expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
    expect(screen.getByText('Column detection failed')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseRevenue.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<RevenueTestingPage />)
    expect(screen.getByTestId('revenue-score-card')).toBeInTheDocument()
    expect(screen.getByTestId('revenue-test-grid')).toBeInTheDocument()
    expect(screen.getByTestId('revenue-flagged-table')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUseRevenue.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<RevenueTestingPage />)
    expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
    expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
    expect(screen.getByText('New Test')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<RevenueTestingPage />)
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
    expect(screen.getByText('Advanced Tests')).toBeInTheDocument()
  })
})
