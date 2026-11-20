/**
 * Sprint 887 (review comparison table): the screen shows the expense change band the CSV and PDF show.
 *
 * The PDF computed its own % changes and HIGH/MODERATE/LOW labels from 10% / 20%
 * thresholds that the screen never showed. The engine now sends `pct_change`,
 * `change_band` and `change_thresholds`; the screen shows them and the thresholds.
 */
import React from 'react'
import { ExpenseCategorySection } from '@/components/trialBalance/ExpenseCategorySection'
import type { ExpenseCategoryReport } from '@/types/expenseCategoryAnalytics'
import { render, screen, fireEvent } from '@/test-utils'

const data: ExpenseCategoryReport = {
  categories: [
    {
      label: 'Cost of Goods Sold',
      key: 'cogs',
      amount: 300000,
      pct_of_revenue: 30,
      prior_amount: 240000,
      prior_pct_of_revenue: 26.7,
      dollar_change: 60000,
      exceeds_threshold: true,
      benchmark_pct: null,
      pct_change: 25,
      change_band: 'both',
    },
    {
      label: 'Payroll & Benefits',
      key: 'payroll',
      amount: 150000,
      pct_of_revenue: 15,
      prior_amount: null,
      prior_pct_of_revenue: null,
      dollar_change: null,
      exceeds_threshold: false,
      benchmark_pct: null,
      pct_change: null,
      change_band: null,
    },
  ],
  total_expenses: 450000,
  total_revenue: 1000000,
  revenue_available: true,
  prior_available: true,
  materiality_threshold: 10000,
  category_count: 2,
  change_thresholds: { pct_both: 20, pct_either: 10, materiality: 10000 },
}

describe('ExpenseCategorySection change band (Sprint 887)', () => {
  it('shows the engine % change and change band', () => {
    render(<ExpenseCategorySection data={data} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText('% Change')).toBeInTheDocument()
    expect(screen.getByText('Change Band')).toBeInTheDocument()
    expect(screen.getByText('+25.00%')).toBeInTheDocument()
    expect(screen.getByText('Change ≥ 20% and over materiality')).toBeInTheDocument()
  })

  it('prints the thresholds behind the bands', () => {
    render(<ExpenseCategorySection data={data} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText(/10% and 20% change \(Paciolus defaults\)/)).toBeInTheDocument()
  })

  it('shows no risk wording', () => {
    render(<ExpenseCategorySection data={data} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.queryByText(/Risk Level|Explanation Req/)).not.toBeInTheDocument()
  })
})
