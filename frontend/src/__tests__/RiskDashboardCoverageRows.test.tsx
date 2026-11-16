/**
 * Sprint 873: materiality coverage rows are not risks.
 *
 * `audit/rules/concentration.py` emits "Represents 42.0% of total revenues —
 * coverage observation, not an anomaly" rows with `coverage_analysis: true`
 * and leaves them out of the risk score, but they carry a severity and a
 * materiality, so the dashboard listed them under "Material Risks".
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { RiskDashboard } from '@/components/risk/RiskDashboard'
import type { AbnormalBalanceExtended } from '@/types/mapping'

jest.mock('framer-motion', () => {
  const React = require('react')
  const strip = (props: Record<string, unknown>) =>
    Object.fromEntries(
      Object.entries(props).filter(
        ([k]) => !['initial', 'animate', 'exit', 'transition', 'variants', 'layout', 'whileHover', 'whileTap'].includes(k),
      ),
    )
  return {
    motion: new Proxy({}, { get: (_t, tag: string) => ({ children, ...rest }: any) => React.createElement(tag, strip(rest), children) }),
    AnimatePresence: ({ children }: any) => React.createElement(React.Fragment, null, children),
  }
})

jest.mock('@/components/risk/AnomalyCard', () => ({
  AnomalyCard: ({ anomaly }: { anomaly: AbnormalBalanceExtended }) => <div data-testid="anomaly">{anomaly.account}</div>,
}))

const base = { type: 'Revenue', amount: 420000, debit: 0, credit: 420000, materiality: 'material' as const }
const anomalies: AbnormalBalanceExtended[] = [
  { ...base, account: 'Suspense Clearing', issue: 'Abnormal balance', severity: 'high' },
  {
    ...base,
    account: 'Product Sales',
    issue: 'Represents 42.0% of total revenues — coverage observation, not an anomaly',
    severity: 'medium',
    coverage_analysis: true,
  },
]

const props = {
  anomalies,
  materialityThreshold: 10000,
  getMappingForAccount: () => ({ currentType: 'revenue' as const, isManual: false }),
  onTypeChange: jest.fn(),
}

describe('RiskDashboard coverage rows', () => {
  it('does not count a coverage observation as a material risk', () => {
    render(<RiskDashboard {...props} displayMode="strict" />)
    expect(screen.getByText('Material Risks (1)')).toBeInTheDocument()
    expect(screen.getAllByTestId('anomaly').map(el => el.textContent)).toEqual(['Suspense Clearing'])
  })

  it('lists it under informational notes instead', () => {
    render(<RiskDashboard {...props} displayMode="all" />)
    fireEvent.click(screen.getByText(/Informational Notes \(1\)/))
    expect(screen.getByText('Product Sales')).toBeInTheDocument()
  })
})
