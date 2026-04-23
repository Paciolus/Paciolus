/**
 * Sprint 689g: CashFlowProjectorPage gating + happy-path render tests.
 */
import CashFlowProjectorPage from '@/app/tools/cash-flow-projector/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useCashFlowProjector } from '@/hooks/useCashFlowProjector'
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(),
}))

jest.mock('@/hooks/useCashFlowProjector', () => ({
  useCashFlowProjector: jest.fn(),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseHook = useCashFlowProjector as jest.Mock

const defaultHookReturn = {
  status: 'idle' as const,
  result: null,
  error: '',
  project: jest.fn(),
  exportCsv: jest.fn(),
  reset: jest.fn(),
}

describe('CashFlowProjectorPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseHook.mockReturnValue(defaultHookReturn)
  })

  it('renders GuestCTA for unauthenticated visitors', () => {
    mockUseAuthSession.mockReturnValue({ user: null, isAuthenticated: false, isLoading: false, token: null })
    render(<CashFlowProjectorPage />)
    expect(screen.getByText('Cash Flow Projector')).toBeInTheDocument()
    expect(screen.getByText(/requires a verified account/i)).toBeInTheDocument()
  })

  it('renders UnverifiedCTA for authenticated but unverified users', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: false, tier: 'solo' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<CashFlowProjectorPage />)
    expect(screen.getByText(/verify your email/i)).toBeInTheDocument()
  })

  it('renders upgrade gate for FREE tier', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<CashFlowProjectorPage />)
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.queryByText(/Forecast Inputs/i)).not.toBeInTheDocument()
  })

  it('renders form + info cards + disclaimer for paid tiers', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'professional' }, isAuthenticated: true, isLoading: false, token: 't',
    })
    render(<CashFlowProjectorPage />)
    expect(screen.getAllByText('Cash Flow Projector').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Forecast Inputs')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Run Projection/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()
    expect(screen.getByText('Three-Scenario Forecast')).toBeInTheDocument()
    expect(screen.getByText('Min-Safe-Cash Alerts')).toBeInTheDocument()
    expect(screen.getByText('Zero-Storage')).toBeInTheDocument()
    expect(screen.getByText(/liquidity sensitivity, not a budget/i)).toBeInTheDocument()
  })
})
