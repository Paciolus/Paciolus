/**
 * InsightMicrocopy Component Tests — Sprint 408: Phase LVII
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import { InsightMicrocopy } from '@/components/workspace/InsightMicrocopy'

// Mock framer-motion
jest.mock('framer-motion', () => {
  const React = require('react')
  return {
    motion: {
      div: React.forwardRef(({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, ...rest }: any, ref: any) => (
        <div ref={ref} {...rest} />
      )),
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
  }
})

// Mock feature flag — enabled by default
let mockFlagEnabled = true
jest.mock('@/lib/featureFlags', () => ({
  isFeatureEnabled: (flag: string) => flag === 'INSIGHT_MICROCOPY' ? mockFlagEnabled : false,
}))

jest.mock('@/utils/motionTokens', () => ({
  TIMING: { settle: 0.5 },
  EASE: { emphasis: [0.2, 0, 0, 1] },
  EMPHASIS_SETTLE: {
    initial: { opacity: 0, x: -2 },
    animate: { opacity: 1, x: 0 },
  },
}))


const baseProps = {
  riskSignals: [],
  followUpSummary: null,
  toolRunTrends: [],
  toolsCovered: 0,
  totalTools: 12,
  proofReadiness: { toolsWithEvidence: 12, totalTools: 12, percentage: 100, level: 'strong' as const },
  isLoading: false,
}

describe('InsightMicrocopy', () => {
  beforeEach(() => {
    mockFlagEnabled = true
  })

  it('renders nothing when flag is off', () => {
    mockFlagEnabled = false
    const { container } = render(<InsightMicrocopy {...baseProps} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when loading', () => {
    const { container } = render(<InsightMicrocopy {...baseProps} isLoading={true} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing when no messages derived', () => {
    // Full coverage + strong = no messages (toolsCovered 0 != totalTools)
    // Actually: toolsCovered=0, totalTools=12 — but proofReadiness level is strong,
    // so no low-evidence message. No signals, no follow-ups, no trends.
    // uncovered=12 but toolsCovered=0 fails the `toolsCovered > 0` check.
    const { container } = render(<InsightMicrocopy {...baseProps} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders section header and message cards', () => {
    render(
      <InsightMicrocopy
        {...baseProps}
        riskSignals={[{ level: 'high', label: 'Test', detail: 'Detail' }]}
      />
    )
    expect(screen.getByText('Intelligence Briefing')).toBeInTheDocument()
    expect(screen.getByText(/surfaced/)).toBeInTheDocument()
  })

  it('renders correct number of cards', () => {
    render(
      <InsightMicrocopy
        {...baseProps}
        riskSignals={[{ level: 'high', label: 'A', detail: '' }]}
        followUpSummary={{
          total_count: 5,
          by_disposition: { not_reviewed: 3 },
          by_severity: { high: 1 },
        } as any}
      />
    )
    // Should have 2 attention messages: clusters + follow-ups
    const cards = screen.getAllByText(/surfaced|follow-up/)
    expect(cards.length).toBe(2)
  })
})
