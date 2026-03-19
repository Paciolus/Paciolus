/**
 * ToolStatusGrid component tests
 *
 * Tests: rendering all tools, completed vs not started badges,
 * run counts, composite scores, trend indicators.
 */
import { ToolStatusGrid } from '@/components/engagement/ToolStatusGrid'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
}))

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}))

jest.mock('@/lib/motion', () => ({
  staggerContainerTight: { hidden: {}, visible: {} },
  fadeUp: { hidden: {}, visible: {} },
}))

describe('ToolStatusGrid', () => {
  it('renders Diagnostic Status heading', () => {
    render(<ToolStatusGrid toolRuns={[]} />)
    expect(screen.getByText('Diagnostic Status')).toBeInTheDocument()
  })

  it('shows Not Started badge when no runs exist for a tool', () => {
    render(<ToolStatusGrid toolRuns={[]} />)
    const notStartedBadges = screen.getAllByText('Not Started')
    expect(notStartedBadges.length).toBeGreaterThan(0)
  })

  it('shows Completed badge when a tool has runs', () => {
    const runs = [
      {
        id: 1,
        tool_name: 'trial_balance' as const,
        run_at: '2026-01-15T10:00:00Z',
        composite_score: 85.5,
        engagement_id: 1,
      },
    ]
    render(<ToolStatusGrid toolRuns={runs} />)
    expect(screen.getByText('Completed')).toBeInTheDocument()
  })

  it('shows run count', () => {
    const runs = [
      { id: 1, tool_name: 'trial_balance' as const, run_at: '2026-01-15T10:00:00Z', composite_score: 85, engagement_id: 1 },
      { id: 2, tool_name: 'trial_balance' as const, run_at: '2026-01-16T10:00:00Z', composite_score: 90, engagement_id: 1 },
    ]
    render(<ToolStatusGrid toolRuns={runs} />)
    expect(screen.getByText('2 runs')).toBeInTheDocument()
  })

  it('shows composite score', () => {
    const runs = [
      { id: 1, tool_name: 'trial_balance' as const, run_at: '2026-01-15T10:00:00Z', composite_score: 85.5, engagement_id: 1 },
    ]
    render(<ToolStatusGrid toolRuns={runs} />)
    expect(screen.getByText('Score: 85.5')).toBeInTheDocument()
  })

  it('renders tool name labels', () => {
    render(<ToolStatusGrid toolRuns={[]} />)
    expect(screen.getByText('TB Diagnostics')).toBeInTheDocument()
    expect(screen.getByText('JE Testing')).toBeInTheDocument()
  })

  it('links to correct tool page', () => {
    render(<ToolStatusGrid toolRuns={[]} />)
    const links = screen.getAllByRole('link')
    const hrefs = links.map(l => l.getAttribute('href'))
    expect(hrefs).toContain('/tools/trial-balance')
  })
})
