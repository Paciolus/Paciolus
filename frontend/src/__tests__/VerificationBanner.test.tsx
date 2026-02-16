/**
 * VerificationBanner component tests
 *
 * Tests: hidden for verified users, visible for unverified,
 * resend button states, dismiss behavior, cooldown display.
 */
import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))

const mockResend = jest.fn()
const mockUseVerification = {
  cooldownSeconds: 0,
  canResend: true,
  isResending: false,
  resendSuccess: false,
  resend: mockResend,
}

jest.mock('@/hooks/useVerification', () => ({
  useVerification: () => mockUseVerification,
}))

const mockUseAuth = {
  user: { id: 1, email: 'test@example.com', is_verified: false },
  isAuthenticated: true,
}

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth,
}))

import { VerificationBanner } from '@/components/auth/VerificationBanner'

describe('VerificationBanner', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    // Reset mock state
    mockUseAuth.user = { id: 1, email: 'test@example.com', is_verified: false }
    mockUseAuth.isAuthenticated = true
    mockUseVerification.cooldownSeconds = 0
    mockUseVerification.canResend = true
    mockUseVerification.isResending = false
    mockUseVerification.resendSuccess = false
  })

  it('renders nothing for verified users', () => {
    mockUseAuth.user = { id: 1, email: 'test@example.com', is_verified: true } as any
    const { container } = render(<VerificationBanner />)
    expect(container.innerHTML).toBe('')
  })

  it('renders nothing when not authenticated', () => {
    mockUseAuth.isAuthenticated = false
    const { container } = render(<VerificationBanner />)
    expect(container.innerHTML).toBe('')
  })

  it('shows verification message for unverified users', () => {
    render(<VerificationBanner />)
    expect(screen.getByText(/email is not yet verified/)).toBeInTheDocument()
  })

  it('shows "Resend Email" button when ready', () => {
    render(<VerificationBanner />)
    expect(screen.getByText('Resend Email')).toBeInTheDocument()
  })

  it('calls resend when button is clicked', async () => {
    const user = userEvent.setup()
    render(<VerificationBanner />)

    await user.click(screen.getByText('Resend Email'))
    expect(mockResend).toHaveBeenCalledTimes(1)
  })

  it('shows "Sending..." when resend is in progress', () => {
    mockUseVerification.isResending = true
    mockUseVerification.canResend = false
    render(<VerificationBanner />)
    expect(screen.getByText('Sending...')).toBeInTheDocument()
  })

  it('shows "Sent!" on success', () => {
    mockUseVerification.resendSuccess = true
    render(<VerificationBanner />)
    expect(screen.getByText('Sent!')).toBeInTheDocument()
  })

  it('shows cooldown timer when cannot resend', () => {
    mockUseVerification.canResend = false
    mockUseVerification.cooldownSeconds = 90
    render(<VerificationBanner />)
    expect(screen.getByText('Resend in 1:30')).toBeInTheDocument()
  })

  it('dismisses banner when close button is clicked', async () => {
    const user = userEvent.setup()
    render(<VerificationBanner />)

    expect(screen.getByText(/email is not yet verified/)).toBeInTheDocument()
    await user.click(screen.getByLabelText('Dismiss verification banner'))

    expect(screen.queryByText(/email is not yet verified/)).not.toBeInTheDocument()
  })
})
