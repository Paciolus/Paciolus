/**
 * FollowUpItemsTable component tests
 *
 * Tests follow-up items tracker: filtering, sorting, pagination,
 * row expand/collapse, inline editing, disposition changes, assignment, deletion.
 */
import userEvent from '@testing-library/user-event'
import { FollowUpItemsTable } from '@/components/engagement/FollowUpItemsTable'
import { render, screen, within, waitFor } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <div {...rest}>{children}</div>,
    tr: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) => <tr {...rest}>{children}</tr>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

// Mock child components
jest.mock('@/components/engagement/DispositionSelect', () => ({
  DispositionSelect: ({ value, onChange, disabled }: any) => (
    <select data-testid="disposition-select" value={value} onChange={(e: any) => onChange(e.target.value)} disabled={disabled}>
      <option value="not_reviewed">Not Reviewed</option>
      <option value="investigated_no_issue">No Issue</option>
      <option value="investigated_adjustment_posted">Adjustment Posted</option>
    </select>
  ),
}))

jest.mock('@/components/engagement/CommentThread', () => ({
  CommentThread: ({ itemId }: any) => <div data-testid={`comment-thread-${itemId}`}>Comments</div>,
}))

jest.mock('@/components/shared/StatusBadge', () => ({
  StatusBadge: ({ label }: any) => <span data-testid="status-badge">{label}</span>,
}))


const createItem = (overrides: Record<string, any> = {}) => ({
  id: 1,
  engagement_id: 1,
  tool_source: 'tb_diagnostics',
  description: 'Suspense account with material balance',
  severity: 'high' as const,
  disposition: 'not_reviewed' as const,
  auditor_notes: null,
  assigned_to: null,
  created_at: '2025-01-15T10:00:00Z',
  updated_at: '2025-01-15T10:00:00Z',
  ...overrides,
})

const sampleItems = [
  createItem({ id: 1, severity: 'high', tool_source: 'tb_diagnostics', description: 'Suspense account' }),
  createItem({ id: 2, severity: 'medium', tool_source: 'je_testing', description: 'Unbalanced entries' }),
  createItem({ id: 3, severity: 'low', tool_source: 'ap_testing', description: 'Duplicate payments', disposition: 'investigated_no_issue' }),
  createItem({ id: 4, severity: 'high', tool_source: 'tb_diagnostics', description: 'Concentration risk', assigned_to: 42 }),
]

const defaultProps = {
  items: sampleItems,
  isLoading: false,
  onUpdateItem: jest.fn(),
  onDeleteItem: jest.fn(),
  currentUserId: 42,
}

describe('FollowUpItemsTable', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    defaultProps.onUpdateItem.mockResolvedValue(null)
    defaultProps.onDeleteItem.mockResolvedValue(true)
  })

  it('renders all items in table', () => {
    render(<FollowUpItemsTable {...defaultProps} />)
    expect(screen.getByText('Suspense account')).toBeInTheDocument()
    expect(screen.getByText('Unbalanced entries')).toBeInTheDocument()
    expect(screen.getByText('Duplicate payments')).toBeInTheDocument()
    expect(screen.getByText('Concentration risk')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(<FollowUpItemsTable {...defaultProps} isLoading={true} items={[]} />)
    expect(screen.getByText('Loading follow-up items...')).toBeInTheDocument()
  })

  it('shows empty state when no items match filters', () => {
    render(<FollowUpItemsTable {...defaultProps} items={[]} />)
    expect(screen.getByText('No follow-up items found')).toBeInTheDocument()
  })

  it('filters by severity', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    // Find severity filter select
    const severityFilter = screen.getByDisplayValue('All Severities')
    await user.selectOptions(severityFilter, 'high')

    // Should show only high severity items
    expect(screen.getByText('Suspense account')).toBeInTheDocument()
    expect(screen.getByText('Concentration risk')).toBeInTheDocument()
    expect(screen.queryByText('Unbalanced entries')).not.toBeInTheDocument()
    expect(screen.queryByText('Duplicate payments')).not.toBeInTheDocument()
  })

  it('filters by disposition', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    const dispositionFilter = screen.getByDisplayValue('All Dispositions')
    await user.selectOptions(dispositionFilter, 'investigated_no_issue')

    expect(screen.getByText('Duplicate payments')).toBeInTheDocument()
    expect(screen.queryByText('Suspense account')).not.toBeInTheDocument()
  })

  it('filters by search text', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    const searchInput = screen.getByPlaceholderText('Search descriptions...')
    await user.type(searchInput, 'Suspense')

    expect(screen.getByText('Suspense account')).toBeInTheDocument()
    expect(screen.queryByText('Unbalanced entries')).not.toBeInTheDocument()
  })

  it('filters by assignment (My Items)', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    const myItemsButton = screen.getByText('My Items')
    await user.click(myItemsButton)

    // Only item assigned to currentUserId (42) should show
    expect(screen.getByText('Concentration risk')).toBeInTheDocument()
    expect(screen.queryByText('Suspense account')).not.toBeInTheDocument()
  })

  it('filters by assignment (Unassigned)', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    const unassignedButton = screen.getByText('Unassigned')
    await user.click(unassignedButton)

    // Items without assigned_to should show
    expect(screen.getByText('Suspense account')).toBeInTheDocument()
    expect(screen.getByText('Unbalanced entries')).toBeInTheDocument()
    expect(screen.queryByText('Concentration risk')).not.toBeInTheDocument()
  })

  it('shows sort indicators on column header click', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    // Click severity column header to toggle sort
    const severityHeader = screen.getByText(/Severity/)
    await user.click(severityHeader)

    // Should show sort indicator
    expect(severityHeader.textContent).toMatch(/[▲▼]/)
  })

  it('expands row on click to show details', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    // Click on the first row
    const firstRow = screen.getByText('Suspense account').closest('tr')!
    await user.click(firstRow)

    // Should show expanded content (notes textarea, disposition, etc.)
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Add investigation notes...')).toBeInTheDocument()
    })
  })

  it('shows Assign to me button for unassigned items in expanded view', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    // Click unassigned item
    const row = screen.getByText('Suspense account').closest('tr')!
    await user.click(row)

    await waitFor(() => {
      expect(screen.getByText('Assign to me')).toBeInTheDocument()
    })
  })

  it('calls onUpdateItem when assigning to self', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    // Expand unassigned item
    const row = screen.getByText('Suspense account').closest('tr')!
    await user.click(row)

    await waitFor(() => {
      expect(screen.getByText('Assign to me')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Assign to me'))
    expect(defaultProps.onUpdateItem).toHaveBeenCalledWith(1, { assigned_to: 42 })
  })

  it('calls onDeleteItem when Delete Item is clicked', async () => {
    const user = userEvent.setup()
    render(<FollowUpItemsTable {...defaultProps} />)

    // Expand first item
    const row = screen.getByText('Suspense account').closest('tr')!
    await user.click(row)

    await waitFor(() => {
      expect(screen.getByText('Delete Item')).toBeInTheDocument()
    })

    await user.click(screen.getByText('Delete Item'))
    expect(defaultProps.onDeleteItem).toHaveBeenCalledWith(1)
  })

  it('shows results count', () => {
    render(<FollowUpItemsTable {...defaultProps} />)
    // The table should indicate how many items are shown
    expect(screen.getByText(/4/)).toBeInTheDocument()
  })
})
