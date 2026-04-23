/**
 * Sprint 689c: IntercompanyEliminationPage gating + happy-path render tests.
 */
import IntercompanyEliminationPage from '@/app/tools/intercompany/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useIntercompanyElimination } from '@/hooks/useIntercompanyElimination'
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(),
}))

jest.mock('@/hooks/useIntercompanyElimination', () => ({
  useIntercompanyElimination: jest.fn(),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseIntercompany = useIntercompanyElimination as jest.Mock

const defaultHookReturn = {
  status: 'idle' as const,
  result: null,
  error: '',
  analyze: jest.fn(),
  exportCsv: jest.fn(),
  reset: jest.fn(),
}

describe('IntercompanyEliminationPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseIntercompany.mockReturnValue(defaultHookReturn)
  })

  it('renders GuestCTA for unauthenticated visitors', () => {
    mockUseAuthSession.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      token: null,
    })

    render(<IntercompanyEliminationPage />)

    expect(screen.getByText('Intercompany Elimination')).toBeInTheDocument()
    expect(screen.getByText(/requires a verified account/i)).toBeInTheDocument()
  })

  it('renders UnverifiedCTA for authenticated but unverified users', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: false, tier: 'solo' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<IntercompanyEliminationPage />)

    expect(screen.getByText(/verify your email/i)).toBeInTheDocument()
  })

  it('renders upgrade gate for FREE tier', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<IntercompanyEliminationPage />)

    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /view plans/i })).toHaveAttribute('href', '/pricing')
    expect(screen.queryByText(/Upload Multi-Entity Trial Balance/i)).not.toBeInTheDocument()
  })

  it('renders upload surface, info cards, and disclaimer for paid tiers', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'professional' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<IntercompanyEliminationPage />)

    expect(screen.getAllByText('Intercompany Elimination').length).toBeGreaterThanOrEqual(1)

    expect(screen.getByText('Upload Multi-Entity Trial Balance')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Run Consolidation/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()

    expect(screen.getByText('Automatic Direction Inference')).toBeInTheDocument()
    expect(screen.getByText('Configurable Tolerance')).toBeInTheDocument()
    expect(screen.getByText('Zero-Storage')).toBeInTheDocument()

    // Disclaimer body sentence is unique (distinct from hero badge / citation footer)
    expect(screen.getByText(/elimination entries on matched reciprocal intercompany balances/i)).toBeInTheDocument()
  })
})
