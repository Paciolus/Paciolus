import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import ForgotPasswordPage from '@/app/(auth)/forgot-password/page'

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

// Mock apiPost
const mockApiPost = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}))

// Mock motion tokens
jest.mock('@/lib/motion', () => ({
  fadeUp: { hidden: {}, visible: () => ({}) },
}))

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({ ok: true, data: { message: 'If an account with that email exists, a password reset link has been sent.' } })
  })

  it('renders the forgot password form', () => {
    render(<ForgotPasswordPage />)
    expect(screen.getByText('Reset Your Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument()
  })

  it('shows error for empty email submission', async () => {
    render(<ForgotPasswordPage />)
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))
    expect(await screen.findByText('Please enter your email address.')).toBeInTheDocument()
  })

  it('calls API and shows success screen on submit', async () => {
    render(<ForgotPasswordPage />)
    fireEvent.change(screen.getByLabelText('Email Address'), { target: { value: 'test@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    await waitFor(() => {
      expect(mockApiPost).toHaveBeenCalledWith('/auth/forgot-password', null, { email: 'test@example.com' })
    })

    expect(await screen.findByText('Check Your Email')).toBeInTheDocument()
  })

  it('shows success screen even on API error (prevents enumeration)', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'Server error' })
    render(<ForgotPasswordPage />)
    fireEvent.change(screen.getByLabelText('Email Address'), { target: { value: 'test@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: /send reset link/i }))

    expect(await screen.findByText('Check Your Email')).toBeInTheDocument()
  })

  it('has link back to login', () => {
    render(<ForgotPasswordPage />)
    const loginLink = screen.getByText(/remember your password/i)
    expect(loginLink).toHaveAttribute('href', '/login')
  })
})
