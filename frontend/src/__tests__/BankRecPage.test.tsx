/**
 * Sprint 96.5: Bank Reconciliation page tests (10 tests)
 */
import BankRecPage from '@/app/tools/bank-rec/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useBankReconciliation } from '@/hooks/useBankReconciliation'
import { fireEvent, render, screen } from '@/test-utils'

const mockRunReconciliation = jest.fn()
const mockReset = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
  })),
}))

jest.mock('@/hooks/useBankReconciliation', () => ({
  useBankReconciliation: jest.fn(() => ({
    status: 'idle', result: null, error: null, reconcile: mockRunReconciliation, reset: mockReset,
  })),
}))

jest.mock('@/utils', () => {
  const actual = jest.requireActual('@/utils')
  return { ...actual, apiDownload: jest.fn().mockResolvedValue({ ok: true, blob: new Blob(), filename: 'test.csv' }), downloadBlob: jest.fn() }
})

jest.mock('@/components/bankRec', () => ({
  MatchSummaryCards: () => <div data-testid="match-summary">Summary</div>,
  BankRecMatchTable: () => <div data-testid="match-table">Matches</div>,
  ReconciliationBridge: () => <div data-testid="rec-bridge">Bridge</div>,
  SplitSearchNotice: ({ disclosure }: any) => <div data-testid="split-search-notice">{disclosure.note}</div>,
}))

jest.mock('@/components/shared', () => ({
  FileDropZone: ({ label }: any) => <div data-testid={`file-drop-${label}`}>{label}</div>,
  GuestCTA: ({ description }: any) => <div data-testid="guest-cta">{description}</div>,
  ZeroStorageNotice: () => <div data-testid="zero-storage-notice">Zero-Storage</div>,
  DisclaimerBox: ({ children }: any) => <div data-testid="disclaimer-box">{children}</div>,
  ToolStatePresence: ({ children }: any) => <div data-testid="tool-state-presence">{children}</div>,
  UpgradeGate: ({ children }: any) => <>{children}</>,
  Citation: ({ code }: any) => <span data-testid="citation">{code}</span>,
  CitationFooter: () => <div data-testid="citation-footer">Citations</div>,
}))
jest.mock('@/components/shared/proof', () => ({
  ProofSummaryBar: () => <div data-testid="proof-summary-bar">Proof</div>,
  ProofPanel: () => null,
  extractBankRecProof: () => ({ overallLevel: 'adequate', overallScore: 75, categories: [] }),
}))
jest.mock('@/hooks/useCanvasAccentSync', () => ({
  useCanvasAccentSync: jest.fn(),
}))
jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseBankRec = useBankReconciliation as jest.Mock

