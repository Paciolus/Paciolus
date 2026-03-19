/**
 * TestResultGrid component tests
 *
 * Tests: rendering tier sections, test cards, flagged counts,
 * clean badge, empty tier sections.
 */
import { TestResultGrid } from '@/components/shared/testing/TestResultGrid'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, children, ...rest }: any) =>
      <div {...rest}>{children}</div>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))

const makeResult = (overrides: Record<string, unknown> = {}) => ({
  test_name: 'Round Amount Test',
  test_key: 'round_amounts',
  test_tier: 'structural' as const,
  entries_flagged: 5,
  total_entries: 1000,
  flag_rate: 0.005,
  severity: 'medium' as const,
  description: 'Flags round dollar amounts',
  flagged_entries: [],
  ...overrides,
})

const tierSections = [
  { tier: 'structural' as const, label: 'Structural Tests' },
  { tier: 'statistical' as const, label: 'Statistical Tests' },
  { tier: 'advanced' as const, label: 'Advanced Tests' },
]

const entryRenderer = (fe: any) => <div>{fe.issue}</div>

describe('TestResultGrid', () => {
  it('renders tier section headings', () => {
    const results = [
      makeResult({ test_tier: 'structural' }),
      makeResult({ test_key: 'benford', test_name: 'Benford', test_tier: 'statistical' }),
    ]
    render(
      <TestResultGrid
        results={results}
        entryRenderer={entryRenderer}
        expandedLabel="entries"
        tierSections={tierSections}
      />
    )
    expect(screen.getByText('Structural Tests')).toBeInTheDocument()
    expect(screen.getByText('Statistical Tests')).toBeInTheDocument()
  })

  it('renders test card names', () => {
    const results = [makeResult()]
    render(
      <TestResultGrid
        results={results}
        entryRenderer={entryRenderer}
        expandedLabel="entries"
        tierSections={tierSections}
      />
    )
    expect(screen.getByText('Round Amount Test')).toBeInTheDocument()
  })

  it('shows flagged count', () => {
    const results = [makeResult({ entries_flagged: 12 })]
    render(
      <TestResultGrid
        results={results}
        entryRenderer={entryRenderer}
        expandedLabel="entries"
        tierSections={tierSections}
      />
    )
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('shows Clean for zero flagged entries', () => {
    const results = [makeResult({ entries_flagged: 0, flag_rate: 0 })]
    render(
      <TestResultGrid
        results={results}
        entryRenderer={entryRenderer}
        expandedLabel="entries"
        tierSections={tierSections}
      />
    )
    expect(screen.getByText('Clean')).toBeInTheDocument()
  })

  it('does not render empty tier sections', () => {
    const results = [makeResult({ test_tier: 'structural' })]
    render(
      <TestResultGrid
        results={results}
        entryRenderer={entryRenderer}
        expandedLabel="entries"
        tierSections={tierSections}
      />
    )
    expect(screen.queryByText('Advanced Tests')).not.toBeInTheDocument()
  })

  it('shows tier badge', () => {
    const results = [makeResult()]
    render(
      <TestResultGrid
        results={results}
        entryRenderer={entryRenderer}
        expandedLabel="entries"
        tierSections={tierSections}
      />
    )
    expect(screen.getByText('Structural')).toBeInTheDocument()
  })
})
