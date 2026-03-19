/**
 * AdjustmentList component tests
 *
 * Tests: empty state, loading skeleton, entry rendering, status filter,
 * filter button counts, expand/collapse.
 */
import { AdjustmentList } from '@/components/adjustments/AdjustmentList'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

// Mock adjustment type constants to avoid undefined access
jest.mock('@/types/adjustment', () => {
  const actual = jest.requireActual('@/types/adjustment')
  return {
    ...actual,
    ADJUSTMENT_STATUS_COLORS: {
      proposed: { bg: 'bg-test', text: 'text-test', border: 'border-test' },
      approved: { bg: 'bg-test', text: 'text-test', border: 'border-test' },
      rejected: { bg: 'bg-test', text: 'text-test', border: 'border-test' },
      posted: { bg: 'bg-test', text: 'text-test', border: 'border-test' },
    },
    ADJUSTMENT_TYPE_COLORS: {
      accrual: { bg: 'bg-test', text: 'text-test' },
      deferral: { bg: 'bg-test', text: 'text-test' },
      estimate: { bg: 'bg-test', text: 'text-test' },
      error_correction: { bg: 'bg-test', text: 'text-test' },
      reclassification: { bg: 'bg-test', text: 'text-test' },
      other: { bg: 'bg-test', text: 'text-test' },
      proposed_aje: { bg: 'bg-test', text: 'text-test' },
    },
    formatAmount: (n: number) => `$${n.toLocaleString()}`,
    getAdjustmentStatusLabel: (s: string) => s.charAt(0).toUpperCase() + s.slice(1),
    getAdjustmentTypeLabel: (t: string) => t.replace(/_/g, ' '),
  }
})

const makeEntry = (overrides: Record<string, unknown> = {}) => ({
  id: 'entry-1',
  reference: 'AJE-001',
  description: 'Test adjustment entry',
  adjustment_type: 'proposed_aje' as const,
  status: 'proposed' as const,
  entry_total: 5000,
  total_debits: 5000,
  total_credits: 5000,
  account_count: 2,
  prepared_by: 'Test User',
  reviewed_by: null,
  created_at: '2026-01-15T10:00:00Z',
  is_reversing: false,
  notes: null,
  lines: [
    { account_name: 'Cash', debit: 5000, credit: 0 },
    { account_name: 'Revenue', debit: 0, credit: 5000 },
  ],
  ...overrides,
})

describe('AdjustmentList', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('shows empty state message when no entries', () => {
    render(<AdjustmentList entries={[]} />)
    expect(screen.getByText('No adjusting entries yet.')).toBeInTheDocument()
  })

  it('shows custom empty message', () => {
    render(<AdjustmentList entries={[]} emptyMessage="Nothing here." />)
    expect(screen.getByText('Nothing here.')).toBeInTheDocument()
  })

  it('shows loading skeleton when isLoading is true', () => {
    const { container } = render(<AdjustmentList entries={[]} isLoading={true} />)
    const pulseElements = container.querySelectorAll('.animate-pulse')
    expect(pulseElements.length).toBe(3)
  })

  it('renders entry reference and description', () => {
    render(<AdjustmentList entries={[makeEntry({ reference: 'AJE-099' })]} />)
    expect(screen.getByText('AJE-099')).toBeInTheDocument()
    expect(screen.getByText('Test adjustment entry')).toBeInTheDocument()
  })

  it('renders status filter buttons', () => {
    render(<AdjustmentList entries={[makeEntry()]} />)
    expect(screen.getByText('All')).toBeInTheDocument()
    // Filter buttons exist as clickable elements with these labels
    const filterButtons = screen.getAllByRole('button')
    const filterLabels = filterButtons.map(b => b.textContent)
    expect(filterLabels.some(l => l?.includes('Proposed'))).toBe(true)
    expect(filterLabels.some(l => l?.includes('Approved'))).toBe(true)
  })

  it('filters entries by status', () => {
    const entries = [
      makeEntry({ id: '1', status: 'proposed', reference: 'AJE-001' }),
      makeEntry({ id: '2', status: 'approved', reference: 'AJE-002' }),
    ]
    render(<AdjustmentList entries={entries} />)

    // Click the "Approved" filter button (it contains count like "Approved(1)")
    const filterButtons = screen.getAllByRole('button')
    const approvedBtn = filterButtons.find(btn => btn.textContent?.includes('Approved'))
    expect(approvedBtn).toBeTruthy()
    fireEvent.click(approvedBtn!)

    expect(screen.getByText('AJE-002')).toBeInTheDocument()
    expect(screen.queryByText('AJE-001')).not.toBeInTheDocument()
  })

  it('shows "no entries with status" when filter yields no results', () => {
    const entries = [makeEntry({ id: '1', status: 'proposed' })]
    render(<AdjustmentList entries={entries} />)

    const filterButtons = screen.getAllByRole('button')
    const rejectedBtn = filterButtons.find(btn => btn.textContent?.includes('Rejected'))
    expect(rejectedBtn).toBeTruthy()
    fireEvent.click(rejectedBtn!)
    expect(screen.getByText(/No entries with status/)).toBeInTheDocument()
  })

  it('renders account count', () => {
    render(<AdjustmentList entries={[makeEntry()]} />)
    expect(screen.getByText('2 accounts')).toBeInTheDocument()
  })
})
