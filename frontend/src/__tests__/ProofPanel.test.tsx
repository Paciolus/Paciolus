/**
 * Sprint 392: ProofPanel component tests
 *
 * Tests the collapsible evidence trace detail view.
 * Covers: collapse/expand toggle, trace bar rendering, test detail table,
 * confidence badge, accessibility attributes, defaultExpanded prop.
 */
import React from 'react'
import { render, screen, fireEvent } from '@/test-utils'
import type { ProofSummary, ProofConfidenceLevel } from '@/types/proof'

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

import { ProofPanel } from '@/components/shared/proof/ProofPanel'

// =============================================================================
// FIXTURES
// =============================================================================

function makeProof(overrides: Partial<ProofSummary> = {}): ProofSummary {
  return {
    dataCompleteness: { label: 'Data Completeness', displayValue: '94%', numericValue: 0.94, level: 'strong' },
    columnConfidence: { label: 'Column Mapping', displayValue: '0.92', numericValue: 0.92, level: 'strong' },
    testCoverage: { label: 'Tests', displayValue: '14/19', numericValue: 0.74, level: 'adequate' },
    unresolvedItems: { label: 'Review', displayValue: '3', numericValue: 0.85, level: 'adequate' },
    weightedScore: 0.87,
    overallLevel: 'strong' as ProofConfidenceLevel,
    scopeDescription: '19 tests on 1,234 journal entries',
    narrativeCopy: 'Data completeness and column mapping support the analysis scope.',
    testDetails: [
      { testName: 'Unbalanced Entries', testKey: 'unbalanced', status: 'clear', flaggedCount: 0 },
      { testName: 'Duplicates', testKey: 'duplicates', status: 'flagged', flaggedCount: 12 },
      { testName: 'Contract Tests', testKey: 'contract', status: 'skipped', flaggedCount: 0 },
    ],
    ...overrides,
  }
}

// =============================================================================
// COLLAPSE / EXPAND
// =============================================================================

describe('ProofPanel collapse/expand', () => {
  it('starts collapsed by default', () => {
    render(<ProofPanel proof={makeProof()} />)
    expect(screen.getByText('Evidence Trace')).toBeInTheDocument()
    // Test detail table should NOT be visible
    expect(screen.queryByText('Unbalanced Entries')).not.toBeInTheDocument()
  })

  it('starts expanded when defaultExpanded is true', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    expect(screen.getByText('Unbalanced Entries')).toBeInTheDocument()
    expect(screen.getByText('Duplicates')).toBeInTheDocument()
  })

  it('expands on click', () => {
    render(<ProofPanel proof={makeProof()} />)
    fireEvent.click(screen.getByRole('button', { name: /Evidence Trace/i }))
    expect(screen.getByText('Unbalanced Entries')).toBeInTheDocument()
  })

  it('collapses on second click', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    fireEvent.click(screen.getByRole('button', { name: /Evidence Trace/i }))
    expect(screen.queryByText('Unbalanced Entries')).not.toBeInTheDocument()
  })
})

// =============================================================================
// ACCESSIBILITY
// =============================================================================

describe('ProofPanel accessibility', () => {
  it('has aria-expanded=false when collapsed', () => {
    render(<ProofPanel proof={makeProof()} />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-expanded', 'false')
  })

  it('has aria-expanded=true when expanded', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-expanded', 'true')
  })

  it('has aria-controls pointing to content', () => {
    render(<ProofPanel proof={makeProof()} />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('aria-controls', 'proof-panel-content')
  })
})

// =============================================================================
// TEST DETAIL TABLE
// =============================================================================

describe('ProofPanel test detail table', () => {
  it('renders all test rows when expanded', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    expect(screen.getByText('Unbalanced Entries')).toBeInTheDocument()
    expect(screen.getByText('Duplicates')).toBeInTheDocument()
    expect(screen.getByText('Contract Tests')).toBeInTheDocument()
  })

  it('shows flagged count for flagged tests', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    expect(screen.getByText('12')).toBeInTheDocument()
  })

  it('shows table headers', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Flagged')).toBeInTheDocument()
  })

  it('handles empty test details gracefully', () => {
    render(<ProofPanel proof={makeProof({ testDetails: [] })} defaultExpanded={true} />)
    // Should not render the table at all
    expect(screen.queryByText('Test')).not.toBeInTheDocument()
  })
})

// =============================================================================
// CONFIDENCE BADGE
// =============================================================================

describe('ProofPanel confidence badge', () => {
  it('renders confidence badge when expanded', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    expect(screen.getByText('Confidence: Strong')).toBeInTheDocument()
  })

  it('shows narrative copy in badge', () => {
    render(<ProofPanel proof={makeProof()} defaultExpanded={true} />)
    expect(screen.getByText('Data completeness and column mapping support the analysis scope.')).toBeInTheDocument()
  })
})
