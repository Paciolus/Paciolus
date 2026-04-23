/**
 * Sprint 689d: W2ReconciliationPage gating + happy-path render tests.
 */
import W2ReconciliationPage from '@/app/tools/w2-reconciliation/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useW2Reconciliation } from '@/hooks/useW2Reconciliation'
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(),
}))

jest.mock('@/hooks/useW2Reconciliation', () => ({
  useW2Reconciliation: jest.fn(),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseHook = useW2Reconciliation as jest.Mock

const defaultHookReturn = {
  status: 'idle' as const,
  result: null,
  error: '',
  analyze: jest.fn(),
  exportCsv: jest.fn(),
  reset: jest.fn(),
}

describe('W2ReconciliationPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseHook.mockReturnValue(defaultHookReturn)
  })

  it('renders GuestCTA for unauthenticated visitors', () => {
    mockUseAuthSession.mockReturnValue({
      user: null, isAuthenticated: false, isLoading: false, token: null,
    })
    render(<W2ReconciliationPage />)
    expect(screen.getByText('W-2 / W-3 Reconciliation')).toBeInTheDocument()
    expect(screen.getByText(/requires a verified account/i)).toBeInTheDocument()
  })

  it('renders UnverifiedCTA for authenticated but unverified users', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: false, tier: 'solo' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<W2ReconciliationPage />)
    expect(screen.getByText(/verify your email/i)).toBeInTheDocument()
  })

  it('renders upgrade gate for FREE tier', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<W2ReconciliationPage />)
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.queryByText(/Upload Reconciliation Inputs/i)).not.toBeInTheDocument()
  })

  it('renders upload surface + info cards + disclaimer for paid tiers', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<W2ReconciliationPage />)
    expect(screen.getAllByText('W-2 / W-3 Reconciliation').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Upload Reconciliation Inputs')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Run Reconciliation/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()
    expect(screen.getByText('Per-Box Reconciliation')).toBeInTheDocument()
    expect(screen.getByText('Form 941 Tie-Out')).toBeInTheDocument()
    expect(screen.getByText('Zero-Storage')).toBeInTheDocument()
    expect(screen.getByText(/candidates for review before filing W-2/i)).toBeInTheDocument()
  })
})
