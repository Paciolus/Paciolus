/**
 * Pricing Launch Billing Hook Tests
 *
 * Tests the useBilling hook API interactions: subscription, usage,
 * checkout, cancel, reactivate, portal, and seat management.
 */
import { renderHook, act } from '@testing-library/react'
import { useBilling } from '@/hooks/useBilling'

// ── Mocks ─────────────────────────────────────────────────────────

const mockToken = 'test-jwt-token'

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ token: mockToken }),
}))

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()

jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}))

describe('PricingLaunchBillingHook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiGet.mockResolvedValue({ data: null, ok: false, status: 500, error: 'default' })
    mockApiPost.mockResolvedValue({ data: null, ok: false, status: 500, error: 'default' })
  })

  // ── fetchSubscription ─────────────────────────────────────

  it('fetchSubscription returns subscription data on success', async () => {
    const subData = {
      id: 1, tier: 'solo', status: 'active', billing_interval: 'monthly',
      current_period_start: null, current_period_end: null,
      cancel_at_period_end: false, seat_count: 1, additional_seats: 0, total_seats: 1,
    }
    mockApiGet.mockResolvedValueOnce({ data: subData, ok: true, status: 200 })

    const { result } = renderHook(() => useBilling())
    let data: unknown
    await act(async () => {
      data = await result.current.fetchSubscription()
    })

    expect(data).toEqual(subData)
    expect(mockApiGet).toHaveBeenCalledWith('/billing/subscription', mockToken)
    expect(result.current.subscription).toEqual(subData)
  })

  it('fetchSubscription handles 401 auth error', async () => {
    mockApiGet.mockResolvedValueOnce({ data: null, ok: false, status: 401, error: 'Unauthorized' })

    const { result } = renderHook(() => useBilling())
    let data: unknown
    await act(async () => {
      data = await result.current.fetchSubscription()
    })

    expect(data).toBeNull()
    expect(result.current.error).toBe('Unauthorized')
  })

  it('fetchSubscription handles network error', async () => {
    mockApiGet.mockResolvedValueOnce({ data: null, ok: false, status: 0, error: 'Network error' })

    const { result } = renderHook(() => useBilling())
    await act(async () => {
      await result.current.fetchSubscription()
    })

    expect(result.current.error).toBe('Network error')
  })

  it('fetchSubscription returns null for free user (no sub)', async () => {
    mockApiGet.mockResolvedValueOnce({
      data: { tier: 'free', status: 'active', id: null, billing_interval: null,
        current_period_start: null, current_period_end: null,
        cancel_at_period_end: false, seat_count: 1, additional_seats: 0, total_seats: 1 },
      ok: true, status: 200,
    })

    const { result } = renderHook(() => useBilling())
    let data: unknown
    await act(async () => {
      data = await result.current.fetchSubscription()
    })

    expect(data).toBeTruthy()
    expect((data as { tier: string }).tier).toBe('free')
  })

  // ── fetchUsage ────────────────────────────────────────────

  it('fetchUsage returns usage data on success', async () => {
    const usageData = {
      diagnostics_used: 5, diagnostics_limit: 20,
      clients_used: 2, clients_limit: 10, tier: 'solo',
    }
    mockApiGet.mockResolvedValueOnce({ data: usageData, ok: true, status: 200 })

    const { result } = renderHook(() => useBilling())
    let data: unknown
    await act(async () => {
      data = await result.current.fetchUsage()
    })

    expect(data).toEqual(usageData)
    expect(mockApiGet).toHaveBeenCalledWith('/billing/usage', mockToken)
  })

  it('fetchUsage handles error', async () => {
    mockApiGet.mockResolvedValueOnce({ data: null, ok: false, status: 500, error: 'Server error' })

    const { result } = renderHook(() => useBilling())
    await act(async () => {
      await result.current.fetchUsage()
    })

    expect(result.current.error).toBe('Server error')
  })

  // ── createCheckoutSession ─────────────────────────────────

  it('createCheckoutSession calls API with correct params', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { checkout_url: 'https://checkout.stripe.com/test' },
      ok: true, status: 201,
    })

    const { result } = renderHook(() => useBilling())
    let url: string | null = null
    await act(async () => {
      url = await result.current.createCheckoutSession('solo', 'monthly')
    })

    expect(url).toBe('https://checkout.stripe.com/test')
    expect(mockApiPost).toHaveBeenCalledWith(
      '/billing/create-checkout-session',
      mockToken,
      expect.objectContaining({
        tier: 'solo',
        interval: 'monthly',
      })
    )
    // Verify URL fields are NOT sent — redirect URLs are server-side derived
    const body = mockApiPost.mock.calls[0][2] as Record<string, unknown>
    expect(body).not.toHaveProperty('success_url')
    expect(body).not.toHaveProperty('cancel_url')
  })

  it('createCheckoutSession includes promo_code when provided', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { checkout_url: 'https://checkout.stripe.com/promo' },
      ok: true, status: 201,
    })

    const { result } = renderHook(() => useBilling())
    await act(async () => {
      await result.current.createCheckoutSession('solo', 'monthly', undefined, 'MONTHLY20')
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/billing/create-checkout-session',
      mockToken,
      expect.objectContaining({ promo_code: 'MONTHLY20' })
    )
  })

  it('createCheckoutSession includes seat_count when provided', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { checkout_url: 'https://checkout.stripe.com/seats' },
      ok: true, status: 201,
    })

    const { result } = renderHook(() => useBilling())
    await act(async () => {
      await result.current.createCheckoutSession('team', 'monthly', 5)
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/billing/create-checkout-session',
      mockToken,
      expect.objectContaining({ seat_count: 5 })
    )
  })

  it('createCheckoutSession returns checkout URL', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { checkout_url: 'https://checkout.stripe.com/url' },
      ok: true, status: 201,
    })

    const { result } = renderHook(() => useBilling())
    let url: string | null = null
    await act(async () => {
      url = await result.current.createCheckoutSession('solo', 'monthly')
    })

    expect(url).toBe('https://checkout.stripe.com/url')
  })

  it('createCheckoutSession handles 400 bad request', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: null, ok: false, status: 400, error: 'No price configured',
    })

    const { result } = renderHook(() => useBilling())
    let url: string | null = null
    await act(async () => {
      url = await result.current.createCheckoutSession('solo', 'monthly')
    })

    expect(url).toBeNull()
    expect(result.current.error).toBe('No price configured')
  })

  // ── cancelSubscription ────────────────────────────────────

  it('cancelSubscription calls cancel endpoint', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { message: 'Canceled' }, ok: true, status: 200,
    })

    const { result } = renderHook(() => useBilling())
    let success: boolean = false
    await act(async () => {
      success = await result.current.cancelSubscription()
    })

    expect(success).toBe(true)
    expect(mockApiPost).toHaveBeenCalledWith('/billing/cancel', mockToken, {})
  })

  it('cancelSubscription returns false on error', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: null, ok: false, status: 404, error: 'No subscription',
    })

    const { result } = renderHook(() => useBilling())
    let success: boolean = true
    await act(async () => {
      success = await result.current.cancelSubscription()
    })

    expect(success).toBe(false)
  })

  // ── reactivateSubscription ────────────────────────────────

  it('reactivateSubscription calls reactivate endpoint', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { message: 'Reactivated' }, ok: true, status: 200,
    })

    const { result } = renderHook(() => useBilling())
    let success: boolean = false
    await act(async () => {
      success = await result.current.reactivateSubscription()
    })

    expect(success).toBe(true)
    expect(mockApiPost).toHaveBeenCalledWith('/billing/reactivate', mockToken, {})
  })

  // ── getPortalUrl ──────────────────────────────────────────

  it('getPortalUrl returns portal URL on success', async () => {
    mockApiGet.mockResolvedValueOnce({
      data: { portal_url: 'https://billing.stripe.com/portal' },
      ok: true, status: 200,
    })

    const { result } = renderHook(() => useBilling())
    let url: string | null = null
    await act(async () => {
      url = await result.current.getPortalUrl()
    })

    expect(url).toBe('https://billing.stripe.com/portal')
    expect(mockApiGet).toHaveBeenCalledWith('/billing/portal-session', mockToken)
  })

  it('getPortalUrl handles no billing account', async () => {
    mockApiGet.mockResolvedValueOnce({
      data: null, ok: false, status: 404, error: 'No billing account',
    })

    const { result } = renderHook(() => useBilling())
    let url: string | null = 'initial'
    await act(async () => {
      url = await result.current.getPortalUrl()
    })

    expect(url).toBeNull()
  })

  // ── addSeats ──────────────────────────────────────────────

  it('addSeats calls add-seats with correct body', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { message: 'Added', seat_count: 3, additional_seats: 5, total_seats: 8 },
      ok: true, status: 200,
    })

    const { result } = renderHook(() => useBilling())
    let success: boolean = false
    await act(async () => {
      success = await result.current.addSeats(5)
    })

    expect(success).toBe(true)
    expect(mockApiPost).toHaveBeenCalledWith('/billing/add-seats', mockToken, { seats: 5 })
  })

  // ── removeSeats ───────────────────────────────────────────

  it('removeSeats calls remove-seats with correct body', async () => {
    mockApiPost.mockResolvedValueOnce({
      data: { message: 'Removed', seat_count: 3, additional_seats: 2, total_seats: 5 },
      ok: true, status: 200,
    })

    const { result } = renderHook(() => useBilling())
    let success: boolean = false
    await act(async () => {
      success = await result.current.removeSeats(3)
    })

    expect(success).toBe(true)
    expect(mockApiPost).toHaveBeenCalledWith('/billing/remove-seats', mockToken, { seats: 3 })
  })

  // ── Loading/error state ───────────────────────────────────

  it('isLoading starts as false', () => {
    const { result } = renderHook(() => useBilling())
    expect(result.current.isLoading).toBe(false)
  })

  it('error state cleared on successful retry', async () => {
    // First call fails
    mockApiGet.mockResolvedValueOnce({
      data: null, ok: false, status: 500, error: 'Temporary error',
    })

    const { result } = renderHook(() => useBilling())
    await act(async () => {
      await result.current.fetchSubscription()
    })
    expect(result.current.error).toBe('Temporary error')

    // Second call succeeds
    mockApiGet.mockResolvedValueOnce({
      data: { id: 1, tier: 'solo', status: 'active', billing_interval: 'monthly',
        current_period_start: null, current_period_end: null,
        cancel_at_period_end: false, seat_count: 1, additional_seats: 0, total_seats: 1 },
      ok: true, status: 200,
    })
    await act(async () => {
      await result.current.fetchSubscription()
    })
    expect(result.current.error).toBeNull()
  })
})
