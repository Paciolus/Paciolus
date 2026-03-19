/**
 * FlaggedEntriesTable component tests
 *
 * Tests: rendering table, empty state, filters, search,
 * severity badge, column rendering.
 */
import { FlaggedEntriesTable } from '@/components/shared/testing/FlaggedEntriesTable'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
    tr: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <tr {...rest}>{children}</tr>,
  },
}))

jest.mock('@/components/ui/Reveal', () => ({
  Reveal: ({ children }: any) => <div>{children}</div>,
}))

jest.mock('@/utils/motionTokens', () => ({
  TIMING: { settle: 0.4 },
  EASE: { emphasis: [0.6, 0, 0.2, 1] },
}))

const columns = [
  {
    field: 'amount',
    label: 'Amount',
    render: (fe: any) => <span>{fe.entry.amount}</span>,
    sortValue: (fe: any) => fe.entry.amount as number,
  },
]

const makeResult = (entries: any[]) => ({
  test_key: 'round_amounts',
  entries_flagged: entries.length,
  flagged_entries: entries,
})

describe('FlaggedEntriesTable', () => {
  it('shows empty message when no flagged entries', () => {
    render(
      <FlaggedEntriesTable
        results={[]}
        columns={columns}
        searchFields={['amount']}
        searchPlaceholder="Search..."
        emptyMessage="No flagged entries found."
        entityLabel="entries"
      />
    )
    expect(screen.getByText('No flagged entries found.')).toBeInTheDocument()
  })

  it('renders table with entries', () => {
    const entries = [
      { entry: { amount: 1000 }, severity: 'high' as const, test_name: 'Round', test_key: 'round', issue: 'Round amount', confidence: 0.9 },
    ]
    render(
      <FlaggedEntriesTable
        results={[makeResult(entries)]}
        columns={columns}
        searchFields={['amount']}
        searchPlaceholder="Search..."
        emptyMessage="None"
        entityLabel="entries"
      />
    )
    expect(screen.getByText('1000')).toBeInTheDocument()
    expect(screen.getByText('Round amount')).toBeInTheDocument()
  })

  it('renders severity badge', () => {
    const entries = [
      { entry: { amount: 500 }, severity: 'high' as const, test_name: 'T', test_key: 'k', issue: 'Issue', confidence: 0.9 },
    ]
    render(
      <FlaggedEntriesTable
        results={[makeResult(entries)]}
        columns={columns}
        searchFields={['amount']}
        searchPlaceholder="Search..."
        emptyMessage="None"
        entityLabel="entries"
      />
    )
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  it('renders filter bar with search input', () => {
    const entries = [
      { entry: { amount: 500 }, severity: 'low' as const, test_name: 'T', test_key: 'k', issue: 'Issue', confidence: 0.5 },
    ]
    render(
      <FlaggedEntriesTable
        results={[makeResult(entries)]}
        columns={columns}
        searchFields={['amount']}
        searchPlaceholder="Search amounts..."
        emptyMessage="None"
        entityLabel="entries"
      />
    )
    expect(screen.getByPlaceholderText('Search amounts...')).toBeInTheDocument()
  })

  it('shows count of entries', () => {
    const entries = [
      { entry: { amount: 100 }, severity: 'low' as const, test_name: 'T', test_key: 'k', issue: 'I1', confidence: 0.5 },
      { entry: { amount: 200 }, severity: 'medium' as const, test_name: 'T', test_key: 'k', issue: 'I2', confidence: 0.6 },
    ]
    render(
      <FlaggedEntriesTable
        results={[makeResult(entries)]}
        columns={columns}
        searchFields={['amount']}
        searchPlaceholder="Search..."
        emptyMessage="None"
        entityLabel="items"
      />
    )
    expect(screen.getByText('2 of 2 items')).toBeInTheDocument()
  })

  it('renders column headers', () => {
    const entries = [
      { entry: { amount: 100 }, severity: 'low' as const, test_name: 'T', test_key: 'k', issue: 'I', confidence: 0.5 },
    ]
    render(
      <FlaggedEntriesTable
        results={[makeResult(entries)]}
        columns={columns}
        searchFields={['amount']}
        searchPlaceholder="Search..."
        emptyMessage="None"
        entityLabel="entries"
      />
    )
    expect(screen.getByText('Amount')).toBeInTheDocument()
    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('Issue')).toBeInTheDocument()
  })
})
