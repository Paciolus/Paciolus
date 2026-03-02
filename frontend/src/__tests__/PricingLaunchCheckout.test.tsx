/**
 * Pricing Launch Checkout Page Tests
 *
 * Tests the checkout page rendering, seat stepper, promo code input,
 * price breakdown, and interaction logic.
 */
import React from 'react'
import CheckoutPage from '@/app/(auth)/checkout/page'
import { render, screen, fireEvent, waitFor } from '@/test-utils'

// ── Mocks ─────────────────────────────────────────────────────────

const mockCreateCheckoutSession = jest.fn()
const mockUseBilling = {
  subscription: null,
  usage: null,
  isLoading: false,
  error: null,
  fetchSubscription: jest.fn(),
  fetchUsage: jest.fn(),
  createCheckoutSession: mockCreateCheckoutSession,
  cancelSubscription: jest.fn(),
  reactivateSubscription: jest.fn(),
  getPortalUrl: jest.fn(),
  addSeats: jest.fn(),
  removeSeats: jest.fn(),
}

jest.mock('@/hooks/useBilling', () => ({
  useBilling: () => mockUseBilling,
}))

jest.mock('framer-motion', () => {
  const R = require('react')
  return {
    motion: new Proxy(
      {},
      {
        get: (_: unknown, tag: string) =>
          R.forwardRef(
            (
              {
                initial,
                animate,
                exit,
                transition,
                variants,
                whileHover,
                whileInView,
                whileTap,
                viewport,
                layout,
                layoutId,
                ...rest
              }: any,
              ref: any
            ) => R.createElement(tag, { ...rest, ref })
          ),
      }
    ),
    AnimatePresence: ({ children }: any) => children,
  }
})

jest.mock('next/link', () => {
  return ({ children, href, ...rest }: any) => (
    <a href={href} {...rest}>
      {children}
    </a>
  )
})

// Mock useSearchParams with controllable return value
let mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
jest.mock('next/navigation', () => ({
  useSearchParams: () => mockSearchParams,
}))

