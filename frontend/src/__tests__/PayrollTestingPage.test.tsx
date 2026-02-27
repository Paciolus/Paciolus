/**
 * Sprint 96.5: Payroll Testing page tests (10 tests)
 */
import PayrollTestingPage from '@/app/tools/payroll-testing/page'
import { useAuth } from '@/contexts/AuthContext'
import { usePayrollTesting } from '@/hooks/usePayrollTesting'
import { render, screen } from '@/test-utils'

const mockRunTests = jest.fn()
const mockReset = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()
const mockFileInputRef = { current: null }

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true, tier: 'team' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

jest.mock('@/hooks/usePayrollTesting', () => ({
  usePayrollTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })),
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

jest.mock('@/components/payrollTesting', () => ({
  PayrollScoreCard: () => <div data-testid="payroll-score-card">ScoreCard</div>,
  PayrollTestResultGrid: () => <div data-testid="payroll-test-grid">Grid</div>,
  PayrollDataQualityBadge: () => <div data-testid="payroll-quality-badge">Quality</div>,
  FlaggedEmployeeTable: () => <div data-testid="payroll-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({
  useCanvasAccentSync: jest.fn(),
}))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractPayrollProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


const mockUseAuth = useAuth as jest.Mock
const mockUsePayroll = usePayrollTesting as jest.Mock

describe('PayrollTestingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true, tier: 'team' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUsePayroll.mockReturnValue({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<PayrollTestingPage />)
    expect(screen.getByText('Payroll & Employee Testing')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user', () => {
    render(<PayrollTestingPage />)
    expect(screen.getByText(/Upload Payroll Register/)).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<PayrollTestingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUsePayroll.mockReturnValue({ status: 'loading', result: null, error: null, runTests: mockRunTests, reset: mockReset })
    render(<PayrollTestingPage />)
    expect(screen.getByText(/Running 11-test battery/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUsePayroll.mockReturnValue({ status: 'error', result: null, error: 'Missing required columns', runTests: mockRunTests, reset: mockReset })
    render(<PayrollTestingPage />)
    expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
    expect(screen.getByText('Missing required columns')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUsePayroll.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<PayrollTestingPage />)
    expect(screen.getByTestId('payroll-score-card')).toBeInTheDocument()
    expect(screen.getByTestId('payroll-test-grid')).toBeInTheDocument()
    expect(screen.getByTestId('payroll-flagged-table')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUsePayroll.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<PayrollTestingPage />)
    expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
    expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
    expect(screen.getByText('New Test')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<PayrollTestingPage />)
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
    expect(screen.getByText('Fraud Indicators')).toBeInTheDocument()
  })

  it('shows upgrade gate for free tier user', () => {
    mockUseAuth.mockReturnValue({ user: { is_verified: true, tier: 'free' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    render(<PayrollTestingPage />)
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.getByText('View Plans')).toBeInTheDocument()
    expect(screen.queryByText(/Upload Payroll Register/)).not.toBeInTheDocument()
  })

  it('shows tool content for team tier user', () => {
    render(<PayrollTestingPage />)
    expect(screen.queryByText('Upgrade Required')).not.toBeInTheDocument()
    expect(screen.getByText(/Upload Payroll Register/)).toBeInTheDocument()
  })
})
