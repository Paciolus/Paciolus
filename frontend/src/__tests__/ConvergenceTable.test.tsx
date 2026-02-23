/**
 * ConvergenceTable component tests — Sprint 288
 *
 * Tests: empty state, table rendering, convergence count badges,
 * tool name labels, disclaimer, export button.
 */
import { ConvergenceTable } from '@/components/engagement/ConvergenceTable'
import type { ConvergenceResponse } from '@/types/engagement'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))


const mockData: ConvergenceResponse = {
  engagement_id: 1,
  total_accounts: 3,
  items: [
    {
      account: 'Cash and Cash Equivalents',
      tools_flagging_it: ['trial_balance', 'journal_entry_testing', 'revenue_testing'],
      convergence_count: 3,
    },
    {
      account: 'Accounts Receivable',
      tools_flagging_it: ['trial_balance', 'ar_aging'],
      convergence_count: 2,
    },
    {
      account: 'Rent Expense',
      tools_flagging_it: ['journal_entry_testing'],
      convergence_count: 1,
    },
  ],
  generated_at: '2026-02-17T10:00:00Z',
}

const emptyData: ConvergenceResponse = {
  engagement_id: 1,
  total_accounts: 0,
  items: [],
  generated_at: '2026-02-17T10:00:00Z',
}

describe('ConvergenceTable', () => {
  const mockExport = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders disclaimer banner', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} />)
    expect(screen.getByText(/Convergence counts indicate how many diagnostic tools flagged an account/)).toBeInTheDocument()
    expect(screen.getByText(/This is NOT a risk score/)).toBeInTheDocument()
  })

  it('renders empty state when no items', () => {
    render(<ConvergenceTable data={emptyData} onExportCsv={mockExport} />)
    expect(screen.getByText(/No convergence data available/)).toBeInTheDocument()
  })

  it('renders account names in table', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} />)
    expect(screen.getByText('Cash and Cash Equivalents')).toBeInTheDocument()
    expect(screen.getByText('Accounts Receivable')).toBeInTheDocument()
    expect(screen.getByText('Rent Expense')).toBeInTheDocument()
  })

  it('renders convergence counts', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} />)
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('renders tool name labels (human readable)', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} />)
    // TB Diagnostics appears in two rows (Cash + AR rows), so use getAllByText
    expect(screen.getAllByText('TB Diagnostics').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('JE Testing').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Revenue Testing')).toBeInTheDocument()
    expect(screen.getByText('AR Aging')).toBeInTheDocument()
  })

  it('renders total accounts count', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} />)
    expect(screen.getByText(/3 accounts flagged across tools/)).toBeInTheDocument()
  })

  it('calls onExportCsv when export button clicked', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} />)
    const exportBtn = screen.getByText('Export CSV')
    fireEvent.click(exportBtn)
    expect(mockExport).toHaveBeenCalledTimes(1)
  })

  it('shows exporting state', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} isExporting />)
    expect(screen.getByText('Exporting...')).toBeInTheDocument()
  })

  it('renders table headers', () => {
    render(<ConvergenceTable data={mockData} onExportCsv={mockExport} />)
    expect(screen.getByText('Account')).toBeInTheDocument()
    expect(screen.getByText('Convergence Count')).toBeInTheDocument()
    expect(screen.getByText('Tools')).toBeInTheDocument()
  })

  it('renders singular account text for 1 account', () => {
    const singleItem: ConvergenceResponse = {
      ...mockData,
      total_accounts: 1,
      items: [mockData.items[0]],
    }
    render(<ConvergenceTable data={singleItem} onExportCsv={mockExport} />)
    expect(screen.getByText(/1 account flagged across tools/)).toBeInTheDocument()
  })
})
