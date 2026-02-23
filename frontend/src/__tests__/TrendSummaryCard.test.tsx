/**
 * TrendSummaryCard component tests — Sprint 277
 *
 * Tests: metric name, current value, direction badge icon,
 * Min/Avg/Max statistics, periods count, compact mode.
 */
import { TrendSummaryCard } from '@/components/analytics/TrendSummaryCard'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => {
  const R = require('react')
  return {
    motion: new Proxy(
      {},
      {
        get: (_: unknown, tag: string) =>
          R.forwardRef(
            (
              {
                initial,
                animate,
                exit,
                transition,
                variants,
                whileHover,
                whileInView,
                whileTap,
                viewport,
                layout,
                layoutId,
                ...rest
              }: any,
              ref: any,
            ) => R.createElement(tag, { ...rest, ref }),
          ),
      },
    ),
    AnimatePresence: ({ children }: any) => children,
  }
})

jest.mock('@/components/analytics/TrendSparkline', () => ({
  TrendSparkline: () => <div data-testid="sparkline" />,
  TrendSparklineMini: () => <div data-testid="sparkline-mini" />,
}))

jest.mock('@/utils', () => ({
  createCardStaggerVariants: jest.fn(() => ({ hidden: {}, visible: {} })),
}))


const defaultProps = {
  name: 'Current Ratio',
  currentValue: '2.50',
  trendData: [
    { period: '2024-Q1', value: 2.1 },
    { period: '2024-Q2', value: 2.3 },
    { period: '2024-Q3', value: 2.5 },
  ],
  direction: 'positive' as const,
  totalChange: 0.4,
  totalChangePercent: 19.0,
  periodsAnalyzed: 3,
  minValue: 2.1,
  maxValue: 2.5,
  averageValue: 2.3,
}

describe('TrendSummaryCard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the metric name', () => {
    render(<TrendSummaryCard {...defaultProps} />)
    expect(screen.getByText('Current Ratio')).toBeInTheDocument()
  })

  it('renders the current value', () => {
    render(<TrendSummaryCard {...defaultProps} />)
    expect(screen.getByText('2.50')).toBeInTheDocument()
  })

  it('renders direction badge with upward arrow for positive direction', () => {
    render(<TrendSummaryCard {...defaultProps} direction="positive" />)
    expect(screen.getByText('\u2191')).toBeInTheDocument()
  })

  it('renders direction badge with downward arrow for negative direction', () => {
    render(<TrendSummaryCard {...defaultProps} direction="negative" />)
    expect(screen.getByText('\u2193')).toBeInTheDocument()
  })

  it('renders direction badge with horizontal arrow for neutral direction', () => {
    render(<TrendSummaryCard {...defaultProps} direction="neutral" />)
    expect(screen.getByText('\u2192')).toBeInTheDocument()
  })

  it('renders Min, Avg, and Max statistics', () => {
    render(<TrendSummaryCard {...defaultProps} />)
    expect(screen.getByText('Min')).toBeInTheDocument()
    expect(screen.getByText('Avg')).toBeInTheDocument()
    expect(screen.getByText('Max')).toBeInTheDocument()
    // Values are formatted via formatValue: 2.1 -> "2.1", 2.3 -> "2.3", 2.5 -> "2.5"
    expect(screen.getByText('2.1')).toBeInTheDocument()
    expect(screen.getByText('2.3')).toBeInTheDocument()
    expect(screen.getByText('2.5')).toBeInTheDocument()
  })

  it('renders the periods analyzed count', () => {
    render(<TrendSummaryCard {...defaultProps} />)
    expect(screen.getByText('3 periods')).toBeInTheDocument()
  })

  it('hides Min/Avg/Max stats in compact mode', () => {
    render(<TrendSummaryCard {...defaultProps} compact={true} />)
    expect(screen.queryByText('Min')).not.toBeInTheDocument()
    expect(screen.queryByText('Avg')).not.toBeInTheDocument()
    expect(screen.queryByText('Max')).not.toBeInTheDocument()
  })
})
