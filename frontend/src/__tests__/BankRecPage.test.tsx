/**
 * Sprint 96.5: Bank Reconciliation page tests (10 tests)
 */
import BankRecPage from '@/app/tools/bank-rec/page'
import { useAuth } from '@/contexts/AuthContext'
import { useBankReconciliation } from '@/hooks/useBankReconciliation'
import { render, screen } from '@/test-utils'

const mockRunReconciliation = jest.fn()
const mockReset = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token',
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


const mockUseAuth = useAuth as jest.Mock
const mockUseBankRec = useBankReconciliation as jest.Mock

describe('BankRecPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: { is_verified: true }, isAuthenticated: true, isLoading: false, logout: jest.fn(), token: 'test-token' })
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
    mockUseAuth.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, logout: jest.fn(), token: null })
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
})
