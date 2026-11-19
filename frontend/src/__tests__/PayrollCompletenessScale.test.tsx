/**
 * Sprint 886 (review OUT-14): payroll completeness arrives on the 0–100 scale
 * every tool uses, and the badge and proof summary show exactly that figure
 * (the API used to send 0–1, so complete data showed as 1%).
 */
import { PayrollDataQualityBadge } from '@/components/payrollTesting/PayrollDataQualityBadge'
import { extractPayrollProof } from '@/components/shared/proof/proofAdapters'
import type { PayrollTestingResult } from '@/types/payrollTesting'
import { render, screen } from '@/test-utils'

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ initial, animate, exit, transition, variants, whileHover, whileInView, whileTap, viewport, layout, layoutId, style, children, ...rest }: any) =>
      <div {...rest} style={style}>{children}</div>,
  },
}))
jest.mock('@/utils/marketingMotion', () => ({
  CountUp: ({ target, suffix }: any) => <span>{target}{suffix || ''}</span>,
}))

const quality = (pct: number) => ({ completeness_score: pct, field_fill_rates: {}, detected_issues: [], total_rows: 20 })

describe.each([0, 50, 100])('payroll completeness %i%%', (pct) => {
  it('badge shows exactly that percentage', () => {
    render(<PayrollDataQualityBadge quality={quality(pct) as never} />)
    expect(screen.getByText(`${pct}%`)).toBeInTheDocument()
  })

  it('proof summary shows exactly that percentage', () => {
    const result = {
      composite_score: { tests_run: 13, total_flagged: 0, total_entries: 20 },
      test_results: [],
      data_quality: quality(pct),
      column_detection: { overall_confidence: 1 },
      filename: 'pr',
    } as unknown as PayrollTestingResult
    expect(extractPayrollProof(result).dataCompleteness.displayValue).toBe(`${pct}%`)
  })
})
