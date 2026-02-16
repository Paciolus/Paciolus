/**
 * CreateClientModal component tests
 *
 * Tests: visibility, empty form, validation, submission, and close.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
    button: ({ initial, animate, exit, transition, variants, whileHover, whileTap, children, ...rest }: any) =>
      <button {...rest}>{children}</button>,
    p: ({ initial, animate, exit, transition, variants, children, ...rest }: any) =>
      <p {...rest}>{children}</p>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { CreateClientModal } from '@/components/portfolio/CreateClientModal'

const mockIndustries = [
  { value: 'technology', label: 'Technology' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'other', label: 'Other' },
]

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  onSubmit: jest.fn(),
  industries: mockIndustries,
}

describe('CreateClientModal', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    defaultProps.onSubmit.mockResolvedValue(true)
  })

  it('does not render when isOpen is false', () => {
    render(<CreateClientModal {...defaultProps} isOpen={false} />)
    expect(screen.queryByText('New Client')).not.toBeInTheDocument()
  })

  it('renders modal with "New Client" title', () => {
    render(<CreateClientModal {...defaultProps} />)
    expect(screen.getByText('New Client')).toBeInTheDocument()
    expect(screen.getByText('Add a client to your portfolio')).toBeInTheDocument()
  })

  it('starts with empty name field', () => {
    render(<CreateClientModal {...defaultProps} />)
    expect(screen.getByLabelText(/Client Name/)).toHaveValue('')
  })

  it('shows validation error for empty name on blur', async () => {
    const user = userEvent.setup()
    render(<CreateClientModal {...defaultProps} />)

    const nameInput = screen.getByLabelText(/Client Name/)
    await user.click(nameInput)
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Client name is required')).toBeInTheDocument()
    })
  })

  it('shows min length validation error', async () => {
    const user = userEvent.setup()
    render(<CreateClientModal {...defaultProps} />)

    const nameInput = screen.getByLabelText(/Client Name/)
    await user.type(nameInput, 'A')
    await user.tab()

    await waitFor(() => {
      expect(screen.getByText('Name must be at least 2 characters')).toBeInTheDocument()
    })
  })

  it('calls onSubmit with form data on valid submission', async () => {
    const user = userEvent.setup()
    render(<CreateClientModal {...defaultProps} />)

    await user.type(screen.getByLabelText(/Client Name/), 'New Corp')
    await user.selectOptions(screen.getByLabelText('Industry'), 'manufacturing')
    await user.click(screen.getByText('Create Client'))

    await waitFor(() => {
      expect(defaultProps.onSubmit).toHaveBeenCalledWith({
        name: 'New Corp',
        industry: 'manufacturing',
        fiscal_year_end: '12-31',
      })
    })
  })

  it('calls onClose on successful creation', async () => {
    const user = userEvent.setup()
    render(<CreateClientModal {...defaultProps} />)

    await user.type(screen.getByLabelText(/Client Name/), 'New Corp')
    await user.click(screen.getByText('Create Client'))

    await waitFor(() => {
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  it('does not close when creation fails', async () => {
    defaultProps.onSubmit.mockResolvedValue(false)
    const user = userEvent.setup()
    render(<CreateClientModal {...defaultProps} />)

    await user.type(screen.getByLabelText(/Client Name/), 'New Corp')
    await user.click(screen.getByText('Create Client'))

    await waitFor(() => {
      expect(defaultProps.onSubmit).toHaveBeenCalled()
    })
    expect(defaultProps.onClose).not.toHaveBeenCalled()
  })

  it('shows Zero-Storage badge', () => {
    render(<CreateClientModal {...defaultProps} />)
    expect(screen.getByText(/Only client metadata is stored/)).toBeInTheDocument()
  })
})
