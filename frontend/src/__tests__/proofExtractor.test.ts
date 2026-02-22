/**
 * Sprint 392: Proof Extractor tests
 *
 * Tests the pure synthesis utility that converts raw metrics
 * into ProofSummary objects. Covers:
 * - deriveConfidenceLevel thresholds
 * - extractProofSummary weighted scoring
 * - All 4 confidence tiers
 * - Narrative copy per level
 * - Unresolved item copy
 * - Edge cases (zeros, boundary values, clamping)
 */

import {
  deriveConfidenceLevel,
  extractProofSummary,
  type ProofExtractionInput,
} from '@/utils/proofExtractor'

// =============================================================================
// FIXTURES
// =============================================================================

function makeInput(overrides: Partial<ProofExtractionInput> = {}): ProofExtractionInput {
  return {
    completenessScore: 95,
    columnConfidence: 0.92,
    testsPassed: 17,
    testsTotal: 19,
    unresolvedCount: 2,
    scopeDescription: '19 tests on 1,234 journal entries',
    testDetails: [
      { testName: 'Test A', testKey: 'test_a', status: 'clear', flaggedCount: 0 },
      { testName: 'Test B', testKey: 'test_b', status: 'flagged', flaggedCount: 5 },
    ],
    ...overrides,
  }
}

// =============================================================================
// deriveConfidenceLevel
// =============================================================================

describe('deriveConfidenceLevel', () => {
  it('returns "strong" for >= 0.85', () => {
    expect(deriveConfidenceLevel(0.85)).toBe('strong')
    expect(deriveConfidenceLevel(0.99)).toBe('strong')
    expect(deriveConfidenceLevel(1.0)).toBe('strong')
  })

  it('returns "adequate" for >= 0.65 and < 0.85', () => {
    expect(deriveConfidenceLevel(0.65)).toBe('adequate')
    expect(deriveConfidenceLevel(0.84)).toBe('adequate')
  })

  it('returns "limited" for >= 0.40 and < 0.65', () => {
    expect(deriveConfidenceLevel(0.40)).toBe('limited')
    expect(deriveConfidenceLevel(0.64)).toBe('limited')
  })

  it('returns "insufficient" for < 0.40', () => {
    expect(deriveConfidenceLevel(0.39)).toBe('insufficient')
    expect(deriveConfidenceLevel(0.0)).toBe('insufficient')
  })

  it('handles exact boundary values', () => {
    expect(deriveConfidenceLevel(0.85)).toBe('strong')
    expect(deriveConfidenceLevel(0.65)).toBe('adequate')
    expect(deriveConfidenceLevel(0.40)).toBe('limited')
  })
})

// =============================================================================
// extractProofSummary — basic structure
// =============================================================================

describe('extractProofSummary', () => {
  it('returns all required fields', () => {
    const result = extractProofSummary(makeInput())

    expect(result.dataCompleteness).toBeDefined()
    expect(result.columnConfidence).toBeDefined()
    expect(result.testCoverage).toBeDefined()
    expect(result.unresolvedItems).toBeDefined()
    expect(typeof result.weightedScore).toBe('number')
    expect(result.overallLevel).toBeDefined()
    expect(result.scopeDescription).toBe('19 tests on 1,234 journal entries')
    expect(typeof result.narrativeCopy).toBe('string')
    expect(result.testDetails).toHaveLength(2)
  })

  it('passes through test details unchanged', () => {
    const result = extractProofSummary(makeInput())
    expect(result.testDetails[0].testName).toBe('Test A')
    expect(result.testDetails[1].status).toBe('flagged')
  })
})

// =============================================================================
// Weighted scoring
// =============================================================================

describe('weighted scoring', () => {
  it('applies 40/30/30 weights correctly', () => {
    // completeness=100% (normalized 1.0), column=1.0, pass=1.0
    const result = extractProofSummary(makeInput({
      completenessScore: 100,
      columnConfidence: 1.0,
      testsPassed: 10,
      testsTotal: 10,
    }))
    // 1.0 * 0.4 + 1.0 * 0.3 + 1.0 * 0.3 = 1.0
    expect(result.weightedScore).toBeCloseTo(1.0, 2)
  })

  it('computes weighted score for mixed values', () => {
    // completeness=50 (0.5), column=0.6, pass=8/10=0.8
    const result = extractProofSummary(makeInput({
      completenessScore: 50,
      columnConfidence: 0.6,
      testsPassed: 8,
      testsTotal: 10,
    }))
    // 0.5 * 0.4 + 0.6 * 0.3 + 0.8 * 0.3 = 0.20 + 0.18 + 0.24 = 0.62
    expect(result.weightedScore).toBeCloseTo(0.62, 2)
  })

  it('handles zero tests total gracefully', () => {
    const result = extractProofSummary(makeInput({
      testsPassed: 0,
      testsTotal: 0,
    }))
    // test pass rate = 0, so weighted = 0.95 * 0.4 + 0.92 * 0.3 + 0 * 0.3
    expect(result.testCoverage.numericValue).toBe(0)
    expect(result.testCoverage.displayValue).toBe('0/0')
  })
})

