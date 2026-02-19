/**
 * ColumnMappingModal component tests
 *
 * Tests: visibility toggle, column selection, uniqueness constraint,
 * completeness validation, confidence indicator colors, detection notes,
 * confirm/cancel callbacks, and backdrop dismiss.
 */
import { render, screen } from '@/test-utils'
import userEvent from '@testing-library/user-event'

import { ColumnMappingModal } from '@/components/mapping/ColumnMappingModal'
import type { ColumnDetectionInfo } from '@/components/mapping/ColumnMappingModal'

// ─── Fixtures ──────────────────────────────────────────────────────────────────

const baseDetection: ColumnDetectionInfo = {
  account_column: 'Account Name',
  debit_column: 'Debit Amount',
  credit_column: 'Credit Amount',
  account_confidence: 0.9,
  debit_confidence: 0.75,
  credit_confidence: 0.4,
  overall_confidence: 0.68,
  requires_mapping: true,
  all_columns: ['Account Name', 'Debit Amount', 'Credit Amount', 'Description', 'Balance'],
  detection_notes: ['Multiple potential debit columns found', 'Credit column has low confidence'],
}

const emptyDetection: ColumnDetectionInfo = {
  account_column: null,
  debit_column: null,
  credit_column: null,
  account_confidence: 0,
  debit_confidence: 0,
  credit_confidence: 0,
  overall_confidence: 0,
  requires_mapping: true,
  all_columns: ['Col A', 'Col B', 'Col C', 'Col D'],
  detection_notes: [],
}

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  onConfirm: jest.fn(),
  columnDetection: baseDetection,
  filename: 'test-tb.csv',
}

