/**
 * Council 2026-11-25 D-2: /checkout/success says the plan is active only after
 * /billing/subscription confirms it (the tier arrives by Stripe webhook).
 */
import React from 'react'
import CheckoutSuccessPage from '@/app/(auth)/checkout/success/page'
import { render, screen, act } from '@/test-utils'

const mockFetchSubscription = jest.fn()
const mockRefreshUser = jest.fn()
let mockAuth: { token: string | null; isLoading: boolean } = { token: 'tok', isLoading: false }

jest.mock('@/hooks/useBilling', () => ({
  useBilling: () => ({ fetchSubscription: mockFetchSubscription }),
}))

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ ...mockAuth, refreshUser: mockRefreshUser }),
}))

jest.mock('next/link', () => {
  return ({ children, href, ...rest }: any) => (
    <a href={href} {...rest}>
      {children}
    </a>
  )
})

async function flush() {
  await act(async () => {
    await Promise.resolve()
  })
}

describe('CheckoutSuccessPage', () => {
  beforeEach(() => {
    jest.useFakeTimers()
    jest.clearAllMocks()
    mockAuth = { token: 'tok', isLoading: false }
    mockRefreshUser.mockResolvedValue(undefined)
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('does not claim an upgrade before the subscription is confirmed', async () => {
    mockFetchSubscription.mockResolvedValue({ tier: 'free', status: 'active' })
    render(<CheckoutSuccessPage />)
    await flush()
    expect(screen.getByTestId('checkout-status')).toHaveTextContent(/Confirming your subscription/)
    expect(screen.queryByText(/new plan is active/)).not.toBeInTheDocument()
  })

  it('confirms once the subscription is trialing', async () => {
    mockFetchSubscription
      .mockResolvedValueOnce({ tier: 'free', status: 'active' })
      .mockResolvedValue({ tier: 'solo', status: 'trialing' })
    render(<CheckoutSuccessPage />)
    await flush()
    await act(async () => {
      jest.advanceTimersByTime(2000)
    })
    await flush()
    await flush()
    expect(screen.getByTestId('checkout-status')).toHaveTextContent(/new plan is active/)
    expect(mockRefreshUser).toHaveBeenCalled()
    expect(screen.getByRole('link', { name: 'Start Using Your Tools' })).toBeInTheDocument()
  })

  it('says it is not confirmed yet after polling gives up, and offers to check again', async () => {
    mockFetchSubscription.mockResolvedValue({ tier: 'free', status: 'active' })
    render(<CheckoutSuccessPage />)
    for (let i = 0; i < 16; i++) {
      await flush()
      await act(async () => {
        jest.advanceTimersByTime(2000)
      })
    }
    await flush()
    expect(screen.getByTestId('checkout-status')).toHaveTextContent(/has not confirmed your subscription yet/)
    expect(screen.getByRole('button', { name: 'Check Again' })).toBeInTheDocument()
    expect(mockFetchSubscription).toHaveBeenCalledTimes(15)
  })

  it('asks a signed-out visitor to sign in instead of claiming anything', async () => {
    mockAuth = { token: null, isLoading: false }
    render(<CheckoutSuccessPage />)
    await flush()
    expect(screen.getByTestId('checkout-status')).toHaveTextContent(/Sign in to see your subscription/)
    expect(mockFetchSubscription).not.toHaveBeenCalled()
  })
})