// =============================================================================
// Confidence tiers (end-to-end)
// =============================================================================

describe('confidence tier mapping', () => {
  it('produces "strong" for high-quality input', () => {
    const result = extractProofSummary(makeInput({
      completenessScore: 95,
      columnConfidence: 0.95,
      testsPassed: 18,
      testsTotal: 19,
    }))
    expect(result.overallLevel).toBe('strong')
  })

  it('produces "adequate" for moderate input', () => {
    const result = extractProofSummary(makeInput({
      completenessScore: 75,
      columnConfidence: 0.70,
      testsPassed: 12,
      testsTotal: 19,
    }))
    expect(result.overallLevel).toBe('adequate')
  })

  it('produces "limited" for weak input', () => {
    const result = extractProofSummary(makeInput({
      completenessScore: 40,
      columnConfidence: 0.45,
      testsPassed: 8,
      testsTotal: 19,
    }))
    expect(result.overallLevel).toBe('limited')
  })

  it('produces "insufficient" for very poor input', () => {
    const result = extractProofSummary(makeInput({
      completenessScore: 10,
      columnConfidence: 0.1,
      testsPassed: 2,
      testsTotal: 19,
    }))
    expect(result.overallLevel).toBe('insufficient')
  })
})

// =============================================================================
// Metric display values
// =============================================================================

describe('metric display values', () => {
  it('formats completeness as percentage', () => {
    const result = extractProofSummary(makeInput({ completenessScore: 94.5 }))
    expect(result.dataCompleteness.displayValue).toBe('95%')
  })

  it('formats column confidence as decimal', () => {
    const result = extractProofSummary(makeInput({ columnConfidence: 0.876 }))
    expect(result.columnConfidence.displayValue).toBe('0.88')
  })

  it('formats test coverage as ratio', () => {
    const result = extractProofSummary(makeInput({ testsPassed: 14, testsTotal: 19 }))
    expect(result.testCoverage.displayValue).toBe('14/19')
  })

  it('formats unresolved as count string', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 3 }))
    expect(result.unresolvedItems.displayValue).toBe('3')
  })

  it('clamps column confidence to 0-1 range', () => {
    const result = extractProofSummary(makeInput({ columnConfidence: 1.5 }))
    expect(result.columnConfidence.numericValue).toBe(1)
  })

  it('clamps completeness at 100', () => {
    const result = extractProofSummary(makeInput({ completenessScore: 150 }))
    expect(result.dataCompleteness.numericValue).toBe(1)
  })
})

// =============================================================================
// Narrative copy
// =============================================================================

describe('narrative copy', () => {
  it('includes level-specific text for strong', () => {
    const result = extractProofSummary(makeInput({
      completenessScore: 95,
      columnConfidence: 0.95,
      testsPassed: 19,
      testsTotal: 19,
      unresolvedCount: 0,
    }))
    expect(result.narrativeCopy).toContain('Data completeness and column mapping support the analysis scope.')
  })

  it('appends unresolved copy when count > 0', () => {
    const result = extractProofSummary(makeInput({
      completenessScore: 95,
      columnConfidence: 0.95,
      testsPassed: 19,
      testsTotal: 19,
      unresolvedCount: 2,
    }))
    expect(result.narrativeCopy).toContain('2 items identified for professional judgment.')
  })

  it('uses singular for 1 unresolved item', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 1 }))
    expect(result.narrativeCopy).toContain('1 item identified for professional judgment.')
  })

  it('uses expanded procedures copy for 4+ items', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 5 }))
    expect(result.narrativeCopy).toContain('5 items require review. Consider expanded procedures.')
  })

  it('omits unresolved copy when count is 0', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 0 }))
    expect(result.narrativeCopy).not.toContain('items')
    expect(result.narrativeCopy).not.toContain('professional judgment')
  })
})

// =============================================================================
// Unresolved metric level
// =============================================================================

describe('unresolved metric level', () => {
  it('is "strong" when 0', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 0 }))
    expect(result.unresolvedItems.level).toBe('strong')
  })

  it('is "adequate" for 1-3', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 3 }))
    expect(result.unresolvedItems.level).toBe('adequate')
  })

  it('is "limited" for 4-10', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 7 }))
    expect(result.unresolvedItems.level).toBe('limited')
  })

  it('is "insufficient" for 11+', () => {
    const result = extractProofSummary(makeInput({ unresolvedCount: 15 }))
    expect(result.unresolvedItems.level).toBe('insufficient')
  })
})
