/**
 * Proof Extractor — Pure synthesis utility (Sprint 390)
 *
 * Converts raw metric inputs into a ProofSummary.
 * Weighted: 40% data completeness, 30% column confidence, 30% test pass rate.
 * No side effects, no API calls — pure function.
 */

import type {
  ProofConfidenceLevel,
  ProofMetric,
  ProofSummary,
  ProofTestDetail,
} from '@/types/proof'

// =============================================================================
// Constants
// =============================================================================

const WEIGHT_COMPLETENESS = 0.4
const WEIGHT_COLUMN = 0.3
const WEIGHT_TEST_PASS = 0.3

const THRESHOLD_STRONG = 0.85
const THRESHOLD_ADEQUATE = 0.65
const THRESHOLD_LIMITED = 0.40

// =============================================================================
// Confidence level derivation
// =============================================================================

export function deriveConfidenceLevel(value: number): ProofConfidenceLevel {
  if (value >= THRESHOLD_STRONG) return 'strong'
  if (value >= THRESHOLD_ADEQUATE) return 'adequate'
  if (value >= THRESHOLD_LIMITED) return 'limited'
  return 'insufficient'
}

// =============================================================================
// Narrative copy
// =============================================================================

const NARRATIVE_COPY: Record<ProofConfidenceLevel, string> = {
  strong: 'Data completeness and column mapping support the analysis scope.',
  adequate: 'Most required fields populated. Column mapping confident.',
  limited: 'Partial field coverage. Some columns assigned with low confidence.',
  insufficient: 'Significant data gaps. Results may not reflect full population.',
}

function unresolvedCopy(count: number): string {
  if (count === 0) return 'All flagged items within test battery coverage.'
  if (count <= 3) return `${count} item${count === 1 ? '' : 's'} identified for professional judgment.`
  return `${count} items require review. Consider expanded procedures.`
}

function unresolvedLevel(count: number): ProofConfidenceLevel {
  if (count === 0) return 'strong'
  if (count <= 3) return 'adequate'
  if (count <= 10) return 'limited'
  return 'insufficient'
}

// =============================================================================
// Metric builders
// =============================================================================

function buildCompletenessMetric(score: number): ProofMetric {
  // score is 0–100 from data_quality.completeness_score
  const normalized = Math.min(score, 100) / 100
  return {
    label: 'Data Completeness',
    displayValue: `${Math.round(score)}%`,
    numericValue: normalized,
    level: deriveConfidenceLevel(normalized),
  }
}

function buildColumnConfidenceMetric(confidence: number): ProofMetric {
  // confidence is 0–1 from column_detection.overall_confidence
  const clamped = Math.max(0, Math.min(1, confidence))
  return {
    label: 'Column Mapping',
    displayValue: clamped.toFixed(2),
    numericValue: clamped,
    level: deriveConfidenceLevel(clamped),
  }
}

function buildTestCoverageMetric(passed: number, total: number): ProofMetric {
  const rate = total > 0 ? passed / total : 0
  return {
    label: 'Tests',
    displayValue: `${passed}/${total}`,
    numericValue: rate,
    level: deriveConfidenceLevel(rate),
  }
}

function buildUnresolvedMetric(count: number): ProofMetric {
  return {
    label: 'Review',
    displayValue: String(count),
    numericValue: count === 0 ? 1 : Math.max(0, 1 - count / 20),
    level: unresolvedLevel(count),
  }
}

// =============================================================================
// Main extractor
// =============================================================================

export interface ProofExtractionInput {
  /** 0–100 data completeness score */
  completenessScore: number
  /** 0–1 column detection confidence */
  columnConfidence: number
  /** Number of tests that passed (no flags) */
  testsPassed: number
  /** Total number of tests run */
  testsTotal: number
  /** Number of unresolved / flagged items requiring review */
  unresolvedCount: number
  /** Tool-specific scope description */
  scopeDescription: string
  /** Per-test breakdown */
  testDetails: ProofTestDetail[]
}

export function extractProofSummary(input: ProofExtractionInput): ProofSummary {
  const completeness = buildCompletenessMetric(input.completenessScore)
  const column = buildColumnConfidenceMetric(input.columnConfidence)
  const coverage = buildTestCoverageMetric(input.testsPassed, input.testsTotal)
  const unresolved = buildUnresolvedMetric(input.unresolvedCount)

  const weightedScore =
    completeness.numericValue * WEIGHT_COMPLETENESS +
    column.numericValue * WEIGHT_COLUMN +
    coverage.numericValue * WEIGHT_TEST_PASS

  const overallLevel = deriveConfidenceLevel(weightedScore)

  // Compose narrative: overall + unresolved
  const narrativeParts = [NARRATIVE_COPY[overallLevel]]
  if (input.unresolvedCount > 0) {
    narrativeParts.push(unresolvedCopy(input.unresolvedCount))
  }

  return {
    dataCompleteness: completeness,
    columnConfidence: column,
    testCoverage: coverage,
    unresolvedItems: unresolved,
    weightedScore,
    overallLevel,
    scopeDescription: input.scopeDescription,
    narrativeCopy: narrativeParts.join(' '),
    testDetails: input.testDetails,
  }
}
