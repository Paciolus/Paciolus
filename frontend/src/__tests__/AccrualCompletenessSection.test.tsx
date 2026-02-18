/**
 * Sprint 298: AccrualCompletenessSection component tests
 *
 * Tests the accrual completeness estimator display section.
 * Covers: expand/collapse, metrics display, accrual accounts table,
 * narrative, export buttons, edge cases.
 */
import React from 'react'
import { render, screen, fireEvent } from '@/test-utils'
import type { AccrualCompletenessReport } from '@/types/accrualCompleteness'

import { AccrualCompletenessSection } from '@/components/trialBalance/AccrualCompletenessSection'

const mockData: AccrualCompletenessReport = {
  accrual_accounts: [
    { account_name: 'Accrued Salaries', balance: 25000, matched_keyword: 'accrued' },
    { account_name: 'Accrued Interest', balance: 5000, matched_keyword: 'accrued' },
  ],
  total_accrued_balance: 30000,
  accrual_account_count: 2,
  monthly_run_rate: 15000,
  accrual_to_run_rate_pct: 200.0,
  threshold_pct: 50,
  below_threshold: false,
  prior_operating_expenses: 180000,
  prior_available: true,
  narrative: 'Total accrued balance is 200.0% of the monthly run-rate (above the 50% threshold).',
}

describe('AccrualCompletenessSection', () => {
  it('renders collapsed header with account count badge', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    expect(screen.getByText('Accrual Completeness Estimator')).toBeInTheDocument()
    expect(screen.getByText('2 accounts')).toBeInTheDocument()
  })

  it('shows ratio badge when prior data is available', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    expect(screen.getByText('Ratio: 200.0%')).toBeInTheDocument()
  })

  it('hides ratio badge when prior data is not available', () => {
    const noPrior = { ...mockData, prior_available: false }
    render(<AccrualCompletenessSection data={noPrior} />)
    expect(screen.queryByText(/Ratio:/)).not.toBeInTheDocument()
  })

  it('does not show expanded content by default', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    expect(screen.queryByText('Total Accrued:')).not.toBeInTheDocument()
  })

  it('expands to show metrics on click', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.getByText('Total Accrued:')).toBeInTheDocument()
    expect(screen.getByText('Monthly Run-Rate:')).toBeInTheDocument()
    expect(screen.getByText('Threshold:')).toBeInTheDocument()
  })

  it('shows below threshold status', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.getByText('Below Threshold:')).toBeInTheDocument()
    expect(screen.getByText('No')).toBeInTheDocument()
  })

  it('shows prior data availability', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.getByText('Prior Data:')).toBeInTheDocument()
    expect(screen.getByText('Available')).toBeInTheDocument()
  })

  it('renders narrative text when provided', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.getByText(/Total accrued balance is 200.0%/)).toBeInTheDocument()
  })

  it('renders accrual accounts table', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.getByText('Accrued Salaries')).toBeInTheDocument()
    expect(screen.getByText('Accrued Interest')).toBeInTheDocument()
    expect(screen.getByText('Keyword')).toBeInTheDocument()
  })

  it('shows singular "account" for count of 1', () => {
    const single = { ...mockData, accrual_account_count: 1 }
    render(<AccrualCompletenessSection data={single} />)
    expect(screen.getByText('1 account')).toBeInTheDocument()
  })

  it('calls onExportPDF when button clicked', () => {
    const onExportPDF = jest.fn()
    render(<AccrualCompletenessSection data={mockData} onExportPDF={onExportPDF} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    fireEvent.click(screen.getByText('Export PDF'))
    expect(onExportPDF).toHaveBeenCalledTimes(1)
  })

  it('calls onExportCSV when button clicked', () => {
    const onExportCSV = jest.fn()
    render(<AccrualCompletenessSection data={mockData} onExportCSV={onExportCSV} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    fireEvent.click(screen.getByText('Export CSV'))
    expect(onExportCSV).toHaveBeenCalledTimes(1)
  })

  it('hides export buttons when no handlers provided', () => {
    render(<AccrualCompletenessSection data={mockData} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.queryByText('Export PDF')).not.toBeInTheDocument()
    expect(screen.queryByText('Export CSV')).not.toBeInTheDocument()
  })

  it('handles null monthly_run_rate gracefully', () => {
    const noRate = { ...mockData, monthly_run_rate: null, accrual_to_run_rate_pct: null }
    render(<AccrualCompletenessSection data={noRate} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.queryByText('Monthly Run-Rate:')).not.toBeInTheDocument()
    expect(screen.queryByText('Ratio:')).not.toBeInTheDocument()
  })

  it('shows "Not provided" when prior is not available', () => {
    const noPrior = { ...mockData, prior_available: false }
    render(<AccrualCompletenessSection data={noPrior} />)
    fireEvent.click(screen.getByText('Accrual Completeness Estimator'))
    expect(screen.getByText('Not provided')).toBeInTheDocument()
  })
})
