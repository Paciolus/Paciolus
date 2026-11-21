/**
 * Sprint 652: useFeatureFlag hook test — verifies the thin wrapper
 * around the static FLAG_REGISTRY. Registry defaults are load-bearing
 * for the premium UI gate, so drift here ships hidden features.
 */
import { renderHook } from '@testing-library/react'
import { useFeatureFlag } from '@/hooks/useFeatureFlag'

describe('useFeatureFlag', () => {
  it('returns true for flags enabled in the registry', () => {
    // SONIFICATION ships on per src/lib/featureFlags.ts.
    const { result } = renderHook(() => useFeatureFlag('SONIFICATION'))
    expect(result.current).toBe(true)
  })

  it('returns false for a name that is not in the registry', () => {
    // Sprint 891: the off-by-default FORMAT_ODS flag was removed (formats come from the backend).
    const { result } = renderHook(() => useFeatureFlag('NOT_A_FLAG' as never))
    expect(result.current).toBe(false)
  })

  it('re-renders idempotent — same flag returns the same value across calls', () => {
    const first = renderHook(() => useFeatureFlag('INSIGHT_MICROCOPY'))
    const second = renderHook(() => useFeatureFlag('INSIGHT_MICROCOPY'))
    expect(first.result.current).toBe(second.result.current)
  })
})
