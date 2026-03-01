/**
 * Register page tests
 *
 * Tests registration form: password strength calculator, real-time validation,
 * password match indicator, terms acceptance, form submission, redirect logic.
 */
import userEvent from '@testing-library/user-event'
import RegisterPage from '@/app/(auth)/register/page'
import { useAuth } from '@/contexts/AuthContext'
import { render, screen, waitFor } from '@/test-utils'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

const mockRegister = jest.fn()
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    register: mockRegister,
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


const mockUseAuth = useAuth as jest.Mock

describe('RegisterPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({
      register: mockRegister,
      isAuthenticated: false,
      isLoading: false,
    })
  })

  it('renders registration form with all fields', () => {
    render(<RegisterPage />)
    expect(screen.getByText('Create Your Account')).toBeInTheDocument()
    expect(screen.getByLabelText('Email Address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
    expect(screen.getByText('Create My Account')).toBeInTheDocument()
  })

  it('shows Zero-Storage badge', () => {
    render(<RegisterPage />)
    expect(screen.getByText('Zero-Storage Architecture')).toBeInTheDocument()
  })

  it('shows login link', () => {
    render(<RegisterPage />)
    expect(screen.getByText('Sign in')).toBeInTheDocument()
    expect(screen.getByText('Already have an account?')).toBeInTheDocument()
  })

  it('shows password strength indicator when typing password', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const passwordInput = screen.getByLabelText('Password')
    await user.type(passwordInput, 'abc')

    // Should show requirements checklist
    expect(screen.getByText('8+ characters')).toBeInTheDocument()
    expect(screen.getByText('Uppercase')).toBeInTheDocument()
    expect(screen.getByText('Lowercase')).toBeInTheDocument()
    expect(screen.getByText('Number')).toBeInTheDocument()
    expect(screen.getByText(/Special character/)).toBeInTheDocument()
  })

  it('shows Very Weak for password with only lowercase', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const passwordInput = screen.getByLabelText('Password')
    await user.type(passwordInput, 'abc')

    expect(screen.getByText('Very Weak')).toBeInTheDocument()
  })

  it('shows Strong for password meeting 4 requirements', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const passwordInput = screen.getByLabelText('Password')
    await user.type(passwordInput, 'Abcdefg1')

    expect(screen.getByText('Strong')).toBeInTheDocument()
  })

  it('shows Very Strong for password meeting all 5 requirements', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const passwordInput = screen.getByLabelText('Password')
    await user.type(passwordInput, 'Abcdefg1!')

    expect(screen.getByText('Very Strong')).toBeInTheDocument()
  })

  it('shows password mismatch indicator', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const passwordInput = screen.getByLabelText('Password')
    const confirmInput = screen.getByLabelText('Confirm Password')

    await user.type(passwordInput, 'Abcdefg1!')
    await user.type(confirmInput, 'Different1!')

    expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
  })

  it('does not show mismatch message when passwords match', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    const passwordInput = screen.getByLabelText('Password')
    const confirmInput = screen.getByLabelText('Confirm Password')

    await user.type(passwordInput, 'Abcdefg1!')
    await user.type(confirmInput, 'Abcdefg1!')

    expect(screen.queryByText('Passwords do not match')).not.toBeInTheDocument()
  })

  it('submit button is disabled until all conditions met', () => {
    render(<RegisterPage />)
    const button = screen.getByText('Create My Account').closest('button')
    expect(button).toBeDisabled()
  })

  it('shows terms of service and privacy policy links', () => {
    render(<RegisterPage />)
    expect(screen.getByText('Terms of Service')).toHaveAttribute('href', '/terms')
    expect(screen.getByText('Privacy Policy')).toHaveAttribute('href', '/privacy')
  })

  it('shows server error on failed registration', async () => {
    mockRegister.mockResolvedValue({ success: false, error: 'Email already registered' })
    const user = userEvent.setup()
    render(<RegisterPage />)

    // Fill valid form
    await user.type(screen.getByLabelText('Email Address'), 'test@example.com')
    await user.type(screen.getByLabelText('Password'), 'Abcdefg1!')
    await user.type(screen.getByLabelText('Confirm Password'), 'Abcdefg1!')

    // Accept terms via checkbox
    const checkbox = screen.getByRole('checkbox')
    await user.click(checkbox)

    // Submit
    const button = screen.getByText('Create My Account').closest('button')!
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('Email already registered')).toBeInTheDocument()
    })
  })

  it('redirects to verification-pending on successful registration', async () => {
    mockRegister.mockResolvedValue({ success: true })
    const user = userEvent.setup()
    render(<RegisterPage />)

    await user.type(screen.getByLabelText('Email Address'), 'new@example.com')
    await user.type(screen.getByLabelText('Password'), 'Abcdefg1!')
    await user.type(screen.getByLabelText('Confirm Password'), 'Abcdefg1!')

    const checkbox = screen.getByRole('checkbox')
    await user.click(checkbox)

    const button = screen.getByText('Create My Account').closest('button')!
    await user.click(button)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/verification-pending?email=new%40example.com')
    })
  })

  it('redirects to home if already authenticated', () => {
    mockUseAuth.mockReturnValue({
      register: mockRegister,
      isAuthenticated: true,
      isLoading: false,
    })
    render(<RegisterPage />)
    expect(mockPush).toHaveBeenCalledWith('/')
  })
})
