/**
 * Login page tests
 *
 * Tests login form: email/password inputs, remember-me toggle, VaultTransition,
 * redirect logic, server error display, submit behavior.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const mockLogin = jest.fn()
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    login: mockLogin,
    user: null,
    isAuthenticated: false,
    isLoading: false,
  })),
}))

jest.mock('@/hooks', () => {
  const actual = jest.requireActual('@/hooks/useFormValidation')
  return {
    useFormValidation: actual.useFormValidation,
    commonValidators: actual.commonValidators,
  }
})

jest.mock('@/components/VaultTransition', () => {
  return function MockVaultTransition({ onComplete }: { onComplete: () => void }) {
    return <div data-testid="vault-transition"><button onClick={onComplete}>Complete Transition</button></div>
  }
})

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
    form: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <form {...rest}>{children}</form>,
    h1: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <h1 {...rest}>{children}</h1>,
    p: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <p {...rest}>{children}</p>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('next/link', () => {
  return ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>
})

import LoginPage from '@/app/(auth)/login/page'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: null,
      isAuthenticated: false,
      isLoading: false,
    })
    // Clear sessionStorage
    sessionStorage.clear()
  })

  it('renders login form with all fields', () => {
    render(<LoginPage />)
    expect(screen.getByText('Obsidian Vault')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByText('Enter Vault')).toBeInTheDocument()
  })

  it('shows Zero-Storage Promise badge', () => {
    render(<LoginPage />)
    expect(screen.getByText('Zero-Storage Promise')).toBeInTheDocument()
  })

  it('shows register link', () => {
    render(<LoginPage />)
    expect(screen.getByText('Create an account')).toBeInTheDocument()
    expect(screen.getByText('New to Paciolus?')).toBeInTheDocument()
  })

  it('shows remember-me checkbox', () => {
    render(<LoginPage />)
    expect(screen.getByText('Remember me')).toBeInTheDocument()
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('shows forgot password button (disabled)', () => {
    render(<LoginPage />)
    const forgotButton = screen.getByText('Forgot password?')
    expect(forgotButton).toBeDisabled()
    expect(forgotButton).toHaveAttribute('title', 'Coming soon')
  })

  it('shows server error on failed login', async () => {
    mockLogin.mockResolvedValue({ success: false, error: 'Invalid email or password' })
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email Address'), 'test@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrongpassword')

    const button = screen.getByText('Enter Vault').closest('button')!
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Invalid email or password')).toBeInTheDocument()
    })
  })

  it('shows VaultTransition on successful login', async () => {
    mockLogin.mockResolvedValue({ success: true })
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: { name: 'Alice', email: 'alice@example.com' },
      isAuthenticated: false,
      isLoading: false,
    })

    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email Address'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), 'password123')

    const button = screen.getByText('Enter Vault').closest('button')!
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByTestId('vault-transition')).toBeInTheDocument()
    })
  })

  it('redirects after VaultTransition completes', async () => {
    mockLogin.mockResolvedValue({ success: true })
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: { name: 'Alice', email: 'alice@example.com' },
      isAuthenticated: false,
      isLoading: false,
    })

    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email Address'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), 'password123')

    const submitButton = screen.getByText('Enter Vault').closest('button')!
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByTestId('vault-transition')).toBeInTheDocument()
    })

    // Complete vault transition
    const completeButton = screen.getByText('Complete Transition')
    await user.click(completeButton)

    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('uses stored redirect path after login', async () => {
    sessionStorage.setItem('paciolus_redirect', '/tools/trial-balance')
    mockLogin.mockResolvedValue({ success: true })
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: { name: 'Alice', email: 'alice@example.com' },
      isAuthenticated: false,
      isLoading: false,
    })

    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email Address'), 'alice@example.com')
    await user.type(screen.getByLabelText('Password'), 'password123')

    const submitButton = screen.getByText('Enter Vault').closest('button')!
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByTestId('vault-transition')).toBeInTheDocument()
    })

    const completeButton = screen.getByText('Complete Transition')
    await user.click(completeButton)

    expect(mockPush).toHaveBeenCalledWith('/tools/trial-balance')
  })

  it('redirects already-authenticated user to home', () => {
    mockUseAuth.mockReturnValue({
      login: mockLogin,
      user: { name: 'Alice', email: 'alice@example.com' },
      isAuthenticated: true,
      isLoading: false,
    })
    render(<LoginPage />)
    expect(mockPush).toHaveBeenCalledWith('/')
  })

  it('shows submitting state while logging in', async () => {
    // Login never resolves to keep submitting state
    mockLogin.mockReturnValue(new Promise(() => {}))
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email Address'), 'test@example.com')
    await user.type(screen.getByLabelText('Password'), 'password123')

    const button = screen.getByText('Enter Vault').closest('button')!
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Unlocking Vault...')).toBeInTheDocument()
    })
  })
})
