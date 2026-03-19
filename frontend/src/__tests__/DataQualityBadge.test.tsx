/**
 * DataQualityBadge component tests
 *
 * Tests: rendering score, quality label, field fill rates,
 * detected issues, row count, entity label.
 */
import { DataQualityBadge } from '@/components/shared/testing/DataQualityBadge'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, style, children, ...rest }: any) =>
      <div {...rest} style={style}>{children}</div>,
  },
}))

jest.mock('@/utils/marketingMotion', () => ({
  CountUp: ({ target, suffix }: any) => <span>{target}{suffix || ''}</span>,
}))

describe('DataQualityBadge', () => {
  const defaultProps = {
    completeness_score: 92,
    field_fill_rates: { amount: 0.98, date: 0.95, description: 0.85 },
    detected_issues: [],
    total_rows: 1500,
    entity_label: 'journal entries',
  }

  it('renders Data Quality heading', () => {
    render(<DataQualityBadge {...defaultProps} />)
    expect(screen.getByText('Data Quality')).toBeInTheDocument()
  })

  it('renders completeness score', () => {
    render(<DataQualityBadge {...defaultProps} />)
    expect(screen.getByText('92%')).toBeInTheDocument()
  })

  it('renders Excellent quality label for 90+ score', () => {
    render(<DataQualityBadge {...defaultProps} />)
    expect(screen.getByText('Excellent')).toBeInTheDocument()
  })

  it('renders Good quality label for 70+ score', () => {
    render(<DataQualityBadge {...defaultProps} completeness_score={75} />)
    expect(screen.getByText('Good')).toBeInTheDocument()
  })

  it('renders Fair quality label for 50+ score', () => {
    render(<DataQualityBadge {...defaultProps} completeness_score={55} />)
    expect(screen.getByText('Fair')).toBeInTheDocument()
  })

  it('renders field fill rates', () => {
    render(<DataQualityBadge {...defaultProps} />)
    expect(screen.getByText('amount')).toBeInTheDocument()
    expect(screen.getByText('98%')).toBeInTheDocument()
  })

  it('renders total rows count', () => {
    render(<DataQualityBadge {...defaultProps} />)
    expect(screen.getByText(/1,500 journal entries analyzed/)).toBeInTheDocument()
  })

  it('renders detected issues when present', () => {
    render(<DataQualityBadge {...defaultProps} detected_issues={['Missing amounts', 'Duplicate entries']} />)
    expect(screen.getByText('Missing amounts')).toBeInTheDocument()
    expect(screen.getByText('Duplicate entries')).toBeInTheDocument()
  })

  it('does not render issues section when no issues', () => {
    const { container } = render(<DataQualityBadge {...defaultProps} detected_issues={[]} />)
    expect(container.querySelector('.border-t.border-theme-divider')).toBeNull()
  })

  it('renders header subtitle when provided', () => {
    render(<DataQualityBadge {...defaultProps} header_subtitle="Based on uploaded data" />)
    expect(screen.getByText('Based on uploaded data')).toBeInTheDocument()
  })
})
