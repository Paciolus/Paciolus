/**
 * EditClientModal component tests
 *
 * Tests: visibility, pre-populated form, validation,
 * delta-only submission, and close behavior.
 */
import userEvent from '@testing-library/user-event'
import { EditClientModal } from '@/components/portfolio/EditClientModal'
import { render, screen, waitFor } from '@/test-utils'

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


const mockClient = {
  id: 1,
  name: 'Acme Corp',
  industry: 'technology' as const,
  fiscal_year_end: '12-31',
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  user_id: 1,
}

const mockIndustries = [
  { value: 'technology', label: 'Technology' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'other', label: 'Other' },
]

const defaultProps = {
  isOpen: true,
  client: mockClient,
  onClose: jest.fn(),
  onSubmit: jest.fn(),
  industries: mockIndustries,
}

describe('EditClientModal', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    defaultProps.onSubmit.mockResolvedValue(mockClient)
  })

  it('returns null when client is null', () => {
    const { container } = render(<EditClientModal {...defaultProps} client={null} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders modal with "Edit Client" title when open', () => {
    render(<EditClientModal {...defaultProps} />)
    expect(screen.getByText('Edit Client')).toBeInTheDocument()
  })

  it('pre-populates form with client data', () => {
    render(<EditClientModal {...defaultProps} />)
    expect(screen.getByLabelText(/Client Name/)).toHaveValue('Acme Corp')
    expect(screen.getByLabelText('Industry')).toHaveValue('technology')
  })

  it('shows validation error for empty name', async () => {
    const user = userEvent.setup()
    render(<EditClientModal {...defaultProps} />)

    const nameInput = screen.getByLabelText(/Client Name/)
    await user.clear(nameInput)
    await user.tab() // trigger blur

    await waitFor(() => {
      expect(screen.getByText('Client name is required')).toBeInTheDocument()
    })
  })

  it('calls onClose without submit when no changes made', async () => {
    const user = userEvent.setup()
    render(<EditClientModal {...defaultProps} />)

    await user.click(screen.getByText('Save Changes'))

    await waitFor(() => {
      expect(defaultProps.onClose).toHaveBeenCalled()
      expect(defaultProps.onSubmit).not.toHaveBeenCalled()
    })
  })

  it('submits only changed fields (delta)', async () => {
    const user = userEvent.setup()
    render(<EditClientModal {...defaultProps} />)

    const nameInput = screen.getByLabelText(/Client Name/)
    await user.clear(nameInput)
    await user.type(nameInput, 'New Name')
    await user.click(screen.getByText('Save Changes'))

    await waitFor(() => {
      expect(defaultProps.onSubmit).toHaveBeenCalledWith(1, { name: 'New Name' })
    })
  })

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup()
    render(<EditClientModal {...defaultProps} />)

    await user.click(screen.getByLabelText('Close modal'))
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('shows "Saving..." when isLoading is true', () => {
    render(<EditClientModal {...defaultProps} isLoading={true} />)
    expect(screen.getByText('Saving...')).toBeInTheDocument()
  })
})
