/**
 * Sprint 869: JE testing counts GL lines (one per row), not journal entries.
 *
 * A 204-entry ledger of 408 lines was reported as "408 journal entries". The
 * count is right; the noun was not. These pin the noun on both app surfaces.
 */
import { render, screen } from '@testing-library/react'
import { JEScoreCard } from '@/components/jeTesting/JEScoreCard'
import { extractJEProof } from '@/components/shared/proof/proofAdapters'

jest.mock('@/components/shared/testing/TestingScoreCard', () => ({
  TestingScoreCard: ({ total_entries, entity_label }: { total_entries: number; entity_label: string }) => (
    <p>{`${total_entries} ${entity_label}`}</p>
  ),
}))

const composite = {
  score: 12,
  risk_tier: 'moderate',
  tests_run: 9,
  total_entries: 408,
  total_flagged: 4,
  flag_rate: 4 / 408,
  flags_by_severity: { high: 0, medium: 2, low: 2 },
  top_findings: [],
}

describe('JE count noun', () => {
  it('the score card counts GL lines', () => {
    render(<JEScoreCard score={composite as never} />)
    expect(screen.getByText('408 GL lines')).toBeInTheDocument()
    expect(screen.queryByText(/journal entries/i)).not.toBeInTheDocument()
  })

  it('the proof summary scope counts GL lines', () => {
    const proof = extractJEProof({
      composite_score: composite,
      test_results: [],
      data_quality: { completeness_score: 100, field_fill_rates: {}, detected_issues: [], total_rows: 408 },
      column_detection: { overall_confidence: 0.9 },
    } as never)
    const text = JSON.stringify(proof)
    expect(text).toContain('9 tests on 408 GL lines')
    expect(text).not.toMatch(/journal entries/i)
  })
})
