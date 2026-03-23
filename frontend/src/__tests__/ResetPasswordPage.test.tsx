import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ResetPasswordPage from '@/app/(auth)/reset-password/page'

// Mock framer-motion
jest.mock('framer-motion', () => {
  const React = require('react')
  return {
    motion: new Proxy({}, {
      get: (_target: unknown, prop: string) =>
        React.forwardRef(({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }, ref: React.Ref<HTMLElement>) => {
          const { initial, animate, variants, custom, whileHover, whileTap, transition, exit, ...safeProps } = props as Record<string, unknown>
          return React.createElement(prop, { ...safeProps, ref }, children)
        }),
    }),
    AnimatePresence: ({ children }: { children: React.ReactNode }) => children,
  }
})

// Mock motion tokens
jest.mock('@/lib/motion', () => ({
  fadeUp: { hidden: {}, visible: () => ({}) },
}))

// Mock apiPost
const mockApiPost = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}))

// Mock next/navigation
const mockPush = jest.fn()
const mockGet = jest.fn()
jest.mock('next/navigation', () => ({
  useSearchParams: () => ({ get: mockGet }),
  useRouter: () => ({ push: mockPush, replace: jest.fn() }),
}))

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({ ok: true, data: { message: 'Your password has been reset successfully.' } })
    // Mock window.history.replaceState
    jest.spyOn(window.history, 'replaceState').mockImplementation(() => {})
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('shows invalid link state when no token in URL', () => {
    mockGet.mockReturnValue(null)
    render(<ResetPasswordPage />)
    expect(screen.getByText('Invalid Reset Link')).toBeInTheDocument()
    expect(screen.getByText('Request a New Link')).toHaveAttribute('href', '/forgot-password')
  })

  it('shows password form when token is present', () => {
    mockGet.mockReturnValue('valid_token_123')
    render(<ResetPasswordPage />)
    expect(screen.getByText('Choose a New Password')).toBeInTheDocument()
    expect(screen.getByLabelText('New Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
  })

  it('calls API even with short password (backend validates)', async () => {
    mockGet.mockReturnValue('valid_token_123')
    mockApiPost.mockResolvedValue({ ok: false, error: 'Validation error' })
    render(<ResetPasswordPage />)

    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'ValidPass1' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'ValidPass1' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalled()
    })
  })

  it('calls API and shows success on valid submission', async () => {
    mockGet.mockReturnValue('valid_token_123')
    render(<ResetPasswordPage />)

    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'NewSecure9!' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'NewSecure9!' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith('/auth/reset-password', null, {
        token: 'valid_token_123',
        new_password: 'NewSecure9!',
      })
    })

    expect(await screen.findByText('Password Reset')).toBeInTheDocument()
    expect(screen.getByText('Go to Login')).toBeInTheDocument()
  })

  it('shows error state on API failure', async () => {
    mockGet.mockReturnValue('valid_token_123')
    mockApiPost.mockResolvedValue({ ok: false, error: 'This reset link has expired.' })
    render(<ResetPasswordPage />)

    fireEvent.change(screen.getByLabelText('New Password'), { target: { value: 'NewSecure9!' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'NewSecure9!' } })
    fireEvent.click(screen.getByRole('button', { name: /reset password/i }))

    expect(await screen.findByText('Reset Failed')).toBeInTheDocument()
  })
})
