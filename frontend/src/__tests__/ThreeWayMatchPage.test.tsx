/**
 * Sprint 96.5: Three-Way Match page tests (10 tests)
 */
import { render, screen } from '@/test-utils'

const mockRunMatch = jest.fn()
const mockReset = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useThreeWayMatch', () => ({
  useThreeWayMatch: jest.fn(() => ({
    status: 'idle', result: null, error: null, runMatch: mockRunMatch, reset: mockReset,
  })),
}))

jest.mock('@/hooks/useTestingExport', () => ({
  useTestingExport: jest.fn(() => ({ exporting: null, lastExportSuccess: null, handleExportMemo: mockHandleExportMemo, handleExportCSV: mockHandleExportCSV })),
}))

jest.mock('@/components/threeWayMatch', () => ({
  MatchSummaryCard: () => <div data-testid="twm-summary-card">Summary</div>,
  MatchResultsTable: () => <div data-testid="twm-results-table">Results</div>,
  UnmatchedDocumentsPanel: () => <div data-testid="twm-unmatched-panel">Unmatched</div>,
  VarianceDetailCard: () => <div data-testid="twm-variance-card">Variances</div>,
}))

jest.mock('@/components/shared', () => ({
  FileDropZone: ({ label }: any) => <div data-testid={`file-drop-${label}`}>{label}</div>,
  GuestCTA: ({ description }: any) => <div data-testid="guest-cta">{description}</div>,
  ZeroStorageNotice: () => <div data-testid="zero-storage-notice">Zero-Storage</div>,
  DisclaimerBox: ({ children }: any) => <div data-testid="disclaimer-box">{children}</div>,
  ToolStatePresence: ({ children }: any) => <div data-testid="tool-state-presence">{children}</div>,
}))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => <div data-testid="proof-panel">Panel</div>,
  extractTWMProof: () => ({}),
}))
jest.mock('@/hooks/useCanvasAccentSync', () => ({
  useCanvasAccentSync: jest.fn(),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { useAuth } from '@/contexts/AuthContext'
import { useThreeWayMatch } from '@/hooks/useThreeWayMatch'
import ThreeWayMatchPage from '@/app/tools/three-way-match/page'

const mockUseAuth = useAuth as jest.Mock
const mockUseTWM = useThreeWayMatch as jest.Mock

describe('ThreeWayMatchPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseTWM.mockReturnValue({ status: 'idle', result: null, error: null, runMatch: mockRunMatch, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<ThreeWayMatchPage />)
    expect(screen.getByText('Three-Way Match Validator')).toBeInTheDocument()
  })

  it('shows triple upload zones for authenticated verified user', () => {
    render(<ThreeWayMatchPage />)
    expect(screen.getByText('Purchase Orders')).toBeInTheDocument()
    expect(screen.getByText('Invoices')).toBeInTheDocument()
    expect(screen.getByText('Receipts / GRN')).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<ThreeWayMatchPage />)
    expect(screen.getByTestId('guest-cta')).toBeInTheDocument()
    expect(screen.getByText(/Three-Way Match Validation requires a verified account/)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseTWM.mockReturnValue({ status: 'loading', result: null, error: null, runMatch: mockRunMatch, reset: mockReset })
    render(<ThreeWayMatchPage />)
    expect(screen.getByText(/Matching 3 files/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseTWM.mockReturnValue({ status: 'error', result: null, error: 'No PO number column', runMatch: mockRunMatch, reset: mockReset })
    render(<ThreeWayMatchPage />)
    expect(screen.getByText('Matching Failed')).toBeInTheDocument()
    expect(screen.getByText('No PO number column')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseTWM.mockReturnValue({
      status: 'success', error: null, runMatch: mockRunMatch, reset: mockReset,
      result: { summary: {}, full_matches: [], partial_matches: [], unmatched_pos: [], unmatched_invoices: [], unmatched_receipts: [], variances: [], data_quality: {}, column_detection: {} },
    })
    render(<ThreeWayMatchPage />)
    expect(screen.getByTestId('twm-summary-card')).toBeInTheDocument()
    expect(screen.getByTestId('twm-results-table')).toBeInTheDocument()
    expect(screen.getByTestId('twm-unmatched-panel')).toBeInTheDocument()
  })

  it('shows export buttons on success', () => {
    mockUseTWM.mockReturnValue({
      status: 'success', error: null, runMatch: mockRunMatch, reset: mockReset,
      result: { summary: {}, full_matches: [], partial_matches: [], unmatched_pos: [], unmatched_invoices: [], unmatched_receipts: [], variances: [], data_quality: {}, column_detection: {} },
    })
    render(<ThreeWayMatchPage />)
    expect(screen.getByText('Download Memo')).toBeInTheDocument()
    expect(screen.getByText('Export CSV')).toBeInTheDocument()
    expect(screen.getByText('New Match')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<ThreeWayMatchPage />)
    expect(screen.getByText('Variance Detection')).toBeInTheDocument()
    expect(screen.getByText('Fuzzy Fallback')).toBeInTheDocument()
  })
})
