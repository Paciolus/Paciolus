/**
 * WorkbookInspector component tests
 *
 * Tests: visibility, sheet selection, select all/deselect all,
 * empty sheet handling, row count aggregation, and confirm/cancel.
 */
import userEvent from '@testing-library/user-event'
import { WorkbookInspector } from '@/components/workbook/WorkbookInspector'
import type { WorkbookInfo } from '@/types/mapping'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, custom, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))


// ─── Fixtures ──────────────────────────────────────────────────────────────────

const mockWorkbook: WorkbookInfo = {
  filename: 'financials-2025.xlsx',
  sheet_count: 3,
  sheets: [
    { name: 'Balance Sheet', row_count: 100, column_count: 5, columns: ['Account', 'Debit', 'Credit', 'Balance', 'Notes'], has_data: true },
    { name: 'Income Statement', row_count: 50, column_count: 3, columns: ['Account', 'Amount', 'Category'], has_data: true },
    { name: 'Empty Sheet', row_count: 0, column_count: 0, columns: [], has_data: false },
  ],
  total_rows: 150,
  is_multi_sheet: true,
  format: 'xlsx',
  requires_sheet_selection: true,
}

const defaultProps = {
  isOpen: true,
  onClose: jest.fn(),
  onConfirm: jest.fn(),
  workbookInfo: mockWorkbook,
}

describe('WorkbookInspector', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  // ─── Visibility ─────────────────────────────────────────────────────

  it('returns null when isOpen is false', () => {
    const { container } = render(<WorkbookInspector {...defaultProps} isOpen={false} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders modal with title when isOpen is true', () => {
    render(<WorkbookInspector {...defaultProps} />)
    expect(screen.getByText('Workbook Inspector')).toBeInTheDocument()
    expect(screen.getByText('financials-2025.xlsx')).toBeInTheDocument()
  })

  // ─── Sheet Summary ─────────────────────────────────────────────────

  it('shows sheet count and total rows', () => {
    render(<WorkbookInspector {...defaultProps} />)
    expect(screen.getByText('3 sheets found')).toBeInTheDocument()
    expect(screen.getByText('150 total rows')).toBeInTheDocument()
  })

  // ─── Sheet List ─────────────────────────────────────────────────────

  it('shows all sheets including empty ones', () => {
    render(<WorkbookInspector {...defaultProps} />)
    expect(screen.getByText('Balance Sheet')).toBeInTheDocument()
    expect(screen.getByText('Income Statement')).toBeInTheDocument()
    expect(screen.getByText('Empty Sheet')).toBeInTheDocument()
  })

  it('marks empty sheets with "Empty" badge', () => {
    render(<WorkbookInspector {...defaultProps} />)
    expect(screen.getByText('Empty')).toBeInTheDocument()
  })

  it('shows row and column counts for each sheet', () => {
    render(<WorkbookInspector {...defaultProps} />)
    expect(screen.getByText('100 rows')).toBeInTheDocument()
    expect(screen.getByText('5 columns')).toBeInTheDocument()
    expect(screen.getByText('50 rows')).toBeInTheDocument()
  })

  it('shows column preview with truncation for many columns', () => {
    render(<WorkbookInspector {...defaultProps} />)
    // Balance Sheet has 5 columns, shows first 4 + "+1 more"
    expect(screen.getByText(/Account, Debit, Credit, Balance/)).toBeInTheDocument()
    expect(screen.getByText(/\+1 more/)).toBeInTheDocument()
  })

  // ─── Pre-selection ──────────────────────────────────────────────────

  it('pre-selects sheets with data by default', () => {
    render(<WorkbookInspector {...defaultProps} />)
    // 2 sheets with data selected → "2 sheets selected"
    expect(screen.getByText('2 sheets selected')).toBeInTheDocument()
    expect(screen.getByText('150 rows to audit')).toBeInTheDocument()
  })

  // ─── Toggle Selection ──────────────────────────────────────────────

  it('deselects a sheet when clicked', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Income Statement'))

    expect(screen.getByText('1 sheet selected')).toBeInTheDocument()
    expect(screen.getByText('100 rows to audit')).toBeInTheDocument()
  })

  it('re-selects a deselected sheet when clicked', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Income Statement'))
    expect(screen.getByText('1 sheet selected')).toBeInTheDocument()

    await user.click(screen.getByText('Income Statement'))
    expect(screen.getByText('2 sheets selected')).toBeInTheDocument()
  })

  // ─── Select All / Deselect All ──────────────────────────────────────

  it('deselects all when "Deselect All" is clicked', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Deselect All'))

    expect(screen.getByText('0 rows to audit')).toBeInTheDocument()
  })

  it('selects all when "Select All" is clicked after deselecting', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Deselect All'))
    await user.click(screen.getByText('Select All'))

    expect(screen.getByText('2 sheets selected')).toBeInTheDocument()
  })

  // ─── Confirm / Cancel ──────────────────────────────────────────────

  it('disables confirm button when no sheets selected', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Deselect All'))

    // Button text changes based on selection count
    const buttons = screen.getAllByRole('button')
    const confirmBtn = buttons.find(b => b.textContent === 'Audit Selected')
    expect(confirmBtn).toBeDisabled()
  })

  it('shows "Consolidate & Audit" when multiple sheets selected', () => {
    render(<WorkbookInspector {...defaultProps} />)
    expect(screen.getByText('Consolidate & Audit')).toBeInTheDocument()
  })

  it('shows "Audit Selected" when single sheet selected', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Income Statement'))
    expect(screen.getByText('Audit Selected')).toBeInTheDocument()
  })

  it('calls onConfirm with selected sheet names', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Consolidate & Audit'))

    expect(defaultProps.onConfirm).toHaveBeenCalledWith(
      expect.arrayContaining(['Balance Sheet', 'Income Statement'])
    )
  })

  it('calls onClose when Cancel is clicked', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Cancel'))
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })

  // ─── Empty Sheet Non-Interactive ────────────────────────────────────

  it('does not toggle empty sheets when clicked', async () => {
    const user = userEvent.setup()
    render(<WorkbookInspector {...defaultProps} />)

    await user.click(screen.getByText('Empty Sheet'))
    // Selection should not change
    expect(screen.getByText('2 sheets selected')).toBeInTheDocument()
  })
})
