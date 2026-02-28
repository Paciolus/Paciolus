/**
 * MetricCard Component Tests
 * Sprint 55: Frontend Test Foundation
 *
 * Tests for the MetricCard component that displays financial ratios.
 */

import { MetricCard } from '@/components/analytics/MetricCard'
import { sampleRatios, warningRatio, concernRatio, uncalculableRatio } from '@/test-utils/fixtures'
import { render, screen } from '@/test-utils'

describe('MetricCard', () => {
  const defaultProps = {
    name: sampleRatios.current_ratio.name,
    value: sampleRatios.current_ratio.display_value,
    interpretation: sampleRatios.current_ratio.interpretation,
    healthStatus: sampleRatios.current_ratio.threshold_status,
    index: 0,
    isCalculable: true,
  }

  describe('rendering', () => {
    it('renders the metric name', () => {
      render(<MetricCard {...defaultProps} />)
      expect(screen.getByText('Current Ratio')).toBeInTheDocument()
    })

    it('renders the metric value', () => {
      render(<MetricCard {...defaultProps} />)
      expect(screen.getByText('2.50')).toBeInTheDocument()
    })

    it('renders the interpretation', () => {
      render(<MetricCard {...defaultProps} />)
      expect(screen.getByText('Healthy liquidity position')).toBeInTheDocument()
    })

    it('renders threshold status label for above_threshold status', () => {
      render(<MetricCard {...defaultProps} />)
      expect(screen.getByText('Above')).toBeInTheDocument()
    })

    it('renders threshold status label for at_threshold status', () => {
      render(
        <MetricCard
          {...defaultProps}
          healthStatus={warningRatio.threshold_status}
          interpretation={warningRatio.interpretation}
        />
      )
      expect(screen.getByText('Near')).toBeInTheDocument()
    })

    it('renders threshold status label for below_threshold status', () => {
      render(
        <MetricCard
          {...defaultProps}
          name={concernRatio.name}
          value={concernRatio.display_value}
          healthStatus={concernRatio.threshold_status}
          interpretation={concernRatio.interpretation}
        />
      )
      expect(screen.getByText('Below')).toBeInTheDocument()
    })
  })

  describe('uncalculable state', () => {
    it('shows N/A for uncalculable ratios', () => {
      render(
        <MetricCard
          {...defaultProps}
          name={uncalculableRatio.name}
          value={uncalculableRatio.display_value}
          healthStatus={uncalculableRatio.threshold_status}
          interpretation={uncalculableRatio.interpretation}
          isCalculable={false}
        />
      )
      expect(screen.getByText('N/A')).toBeInTheDocument()
    })
  })

  describe('variance display', () => {
    it('renders variance when provided', () => {
      render(
        <MetricCard
          {...defaultProps}
          variance={{
            direction: 'positive',
            displayText: '+11.1%',
            changePercent: 11.1,
          }}
        />
      )
      expect(screen.getByText('+11.1%')).toBeInTheDocument()
    })

    it('does not render variance when not provided', () => {
      render(<MetricCard {...defaultProps} />)
      expect(screen.queryByText(/%$/)).not.toBeInTheDocument()
    })
  })

  describe('compact mode', () => {
    it('renders in compact mode when specified', () => {
      const { container } = render(<MetricCard {...defaultProps} compact />)
      // Compact mode should still render the card
      expect(screen.getByText('Current Ratio')).toBeInTheDocument()
      // The container should exist
      expect(container.firstChild).toBeInTheDocument()
    })
  })
})
