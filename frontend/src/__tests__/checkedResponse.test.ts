/**
 * Sprint 890 (CEO brief 15C): upload responses are checked against the published schema's
 * required keys instead of being cast.
 */
import { RESPONSE_REQUIRED_KEYS } from '@/types/generated/responseRequiredKeys'
import { checkedResponse, ResponseShapeError } from '@/utils/checkedResponse'

describe('checkedResponse', () => {
  it('passes a response that has every required key', () => {
    const body = { composite_score: {}, test_results: [] }
    expect(checkedResponse('/audit/journal-entries', body)).toBe(body)
  })

  it('names the missing keys', () => {
    expect(() => checkedResponse('/audit/journal-entries', { test_results: [] })).toThrow(ResponseShapeError)
    try {
      checkedResponse('/audit/journal-entries', { test_results: [] })
    } catch (e) {
      expect((e as ResponseShapeError).missing).toEqual(['composite_score'])
    }
  })

  it('refuses a body that is not an object', () => {
    expect(() => checkedResponse('/audit/ap-payments', null)).toThrow(ResponseShapeError)
    expect(() => checkedResponse('/audit/ap-payments', [])).toThrow(ResponseShapeError)
  })

  it('covers every upload hook endpoint', () => {
    for (const endpoint of [
      '/audit/ap-payments', '/audit/ar-aging', '/audit/bank-reconciliation', '/audit/fixed-assets',
      '/audit/inventory-testing', '/audit/journal-entries', '/audit/payroll-testing',
      '/audit/revenue-testing', '/audit/three-way-match',
    ]) {
      expect(RESPONSE_REQUIRED_KEYS[endpoint]?.length).toBeGreaterThan(0)
    }
  })
})
