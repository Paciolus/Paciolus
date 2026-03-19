/**
 * UpgradeGate component tests
 *
 * Tests: access for paid tiers, restriction for free tier,
 * custom message, View Plans link.
 */
import { UpgradeGate } from '@/components/shared/UpgradeGate'
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

describe('UpgradeGate', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUser = null
  })

  it('renders children for solo tier (paid = all tools)', () => {
    mockUser = { tier: 'solo' }
    render(
      <UpgradeGate toolName="journal_entry_testing">
        <div>JE Testing Content</div>
      </UpgradeGate>
    )
    expect(screen.getByText('JE Testing Content')).toBeInTheDocument()
  })

  it('renders children for professional tier', () => {
    mockUser = { tier: 'professional' }
    render(
      <UpgradeGate toolName="ap_testing">
        <div>AP Content</div>
      </UpgradeGate>
    )
    expect(screen.getByText('AP Content')).toBeInTheDocument()
  })

  it('renders children for free tier on allowed tools', () => {
    mockUser = { tier: 'free' }
    render(
      <UpgradeGate toolName="trial_balance">
        <div>TB Content</div>
      </UpgradeGate>
    )
    expect(screen.getByText('TB Content')).toBeInTheDocument()
  })

  it('shows upgrade CTA for free tier on restricted tools', () => {
    mockUser = { tier: 'free' }
    render(
      <UpgradeGate toolName="journal_entry_testing">
        <div>Restricted Content</div>
      </UpgradeGate>
    )
    expect(screen.queryByText('Restricted Content')).not.toBeInTheDocument()
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
  })

  it('shows View Plans link', () => {
    mockUser = { tier: 'free' }
    render(
      <UpgradeGate toolName="ap_testing">
        <div>Content</div>
      </UpgradeGate>
    )
    const link = screen.getByRole('link', { name: 'View Plans' })
    expect(link).toHaveAttribute('href', '/pricing')
  })

  it('shows custom message', () => {
    mockUser = { tier: 'free' }
    render(
      <UpgradeGate toolName="payroll_testing" message="Custom restriction message.">
        <div>Content</div>
      </UpgradeGate>
    )
    expect(screen.getByText('Custom restriction message.')).toBeInTheDocument()
  })

  it('shows current plan name', () => {
    mockUser = { tier: 'free' }
    render(
      <UpgradeGate toolName="revenue_testing">
        <div>Content</div>
      </UpgradeGate>
    )
    expect(screen.getByText('Free')).toBeInTheDocument()
  })

  it('defaults to free when no user', () => {
    mockUser = null
    render(
      <UpgradeGate toolName="ap_testing">
        <div>Content</div>
      </UpgradeGate>
    )
    expect(screen.getByText('Upgrade Required')).toBeInTheDocument()
  })
})
