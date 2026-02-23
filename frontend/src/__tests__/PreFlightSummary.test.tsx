/**
 * Sprint 283: PreFlightSummary component tests
 *
 * Tests the pre-flight data quality summary display.
 * Covers: readiness score, issues list, column detection, remediation, proceed button.
 */
import React from 'react'
import { PreFlightSummary } from '@/components/preflight/PreFlightSummary'
import type { PreFlightReport } from '@/types/preflight'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => {
  const R = require('react')
  return {
    motion: new Proxy(
      {},
      {
        get: (_: unknown, tag: string) =>
          R.forwardRef(
            (
              {
                initial,
                animate,
                exit,
                transition,
                variants,
                whileHover,
                whileInView,
                whileTap,
                viewport,
                layout,
                layoutId,
                ...rest
              }: any,
              ref: any
            ) => R.createElement(tag, { ...rest, ref })
          ),
      }
    ),
    AnimatePresence: ({ children }: any) => children,
  }
})


const mockReport: PreFlightReport = {
  filename: 'test_tb.csv',
  row_count: 150,
  column_count: 3,
  readiness_score: 85.0,
  readiness_label: 'Ready',
  columns: [
    { role: 'account', detected_name: 'Account Name', confidence: 0.95, status: 'found' },
    { role: 'debit', detected_name: 'Debit', confidence: 1.0, status: 'found' },
    { role: 'credit', detected_name: 'Credit', confidence: 1.0, status: 'found' },
  ],
  issues: [
    {
      category: 'zero_balance',
      severity: 'low',
      message: '5 rows have zero balance in both debit and credit columns (3% of rows)',
      affected_count: 5,
      remediation: 'Zero-balance rows add noise to the analysis.',
    },
    {
      category: 'null_values',
      severity: 'medium',
      message: "Column 'Account Name' has 3 null/empty values (2.0% of rows)",
      affected_count: 3,
      remediation: "Review rows with missing 'Account Name' values.",
    },
  ],
  duplicates: [],
  encoding_anomalies: [],
  mixed_sign_accounts: [],
  zero_balance_count: 5,
  null_counts: { 'Account Name': 3 },
}

describe('PreFlightSummary', () => {
  const onProceed = jest.fn()
  const onExportPDF = jest.fn()
  const onExportCSV = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders readiness score and label', () => {
    render(
      <PreFlightSummary
        report={mockReport}
        onProceed={onProceed}
        onExportPDF={onExportPDF}
        onExportCSV={onExportCSV}
      />
    )

    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('Ready')).toBeInTheDocument()
    expect(screen.getByText('Data Readiness')).toBeInTheDocument()
  })

  it('renders issues list sorted by severity (medium before low)', () => {
    render(
      <PreFlightSummary
        report={mockReport}
        onProceed={onProceed}
        onExportPDF={onExportPDF}
        onExportCSV={onExportCSV}
      />
    )

    expect(screen.getByText('Issues (2)')).toBeInTheDocument()

    // Both issues should be visible
    expect(screen.getByText(/Column 'Account Name' has 3 null/)).toBeInTheDocument()
    expect(screen.getByText(/5 rows have zero balance/)).toBeInTheDocument()

    // Medium should appear before low (check DOM order)
    const badges = screen.getAllByText(/MEDIUM|LOW/)
    expect(badges[0]).toHaveTextContent('MEDIUM')
    expect(badges[1]).toHaveTextContent('LOW')
  })

  it('renders column detection grid', () => {
    render(
      <PreFlightSummary
        report={mockReport}
        onProceed={onProceed}
        onExportPDF={onExportPDF}
        onExportCSV={onExportCSV}
      />
    )

    expect(screen.getByText('Column Detection')).toBeInTheDocument()
    expect(screen.getByText('Account Name')).toBeInTheDocument()
    expect(screen.getByText('Debit')).toBeInTheDocument()
    expect(screen.getByText('Credit')).toBeInTheDocument()
  })

  it('renders remediation guidance on expand', () => {
    render(
      <PreFlightSummary
        report={mockReport}
        onProceed={onProceed}
        onExportPDF={onExportPDF}
        onExportCSV={onExportCSV}
      />
    )

    // Click the first issue (medium severity — null_values) to expand
    const issueButton = screen.getByText(/Column 'Account Name' has 3 null/).closest('button')
    expect(issueButton).toBeTruthy()
    fireEvent.click(issueButton!)

    expect(screen.getByText(/Review rows with missing/)).toBeInTheDocument()
  })

  it('proceed button calls handler', () => {
    render(
      <PreFlightSummary
        report={mockReport}
        onProceed={onProceed}
        onExportPDF={onExportPDF}
        onExportCSV={onExportCSV}
      />
    )

    const proceedButton = screen.getByText('Proceed to Full Analysis')
    fireEvent.click(proceedButton)
    expect(onProceed).toHaveBeenCalledTimes(1)
  })

  it('renders no issues message when report has no issues', () => {
    const cleanReport: PreFlightReport = {
      ...mockReport,
      issues: [],
      readiness_score: 100,
      readiness_label: 'Ready',
    }

    render(
      <PreFlightSummary
        report={cleanReport}
        onProceed={onProceed}
        onExportPDF={onExportPDF}
        onExportCSV={onExportCSV}
      />
    )

    expect(screen.getByText('No data quality issues detected.')).toBeInTheDocument()
  })
})
