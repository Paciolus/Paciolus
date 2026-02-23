/**
 * Sprint 298: ExpenseCategorySection component tests
 *
 * Tests the expense category analytical procedures display section.
 * Covers: expand/collapse, summary stats, category bars, table rendering,
 * prior period columns, export buttons, edge cases.
 */
import React from 'react'
import { ExpenseCategorySection } from '@/components/trialBalance/ExpenseCategorySection'
import { render, screen, fireEvent } from '@/test-utils'
import type { ExpenseCategoryReport } from '@/types/expenseCategoryAnalytics'


const mockData: ExpenseCategoryReport = {
  categories: [
    {
      label: 'Cost of Goods Sold',
      key: 'cogs',
      amount: 120000,
      pct_of_revenue: 48.0,
      prior_amount: 110000,
      prior_pct_of_revenue: 44.0,
      dollar_change: 10000,
      exceeds_materiality: true,
      benchmark_pct: null,
    },
    {
      label: 'Payroll & Benefits',
      key: 'payroll',
      amount: 60000,
      pct_of_revenue: 24.0,
      prior_amount: 55000,
      prior_pct_of_revenue: 22.0,
      dollar_change: 5000,
      exceeds_materiality: false,
      benchmark_pct: null,
    },
    {
      label: 'Other Operating',
      key: 'other_operating',
      amount: 20000,
      pct_of_revenue: 8.0,
      prior_amount: null,
      prior_pct_of_revenue: null,
      dollar_change: null,
      exceeds_materiality: false,
      benchmark_pct: null,
    },
  ],
  total_expenses: 200000,
  total_revenue: 250000,
  revenue_available: true,
  prior_available: true,
  materiality_threshold: 7500,
  category_count: 3,
}

describe('ExpenseCategorySection', () => {
  it('renders collapsed header with badges', () => {
    render(<ExpenseCategorySection data={mockData} />)
    expect(screen.getByText('Expense Category Analysis')).toBeInTheDocument()
    expect(screen.getByText('3 categories')).toBeInTheDocument()
  })

  it('does not show expanded content by default', () => {
    render(<ExpenseCategorySection data={mockData} />)
    expect(screen.queryByText('Summary')).not.toBeInTheDocument()
  })

  it('expands to show summary stats on click', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText('Total Expenses:')).toBeInTheDocument()
    expect(screen.getByText('Total Revenue:')).toBeInTheDocument()
    expect(screen.getByText('Expense Ratio:')).toBeInTheDocument()
    expect(screen.getByText('Active Categories:')).toBeInTheDocument()
    expect(screen.getByText('Materiality:')).toBeInTheDocument()
  })

  it('shows expense ratio as percentage', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    // 200000/250000 * 100 = 80.00% — appears in summary and total row
    const matches = screen.getAllByText('80.00%')
    expect(matches.length).toBeGreaterThanOrEqual(1)
  })

  it('shows N/A for expense ratio when revenue not available', () => {
    const noRev = { ...mockData, revenue_available: false }
    render(<ExpenseCategorySection data={noRev} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    const naElements = screen.getAllByText('N/A')
    expect(naElements.length).toBeGreaterThan(0)
  })

  it('renders category distribution bars', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText('Category Distribution')).toBeInTheDocument()
    // Category labels appear in both bars and table — use getAllByText
    const cogsLabels = screen.getAllByText('Cost of Goods Sold')
    expect(cogsLabels.length).toBeGreaterThanOrEqual(1)
    const payrollLabels = screen.getAllByText('Payroll & Benefits')
    expect(payrollLabels.length).toBeGreaterThanOrEqual(1)
  })

  it('renders detailed breakdown table', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText('Category Breakdown')).toBeInTheDocument()
    expect(screen.getByText('% of Revenue')).toBeInTheDocument()
  })

  it('shows prior period columns when prior data available', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText('Prior Amount')).toBeInTheDocument()
    expect(screen.getByText('$ Change')).toBeInTheDocument()
    expect(screen.getByText('Exceeds Mat.')).toBeInTheDocument()
  })

  it('hides prior period columns when no prior data', () => {
    const noPrior: ExpenseCategoryReport = {
      ...mockData,
      prior_available: false,
      categories: mockData.categories.map(c => ({
        ...c,
        prior_amount: null,
        prior_pct_of_revenue: null,
        dollar_change: null,
      })),
    }
    render(<ExpenseCategorySection data={noPrior} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.queryByText('Prior Amount')).not.toBeInTheDocument()
    expect(screen.queryByText('$ Change')).not.toBeInTheDocument()
  })

  it('shows exceeds materiality as Yes/No text', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    // COGS exceeds materiality (Yes), Payroll does not (No)
    expect(screen.getByText('Yes')).toBeInTheDocument()
  })

  it('shows total row in breakdown table', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText('Total')).toBeInTheDocument()
  })

  it('calls onExportPDF when button clicked', () => {
    const onExportPDF = jest.fn()
    render(<ExpenseCategorySection data={mockData} onExportPDF={onExportPDF} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    fireEvent.click(screen.getByText('Export PDF'))
    expect(onExportPDF).toHaveBeenCalledTimes(1)
  })

  it('calls onExportCSV when button clicked', () => {
    const onExportCSV = jest.fn()
    render(<ExpenseCategorySection data={mockData} onExportCSV={onExportCSV} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    fireEvent.click(screen.getByText('Export CSV'))
    expect(onExportCSV).toHaveBeenCalledTimes(1)
  })

  it('hides export buttons when no handlers provided', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.queryByText('Export PDF')).not.toBeInTheDocument()
    expect(screen.queryByText('Export CSV')).not.toBeInTheDocument()
  })

  it('shows prior data availability in summary', () => {
    render(<ExpenseCategorySection data={mockData} />)
    fireEvent.click(screen.getByText('Expense Category Analysis'))
    expect(screen.getByText('Prior Data:')).toBeInTheDocument()
    expect(screen.getByText('Available')).toBeInTheDocument()
  })
})
