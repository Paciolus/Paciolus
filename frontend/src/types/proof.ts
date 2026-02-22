/**
 * Proof Architecture — Type System (Sprint 390)
 *
 * Domain-agnostic evidence synthesis types.
 * ProofSummary answers: "How well-evidenced are these results?"
 * Sits above ScoreCard (domain-rich) and DataQualityBadge (completeness-focused).
 */

/** Confidence tier — drives color semantics and narrative copy */
export type ProofConfidenceLevel = 'strong' | 'adequate' | 'limited' | 'insufficient'

/** Single metric within the proof summary strip */
export interface ProofMetric {
  label: string
  /** Display value (e.g., "94%", "0.92", "14/19", "3") */
  displayValue: string
  /** Normalized 0–1 value for color computation */
  numericValue: number
  /** Per-metric confidence level */
  level: ProofConfidenceLevel
}

/** Aggregated proof summary for a single tool run */
export interface ProofSummary {
  dataCompleteness: ProofMetric
  columnConfidence: ProofMetric
  testCoverage: ProofMetric
  unresolvedItems: ProofMetric
  /** Weighted composite: 40% completeness + 30% column + 30% test pass rate */
  weightedScore: number
  /** Overall confidence level derived from weightedScore */
  overallLevel: ProofConfidenceLevel
  /** Tool-specific scope line (e.g., "19 tests on 1,234 journal entries") */
  scopeDescription: string
  /** Factual narrative copy per confidence level */
  narrativeCopy: string
  /** Per-test breakdown for detail panel */
  testDetails: ProofTestDetail[]
}

/** Individual test result for the ProofPanel detail view */
export interface ProofTestDetail {
  testName: string
  testKey: string
  status: 'clear' | 'flagged' | 'skipped'
  flaggedCount: number
}

/** Adapter interface — each tool implements one */
export interface ToolProofAdapter<T = unknown> {
  toolName: string
  standard: string
  extract: (result: T) => ProofSummary
}