describe('BankRecPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuthSession.mockReturnValue({ user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
    mockUseBankRec.mockReturnValue({ status: 'idle', result: null, error: null, reconcile: mockRunReconciliation, reset: mockReset })
  })

  it('renders hero header', () => {
    render(<BankRecPage />)
    expect(screen.getByText('Bank Statement Reconciliation')).toBeInTheDocument()
  })

  it('shows dual upload zones for authenticated verified user', () => {
    render(<BankRecPage />)
    expect(screen.getByText('Bank Statement')).toBeInTheDocument()
    expect(screen.getByText('GL Cash Detail')).toBeInTheDocument()
  })

  it('shows sign-in CTA for unauthenticated user', () => {
    mockUseAuthSession.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
    render(<BankRecPage />)
    expect(screen.getByTestId('guest-cta')).toBeInTheDocument()
    expect(screen.getByText(/Bank Reconciliation requires a verified account/)).toBeInTheDocument()
  })

  it('shows loading state', () => {
    mockUseBankRec.mockReturnValue({ status: 'loading', result: null, error: null, reconcile: mockRunReconciliation, reset: mockReset })
    render(<BankRecPage />)
    expect(screen.getByText(/Reconciling/)).toBeInTheDocument()
  })

  it('shows error state with retry button', () => {
    mockUseBankRec.mockReturnValue({ status: 'error', result: null, error: 'No matching columns', reconcile: mockRunReconciliation, reset: mockReset })
    render(<BankRecPage />)
    expect(screen.getByText('Reconciliation Failed')).toBeInTheDocument()
    expect(screen.getByText('No matching columns')).toBeInTheDocument()
    expect(screen.getByText('Try Again')).toBeInTheDocument()
  })

  it('shows result components on success', () => {
    mockUseBankRec.mockReturnValue({
      status: 'success', error: null, reconcile: mockRunReconciliation, reset: mockReset,
      result: { summary: { matched_count: 0, matched_amount: 0, bank_only_count: 0, bank_only_amount: 0, ledger_only_count: 0, ledger_only_amount: 0, reconciling_difference: 0, total_bank: 0, total_ledger: 0, matches: [] }, bank_column_detection: { requires_mapping: false, detection_notes: [] }, ledger_column_detection: { requires_mapping: false, detection_notes: [] } },
    })
    render(<BankRecPage />)
    expect(screen.getByTestId('match-summary')).toBeInTheDocument()
    expect(screen.getByTestId('match-table')).toBeInTheDocument()
    expect(screen.getByTestId('rec-bridge')).toBeInTheDocument()
  })

  it('shows the split-search disclosure when the API returns one (Sprint 833)', () => {
    mockUseBankRec.mockReturnValue({
      status: 'success', error: null, reconcile: mockRunReconciliation, reset: mockReset,
      result: {
        summary: { matched_count: 0, matched_amount: 0, bank_only_count: 1, bank_only_amount: 10, ledger_only_count: 0, ledger_only_amount: 0, reconciling_difference: 10, total_bank: 10, total_ledger: 0, matches: [] },
        bank_column_detection: { requires_mapping: false, detection_notes: [] },
        ledger_column_detection: { requires_mapping: false, detection_notes: [] },
        split_search: { date_window_days: 0, max_candidates: 20, max_set_size: 4, limited_count: 1, note: '1 bank item was not searched exhaustively' },
      },
    })
    render(<BankRecPage />)
    expect(screen.getByTestId('split-search-notice')).toHaveTextContent('1 bank item was not searched exhaustively')
  })

  it('shows export button on success', () => {
    mockUseBankRec.mockReturnValue({
      status: 'success', error: null, reconcile: mockRunReconciliation, reset: mockReset,
      result: { summary: { matched_count: 0, matched_amount: 0, bank_only_count: 0, bank_only_amount: 0, ledger_only_count: 0, ledger_only_amount: 0, reconciling_difference: 0, total_bank: 0, total_ledger: 0, matches: [] }, bank_column_detection: { requires_mapping: false, detection_notes: [] }, ledger_column_detection: { requires_mapping: false, detection_notes: [] } },
    })
    render(<BankRecPage />)
    expect(screen.getByText('Export CSV')).toBeInTheDocument()
    expect(screen.getByText('New Reconciliation')).toBeInTheDocument()
  })

  it('shows info cards in idle state', () => {
    render(<BankRecPage />)
    expect(screen.getByText('Exact Matching')).toBeInTheDocument()
    expect(screen.getByText('CSV Export')).toBeInTheDocument()
  })

  // Sprint 839: per-run materiality
  describe('run settings', () => {
    const openPanel = () => fireEvent.click(screen.getByRole('button', { name: /Run settings/ }))

    it('passes no thresholds until the user enters one', () => {
      render(<BankRecPage />)
      expect(mockUseBankRec).toHaveBeenLastCalledWith({ materiality: undefined, performanceMateriality: undefined })
    })

    it('passes entered materiality and performance materiality to the hook', () => {
      render(<BankRecPage />)
      openPanel()
      fireEvent.change(screen.getByLabelText('Materiality'), { target: { value: '80,000' } })
      fireEvent.change(screen.getByLabelText('Performance materiality'), { target: { value: '60000' } })
      expect(mockUseBankRec).toHaveBeenLastCalledWith({ materiality: 80000, performanceMateriality: 60000 })
      expect(screen.getByRole('button', { name: /Run settings/ })).toHaveTextContent('2 set for this run')
    })

    it('shows an error and blocks the run for an unusable value', () => {
      render(<BankRecPage />)
      openPanel()
      fireEvent.change(screen.getByLabelText('Materiality'), { target: { value: '-10' } })
      expect(screen.getByText('Materiality must be 0 or more.')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Reconcile' })).toBeDisabled()
    })

    it('states which thresholds the run used and where each came from', () => {
      mockUseBankRec.mockReturnValue({
        status: 'success', error: null, reconcile: mockRunReconciliation, reset: mockReset,
        result: { summary: { matched_count: 0, matched_amount: 0, bank_only_count: 0, bank_only_amount: 0, ledger_only_count: 0, ledger_only_amount: 0, reconciling_difference: 0, total_bank: 0, total_ledger: 0, matches: [] }, bank_column_detection: { requires_mapping: false, detection_notes: [] }, ledger_column_detection: { requires_mapping: false, detection_notes: [] },
          active_thresholds: {
            materiality: '80000.0', performance_materiality: '50000.00', amount_tolerance: '0.01', date_tolerance_days: 0,
            materiality_source: 'caller', threshold_sources: { materiality: 'caller', performance_materiality: 'default' },
          },
        },
      })
      render(<BankRecPage />)
      const applied = screen.getByTestId('bank-rec-thresholds-applied')
      expect(applied).toHaveTextContent('Materiality: $80,000.00 (entered for this run)')
      expect(applied).toHaveTextContent('Performance materiality: $50,000.00 (Paciolus default)')
    })
  })
})
