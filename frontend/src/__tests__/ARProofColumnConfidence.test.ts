/**
 * Sprint 886 (review OUT-15): AR column confidence is the mean of the TB and
 * sub-ledger detections the run carried — the same rule as the PDF memo
 * (`shared/memo_base.mean_confidence`). No detection is "Not available", not 0.
 */
import { extractARProof } from '@/components/shared/proof/proofAdapters'
import type { ARAgingResult } from '@/types/arAging'

const result = (tb: number | null, sl: number | null): ARAgingResult =>
  ({
    composite_score: { tests_run: 12, total_flagged: 0 },
    test_results: [],
    data_quality: { completeness_score: 100, total_tb_accounts: 3, total_subledger_entries: 3 },
    tb_column_detection: tb === null ? null : { overall_confidence: tb },
    sl_column_detection: sl === null ? null : { overall_confidence: sl },
    ar_summary: null,
  }) as unknown as ARAgingResult

describe('AR proof column confidence', () => {
  it('is the mean of TB 0.8 and sub-ledger 1.0 (0.90, as the memo prints 90%)', () => {
    expect(extractARProof(result(0.8, 1.0)).columnConfidence.displayValue).toBe('0.90')
  })

  it('is the TB detection alone on a TB-only run', () => {
    expect(extractARProof(result(0.8, null)).columnConfidence.displayValue).toBe('0.80')
  })

  it('is Not available when no detection was carried', () => {
    expect(extractARProof(result(null, null)).columnConfidence.displayValue).toBe('Not available')
  })
})
