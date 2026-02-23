/**
 * Proof Adapters — 9 tool-specific extractors (Sprint 390)
 *
 * Each adapter maps a tool's result shape into the ProofExtractionInput
 * consumed by extractProofSummary(). Domain-specific logic stays here;
 * the extractor stays domain-agnostic.
 */

import type { APTestingResult } from '@/types/apTesting'
import type { ARAgingResult } from '@/types/arAging'
import type { BankRecResult } from '@/types/bankRec'
import type { FixedAssetTestingResult } from '@/types/fixedAssetTesting'
import type { InventoryTestingResult } from '@/types/inventoryTesting'
import type { JETestingResult } from '@/types/jeTesting'
import type { PayrollTestingResult } from '@/types/payrollTesting'
import type { ProofSummary, ProofTestDetail } from '@/types/proof'
import type { RevenueTestingResult } from '@/types/revenueTesting'
import type { ThreeWayMatchResult } from '@/types/threeWayMatch'
import { extractProofSummary, type ProofExtractionInput } from '@/utils/proofExtractor'

// =============================================================================
// Helpers for standard 7-tool pattern
// =============================================================================

interface StandardTestResult {
  test_name: string
  test_key: string
  entries_flagged: number
  skipped?: boolean
}

function buildTestDetails(results: StandardTestResult[]): ProofTestDetail[] {
  return results.map((tr) => ({
    testName: tr.test_name,
    testKey: tr.test_key,
    status: tr.skipped ? 'skipped' as const : tr.entries_flagged > 0 ? 'flagged' as const : 'clear' as const,
    flaggedCount: tr.entries_flagged,
  }))
}

function countPassed(results: StandardTestResult[]): number {
  return results.filter((tr) => !tr.skipped && tr.entries_flagged === 0).length
}

function countRunnable(results: StandardTestResult[]): number {
  return results.filter((tr) => !tr.skipped).length
}

function formatNumber(n: number): string {
  return n.toLocaleString('en-US')
}

// =============================================================================
// Standard adapters (JE, AP, Payroll, Revenue, FA, Inventory)
// =============================================================================

function extractStandard(
  input: {
    compositeScore: { tests_run: number; total_entries?: number; total_flagged: number }
    testResults: StandardTestResult[]
    dataQuality: { completeness_score: number; total_rows?: number }
    columnConfidence: number
    totalEntries: number
    testsLabel: string
    entriesLabel: string
  },
): ProofExtractionInput {
  const { compositeScore, testResults, dataQuality, columnConfidence, totalEntries, testsLabel, entriesLabel } = input
  const testDetails = buildTestDetails(testResults)
  const runnable = countRunnable(testResults)
  const passed = countPassed(testResults)

  return {
    completenessScore: dataQuality.completeness_score,
    columnConfidence,
    testsPassed: passed,
    testsTotal: runnable,
    unresolvedCount: compositeScore.total_flagged,
    scopeDescription: `${testsLabel} tests on ${formatNumber(totalEntries)} ${entriesLabel}`,
    testDetails,
  }
}

// --- JE ---
export function extractJEProof(result: JETestingResult): ProofSummary {
  return extractProofSummary(extractStandard({
    compositeScore: result.composite_score,
    testResults: result.test_results,
    dataQuality: result.data_quality,
    columnConfidence: result.column_detection?.overall_confidence ?? 0,
    totalEntries: result.composite_score.total_entries,
    testsLabel: String(result.composite_score.tests_run),
    entriesLabel: 'journal entries',
  }))
}

// --- AP ---
export function extractAPProof(result: APTestingResult): ProofSummary {
  return extractProofSummary(extractStandard({
    compositeScore: result.composite_score,
    testResults: result.test_results,
    dataQuality: result.data_quality,
    columnConfidence: result.column_detection?.overall_confidence ?? 0,
    totalEntries: result.composite_score.total_entries,
    testsLabel: String(result.composite_score.tests_run),
    entriesLabel: 'payments',
  }))
}

