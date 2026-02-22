/**
 * Feature Flag Tests — Sprint 406: Phase LVII
 */

import { isFeatureEnabled, type FeatureFlag } from '@/lib/featureFlags'

describe('isFeatureEnabled', () => {
  it('returns a boolean for SONIFICATION', () => {
    const result = isFeatureEnabled('SONIFICATION')
    expect(typeof result).toBe('boolean')
  })

  it('returns a boolean for INSIGHT_MICROCOPY', () => {
    const result = isFeatureEnabled('INSIGHT_MICROCOPY')
    expect(typeof result).toBe('boolean')
  })

  it('returns a boolean for INTELLIGENCE_WATERMARK', () => {
    const result = isFeatureEnabled('INTELLIGENCE_WATERMARK')
    expect(typeof result).toBe('boolean')
  })

  it('returns false for unknown keys cast at runtime', () => {
    // Runtime safety: dynamic string that bypasses compile-time check
    const result = isFeatureEnabled('NONEXISTENT_FLAG' as FeatureFlag)
    expect(result).toBe(false)
  })
})
