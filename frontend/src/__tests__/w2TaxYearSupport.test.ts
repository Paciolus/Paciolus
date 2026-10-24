/**
 * Sprint 839: the backend's unsupported-tax-year refusal becomes a message a
 * preparer can act on; other errors pass through unchanged.
 */
import { describeW2Error, unsupportedTaxYearMessage } from '@/components/w2Reconciliation/taxYearSupport'

const REFUSAL =
  'No statutory limit table for tax year 2026. Tables available: 2025. Supply the figures for your filing year ' +
  'via the `statutory_limits` override, or wait for the 2026 table to be added with practitioner-confirmed figures.'

describe('describeW2Error', () => {
  it('rewrites the unsupported-year refusal without API jargon', () => {
    const message = describeW2Error(REFUSAL, 2026)!
    expect(message).toContain('Tax year 2026 cannot be reconciled in the app yet')
    expect(message).toContain('only for tax year 2025')
    expect(message).not.toContain('statutory_limits')
  })

  it('lists every year the backend names', () => {
    const message = describeW2Error(REFUSAL.replace('Tables available: 2025.', 'Tables available: 2024, 2025.'), 2026)!
    expect(message).toContain('only for tax years 2024, 2025')
  })

  it('passes other errors through', () => {
    expect(describeW2Error('Tolerance must be a number', 2025)).toBe('Tolerance must be a number')
    expect(describeW2Error(undefined, 2025)).toBeUndefined()
  })
})

describe('unsupportedTaxYearMessage', () => {
  it('handles an empty list', () => {
    expect(unsupportedTaxYearMessage(2026, [])).toContain('only for no tax year yet')
  })
})
