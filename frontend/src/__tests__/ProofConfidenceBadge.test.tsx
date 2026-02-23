/**
 * Sprint 392: ProofConfidenceBadge component tests
 *
 * Tests the compact confidence tier badge displayed in the ProofPanel.
 * Covers: 4 level stylings, narrative display, optional narrative.
 */
import React from 'react'
import { ProofConfidenceBadge } from '@/components/shared/proof/ProofConfidenceBadge'
import { render, screen } from '@/test-utils'
import type { ProofConfidenceLevel } from '@/types/proof'


// =============================================================================
// LEVEL LABELS
// =============================================================================

describe('ProofConfidenceBadge levels', () => {
  const levels: { level: ProofConfidenceLevel; label: string; bgClass: string }[] = [
    { level: 'strong', label: 'Strong', bgClass: 'bg-sage-50' },
    { level: 'adequate', label: 'Adequate', bgClass: 'bg-sage-50/60' },
    { level: 'limited', label: 'Limited', bgClass: 'bg-oatmeal-100' },
    { level: 'insufficient', label: 'Insufficient', bgClass: 'bg-clay-50' },
  ]

  levels.forEach(({ level, label, bgClass }) => {
    it(`renders "${label}" label for ${level} level`, () => {
      render(<ProofConfidenceBadge level={level} />)
      expect(screen.getByText(`Confidence: ${label}`)).toBeInTheDocument()
    })

    it(`applies ${bgClass} background for ${level} level`, () => {
      const { container } = render(<ProofConfidenceBadge level={level} />)
      const badge = container.firstChild as HTMLElement
      expect(badge.className).toContain(bgClass)
    })
  })
})

// =============================================================================
// NARRATIVE
// =============================================================================

describe('ProofConfidenceBadge narrative', () => {
  it('renders narrative text when provided', () => {
    render(
      <ProofConfidenceBadge
        level="strong"
        narrative="Data completeness and column mapping support the analysis scope."
      />
    )
    expect(screen.getByText('Data completeness and column mapping support the analysis scope.')).toBeInTheDocument()
  })

  it('omits narrative paragraph when not provided', () => {
    const { container } = render(<ProofConfidenceBadge level="strong" />)
    const paragraphs = container.querySelectorAll('p')
    expect(paragraphs).toHaveLength(0)
  })
})
