/**
 * Sprint 129: Fixed Asset Testing page tests (10 tests)
 */
import FixedAssetTestingPage from '@/app/tools/fixed-assets/page'
import { useAuth } from '@/contexts/AuthContext'
import { useFixedAssetTesting } from '@/hooks/useFixedAssetTesting'
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

jest.mock('@/hooks/useFixedAssetTesting', () => ({
  useFixedAssetTesting: jest.fn(() => ({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })),
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

jest.mock('@/components/fixedAssetTesting', () => ({
  FixedAssetScoreCard: () => <div data-testid="fa-score-card">ScoreCard</div>,
  FixedAssetTestResultGrid: () => <div data-testid="fa-test-grid">Grid</div>,
  FixedAssetDataQualityBadge: () => <div data-testid="fa-quality-badge">Quality</div>,
  FlaggedFixedAssetTable: () => <div data-testid="fa-flagged-table">Flagged</div>,
}))

jest.mock('@/hooks/useCanvasAccentSync', () => ({
  useCanvasAccentSync: jest.fn(),
}))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractFAProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


const mockUseAuth = useAuth as jest.Mock
const mockUseFA = useFixedAssetTesting as jest.Mock

describe('FixedAssetTestingPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true, tier: 'team' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseFA.mockReturnValue({ status: 'idle', result: null, error: null, runTests: mockRunTests, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<FixedAssetTestingPage />)
    expect(screen.getByText('Fixed Asset Testing')).toBeInTheDocument()
  })

  it('shows upload zone for authenticated verified user', () => {
    render(<FixedAssetTestingPage />)
    expect(screen.getByText(/Upload Fixed Asset Register/)).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<FixedAssetTestingPage />)
    expect(screen.getByText('Sign In')).toBeInTheDocument()
    expect(screen.getByText('Create Account')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseFA.mockReturnValue({ status: 'loading', result: null, error: null, runTests: mockRunTests, reset: mockReset })
    render(<FixedAssetTestingPage />)
    expect(screen.getByText(/Running 9-test fixed asset battery/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseFA.mockReturnValue({ status: 'error', result: null, error: 'Column detection failed', runTests: mockRunTests, reset: mockReset })
    render(<FixedAssetTestingPage />)
    expect(screen.getByText('Analysis Failed')).toBeInTheDocument()
    expect(screen.getByText('Column detection failed')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseFA.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<FixedAssetTestingPage />)
    expect(screen.getByTestId('fa-score-card')).toBeInTheDocument()
    expect(screen.getByTestId('fa-test-grid')).toBeInTheDocument()
    expect(screen.getByTestId('fa-flagged-table')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUseFA.mockReturnValue({
      status: 'success', error: null, runTests: mockRunTests, reset: mockReset,
      result: { composite_score: {}, test_results: [], data_quality: {}, column_detection: {} },
    })
    render(<FixedAssetTestingPage />)
    expect(screen.getByText('Download Testing Memo')).toBeInTheDocument()
    expect(screen.getByText('Export Flagged CSV')).toBeInTheDocument()
    expect(screen.getByText('New Test')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<FixedAssetTestingPage />)
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
    expect(screen.getByText('Advanced Tests')).toBeInTheDocument()
  })

  it('shows upgrade gate for free tier user', () => {
    mockUseAuth.mockReturnValue({ user: { is_verified: true, tier: 'free' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    render(<FixedAssetTestingPage />)
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.getByText('View Plans')).toBeInTheDocument()
    expect(screen.queryByText(/Upload Fixed Asset Register/)).not.toBeInTheDocument()
  })

  it('shows tool content for team tier user', () => {
    render(<FixedAssetTestingPage />)
    expect(screen.queryByText('Upgrade Required')).not.toBeInTheDocument()
    expect(screen.getByText(/Upload Fixed Asset Register/)).toBeInTheDocument()
  })
})
