/**
 * Sprint 96.5: AP Testing page tests (10 tests)
 */
import { render, screen } from '@/test-utils'

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

jest.mock('@/hooks/useAPTesting', () => ({
  useAPTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })),
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

jest.mock('@/components/apTesting', () => ({
  APScoreCard: () => <div data-testid="ap-score-card">ScoreCard</div>,
  APTestResultGrid: () => <div data-testid="ap-test-grid">Grid</div>,
  APDataQualityBadge: () => <div data-testid="ap-quality-badge">Quality</div>,
  FlaggedPaymentTable: () => <div data-testid="ap-flagged-table">Flagged</div>,
}))

jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useAuth } from '@/contexts/AuthContext'
import { useAPTesting } from '@/hooks/useAPTesting'
import APTestingPage from '@/app/tools/ap-testing/page'

const mockUseAuth = useAuth as jest.Mock
const mockUseAP = useAPTesting as jest.Mock

describe('APTestingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseAP.mockReturnValue({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<APTestingPage />)
    expect(screen.getByText('AP Payment Testing')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user', () => {
    render(<APTestingPage />)
    expect(screen.getByText(/Upload AP Payment Register/)).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<APTestingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseAP.mockReturnValue({ status: 'loading', result: null, error: null, runTests: mockRunTests, reset: mockReset })
    render(<APTestingPage />)
    expect(screen.getByText(/Running 13-test battery/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseAP.mockReturnValue({ status: 'error', result: null, error: 'Column detection failed', runTests: mockRunTests, reset: mockReset })
    render(<APTestingPage />)
    expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
    expect(screen.getByText('Column detection failed')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseAP.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<APTestingPage />)
    expect(screen.getByTestId('ap-score-card')).toBeInTheDocument()
    expect(screen.getByTestId('ap-test-grid')).toBeInTheDocument()
    expect(screen.getByTestId('ap-flagged-table')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUseAP.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<APTestingPage />)
    expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
    expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
    expect(screen.getByText('New Test')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<APTestingPage />)
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
    expect(screen.getByText('Fraud Indicators')).toBeInTheDocument()
  })
})