// --- Payroll ---
export function extractPayrollProof(result: PayrollTestingResult): ProofSummary {
  return extractProofSummary(extractStandard({
    compositeScore: result.composite_score,
    testResults: result.test_results,
    dataQuality: result.data_quality,
    columnConfidence: result.column_detection?.overall_confidence ?? 0,
    totalEntries: result.composite_score.total_entries,
    testsLabel: String(result.composite_score.tests_run),
    entriesLabel: 'payroll records',
  }))
}

// --- Revenue ---
export function extractRevenueProof(result: RevenueTestingResult): ProofSummary {
  const testResults = result.test_results.map((tr) => ({
    ...tr,
    skipped: 'skipped' in tr ? (tr as unknown as { skipped: boolean }).skipped : false,
  }))
  return extractProofSummary(extractStandard({
    compositeScore: result.composite_score,
    testResults,
    dataQuality: result.data_quality,
    columnConfidence: result.column_detection?.overall_confidence ?? 0,
    totalEntries: result.composite_score.total_entries,
    testsLabel: String(result.composite_score.tests_run),
    entriesLabel: 'revenue entries',
  }))
}

// --- AR Aging (oddball: different data quality shape, mandatory skipped) ---
export function extractARProof(result: ARAgingResult): ProofSummary {
  const testResults = result.test_results.map((tr) => ({
    ...tr,
    skipped: tr.skipped,
  }))

  // AR uses total_tb_accounts instead of total_rows, and has a different composite shape
  const totalEntries = result.data_quality.total_tb_accounts +
    (result.data_quality.total_subledger_entries ?? 0)

  // Column confidence from tb_column_detection (loosely typed)
  const tbConf = (result.tb_column_detection as Record<string, unknown> | null)?.overall_confidence
  const slConf = (result.sl_column_detection as Record<string, unknown> | null)?.overall_confidence
  const columnConfidence = typeof tbConf === 'number'
    ? (typeof slConf === 'number' ? (tbConf + slConf) / 2 : tbConf)
    : 0

  return extractProofSummary({
    completenessScore: result.data_quality.completeness_score,
    columnConfidence,
    testsPassed: countPassed(testResults),
    testsTotal: countRunnable(testResults),
    unresolvedCount: result.composite_score.total_flagged,
    scopeDescription: `${result.composite_score.tests_run} tests on ${formatNumber(totalEntries)} receivables`,
    testDetails: buildTestDetails(testResults),
  })
}

// --- Fixed Assets ---
export function extractFAProof(result: FixedAssetTestingResult): ProofSummary {
  return extractProofSummary(extractStandard({
    compositeScore: result.composite_score,
    testResults: result.test_results,
    dataQuality: result.data_quality,
    columnConfidence: result.column_detection?.overall_confidence ?? 0,
    totalEntries: result.composite_score.total_entries,
    testsLabel: String(result.composite_score.tests_run),
    entriesLabel: 'assets',
  }))
}

// --- Inventory ---
export function extractInventoryProof(result: InventoryTestingResult): ProofSummary {
  return extractProofSummary(extractStandard({
    compositeScore: result.composite_score,
    testResults: result.test_results,
    dataQuality: result.data_quality,
    columnConfidence: result.column_detection?.overall_confidence ?? 0,
    totalEntries: result.composite_score.total_entries,
    testsLabel: String(result.composite_score.tests_run),
    entriesLabel: 'items',
  }))
}

// =============================================================================
// Bank Reconciliation (completely different shape)
// =============================================================================

