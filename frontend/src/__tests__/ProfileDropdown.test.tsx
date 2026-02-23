/**
 * ProfileDropdown component tests
 *
 * Tests: trigger button, dropdown toggle, navigation links,
 * logout, click-outside dismiss, Escape key dismiss, email truncation.
 */
import userEvent from '@testing-library/user-event'
import { ProfileDropdown } from '@/components/auth/ProfileDropdown'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

jest.mock('next/link', () => {
  return ({ href, children, ...rest }: any) => (
    <a href={href} {...rest}>{children}</a>
  )
})


const defaultProps = {
  user: { email: 'auditor@paciolus.com' },
  onLogout: jest.fn(),
}

describe('ProfileDropdown', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ─── Trigger Button ─────────────────────────────────────────────────

  it('renders trigger button with user initial', () => {
    render(<ProfileDropdown {...defaultProps} />)
    expect(screen.getByText('A')).toBeInTheDocument() // First char of "auditor@..."
  })

  it('has aria-expanded=false when closed', () => {
    render(<ProfileDropdown {...defaultProps} />)
    const trigger = screen.getByRole('button', { expanded: false })
    expect(trigger).toBeInTheDocument()
  })

  // ─── Dropdown Toggle ───────────────────────────────────────────────

  it('opens dropdown on click', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)

    await user.click(screen.getByRole('button'))
    expect(screen.getByText('Vault Access')).toBeInTheDocument()
    expect(screen.getByText('Welcome back')).toBeInTheDocument()
  })

  it('shows user email in dropdown', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)

    await user.click(screen.getByRole('button'))
    expect(screen.getByText('auditor@paciolus.com')).toBeInTheDocument()
  })

  it('closes dropdown on second click', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)

    const trigger = screen.getByRole('button')
    await user.click(trigger)
    expect(screen.getByText('Vault Access')).toBeInTheDocument()

    await user.click(trigger)
    expect(screen.queryByText('Vault Access')).not.toBeInTheDocument()
  })

  // ─── Navigation Links ──────────────────────────────────────────────

  it('shows all navigation items when open', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)
    await user.click(screen.getByRole('button'))

    expect(screen.getByText('TB Diagnostics')).toBeInTheDocument()
    expect(screen.getByText('Multi-Period Comparison')).toBeInTheDocument()
    expect(screen.getByText('JE Testing')).toBeInTheDocument()
    expect(screen.getByText('Client Portfolio')).toBeInTheDocument()
    expect(screen.getByText('Profile Settings')).toBeInTheDocument()
    expect(screen.getByText('Practice Settings')).toBeInTheDocument()
  })

  it('shows Zero-Storage Active badge', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)
    await user.click(screen.getByRole('button'))

    expect(screen.getByText('Zero-Storage Active')).toBeInTheDocument()
  })

  // ─── Logout ─────────────────────────────────────────────────────────

  it('calls onLogout and closes dropdown on Sign out', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)

    await user.click(screen.getByRole('button'))
    await user.click(screen.getByText('Sign out'))

    expect(defaultProps.onLogout).toHaveBeenCalledTimes(1)
    expect(screen.queryByText('Vault Access')).not.toBeInTheDocument()
  })

  // ─── Escape Key ─────────────────────────────────────────────────────

  it('closes dropdown on Escape key', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)

    await user.click(screen.getByRole('button'))
    expect(screen.getByText('Vault Access')).toBeInTheDocument()

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByText('Vault Access')).not.toBeInTheDocument()
  })

  // ─── Click Outside ──────────────────────────────────────────────────

  it('closes dropdown on click outside', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)

    await user.click(screen.getByRole('button'))
    expect(screen.getByText('Vault Access')).toBeInTheDocument()

    // Click outside the dropdown
    fireEvent.mouseDown(document.body)
    expect(screen.queryByText('Vault Access')).not.toBeInTheDocument()
  })

  // ─── Email Truncation ──────────────────────────────────────────────

  it('truncates long email addresses', async () => {
    const user = userEvent.setup()
    render(
      <ProfileDropdown
        user={{ email: 'very.long.email.address@professional-firm.com' }}
        onLogout={jest.fn()}
      />
    )

    await user.click(screen.getByRole('button'))
    // email.slice(0, 21) + '...' = 'very.long.email.addre...'
    expect(screen.getByText('very.long.email.addre...')).toBeInTheDocument()
  })

  it('does not truncate short email addresses', async () => {
    const user = userEvent.setup()
    render(<ProfileDropdown {...defaultProps} />)

    await user.click(screen.getByRole('button'))
    expect(screen.getByText('auditor@paciolus.com')).toBeInTheDocument()
    expect(screen.queryByText(/\.\.\./)).not.toBeInTheDocument()
  })
})
