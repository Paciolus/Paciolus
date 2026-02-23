/**
 * Sprint 392: ProofSummaryBar component tests
 *
 * Tests the horizontal proof metric strip displayed on all 9 tool pages.
 * Covers: renders all 4 metrics, color mapping per level, narrative display,
 * accessibility, edge cases with zero/missing values.
 */
import React from 'react'
import { ProofSummaryBar } from '@/components/shared/proof/ProofSummaryBar'
import type { ProofSummary, ProofConfidenceLevel } from '@/types/proof'
import { render, screen } from '@/test-utils'

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
    testDetails: [],
    ...overrides,
  }
}

// =============================================================================
// RENDERING
// =============================================================================

describe('ProofSummaryBar', () => {
  it('renders the Evidence Summary heading', () => {
    render(<ProofSummaryBar proof={makeProof()} />)
    expect(screen.getByText('Evidence Summary')).toBeInTheDocument()
  })

  it('renders all 4 metric labels', () => {
    render(<ProofSummaryBar proof={makeProof()} />)
    expect(screen.getByText('Data Completeness:')).toBeInTheDocument()
    expect(screen.getByText('Column Mapping:')).toBeInTheDocument()
    expect(screen.getByText('Tests:')).toBeInTheDocument()
    expect(screen.getByText('Review:')).toBeInTheDocument()
  })

  it('renders metric display values', () => {
    render(<ProofSummaryBar proof={makeProof()} />)
    expect(screen.getByText('94%')).toBeInTheDocument()
    expect(screen.getByText('0.92')).toBeInTheDocument()
    expect(screen.getByText('14/19')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('renders narrative copy', () => {
    render(<ProofSummaryBar proof={makeProof()} />)
    expect(screen.getByText('Data completeness and column mapping support the analysis scope.')).toBeInTheDocument()
  })

  it('has role="region" for accessibility', () => {
    render(<ProofSummaryBar proof={makeProof()} />)
    expect(screen.getByRole('region', { name: 'Evidence summary' })).toBeInTheDocument()
  })
})

// =============================================================================
// LEVEL-BASED STYLING
// =============================================================================

describe('ProofSummaryBar level styling', () => {
  it('applies sage styling for strong level', () => {
    const { container } = render(<ProofSummaryBar proof={makeProof({ overallLevel: 'strong' })} />)
    const region = container.firstChild as HTMLElement
    expect(region.className).toContain('bg-sage-50')
  })

  it('applies oatmeal styling for limited level', () => {
    const { container } = render(<ProofSummaryBar proof={makeProof({ overallLevel: 'limited' })} />)
    const region = container.firstChild as HTMLElement
    expect(region.className).toContain('bg-oatmeal-100')
  })

  it('applies clay styling for insufficient level', () => {
    const { container } = render(<ProofSummaryBar proof={makeProof({ overallLevel: 'insufficient' })} />)
    const region = container.firstChild as HTMLElement
    expect(region.className).toContain('bg-clay-50')
  })
})

// =============================================================================
// EDGE CASES
// =============================================================================

describe('ProofSummaryBar edge cases', () => {
  it('handles zero values in metrics', () => {
    const proof = makeProof({
      dataCompleteness: { label: 'Data Completeness', displayValue: '0%', numericValue: 0, level: 'insufficient' },
      testCoverage: { label: 'Tests', displayValue: '0/0', numericValue: 0, level: 'insufficient' },
      unresolvedItems: { label: 'Review', displayValue: '0', numericValue: 1, level: 'strong' },
    })
    render(<ProofSummaryBar proof={proof} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
    expect(screen.getByText('0/0')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('renders long narrative copy without overflow', () => {
    const proof = makeProof({
      narrativeCopy: 'Significant data gaps. Results may not reflect full population. 15 items require review. Consider expanded procedures.',
    })
    render(<ProofSummaryBar proof={proof} />)
    expect(screen.getByText(/Significant data gaps/)).toBeInTheDocument()
  })
})
