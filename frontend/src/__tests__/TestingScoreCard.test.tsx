/**
 * TestingScoreCard component tests
 *
 * Tests: rendering score, risk tier, stats grid,
 * top findings, severity counts, flag rate.
 */
import { TestingScoreCard } from '@/components/shared/testing/TestingScoreCard'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, style, children, ...rest }: any) =>
      <div {...rest} style={style}>{children}</div>,
    circle: ({ initial, animate, exit, transition, style, children, ...rest }: any) =>
      <circle {...rest} style={style}>{children}</circle>,
    span: ({ initial, animate, exit, transition, style, children, ...rest }: any) =>
      <span {...rest} style={style}>{children}</span>,
  },
}))

jest.mock('@/utils/marketingMotion', () => ({
  CountUp: ({ target }: any) => <span>{target}</span>,
}))

jest.mock('@/utils/motionTokens', () => ({
  TIMING: { settle: 0.4 },
  EASE: { emphasis: [0.6, 0, 0.2, 1] },
}))

jest.mock('@/types/testingShared', () => ({
  TESTING_RISK_TIER_COLORS: {
    low: { text: 'text-sage-600', bg: 'bg-sage-50', border: 'border-sage-200' },
    elevated: { text: 'text-oatmeal-600', bg: 'bg-oatmeal-50', border: 'border-oatmeal-200' },
    moderate: { text: 'text-clay-500', bg: 'bg-clay-50', border: 'border-clay-200' },
    high: { text: 'text-clay-600', bg: 'bg-clay-50', border: 'border-clay-200' },
  },
  TESTING_RISK_TIER_LABELS: {
    low: 'Low Risk',
    elevated: 'Elevated',
    moderate: 'Moderate',
    high: 'High Risk',
  },
}))

const defaultProps = {
  score: 85,
  risk_tier: 'low' as const,
  tests_run: 19,
  total_entries: 5000,
  total_flagged: 25,
  flag_rate: 0.005,
  flags_by_severity: { high: 3, medium: 12, low: 10 },
  top_findings: ['Unusual weekend postings', 'Round amount entries'],
  entity_label: 'journal entries',
}

describe('TestingScoreCard', () => {
  it('renders score', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('/ 100')).toBeInTheDocument()
  })

  it('renders risk tier badge', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText('Low Risk')).toBeInTheDocument()
  })

  it('renders default title', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText('Composite Diagnostic Score')).toBeInTheDocument()
  })

  it('renders custom title', () => {
    render(<TestingScoreCard {...defaultProps} title="Custom Score Title" />)
    expect(screen.getByText('Custom Score Title')).toBeInTheDocument()
  })

  it('renders tests run and entity count', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText(/19 tests analyzed 5,000 journal entries/)).toBeInTheDocument()
  })

  it('renders flagged count', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText('25')).toBeInTheDocument()
    expect(screen.getByText('Flagged')).toBeInTheDocument()
  })

  it('renders flag rate', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText('0.5%')).toBeInTheDocument()
    expect(screen.getByText('Flag Rate')).toBeInTheDocument()
  })

  it('renders severity counts', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText('H / M / L')).toBeInTheDocument()
  })

  it('renders top findings', () => {
    render(<TestingScoreCard {...defaultProps} />)
    expect(screen.getByText('Top Findings')).toBeInTheDocument()
    expect(screen.getByText('Unusual weekend postings')).toBeInTheDocument()
    expect(screen.getByText('Round amount entries')).toBeInTheDocument()
  })

  it('does not render findings section when empty', () => {
    render(<TestingScoreCard {...defaultProps} top_findings={[]} />)
    expect(screen.queryByText('Top Findings')).not.toBeInTheDocument()
  })
})
