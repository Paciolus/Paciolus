/**
 * Sprint 298: PopulationProfileSection component tests
 *
 * Tests the TB population profile display section.
 * Covers: expand/collapse, Gini badge, descriptive stats, magnitude bars,
 * top-10 table, section density table, sparse flagging, export buttons.
 */
import React from 'react'
import { PopulationProfileSection } from '@/components/trialBalance/PopulationProfileSection'
import { render, screen, fireEvent } from '@/test-utils'
import type { PopulationProfile } from '@/types/populationProfile'


const mockData: PopulationProfile = {
  account_count: 50,
  total_abs_balance: 1000000,
  mean_abs_balance: 20000,
  median_abs_balance: 12000,
  std_dev_abs_balance: 35000,
  min_abs_balance: 100,
  max_abs_balance: 250000,
  p25: 5000,
  p75: 30000,
  gini_coefficient: 0.65,
  gini_interpretation: 'High',
  buckets: [
    { label: '0 – 1K', lower: 0, upper: 1000, count: 10, sum_abs: 5000, percent_count: 20 },
    { label: '1K – 10K', lower: 1000, upper: 10000, count: 15, sum_abs: 75000, percent_count: 30 },
    { label: '10K – 100K', lower: 10000, upper: 100000, count: 20, sum_abs: 600000, percent_count: 40 },
    { label: '100K+', lower: 100000, upper: null, count: 5, sum_abs: 320000, percent_count: 10 },
  ],
  top_accounts: [
    { rank: 1, account: 'Cash', category: 'Asset', net_balance: 250000, abs_balance: 250000, percent_of_total: 25.0 },
    { rank: 2, account: 'Revenue', category: 'Revenue', net_balance: -180000, abs_balance: 180000, percent_of_total: 18.0 },
  ],
  section_density: [
    { section_label: 'Current Assets', section_letters: ['A', 'B'], account_count: 12, section_balance: 300000, balance_per_account: 25000, is_sparse: false },
    { section_label: 'Fixed Assets', section_letters: ['C'], account_count: 2, section_balance: 500000, balance_per_account: 250000, is_sparse: true },
    { section_label: 'Current Liabilities', section_letters: ['G', 'H'], account_count: 8, section_balance: 150000, balance_per_account: 18750, is_sparse: false },
  ],
}

describe('PopulationProfileSection', () => {
  it('renders collapsed header with account count badge', () => {
    render(<PopulationProfileSection data={mockData} />)
    expect(screen.getByText('TB Population Profile')).toBeInTheDocument()
    expect(screen.getByText('50 accounts')).toBeInTheDocument()
  })

  it('renders Gini badge with interpretation', () => {
    render(<PopulationProfileSection data={mockData} />)
    expect(screen.getByText('Gini: 0.65 (High)')).toBeInTheDocument()
  })

  it('does not show expanded content by default', () => {
    render(<PopulationProfileSection data={mockData} />)
    expect(screen.queryByText('Descriptive Statistics')).not.toBeInTheDocument()
  })

  it('expands to show descriptive statistics on click', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText('Descriptive Statistics')).toBeInTheDocument()
    expect(screen.getByText('Mean:')).toBeInTheDocument()
    expect(screen.getByText('Median:')).toBeInTheDocument()
    expect(screen.getByText('Std Dev:')).toBeInTheDocument()
    expect(screen.getByText('Min:')).toBeInTheDocument()
    expect(screen.getByText('Max:')).toBeInTheDocument()
    expect(screen.getByText('Total:')).toBeInTheDocument()
    expect(screen.getByText('P25:')).toBeInTheDocument()
    expect(screen.getByText('P75:')).toBeInTheDocument()
    expect(screen.getByText('IQR:')).toBeInTheDocument()
  })

  it('renders magnitude distribution bars', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText('Magnitude Distribution')).toBeInTheDocument()
    expect(screen.getByText('0 – 1K')).toBeInTheDocument()
    expect(screen.getByText('1K – 10K')).toBeInTheDocument()
    expect(screen.getByText('10K – 100K')).toBeInTheDocument()
    expect(screen.getByText('100K+')).toBeInTheDocument()
  })

  it('shows Gini callout with detailed coefficient', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText('0.6500')).toBeInTheDocument()
    expect(screen.getByText('High Concentration')).toBeInTheDocument()
  })

  it('shows Gini informational text', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText(/Gini of 0 means all accounts have equal balances/)).toBeInTheDocument()
  })

  it('renders top accounts table', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText('Top 2 Accounts by Absolute Balance')).toBeInTheDocument()
    expect(screen.getByText('Cash')).toBeInTheDocument()
    // "Revenue" appears as both account name and category — use getAllByText
    const revenueElements = screen.getAllByText('Revenue')
    expect(revenueElements.length).toBe(2)
    expect(screen.getByText('25.0%')).toBeInTheDocument()
  })

  it('renders section density table', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText('Account Density by Section')).toBeInTheDocument()
    expect(screen.getByText('Current Assets')).toBeInTheDocument()
    expect(screen.getByText('Fixed Assets')).toBeInTheDocument()
    expect(screen.getByText('Current Liabilities')).toBeInTheDocument()
  })

  it('shows sparse badge count in density header', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText('1 sparse')).toBeInTheDocument()
  })

  it('shows section letters in density table', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.getByText('A, B')).toBeInTheDocument()
    expect(screen.getByText('C')).toBeInTheDocument()
    expect(screen.getByText('G, H')).toBeInTheDocument()
  })

  it('hides density table when section_density is undefined', () => {
    const noSections = { ...mockData, section_density: undefined }
    render(<PopulationProfileSection data={noSections} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.queryByText('Account Density by Section')).not.toBeInTheDocument()
  })

  it('calls onExportPDF when button clicked', () => {
    const onExportPDF = jest.fn()
    render(<PopulationProfileSection data={mockData} onExportPDF={onExportPDF} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    fireEvent.click(screen.getByText('Export PDF'))
    expect(onExportPDF).toHaveBeenCalledTimes(1)
  })

  it('calls onExportCSV when button clicked', () => {
    const onExportCSV = jest.fn()
    render(<PopulationProfileSection data={mockData} onExportCSV={onExportCSV} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    fireEvent.click(screen.getByText('Export CSV'))
    expect(onExportCSV).toHaveBeenCalledTimes(1)
  })

  it('hides export buttons when no handlers provided', () => {
    render(<PopulationProfileSection data={mockData} />)
    fireEvent.click(screen.getByText('TB Population Profile'))
    expect(screen.queryByText('Export PDF')).not.toBeInTheDocument()
    expect(screen.queryByText('Export CSV')).not.toBeInTheDocument()
  })

  it('uses correct Gini color for Low interpretation', () => {
    const lowGini = { ...mockData, gini_coefficient: 0.2, gini_interpretation: 'Low' as const }
    render(<PopulationProfileSection data={lowGini} />)
    expect(screen.getByText('Gini: 0.20 (Low)')).toBeInTheDocument()
  })
})
