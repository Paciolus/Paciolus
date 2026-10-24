/**
 * Sprint 839: the bank-rec and three-way-match hooks hand their per-run
 * values to the upload's FormData builder.
 */
import { renderHook } from '@testing-library/react'
import { useBankReconciliation } from '@/hooks/useBankReconciliation'
import { useThreeWayMatch } from '@/hooks/useThreeWayMatch'

const captured: { buildFormData?: (...files: File[]) => FormData; endpoint?: string } = {}

jest.mock('@/hooks/useAuditUpload', () => ({
  useAuditUpload: jest.fn((options: { buildFormData: (...files: File[]) => FormData; endpoint: string }) => {
    captured.buildFormData = options.buildFormData
    captured.endpoint = options.endpoint
    return { status: 'idle', result: null, error: '', run: jest.fn(), reset: jest.fn() }
  }),
}))

const file = (name: string) => new File(['x'], name, { type: 'text/csv' })

describe('useBankReconciliation', () => {
  it('appends entered thresholds', () => {
    renderHook(() => useBankReconciliation({ materiality: 40000, performanceMateriality: 30000 }))
    expect(captured.endpoint).toBe('/audit/bank-reconciliation')
    const fd = captured.buildFormData!(file('b.csv'), file('l.csv'))
    expect(fd.get('materiality')).toBe('40000')
    expect(fd.get('performance_materiality')).toBe('30000')
    expect(fd.get('bank_file')).toBeInstanceOf(File)
  })

  it('sends no threshold fields without input', () => {
    renderHook(() => useBankReconciliation())
    const fd = captured.buildFormData!(file('b.csv'), file('l.csv'))
    expect(fd.has('materiality')).toBe(false)
    expect(fd.has('performance_materiality')).toBe(false)
  })
})

describe('useThreeWayMatch', () => {
  it('appends only the supplied overrides', () => {
    renderHook(() => useThreeWayMatch({ amount_tolerance: 5, enable_fuzzy_matching: false }))
    expect(captured.endpoint).toBe('/audit/three-way-match')
    const fd = captured.buildFormData!(file('po.csv'), file('i.csv'), file('r.csv'))
    expect(fd.get('amount_tolerance')).toBe('5')
    expect(fd.get('enable_fuzzy_matching')).toBe('false')
    expect(fd.has('date_window_days')).toBe(false)
    expect(fd.get('receipt_file')).toBeInstanceOf(File)
  })

  it('sends no override fields without input', () => {
    renderHook(() => useThreeWayMatch())
    const fd = captured.buildFormData!(file('po.csv'), file('i.csv'), file('r.csv'))
    expect(Array.from(fd.keys()).sort()).toEqual(['invoice_file', 'po_file', 'receipt_file'])
  })
})
