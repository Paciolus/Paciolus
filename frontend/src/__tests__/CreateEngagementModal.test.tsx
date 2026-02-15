/**
 * CreateEngagementModal component tests
 *
 * Tests engagement creation modal: client selection, date validation,
 * materiality configuration, form submission, error display, modal close.
 */
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

import { CreateEngagementModal } from '@/components/engagement/CreateEngagementModal'

const sampleClients = [
  { id: 1, name: 'Acme Corp', industry: 'Technology', fiscal_year_end: '12-31', created_at: '2025-01-01', updated_at: '2025-01-01' },
  { id: 2, name: 'Widget Inc', industry: 'Manufacturing', fiscal_year_end: '06-30', created_at: '2025-02-01', updated_at: '2025-02-01' },
]

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  onSubmit: jest.fn(),
  clients: sampleClients,
  isLoading: false,
}

describe('CreateEngagementModal', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    defaultProps.onSubmit.mockResolvedValue(true)
  })

  it('renders modal with title when open', () => {
    render(<CreateEngagementModal {...defaultProps} />)
    expect(screen.getByText('New Diagnostic Workspace')).toBeInTheDocument()
  })

  it('does not render when closed', () => {
    render(<CreateEngagementModal {...defaultProps} isOpen={false} />)
    expect(screen.queryByText('New Diagnostic Workspace')).not.toBeInTheDocument()
  })

  it('shows client dropdown with all clients', () => {
    render(<CreateEngagementModal {...defaultProps} />)
    expect(screen.getByText('Select a client...')).toBeInTheDocument()
    expect(screen.getByText('Acme Corp')).toBeInTheDocument()
    expect(screen.getByText('Widget Inc')).toBeInTheDocument()
  })

  it('shows period date inputs', () => {
    render(<CreateEngagementModal {...defaultProps} />)
    const dateInputs = screen.getAllByDisplayValue('')
    // Should have at least 2 date inputs
    expect(dateInputs.length).toBeGreaterThanOrEqual(2)
  })

  it('shows materiality configuration section', () => {
    render(<CreateEngagementModal {...defaultProps} />)
    expect(screen.getByText('None')).toBeInTheDocument() // Default materiality basis option
  })

  it('shows error when submitting without client', async () => {
    const user = userEvent.setup()
    render(<CreateEngagementModal {...defaultProps} />)

    const submitButton = screen.getByText('Create Workspace')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Please select a client')).toBeInTheDocument()
    })
  })

  it('shows error when period end is before period start', async () => {
    const user = userEvent.setup()
    render(<CreateEngagementModal {...defaultProps} />)

    // Select client
    const clientSelect = screen.getByDisplayValue('Select a client...')
    await user.selectOptions(clientSelect, '1')

    // Set dates (end before start)
    const dateInputs = document.querySelectorAll('input[type="date"]')
    await user.type(dateInputs[0] as HTMLElement, '2025-12-31')
    await user.type(dateInputs[1] as HTMLElement, '2025-01-01')

    const submitButton = screen.getByText('Create Workspace')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Period end must be after period start')).toBeInTheDocument()
    })
  })

  it('calls onSubmit with correct data on valid submission', async () => {
    const user = userEvent.setup()
    render(<CreateEngagementModal {...defaultProps} />)

    // Select client
    const clientSelect = screen.getByDisplayValue('Select a client...')
    await user.selectOptions(clientSelect, '1')

    // Set valid dates
    const dateInputs = document.querySelectorAll('input[type="date"]')
    await user.type(dateInputs[0] as HTMLElement, '2025-01-01')
    await user.type(dateInputs[1] as HTMLElement, '2025-12-31')

    const submitButton = screen.getByText('Create Workspace')
    await user.click(submitButton)

    await waitFor(() => {
      expect(defaultProps.onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          client_id: 1,
        })
      )
    })
  })

  it('closes modal on successful submission', async () => {
    defaultProps.onSubmit.mockResolvedValue(true)
    const user = userEvent.setup()
    render(<CreateEngagementModal {...defaultProps} />)

    const clientSelect = screen.getByDisplayValue('Select a client...')
    await user.selectOptions(clientSelect, '1')

    const dateInputs = document.querySelectorAll('input[type="date"]')
    await user.type(dateInputs[0] as HTMLElement, '2025-01-01')
    await user.type(dateInputs[1] as HTMLElement, '2025-12-31')

    await user.click(screen.getByText('Create Workspace'))

    await waitFor(() => {
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  it('does not close on failed submission', async () => {
    defaultProps.onSubmit.mockResolvedValue(false)
    const user = userEvent.setup()
    render(<CreateEngagementModal {...defaultProps} />)

    const clientSelect = screen.getByDisplayValue('Select a client...')
    await user.selectOptions(clientSelect, '1')

    const dateInputs = document.querySelectorAll('input[type="date"]')
    await user.type(dateInputs[0] as HTMLElement, '2025-01-01')
    await user.type(dateInputs[1] as HTMLElement, '2025-12-31')

    await user.click(screen.getByText('Create Workspace'))

    await waitFor(() => {
      expect(defaultProps.onSubmit).toHaveBeenCalled()
    })
    // onClose should NOT have been called since submission returned false
    expect(defaultProps.onClose).not.toHaveBeenCalled()
  })

  it('calls onClose when Cancel is clicked', async () => {
    const user = userEvent.setup()
    render(<CreateEngagementModal {...defaultProps} />)

    await user.click(screen.getByText('Cancel'))
    expect(defaultProps.onClose).toHaveBeenCalled()
  })

  it('shows Creating... while submitting', () => {
    render(<CreateEngagementModal {...defaultProps} isLoading={true} />)
    expect(screen.getByText('Creating...')).toBeInTheDocument()
  })
})
