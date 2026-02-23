/**
 * KeyMetricsSection Component Tests
 * Sprint 55: Frontend Test Foundation
 *
 * Tests for the KeyMetricsSection component that displays financial ratios dashboard.
 */

import { KeyMetricsSection } from '@/components/analytics/KeyMetricsSection'
import { sampleAnalytics, sampleAnalyticsNoVariance } from '@/test-utils/fixtures'
import { render, screen } from '@/test-utils'

describe('KeyMetricsSection', () => {
  describe('rendering', () => {
    it('renders the section header', () => {
      render(<KeyMetricsSection analytics={sampleAnalytics} />)
      expect(screen.getByText('Key Metrics')).toBeInTheDocument()
    })

    it('renders the subtitle with ratio count', () => {
      render(<KeyMetricsSection analytics={sampleAnalytics} />)
      expect(screen.getByText('9 financial ratios')).toBeInTheDocument()
    })

    it('renders core ratios', () => {
      render(<KeyMetricsSection analytics={sampleAnalytics} />)
      expect(screen.getByText('Current Ratio')).toBeInTheDocument()
      expect(screen.getByText('Quick Ratio')).toBeInTheDocument()
      expect(screen.getByText('Debt to Equity')).toBeInTheDocument()
      expect(screen.getByText('Gross Margin')).toBeInTheDocument()
    })

    it('renders category totals summary', () => {
      render(<KeyMetricsSection analytics={sampleAnalytics} />)
      expect(screen.getByText(/Assets:/)).toBeInTheDocument()
      expect(screen.getByText(/Liabilities:/)).toBeInTheDocument()
      expect(screen.getByText(/Equity:/)).toBeInTheDocument()
    })
  })

  describe('variance badge', () => {
    it('shows variance active badge when previous data exists', () => {
      render(<KeyMetricsSection analytics={sampleAnalytics} />)
      expect(screen.getByText('Variance Active')).toBeInTheDocument()
    })

    it('does not show variance badge when no previous data', () => {
      render(<KeyMetricsSection analytics={sampleAnalyticsNoVariance} />)
      expect(screen.queryByText('Variance Active')).not.toBeInTheDocument()
    })
  })

  describe('disabled state', () => {
    it('applies disabled styling when disabled', () => {
      const { container } = render(
        <KeyMetricsSection analytics={sampleAnalytics} disabled />
      )
      expect(container.firstChild).toHaveClass('opacity-50')
      expect(container.firstChild).toHaveClass('pointer-events-none')
    })
  })

  describe('empty state', () => {
    it('shows empty state when no ratios are calculable', () => {
      const emptyAnalytics = {
        ...sampleAnalytics,
        ratios: {
          current_ratio: {
            ...sampleAnalytics.ratios.current_ratio,
            is_calculable: false,
          },
          quick_ratio: {
            ...sampleAnalytics.ratios.quick_ratio,
            is_calculable: false,
          },
          debt_to_equity: {
            ...sampleAnalytics.ratios.debt_to_equity,
            is_calculable: false,
          },
          gross_margin: {
            ...sampleAnalytics.ratios.gross_margin,
            is_calculable: false,
          },
        },
      }
      render(<KeyMetricsSection analytics={emptyAnalytics} />)
      expect(screen.getByText('Limited Account Classification')).toBeInTheDocument()
    })
  })
})
