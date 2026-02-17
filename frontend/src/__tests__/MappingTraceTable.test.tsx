/**
 * Sprint 284: MappingTraceTable component tests
 *
 * Tests the account-to-statement mapping trace table.
 * Covers: group headers, line items, tied/untied badges, expand/collapse, summary.
 */
import React from 'react'
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

import { MappingTraceTable } from '@/components/financialStatements/MappingTraceTable'
import type { MappingTraceEntry } from '@/components/financialStatements/types'

const tiedEntry: MappingTraceEntry = {
  statement: 'Balance Sheet',
  lineLabel: 'Cash and Cash Equivalents',
  leadSheetRef: 'A',
  leadSheetName: 'Cash and Cash Equivalents',
  statementAmount: 50000,
  accountCount: 2,
  accounts: [
    { accountName: 'Cash at Bank', debit: 30000, credit: 0, netBalance: 30000, confidence: 0.95, matchedKeywords: ['cash'] },
    { accountName: 'Petty Cash', debit: 20000, credit: 0, netBalance: 20000, confidence: 1.0, matchedKeywords: ['cash'] },
  ],
  isTied: true,
  tieDifference: 0,
}

const untiedEntry: MappingTraceEntry = {
  statement: 'Income Statement',
  lineLabel: 'Revenue',
  leadSheetRef: 'L',
  leadSheetName: 'Revenue',
  statementAmount: 150000,
  accountCount: 1,
  accounts: [
    { accountName: 'Product Revenue', debit: 0, credit: 100000, netBalance: -100000, confidence: 0.90, matchedKeywords: ['revenue'] },
  ],
  isTied: false,
  tieDifference: 50000,
}

const emptyEntry: MappingTraceEntry = {
  statement: 'Balance Sheet',
  lineLabel: 'Inventory',
  leadSheetRef: 'C',
  leadSheetName: 'Inventory',
  statementAmount: 0,
  accountCount: 0,
  accounts: [],
  isTied: true,
  tieDifference: 0,
}

describe('MappingTraceTable', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders statement group headers', () => {
    render(<MappingTraceTable entries={[tiedEntry, untiedEntry]} />)
    expect(screen.getByText('Balance Sheet')).toBeInTheDocument()
    expect(screen.getByText('Income Statement')).toBeInTheDocument()
  })

  it('renders line items with lead sheet refs', () => {
    render(<MappingTraceTable entries={[tiedEntry, emptyEntry]} />)
    expect(screen.getByText('Cash and Cash Equivalents')).toBeInTheDocument()
    expect(screen.getByText('Inventory')).toBeInTheDocument()
    expect(screen.getByText('A')).toBeInTheDocument()
    expect(screen.getByText('C')).toBeInTheDocument()
  })

  it('shows tied badge for tied entries', () => {
    render(<MappingTraceTable entries={[tiedEntry]} />)
    expect(screen.getByText('Tied')).toBeInTheDocument()
  })

  it('shows untied badge for untied entries', () => {
    render(<MappingTraceTable entries={[untiedEntry]} />)
    expect(screen.getByText('Untied')).toBeInTheDocument()
  })

  it('expands to show accounts on click', () => {
    render(<MappingTraceTable entries={[tiedEntry]} />)

    // Accounts should not be visible initially
    expect(screen.queryByText('Cash at Bank')).not.toBeInTheDocument()

    // Click to expand
    fireEvent.click(screen.getByText('Cash and Cash Equivalents'))

    // Accounts should now be visible
    expect(screen.getByText('Cash at Bank')).toBeInTheDocument()
    expect(screen.getByText('Petty Cash')).toBeInTheDocument()
  })

  it('shows summary badge', () => {
    render(<MappingTraceTable entries={[tiedEntry, emptyEntry]} />)
    expect(screen.getByText('All 2 lines tied')).toBeInTheDocument()
  })

  it('shows untied summary when entries are untied', () => {
    render(<MappingTraceTable entries={[tiedEntry, untiedEntry]} />)
    expect(screen.getByText('1 of 2 lines untied')).toBeInTheDocument()
  })
})
