/**
 * Proof Architecture — Barrel export (Sprint 390-391)
 */

export { ProofSummaryBar } from './ProofSummaryBar'
export type { ProofSummaryBarProps } from './ProofSummaryBar'

export { ProofPanel } from './ProofPanel'
export type { ProofPanelProps } from './ProofPanel'

export { ProofTraceBar } from './ProofTraceBar'
export type { ProofTraceBarProps } from './ProofTraceBar'

export { ProofConfidenceBadge } from './ProofConfidenceBadge'
export type { ProofConfidenceBadgeProps } from './ProofConfidenceBadge'

export {
  extractJEProof,
  extractAPProof,
  extractPayrollProof,
  extractRevenueProof,
  extractARProof,
  extractFAProof,
  extractInventoryProof,
  extractBankRecProof,
  extractTWMProof,
} from './proofAdapters'
