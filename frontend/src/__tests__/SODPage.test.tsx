/**
 * Sprint 689b: SODPage gating + happy-path render tests.
 *
 * Sprint 789 retargeted the gating cases. SoD is no longer Enterprise-only, so
 * the boundary moved from Enterprise/below to paid/Free — the same boundary
 * every other paid tool has. Professional and Solo now get the upload surface;
 * only Free sees the gate.
 */
import SODPage from '@/app/tools/sod/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useSOD } from '@/hooks/useSOD'
import { render, screen } from '@/test-utils'

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(),
}))

jest.mock('@/hooks/useSOD', () => ({
  useSOD: jest.fn(),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseSOD = useSOD as jest.Mock

const defaultHookReturn = {
  status: 'idle' as const,
  result: null,
  rules: [],
  error: '',
  analyze: jest.fn(),
  loadRules: jest.fn(),
  exportCsv: jest.fn(),
  reset: jest.fn(),
}

describe('SODPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseSOD.mockReturnValue(defaultHookReturn)
  })

  it('renders GuestCTA for unauthenticated visitors', () => {
    mockUseAuthSession.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      token: null,
    })

    render(<SODPage />)

    expect(screen.getByText('Segregation of Duties Checker')).toBeInTheDocument()
    expect(screen.getByText(/requires a verified account on a paid plan/i)).toBeInTheDocument()
  })

  it('renders UnverifiedCTA for authenticated but unverified users', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: false, tier: 'enterprise' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<SODPage />)

    expect(screen.getByText(/verify your email/i)).toBeInTheDocument()
  })

  it('renders the upgrade gate for Free tier only', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<SODPage />)

    // UpgradeGate renders a generic "Upgrade Required" heading
    expect(screen.getByRole('heading', { name: /Upgrade Required/i, level: 3 })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /view plans/i })).toHaveAttribute('href', '/pricing')
    expect(screen.queryByText(/Upload Matrices/i)).not.toBeInTheDocument()
  })

  // Sprint 789: the regression this sprint fixed. SoD 403'd Solo and
  // Professional while the Terms of Service tier table, the pricing page and
  // the entitlements table all sold it to both. Both tiers are asserted
  // because the old gate was a single tier comparison — blocking either one
  // again should fail here.
  it.each(['solo', 'professional'])('renders the upload surface for %s tier', (tier) => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<SODPage />)

    expect(screen.getByText('Upload Matrices')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Run SoD Analysis/i })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /Upgrade Required/i })).not.toBeInTheDocument()
    expect(defaultHookReturn.loadRules).toHaveBeenCalled()
  })

  it('renders upload surface, info cards, and disclaimer for Enterprise tier', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'enterprise' },
      isAuthenticated: true,
      isLoading: false,
      token: 'test-token',
    })

    render(<SODPage />)

    // Hero
    expect(screen.getAllByText('Segregation of Duties Checker').length).toBeGreaterThanOrEqual(1)

    // loadRules fires on mount for any verified, authenticated user
    expect(defaultHookReturn.loadRules).toHaveBeenCalled()

    // Upload surface
    expect(screen.getByText('Upload Matrices')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Run SoD Analysis/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Download CSV/i })).toBeInTheDocument()

    // Info cards
    expect(screen.getByText('Hardcoded Rule Library')).toBeInTheDocument()
    expect(screen.getByText('Per-User Risk Ranking')).toBeInTheDocument()
    expect(screen.getByText('Zero-Storage')).toBeInTheDocument()

    // Disclaimer + badge + citation footer all cite COSO 2013
    expect(screen.getAllByText(/COSO 2013/i).length).toBeGreaterThanOrEqual(1)
    // Disclaimer body text is unique
    expect(screen.getByText(/segregation-of-incompatible-duties guidance/i)).toBeInTheDocument()
  })
})