export function extractBankRecProof(result: BankRecResult): ProofSummary {
  const { summary } = result

  const totalItems = summary.matched_count + summary.bank_only_count + summary.ledger_only_count
  const matchRate = totalItems > 0 ? summary.matched_count / totalItems : 0

  // Bank rec has no formal "test battery" — treat match rate as pass rate
  const bankConf = result.bank_column_detection?.overall_confidence ?? 0
  const ledgerConf = result.ledger_column_detection?.overall_confidence ?? 0
  const avgColumnConf = (bankConf + ledgerConf) / 2

  // Completeness: proxy from match rate (high match = complete data)
  const completenessProxy = matchRate * 100

  // Unresolved = unmatched items
  const unresolved = summary.bank_only_count + summary.ledger_only_count

  // Test details: synthesize from reconciliation categories
  const testDetails: ProofTestDetail[] = [
    { testName: 'Exact Match', testKey: 'matched', status: 'clear', flaggedCount: 0 },
    { testName: 'Bank-Only Items', testKey: 'bank_only', status: summary.bank_only_count > 0 ? 'flagged' : 'clear', flaggedCount: summary.bank_only_count },
    { testName: 'Ledger-Only Items', testKey: 'ledger_only', status: summary.ledger_only_count > 0 ? 'flagged' : 'clear', flaggedCount: summary.ledger_only_count },
  ]

  return extractProofSummary({
    completenessScore: completenessProxy,
    columnConfidence: avgColumnConf,
    testsPassed: testDetails.filter((t) => t.status === 'clear').length,
    testsTotal: testDetails.length,
    unresolvedCount: unresolved,
    scopeDescription: `Reconciliation of ${formatNumber(totalItems)} items`,
    testDetails,
  })
}

// =============================================================================
// Three-Way Match (completely different shape)
// =============================================================================

export function extractTWMProof(result: ThreeWayMatchResult): ProofSummary {
  const { summary, data_quality, column_detection } = result

  const totalDocs = summary.total_pos + summary.total_invoices + summary.total_receipts

  // Column confidence: average of 3 detection results
  const poConf = column_detection?.po?.overall_confidence ?? 0
  const invConf = column_detection?.invoice?.overall_confidence ?? 0
  const rcptConf = column_detection?.receipt?.overall_confidence ?? 0
  const avgColumnConf = (poConf + invConf + rcptConf) / 3

  // Completeness from data_quality.overall_quality_score (0-100)
  const completenessScore = data_quality?.overall_quality_score ?? 0

  // Unresolved = unmatched documents
  const unresolved = (result.unmatched_pos?.length ?? 0) +
    (result.unmatched_invoices?.length ?? 0) +
    (result.unmatched_receipts?.length ?? 0)

  // Test details: synthesize from match categories
  const testDetails: ProofTestDetail[] = [
    { testName: 'Full Matches', testKey: 'full_match', status: 'clear', flaggedCount: 0 },
    { testName: 'Partial Matches', testKey: 'partial_match', status: result.partial_matches.length > 0 ? 'flagged' : 'clear', flaggedCount: result.partial_matches.length },
    { testName: 'Material Variances', testKey: 'variances', status: summary.material_variances_count > 0 ? 'flagged' : 'clear', flaggedCount: summary.material_variances_count },
    { testName: 'Unmatched POs', testKey: 'unmatched_po', status: result.unmatched_pos.length > 0 ? 'flagged' : 'clear', flaggedCount: result.unmatched_pos.length },
    { testName: 'Unmatched Invoices', testKey: 'unmatched_inv', status: result.unmatched_invoices.length > 0 ? 'flagged' : 'clear', flaggedCount: result.unmatched_invoices.length },
    { testName: 'Unmatched Receipts', testKey: 'unmatched_rcpt', status: result.unmatched_receipts.length > 0 ? 'flagged' : 'clear', flaggedCount: result.unmatched_receipts.length },
  ]

  const passed = testDetails.filter((t) => t.status === 'clear').length

  return extractProofSummary({
    completenessScore,
    columnConfidence: avgColumnConf,
    testsPassed: passed,
    testsTotal: testDetails.length,
    unresolvedCount: unresolved,
    scopeDescription: `Matching of ${formatNumber(totalDocs)} transactions`,
    testDetails,
  })
}