describe('PricingLaunchCheckout', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseBilling.error = null
    mockUseBilling.isLoading = false
    mockCreateCheckoutSession.mockResolvedValue('https://checkout.stripe.com/test')
    mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
  })

  // ── Plan summary rendering ────────────────────────────────

  it('renders Solo plan summary for plan=solo', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText('Solo')).toBeInTheDocument()
  })

  it('renders Professional plan summary for plan=professional', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText('Professional')).toBeInTheDocument()
  })

  // ── Price display ────────────────────────────────────────

  it('displays monthly price correctly for solo', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
    render(<CheckoutPage />)
    const priceElements = screen.getAllByText('$100/mo')
    expect(priceElements.length).toBeGreaterThanOrEqual(1)
  })

  it('displays annual price correctly for professional', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=annual')
    render(<CheckoutPage />)
    const priceElements = screen.getAllByText('$5,000/yr')
    expect(priceElements.length).toBeGreaterThanOrEqual(1)
  })

  // ── Seat stepper visibility ─────────────────────────────

  it('shows seat stepper for professional plan', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText('Additional Seats')).toBeInTheDocument()
  })

  it('does not show seat stepper for solo plan', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.queryByText('Additional Seats')).not.toBeInTheDocument()
  })

  // ── Seat stepper interaction ────────────────────────────

  it('increments seat count when add button clicked', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly')
    render(<CheckoutPage />)
    const addButton = screen.getByLabelText('Add seat')
    fireEvent.click(addButton)
    // After clicking, the seat counter span should show 1
    // The counter is in a span with tabular-nums class between - and + buttons
    const seatDisplay = screen.getByLabelText('Add seat').previousElementSibling
    expect(seatDisplay?.textContent?.trim()).toBe('1')
  })

  it('decrements seat count when remove button clicked', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly&seats=3')
    render(<CheckoutPage />)
    const removeButton = screen.getByLabelText('Remove seat')
    fireEvent.click(removeButton)
    // After clicking, the seat counter should show 2
    const addButton = screen.getByLabelText('Add seat')
    const seatDisplay = addButton.previousElementSibling
    expect(seatDisplay?.textContent?.trim()).toBe('2')
  })

  it('max additional seats is 13 for professional plan', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly&seats=13')
    render(<CheckoutPage />)
    const addButton = screen.getByLabelText('Add seat')
    expect(addButton).toBeDisabled()
  })

  // ── Promo code input ────────────────────────────────────

  it('renders promo code input', () => {
    render(<CheckoutPage />)
    expect(screen.getByLabelText('Promo Code')).toBeInTheDocument()
  })

  it('accepts MONTHLY20 for monthly interval', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
    render(<CheckoutPage />)
    const input = screen.getByPlaceholderText('Enter code')
    fireEvent.change(input, { target: { value: 'MONTHLY20' } })
    const applyBtn = screen.getByRole('button', { name: 'Apply' })
    fireEvent.click(applyBtn)
    // Should show the applied code
    expect(screen.getByText('MONTHLY20')).toBeInTheDocument()
  })

  it('rejects ANNUAL10 for monthly interval', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
    render(<CheckoutPage />)
    const input = screen.getByPlaceholderText('Enter code')
    fireEvent.change(input, { target: { value: 'ANNUAL10' } })
    const applyBtn = screen.getByRole('button', { name: 'Apply' })
    fireEvent.click(applyBtn)
    // Should show error
    expect(screen.getByRole('alert')).toBeInTheDocument()
  })

  // ── Price breakdown ─────────────────────────────────────

  it('shows base price in breakdown', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText('Price Breakdown')).toBeInTheDocument()
    expect(screen.getByText('Professional plan')).toBeInTheDocument()
  })

  it('shows seat cost in breakdown when seats added', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly&seats=3')
    render(<CheckoutPage />)
    expect(screen.getByText(/3 additional seats/)).toBeInTheDocument()
  })

  // ── CTA button ──────────────────────────────────────────

  it('shows "Continue to Checkout" button', () => {
    render(<CheckoutPage />)
    expect(screen.getByRole('button', { name: 'Continue to Checkout' })).toBeInTheDocument()
  })

  // ── Invalid plan param → error state ────────────────────

  it('shows error for invalid plan param', () => {
    mockSearchParams = new URLSearchParams('plan=platinum&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText('Invalid Plan')).toBeInTheDocument()
  })

  // ── Missing plan param → error state ────────────────────

  it('shows error when plan param is missing', () => {
    mockSearchParams = new URLSearchParams('interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText('Invalid Plan')).toBeInTheDocument()
  })

  // ── URL params parsed correctly ─────────────────────────

  it('parses interval param from URL', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=annual')
    render(<CheckoutPage />)
    const priceElements = screen.getAllByText('$1,000/yr')
    expect(priceElements.length).toBeGreaterThanOrEqual(1)
  })

  it('parses seats param from URL', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly&seats=5')
    render(<CheckoutPage />)
    // Verify seats are parsed by checking the seat counter display
    const addButton = screen.getByLabelText('Add seat')
    const seatDisplay = addButton.previousElementSibling
    expect(seatDisplay?.textContent?.trim()).toBe('5')
  })

  // ── Annual savings copy ─────────────────────────────────

  it('shows annual savings info for annual plans', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=annual')
    render(<CheckoutPage />)
    expect(screen.getByText(/Annual billing saves ~17%/)).toBeInTheDocument()
  })

  // ── API error display ───────────────────────────────────

  it('displays API error when present', () => {
    mockUseBilling.error = 'Something went wrong'
    render(<CheckoutPage />)
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong')
  })

  // ── Stripe redirect text ────────────────────────────────

  it('shows Stripe redirect notice', () => {
    render(<CheckoutPage />)
    expect(screen.getByText(/redirected to our secure payment partner, Stripe/)).toBeInTheDocument()
  })

  // ── Back to plans link ──────────────────────────────────

  it('has "Back to Plans" link', () => {
    render(<CheckoutPage />)
    expect(screen.getByText('Back to Plans')).toBeInTheDocument()
  })

  // ── Seats included display ──────────────────────────────

  it('shows base seats included for professional plan', () => {
    mockSearchParams = new URLSearchParams('plan=professional&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText(/7 seats included/)).toBeInTheDocument()
  })

  it('shows base seat included for solo plan', () => {
    mockSearchParams = new URLSearchParams('plan=solo&interval=monthly')
    render(<CheckoutPage />)
    expect(screen.getByText(/1 seat included/)).toBeInTheDocument()
  })
})
