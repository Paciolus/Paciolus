/**
 * WorkpaperIndex component tests
 *
 * Tests: header display, document register table,
 * follow-up summary, and sign-off section.
 */
import { WorkpaperIndex } from '@/components/engagement/WorkpaperIndex'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    tr: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <tr {...rest}>{children}</tr>,
  },
}))


const mockIndex = {
  client_name: 'Acme Corp',
  period_start: '2025-01-01',
  period_end: '2025-12-31',
  generated_at: '2026-02-15T10:30:00Z',
  document_register: [
    {
      tool_name: 'tb_diagnostics',
      tool_label: 'TB Diagnostics',
      status: 'completed' as const,
      run_count: 3,
      last_run_date: '2026-02-14T08:00:00Z',
      lead_sheet_refs: ['A-100'],
    },
    {
      tool_name: 'je_testing',
      tool_label: 'JE Testing',
      status: 'not_started' as const,
      run_count: 0,
      last_run_date: null,
      lead_sheet_refs: [],
    },
  ],
  follow_up_summary: {
    total_count: 5,
    by_severity: { high: 1, medium: 2, low: 2 },
    by_disposition: { open: 3, resolved: 2 },
    by_tool_source: { 'TB Diagnostics': 3, 'AP Testing': 2 },
  },
}

const emptyFollowUpIndex = {
  ...mockIndex,
  follow_up_summary: {
    total_count: 0,
    by_severity: {},
    by_disposition: {},
    by_tool_source: {},
  },
}

describe('WorkpaperIndex', () => {
  it('renders header with client name', () => {
    render(<WorkpaperIndex index={mockIndex} />)
    expect(screen.getByText('Workpaper Index')).toBeInTheDocument()
    expect(screen.getByText(/Acme Corp/)).toBeInTheDocument()
  })

  it('shows tools completed count', () => {
    render(<WorkpaperIndex index={mockIndex} />)
    expect(screen.getByText('1 / 2')).toBeInTheDocument()
  })

  it('renders document register table with entries', () => {
    render(<WorkpaperIndex index={mockIndex} />)
    // "TB Diagnostics" appears in both table and follow-up summary
    expect(screen.getAllByText('TB Diagnostics').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('JE Testing')).toBeInTheDocument()
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('Not Started')).toBeInTheDocument()
  })

  it('shows run counts', () => {
    render(<WorkpaperIndex index={mockIndex} />)
    // "3" and "0" may appear in multiple places (run counts + follow-up summary)
    expect(screen.getAllByText('3').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(1)
  })

  it('shows lead sheet references', () => {
    render(<WorkpaperIndex index={mockIndex} />)
    expect(screen.getByText('A-100')).toBeInTheDocument()
  })

  it('shows follow-up summary when items exist', () => {
    render(<WorkpaperIndex index={mockIndex} />)
    expect(screen.getByText('Follow-Up Summary')).toBeInTheDocument()
    expect(screen.getByText('By Severity')).toBeInTheDocument()
    expect(screen.getByText('By Disposition')).toBeInTheDocument()
    expect(screen.getByText('By Tool')).toBeInTheDocument()
  })

  it('does not show follow-up summary when no items', () => {
    render(<WorkpaperIndex index={emptyFollowUpIndex} />)
    expect(screen.queryByText('Follow-Up Summary')).not.toBeInTheDocument()
  })

  it('shows sign-off section with blank fields', () => {
    render(<WorkpaperIndex index={mockIndex} />)
    expect(screen.getByText('Sign-Off')).toBeInTheDocument()
    expect(screen.getByText('Prepared By')).toBeInTheDocument()
    expect(screen.getByText('Reviewed By')).toBeInTheDocument()
    expect(screen.getByText('Date')).toBeInTheDocument()
  })
})
