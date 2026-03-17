/**
 * Sprint 548: Billing Settings page tests.
 */
import BillingSettingsPage from '@/app/settings/billing/page'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useBilling } from '@/hooks/useBilling'
import { render, screen } from '@/test-utils'

const mockFetchSubscription = jest.fn()
const mockFetchUsage = jest.fn()
const mockCancelSubscription = jest.fn()
const mockReactivateSubscription = jest.fn()
const mockGetPortalUrl = jest.fn()
const mockAddSeats = jest.fn()
const mockRemoveSeats = jest.fn()
const mockPush = jest.fn()

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({
    user: { is_verified: true, tier: 'solo' },
    isAuthenticated: true,
    isLoading: false,
  })),
}))

jest.mock('@/hooks/useBilling', () => ({
  useBilling: jest.fn(() => ({
    subscription: null,
    usage: null,
    isLoading: false,
    error: null,
    fetchSubscription: mockFetchSubscription,
    fetchUsage: mockFetchUsage,
    cancelSubscription: mockCancelSubscription,
    reactivateSubscription: mockReactivateSubscription,
    getPortalUrl: mockGetPortalUrl,
    addSeats: mockAddSeats,
    removeSeats: mockRemoveSeats,
  })),
}))

jest.mock('@/components/billing/CancelModal', () => ({
  CancelModal: () => null,
}))
jest.mock('@/components/billing/PlanCard', () => ({
  PlanCard: ({ tier }: { tier: string }) => <div data-testid="plan-card">{tier}</div>,
}))
jest.mock('@/components/billing/UpgradeModal', () => ({
  UpgradeModal: () => null,
}))
jest.mock('@/components/shared/UsageMeter', () => ({
  UsageMeter: ({ label }: { label: string }) => <div data-testid="usage-meter">{label}</div>,
}))
jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children, ...rest }: any) => <div {...rest}>{children}</div>,
}))

const mockUseAuthSession = useAuthSession as jest.Mock
const mockUseBilling = useBilling as jest.Mock

describe('BillingSettingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'solo' },
      isAuthenticated: true,
      isLoading: false,
    })
    mockUseBilling.mockReturnValue({
      subscription: { tier: 'solo', status: 'active', billing_interval: 'monthly', cancel_at_period_end: false, total_seats: 1, seat_count: 1, additional_seats: 0 },
      usage: { diagnostics_used: 5, diagnostics_limit: 50, clients_used: 2, clients_limit: 10 },
      isLoading: false,
      error: null,
      fetchSubscription: mockFetchSubscription,
      fetchUsage: mockFetchUsage,
      cancelSubscription: mockCancelSubscription,
      reactivateSubscription: mockReactivateSubscription,
      getPortalUrl: mockGetPortalUrl,
      addSeats: mockAddSeats,
      removeSeats: mockRemoveSeats,
    })
  })

  it('renders plan details for a subscribed user', () => {
    render(<BillingSettingsPage />)
    expect(screen.getByText('Billing & Subscription')).toBeInTheDocument()
    expect(screen.getByTestId('plan-card')).toBeInTheDocument()
    expect(screen.getByText('Current Plan')).toBeInTheDocument()
  })

  it('renders upgrade CTA for a free-tier user', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'free' },
      isAuthenticated: true,
      isLoading: false,
    })
    mockUseBilling.mockReturnValue({
      subscription: null,
      usage: { diagnostics_used: 0, diagnostics_limit: 3, clients_used: 0, clients_limit: 1 },
      isLoading: false,
      error: null,
      fetchSubscription: mockFetchSubscription,
      fetchUsage: mockFetchUsage,
      cancelSubscription: mockCancelSubscription,
      reactivateSubscription: mockReactivateSubscription,
      getPortalUrl: mockGetPortalUrl,
      addSeats: mockAddSeats,
      removeSeats: mockRemoveSeats,
    })
    render(<BillingSettingsPage />)
    expect(screen.getByText('Start Free Trial')).toBeInTheDocument()
  })

  it('renders usage meters when usage data is available', () => {
    render(<BillingSettingsPage />)
    const meters = screen.getAllByTestId('usage-meter')
    expect(meters.length).toBeGreaterThanOrEqual(2)
  })

  it('renders error banner when billing fetch fails', () => {
    mockUseBilling.mockReturnValue({
      subscription: null,
      usage: null,
      isLoading: false,
      error: 'Failed to fetch billing data',
      fetchSubscription: mockFetchSubscription,
      fetchUsage: mockFetchUsage,
      cancelSubscription: mockCancelSubscription,
      reactivateSubscription: mockReactivateSubscription,
      getPortalUrl: mockGetPortalUrl,
      addSeats: mockAddSeats,
      removeSeats: mockRemoveSeats,
    })
    render(<BillingSettingsPage />)
    expect(screen.getByText('Failed to fetch billing data')).toBeInTheDocument()
  })

  it('shows loading spinner during auth loading', () => {
    mockUseAuthSession.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
    })
    render(<BillingSettingsPage />)
    expect(screen.getByText('Loading billing...')).toBeInTheDocument()
  })

  it('fetches subscription and usage on mount', () => {
    render(<BillingSettingsPage />)
    expect(mockFetchSubscription).toHaveBeenCalled()
    expect(mockFetchUsage).toHaveBeenCalled()
  })
})
