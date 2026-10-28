/**
 * FeatureGate component tests
 *
 * Tests: access granted, access denied, hidden mode,
 * custom message, current plan display.
 */
import { FeatureGate } from '@/components/shared/FeatureGate'
import { render, screen } from '@/test-utils'

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}))

let mockUser: any = null
jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ user: mockUser }),
}))

jest.mock('@/utils/telemetry', () => ({
  trackEvent: jest.fn(),
}))

describe('FeatureGate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUser = null
  })

  it('renders children when user has access (enterprise accessing enterprise feature)', () => {
    mockUser = { tier: 'enterprise' }
    render(
      <FeatureGate feature="bulk_upload">
        <div>Protected Content</div>
      </FeatureGate>
    )
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('renders children when user tier exceeds minimum (enterprise accessing professional feature)', () => {
    mockUser = { tier: 'enterprise' }
    render(
      <FeatureGate feature="export_sharing">
        <div>Sharing Feature</div>
      </FeatureGate>
    )
    expect(screen.getByText('Sharing Feature')).toBeInTheDocument()
  })

  it('shows upgrade CTA when user lacks access', () => {
    mockUser = { tier: 'solo' }
    render(
      <FeatureGate feature="export_sharing">
        <div>Hidden Content</div>
      </FeatureGate>
    )
    expect(screen.queryByText('Hidden Content')).not.toBeInTheDocument()
    expect(screen.getByText('Export Sharing')).toBeInTheDocument()
    expect(screen.getByText(/requires a Professional plan/)).toBeInTheDocument()
  })

  // Sprint 858: every gated feature needs Professional or Enterprise, which are
  // sales-only while SELF_SERVE_TEAM_TIERS_ENABLED is off.
  it.each(['admin_dashboard', 'export_sharing', 'custom_branding'] as const)(
    'shows a Contact us link (not View Plans) for %s while team tiers are sales-only',
    (feature) => {
      mockUser = { tier: 'free' }
      render(
        <FeatureGate feature={feature}>
          <div>Dashboard</div>
        </FeatureGate>
      )
      expect(screen.queryByText('View Plans')).not.toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Contact us' })).toHaveAttribute('href', '/contact?inquiry=Organization')
    },
  )

  it('renders nothing when hidden mode is enabled and access denied', () => {
    mockUser = { tier: 'free' }
    const { container } = render(
      <FeatureGate feature="bulk_upload" hidden>
        <div>Content</div>
      </FeatureGate>
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows custom message when provided', () => {
    mockUser = { tier: 'free' }
    render(
      <FeatureGate feature="export_sharing" message="Custom upgrade message here.">
        <div>Content</div>
      </FeatureGate>
    )
    expect(screen.getByText('Custom upgrade message here.')).toBeInTheDocument()
  })

  it('shows current plan name', () => {
    mockUser = { tier: 'solo' }
    render(
      <FeatureGate feature="admin_dashboard">
        <div>Content</div>
      </FeatureGate>
    )
    expect(screen.getByText('Solo')).toBeInTheDocument()
  })

  it('defaults to free tier when no user', () => {
    mockUser = null
    render(
      <FeatureGate feature="export_sharing">
        <div>Content</div>
      </FeatureGate>
    )
    expect(screen.getByText('Free')).toBeInTheDocument()
  })
})
