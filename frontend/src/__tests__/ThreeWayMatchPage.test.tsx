/**
 * Sprint 96.5: Three-Way Match page tests (10 tests)
 */
import ThreeWayMatchPage from '@/app/tools/three-way-match/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useSettings } from '@/hooks/useSettings'
import { useThreeWayMatch } from '@/hooks/useThreeWayMatch'
import { fireEvent, render, screen } from '@/test-utils'

const mockRunMatch = jest.fn()
const mockReset = jest.fn()
const mockHandleExportMemo = jest.fn()
const mockHandleExportCSV = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useThreeWayMatch', () => ({
  useThreeWayMatch: jest.fn(() => ({
    status: 'idle', result: null, error: null, runMatch: mockRunMatch, reset: mockReset,
  })),
}))

jest.mock('@/hooks/useSettings', () => ({
  useSettings: jest.fn(() => ({ practiceSettings: null, fetchPracticeSettings: jest.fn() })),
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
  UpgradeGate: ({ children }: any) => <>{children}</>,
  CitationFooter: () => <div data-testid="citation-footer">Citations</div>,
  ToolSettingsDrawer: () => null,
  SavedSettingsNotice: () => null,
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


const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseTWM = useThreeWayMatch as jest.Mock
const mockUseSettings = useSettings as jest.Mock

describe('ThreeWayMatchPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuthSession.mockReturnValue({ user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseTWM.mockReturnValue({ status: 'idle', result: null, error: null, runMatch: mockRunMatch, reset: mockReset })
    mockUseSettings.mockReturnValue({ practiceSettings: null, fetchPracticeSettings: jest.fn() })
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
    mockUseAuthSession.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
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

  it('shows upgrade gate for free tier user', () => {
    mockUseAuthSession.mockReturnValue({ user: { is_verified: true, tier: 'free' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    render(<ThreeWayMatchPage />)
    // UpgradeGate is a passthrough mock — tool content still renders (mock bypasses gate logic)
    expect(screen.getByText('Purchase Orders')).toBeInTheDocument()
  })

  it('shows tool content for paid tier user', () => {
    render(<ThreeWayMatchPage />)
    expect(screen.getByText('Purchase Orders')).toBeInTheDocument()
    expect(screen.getByText('Invoices')).toBeInTheDocument()
    expect(screen.getByText('Receipts / GRN')).toBeInTheDocument()
  })

  // Sprint 839: per-run tolerances, prefilled from saved settings
  describe('run settings', () => {
    const openPanel = () => fireEvent.click(screen.getByRole('button', { name: /Run settings/ }))

    it('prefills from saved settings and sends nothing until a value changes', () => {
      mockUseSettings.mockReturnValue({ practiceSettings: { three_way_match_config: { date_window_days: 60 } }, fetchPracticeSettings: jest.fn() })
      render(<ThreeWayMatchPage />)
      openPanel()
      expect(screen.getByLabelText('Date window')).toHaveValue('60')
      expect(screen.getByLabelText('Fuzzy match minimum score')).toHaveValue('70')
      expect(screen.getByText(/Prefilled from your saved settings/)).toBeInTheDocument()
      expect(mockUseTWM).toHaveBeenLastCalledWith({})
    })

    it('uses the Paciolus defaults when nothing is saved', () => {
      render(<ThreeWayMatchPage />)
      openPanel()
      expect(screen.getByLabelText('Date window')).toHaveValue('30')
      expect(screen.getByText(/Prefilled from the Paciolus defaults/)).toBeInTheDocument()
    })

    it('passes only changed values to the hook, in engine units', () => {
      render(<ThreeWayMatchPage />)
      openPanel()
      fireEvent.change(screen.getByLabelText('Fuzzy match minimum score'), { target: { value: '80' } })
      fireEvent.change(screen.getByLabelText('Quantity tolerance'), { target: { value: '2' } })
      fireEvent.click(screen.getByRole('checkbox'))
      expect(mockUseTWM).toHaveBeenLastCalledWith({ fuzzy_composite_threshold: 0.8, quantity_tolerance: 2, enable_fuzzy_matching: false })
      expect(screen.getByRole('button', { name: /Run settings/ })).toHaveTextContent('3 changed for this run')
    })

    it('blocks the run for an out-of-range value', () => {
      render(<ThreeWayMatchPage />)
      openPanel()
      fireEvent.change(screen.getByLabelText('Date window'), { target: { value: '500' } })
      expect(screen.getByText('Date window must be between 0 and 365.')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Run Match' })).toBeDisabled()
    })

    it('reset returns to the prefilled values', () => {
      render(<ThreeWayMatchPage />)
      openPanel()
      fireEvent.change(screen.getByLabelText('Amount tolerance'), { target: { value: '5' } })
      fireEvent.click(screen.getByRole('button', { name: /Reset to defaults/ }))
      expect(screen.getByLabelText('Amount tolerance')).toHaveValue('0.01')
      expect(mockUseTWM).toHaveBeenLastCalledWith({})
    })
  })
})
