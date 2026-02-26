/**
 * CreateEngagementModal component tests
 *
 * Tests engagement creation modal: client selection, date validation,
 * materiality configuration, form submission, error display, modal close.
 *
 * React 19 compat: Uses fireEvent.change + act-wrapped fireEvent.submit
 * instead of userEvent.click on submit buttons, which is unreliable
 * with React 19's batched state updates + jsdom's requestSubmit.
 */
import { act, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CreateEngagementModal } from '@/components/engagement/CreateEngagementModal'
import { render, screen, waitFor } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


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

/** Submit the form using act-wrapped fireEvent (React 19 compatible) */
async function submitForm() {
  const form = screen.getByText('Create Workspace').closest('form')!
  await act(async () => {
    fireEvent.submit(form)
  })
}

/** Set date inputs via fireEvent.change */
function setDates(start: string, end: string) {
  const dateInputs = document.querySelectorAll('input[type="date"]')
  fireEvent.change(dateInputs[0] as HTMLElement, { target: { value: start } })
  fireEvent.change(dateInputs[1] as HTMLElement, { target: { value: end } })
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
    render(<CreateEngagementModal {...defaultProps} />)

    await submitForm()

    await waitFor(() => {
      expect(screen.getByText('Please select a client')).toBeInTheDocument()
    })
  })

  it('shows error when period end is before period start', async () => {
    render(<CreateEngagementModal {...defaultProps} />)

    // Select client
    const clientSelect = screen.getByDisplayValue('Select a client...')
    fireEvent.change(clientSelect, { target: { value: '1' } })

    // Set dates (end before start)
    setDates('2025-12-31', '2025-01-01')

    await submitForm()

    await waitFor(() => {
      expect(screen.getByText('Period end must be after period start')).toBeInTheDocument()
    })
  })

  it('calls onSubmit with correct data on valid submission', async () => {
    render(<CreateEngagementModal {...defaultProps} />)

    // Select client
    const clientSelect = screen.getByDisplayValue('Select a client...')
    fireEvent.change(clientSelect, { target: { value: '1' } })

    // Set valid dates
    setDates('2025-01-01', '2025-12-31')

    await submitForm()

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
    render(<CreateEngagementModal {...defaultProps} />)

    const clientSelect = screen.getByDisplayValue('Select a client...')
    fireEvent.change(clientSelect, { target: { value: '1' } })
    setDates('2025-01-01', '2025-12-31')

    await submitForm()

    await waitFor(() => {
      expect(defaultProps.onClose).toHaveBeenCalled()
    })
  })

  it('does not close on failed submission', async () => {
    defaultProps.onSubmit.mockResolvedValue(false)
    render(<CreateEngagementModal {...defaultProps} />)

    const clientSelect = screen.getByDisplayValue('Select a client...')
    fireEvent.change(clientSelect, { target: { value: '1' } })
    setDates('2025-01-01', '2025-12-31')

    await submitForm()

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
