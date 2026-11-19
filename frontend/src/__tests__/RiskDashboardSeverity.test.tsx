/**
 * Sprint 886 (review comparison table): the trial balance screen shows the three
 * severity counts separately — low was added into "Medium" — as the PDF now does.
 */
import { RiskDashboard } from '@/components/risk/RiskDashboard'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: { div: ({ initial, animate, exit, transition, variants, layout, children, ...rest }: any) => <div {...rest}>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}))
jest.mock('@/components/risk/AnomalyCard', () => ({ AnomalyCard: () => <div /> }))

it('shows High 3, Medium 2 and Low 1 as three counts', () => {
  render(
    <RiskDashboard
      anomalies={[{ account: 'Cash', materiality: 'material', severity: 'high' } as never]}
      riskSummary={{ total_anomalies: 6, high_severity: 3, medium_severity: 2, low_severity: 1, informational_count: 0 } as never}
      materialityThreshold={500}
      getMappingForAccount={() => ({ currentType: 'asset' as never, isManual: false })}
      onTypeChange={jest.fn()}
    />,
  )
  for (const [label, count] of [['High', '3'], ['Medium', '2'], ['Low', '1']]) {
    expect(screen.getByText(label).previousSibling).toHaveTextContent(count)
  }
})