describe('ColumnMappingModal', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ─── Visibility ─────────────────────────────────────────────────────

  it('returns null when isOpen is false', () => {
    const { container } = render(<ColumnMappingModal {...defaultProps} isOpen={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders modal dialog when isOpen is true', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    expect(screen.getByText('Column Mapping Required')).toBeInTheDocument()
  })

  // ─── Filename Display ──────────────────────────────────────────────

  it('shows the filename in the description', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    expect(screen.getByText('test-tb.csv')).toBeInTheDocument()
  })

  // ─── Pre-selected Columns ──────────────────────────────────────────

  it('pre-selects detected columns', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    const accountSelect = screen.getByLabelText(/Account Name Column/)
    const debitSelect = screen.getByLabelText(/Debit Column/)
    const creditSelect = screen.getByLabelText(/Credit Column/)

    expect(accountSelect).toHaveValue('Account Name')
    expect(debitSelect).toHaveValue('Debit Amount')
    expect(creditSelect).toHaveValue('Credit Amount')
  })

  it('starts with empty selections when nothing detected', () => {
    render(<ColumnMappingModal {...defaultProps} columnDetection={emptyDetection} />)
    const accountSelect = screen.getByLabelText(/Account Name Column/)
    expect(accountSelect).toHaveValue('')
  })

  // ─── Column Options ────────────────────────────────────────────────

  it('shows all columns as options in each select', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    const selects = screen.getAllByRole('combobox')
    // Each select should have placeholder + 5 columns = 6 options
    selects.forEach(select => {
      const options = select.querySelectorAll('option')
      expect(options.length).toBe(6) // placeholder + 5 columns
    })
  })

  it('marks detected columns in option text', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    // The detected account column option should show "(detected)"
    const accountSelect = screen.getByLabelText(/Account Name Column/)
    const options = accountSelect.querySelectorAll('option')
    const detectedOption = Array.from(options).find(o => o.textContent?.includes('(detected)'))
    expect(detectedOption).toBeDefined()
    expect(detectedOption?.textContent).toContain('Account Name')
  })

  // ─── Confidence Display Colors ──────────────────────────────────────

  it('shows high confidence (>=0.8) in sage color', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    // Account confidence is 0.9 → 90%
    const percentages = screen.getAllByText('90%')
    expect(percentages.length).toBeGreaterThanOrEqual(1)
    expect(percentages[0].className).toContain('text-sage')
  })

  it('shows medium confidence (>=0.5, <0.8) in content-primary color', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    // Debit confidence is 0.75 → 75%
    const percentage = screen.getByText('75%')
    expect(percentage.className).toContain('text-content-primary')
  })

  it('shows low confidence (<0.5) in clay color', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    // Credit confidence is 0.4 → 40%
    const percentage = screen.getByText('40%')
    expect(percentage.className).toContain('text-clay')
  })

  it('shows overall confidence in header', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    expect(screen.getByText('68%')).toBeInTheDocument()
  })

  // ─── Detection Notes ────────────────────────────────────────────────

  it('shows detection notes when present', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    expect(screen.getByText('Multiple potential debit columns found')).toBeInTheDocument()
    expect(screen.getByText('Credit column has low confidence')).toBeInTheDocument()
  })

  it('does not show detection notes section when empty', () => {
    render(<ColumnMappingModal {...defaultProps} columnDetection={emptyDetection} />)
    expect(screen.queryByText('Detection Notes:')).not.toBeInTheDocument()
  })

  // ─── Validation: Completeness ───────────────────────────────────────

  it('disables Confirm when not all columns are selected', () => {
    render(<ColumnMappingModal {...defaultProps} columnDetection={emptyDetection} />)
    const confirmButton = screen.getByRole('button', { name: 'Confirm Mapping' })
    expect(confirmButton).toBeDisabled()
  })

  it('enables Confirm when all unique columns are selected', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    const confirmButton = screen.getByRole('button', { name: 'Confirm Mapping' })
    expect(confirmButton).not.toBeDisabled()
  })

  // ─── Validation: Uniqueness ─────────────────────────────────────────

  it('disables Confirm when duplicate columns are selected', async () => {
    const user = userEvent.setup()
    render(<ColumnMappingModal {...defaultProps} />)

    // Change debit column to same as account column
    const debitSelect = screen.getByLabelText(/Debit Column/)
    await user.selectOptions(debitSelect, 'Account Name')

    const confirmButton = screen.getByRole('button', { name: 'Confirm Mapping' })
    expect(confirmButton).toBeDisabled()
  })

  it('shows uniqueness warning when duplicate columns are selected', async () => {
    const user = userEvent.setup()
    render(<ColumnMappingModal {...defaultProps} />)

    const debitSelect = screen.getByLabelText(/Debit Column/)
    await user.selectOptions(debitSelect, 'Account Name')

    expect(screen.getByText('Each column must be unique. Please select different columns.')).toBeInTheDocument()
  })

  it('does not show uniqueness warning when columns are unique', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    expect(screen.queryByText('Each column must be unique. Please select different columns.')).not.toBeInTheDocument()
  })

  // ─── Confirm / Cancel ──────────────────────────────────────────────

  it('calls onConfirm with correct mapping when confirmed', async () => {
    const user = userEvent.setup()
    render(<ColumnMappingModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Confirm Mapping' }))

    expect(defaultProps.onConfirm).toHaveBeenCalledWith({
      account_column: 'Account Name',
      debit_column: 'Debit Amount',
      credit_column: 'Credit Amount',
    })
  })

  it('does not call onConfirm when columns are invalid', async () => {
    const user = userEvent.setup()
    render(<ColumnMappingModal {...defaultProps} columnDetection={emptyDetection} />)

    // Confirm button is disabled, click it anyway
    const confirmButton = screen.getByRole('button', { name: 'Confirm Mapping' })
    await user.click(confirmButton)

    expect(defaultProps.onConfirm).not.toHaveBeenCalled()
  })

  it('calls onClose when Cancel button is clicked', async () => {
    const user = userEvent.setup()
    render(<ColumnMappingModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup()
    render(<ColumnMappingModal {...defaultProps} />)

    // Backdrop has aria-hidden="true"
    const backdrop = document.querySelector('[aria-hidden="true"]')!
    await user.click(backdrop)
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  // ─── Zero-Storage Badge ─────────────────────────────────────────────

  it('shows Session Only badge', () => {
    render(<ColumnMappingModal {...defaultProps} />)
    expect(screen.getByText('Session Only')).toBeInTheDocument()
  })

  // ─── Column Change ─────────────────────────────────────────────────

  it('allows changing column selections', async () => {
    const user = userEvent.setup()
    render(<ColumnMappingModal {...defaultProps} />)

    const accountSelect = screen.getByLabelText(/Account Name Column/)
    await user.selectOptions(accountSelect, 'Description')

    expect(accountSelect).toHaveValue('Description')

    // Confirm with new mapping
    await user.click(screen.getByRole('button', { name: 'Confirm Mapping' }))
    expect(defaultProps.onConfirm).toHaveBeenCalledWith({
      account_column: 'Description',
      debit_column: 'Debit Amount',
      credit_column: 'Credit Amount',
    })
  })
})
