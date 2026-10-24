/**
 * Sprint 839: per-run inputs send the right form fields, and empty inputs
 * send nothing (so the saved setting or Paciolus default applies).
 */
import { validateBankRecThresholds } from '@/components/bankRec/BankRecRunSettings'
import { computeTWMRunOverrides, twmBaseline } from '@/components/threeWayMatch/TWMRunSettings'
import { buildBankRecFormData } from '@/hooks/useBankReconciliation'
import { buildThreeWayMatchFormData } from '@/hooks/useThreeWayMatch'
import { DEFAULT_THREE_WAY_MATCH_CONFIG } from '@/types/settings'
import { parseRunInput } from '@/utils/runSettingInput'

const file = (name: string) => new File(['x'], name, { type: 'text/csv' })

function fieldNames(fd: FormData): string[] {
  return Array.from(fd.keys()).sort()
}

describe('parseRunInput', () => {
  it('treats empty as not set', () => {
    expect(parseRunInput('  ', { label: 'X' })).toEqual({ value: undefined, error: null })
  })
  it('accepts dollar formatting for currency fields', () => {
    expect(parseRunInput('$25,000.50', { label: 'X', currency: true }).value).toBe(25000.5)
  })
  it('rejects negatives, junk, fractions for whole-number fields and out-of-range values', () => {
    expect(parseRunInput('-1', { label: 'Materiality' }).error).toBe('Materiality must be 0 or more.')
    expect(parseRunInput('12abc', { label: 'X' }).error).toBe('X must be a number.')
    expect(parseRunInput('1e5', { label: 'X' }).error).toBe('X must be a number.')
    expect(parseRunInput('2.5', { label: 'Days', integer: true }).error).toBe('Days must be a whole number.')
    expect(parseRunInput('400', { label: 'Days', max: 365 }).error).toBe('Days must be between 0 and 365.')
  })
})

describe('bank reconciliation', () => {
  it('sends only the files when no threshold is entered', () => {
    const { thresholds, valid } = validateBankRecThresholds({ materiality: '', performanceMateriality: '' })
    expect(valid).toBe(true)
    expect(fieldNames(buildBankRecFormData(file('b.csv'), file('l.csv'), thresholds))).toEqual(['bank_file', 'ledger_file'])
  })

  it('sends materiality and performance materiality as plain numbers', () => {
    const { thresholds } = validateBankRecThresholds({ materiality: '$75,000', performanceMateriality: '56250' })
    const fd = buildBankRecFormData(file('b.csv'), file('l.csv'), thresholds)
    expect(fd.get('materiality')).toBe('75000')
    expect(fd.get('performance_materiality')).toBe('56250')
  })

  it('sends only the threshold that was entered', () => {
    const { thresholds } = validateBankRecThresholds({ materiality: '', performanceMateriality: '10000' })
    const fd = buildBankRecFormData(file('b.csv'), file('l.csv'), thresholds)
    expect(fd.has('materiality')).toBe(false)
    expect(fd.get('performance_materiality')).toBe('10000')
  })

  it('flags negative values and performance materiality above materiality', () => {
    expect(validateBankRecThresholds({ materiality: '-5', performanceMateriality: '' }).errors.materiality)
      .toBe('Materiality must be 0 or more.')
    const crossed = validateBankRecThresholds({ materiality: '10000', performanceMateriality: '20000' })
    expect(crossed.valid).toBe(false)
    expect(crossed.errors.performanceMateriality).toBe('Performance materiality cannot exceed materiality.')
  })
})

describe('three-way match', () => {
  it('sends only the files when nothing was changed', () => {
    const { overrides, valid } = computeTWMRunOverrides({}, twmBaseline(null))
    expect(valid).toBe(true)
    expect(overrides).toEqual({})
    expect(fieldNames(buildThreeWayMatchFormData(file('po.csv'), file('i.csv'), file('r.csv'), overrides)))
      .toEqual(['invoice_file', 'po_file', 'receipt_file'])
  })

  it('sends changed fields in engine units (percentages as fractions)', () => {
    const { overrides } = computeTWMRunOverrides(
      { fuzzy_composite_threshold: '80', date_window_days: '45', quantity_tolerance: '2', enable_fuzzy_matching: false },
      twmBaseline(null),
    )
    const fd = buildThreeWayMatchFormData(file('po.csv'), file('i.csv'), file('r.csv'), overrides)
    expect(fd.get('fuzzy_composite_threshold')).toBe('0.8')
    expect(fd.get('date_window_days')).toBe('45')
    expect(fd.get('quantity_tolerance')).toBe('2')
    expect(fd.get('enable_fuzzy_matching')).toBe('false')
    expect(fd.has('amount_tolerance')).toBe(false)
  })

  it('sends a value the user entered even when it equals the prefill (PR #230 review)', () => {
    const saved = twmBaseline({ ...DEFAULT_THREE_WAY_MATCH_CONFIG, price_variance_threshold: 0.1 })
    const { overrides } = computeTWMRunOverrides({ price_variance_threshold: '10', amount_tolerance: '0.01' }, saved)
    expect(overrides).toEqual({ price_variance_threshold: 0.1, amount_tolerance: 0.01 })
  })

  it('sends every displayed value when asked to (saved settings unavailable)', () => {
    const { overrides } = computeTWMRunOverrides({}, twmBaseline(null), { sendAll: true })
    expect(Object.keys(overrides)).toHaveLength(7)
    expect(overrides.date_window_days).toBe(DEFAULT_THREE_WAY_MATCH_CONFIG.date_window_days)
  })

  it('compares against saved settings, so a change back to the engine default is sent', () => {
    const saved = twmBaseline({ ...DEFAULT_THREE_WAY_MATCH_CONFIG, date_window_days: 60 })
    expect(computeTWMRunOverrides({ date_window_days: '30' }, saved).overrides).toEqual({ date_window_days: 30 })
  })

  it('ignores saved values of the wrong type in the prefill', () => {
    const baseline = twmBaseline({ date_window_days: 'soon' as unknown as number, amount_tolerance: 5 })
    expect(baseline.date_window_days).toBe(DEFAULT_THREE_WAY_MATCH_CONFIG.date_window_days)
    expect(baseline.amount_tolerance).toBe(5)
  })

  it('blocks a run with an unusable or cleared field', () => {
    const result = computeTWMRunOverrides({ date_window_days: '400', amount_tolerance: '' }, twmBaseline(null))
    expect(result.valid).toBe(false)
    expect(result.errors.date_window_days).toBe('Date window must be between 0 and 365.')
    expect(result.errors.amount_tolerance).toMatch(/Enter a value for amount tolerance/)
  })
})
