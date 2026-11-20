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
jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children, ...rest }: any) => <div {...rest}>{children}</div>,
}))

const mockUseAuthSession = useAuthSession as jest.Mock

/**
 * Sprint 888 (13D): a `/billing/usage` body exactly as `UsageResponse`
 * (backend/schemas/billing_schemas.py) sends it. Limits are the ones in
 * backend/shared/entitlements.py: Free 10 uploads / 3 clients, Solo 100 /
 * unlimited (0), Professional 500 / unlimited.
 */
function usageResponse(tier: 'free' | 'solo' | 'professional', uploadsUsed: number, clientsUsed: number) {
  const limits = { free: [10, 3], solo: [100, 0], professional: [500, 0] }[tier]
  return {
    uploads_used: uploadsUsed,
    uploads_limit: limits[0],
    diagnostics_used: uploadsUsed,
    diagnostics_limit: limits[0],
    clients_used: clientsUsed,
    clients_limit: limits[1],
    tier,
  }
}
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
      usage: usageResponse('solo', 5, 2),
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
      usage: usageResponse('free', 4, 1),
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
    // The real UsageMeter shows the Free allowance from the response.
    expect(screen.getByText('4 / 10')).toBeInTheDocument()
    expect(screen.getByText('1 / 3')).toBeInTheDocument()
  })

  it('a Professional subscription gets Contact us, not Add Seat, while team tiers are sales-only (Sprint 858)', () => {
    mockUseAuthSession.mockReturnValue({
      user: { is_verified: true, tier: 'professional' },
      isAuthenticated: true,
      isLoading: false,
    })
    mockUseBilling.mockReturnValue({
      subscription: { tier: 'professional', status: 'active', billing_interval: 'monthly', cancel_at_period_end: false, total_seats: 8, seat_count: 7, additional_seats: 1 },
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
    })
    render(<BillingSettingsPage />)
    expect(screen.queryByText('Add Seat')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Contact us to add seats/ })).toHaveAttribute('href', '/contact?inquiry=Organization')
    // Removing seats is not a purchase and stays self-serve.
    expect(screen.getByText('Remove Seat')).toBeInTheDocument()
  })

  it('renders the Solo allowance from a real /billing/usage response', () => {
    render(<BillingSettingsPage />)
    expect(screen.getByText('Diagnostics this month')).toBeInTheDocument()
    expect(screen.getByText('5 / 100')).toBeInTheDocument()
    // Solo clients are unlimited (clients_limit 0).
    expect(screen.getByText('Clients')).toBeInTheDocument()
    expect(screen.getByText('Unlimited')).toBeInTheDocument()
  })

  it('shows a Professional subscriber at the 500 limit as at limit', () => {
    mockUseBilling.mockReturnValue({
      ...mockUseBilling(),
      subscription: { tier: 'professional', status: 'active', billing_interval: 'monthly', cancel_at_period_end: false, total_seats: 7, seat_count: 7, additional_seats: 0 },
      usage: usageResponse('professional', 500, 12),
    })
    render(<BillingSettingsPage />)
    expect(screen.getByText('500 / 500')).toHaveClass('text-clay-600')
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
