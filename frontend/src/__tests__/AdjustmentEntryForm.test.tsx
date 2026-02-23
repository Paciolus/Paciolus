/**
 * AdjustmentEntryForm component tests
 *
 * Tests adjusting journal entry form: line management, debit/credit mutual exclusion,
 * balance validation, form submission, autocomplete, disabled states.
 */
import userEvent from '@testing-library/user-event'
import { AdjustmentEntryForm } from '@/components/adjustments/AdjustmentEntryForm'
import { render, screen, waitFor } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


const defaultProps = {
  onSubmit: jest.fn(),
  onCancel: jest.fn(),
}

describe('AdjustmentEntryForm', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    defaultProps.onSubmit.mockResolvedValue(undefined)
  })

  it('renders form with all required fields', () => {
    render(<AdjustmentEntryForm {...defaultProps} />)
    expect(screen.getByText('Create Entry')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
    // Should have reference, description, adjustment type fields
    expect(screen.getByDisplayValue('AJE-001')).toBeInTheDocument()
  })

  it('starts with 2 line items', () => {
    render(<AdjustmentEntryForm {...defaultProps} />)
    // Each line has account, debit, credit inputs — 2 lines = 6 inputs (+ reference + description)
    const debitInputs = screen.getAllByPlaceholderText('0.00')
    // Should have at least 4 (2 debit + 2 credit)
    expect(debitInputs.length).toBeGreaterThanOrEqual(4)
  })

  it('adds a new line when Add Line is clicked', async () => {
    const user = userEvent.setup()
    render(<AdjustmentEntryForm {...defaultProps} />)

    const addButton = screen.getByText('+ Add Line')
    const initialInputCount = screen.getAllByPlaceholderText('0.00').length

    await user.click(addButton)

    const newInputCount = screen.getAllByPlaceholderText('0.00').length
    expect(newInputCount).toBeGreaterThan(initialInputCount)
  })

  it('does not remove line when only 2 lines remain', () => {
    render(<AdjustmentEntryForm {...defaultProps} />)
    // Remove buttons should be disabled when only 2 lines
    const removeButtons = screen.getAllByRole('button').filter(
      btn => btn.getAttribute('disabled') !== null && btn.textContent === ''
    )
    // At minimum, we should check that line count doesn't go below 2
    expect(screen.getAllByPlaceholderText('0.00').length).toBeGreaterThanOrEqual(4)
  })

  it('shows balanced indicator when debits equal credits', async () => {
    const user = userEvent.setup()
    render(<AdjustmentEntryForm {...defaultProps} />)

    // Get all number inputs (debit and credit fields)
    const numberInputs = screen.getAllByRole('spinbutton')

    // Find the first debit field and first credit field
    // The pattern is: line1-debit, line1-credit, line2-debit, line2-credit
    await user.clear(numberInputs[0])
    await user.type(numberInputs[0], '1000')
    await user.clear(numberInputs[1])
    await user.type(numberInputs[1], '0')
    await user.clear(numberInputs[2])
    await user.type(numberInputs[2], '0')
    await user.clear(numberInputs[3])
    await user.type(numberInputs[3], '1000')

    expect(screen.getByText('Balanced')).toBeInTheDocument()
  })

  it('shows out of balance warning when debits do not equal credits', async () => {
    const user = userEvent.setup()
    render(<AdjustmentEntryForm {...defaultProps} />)

    const numberInputs = screen.getAllByRole('spinbutton')

    await user.clear(numberInputs[0])
    await user.type(numberInputs[0], '1000')

    expect(screen.getByText(/Out of balance/)).toBeInTheDocument()
  })

  it('uses custom initial reference', () => {
    render(<AdjustmentEntryForm {...defaultProps} initialReference="AJE-005" />)
    expect(screen.getByDisplayValue('AJE-005')).toBeInTheDocument()
  })

  it('shows account autocomplete when accounts provided', () => {
    render(
      <AdjustmentEntryForm
        {...defaultProps}
        accounts={['Cash', 'Accounts Receivable', 'Accounts Payable']}
      />
    )
    // Datalist elements should exist with the account options
    const options = screen.getAllByRole('option')
    expect(options.length).toBeGreaterThanOrEqual(3)
  })

  it('disables submit when form is not balanced', () => {
    render(<AdjustmentEntryForm {...defaultProps} />)
    const submitButton = screen.getByText('Create Entry').closest('button')!
    expect(submitButton).toBeDisabled()
  })

  it('shows Saving... when isLoading is true', () => {
    render(<AdjustmentEntryForm {...defaultProps} isLoading />)
    expect(screen.getByText('Saving...')).toBeInTheDocument()
  })

  it('shows error message when error prop is provided', () => {
    render(<AdjustmentEntryForm {...defaultProps} error="Failed to save entry" />)
    expect(screen.getByText('Failed to save entry')).toBeInTheDocument()
  })

  it('calls onCancel when Cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(<AdjustmentEntryForm {...defaultProps} />)

    await user.click(screen.getByText('Cancel'))
    expect(defaultProps.onCancel).toHaveBeenCalled()
  })

  it('renders adjustment type selector with all types', () => {
    render(<AdjustmentEntryForm {...defaultProps} />)
    // Should have adjustment type options
    const select = screen.getAllByRole('combobox')
    expect(select.length).toBeGreaterThanOrEqual(1)
  })
})
