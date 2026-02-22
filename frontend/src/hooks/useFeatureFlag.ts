/**
 * useFeatureFlag — Sprint 406: Phase LVII
 *
 * Thin React hook wrapper around the static feature flag registry.
 */

import { isFeatureEnabled, type FeatureFlag } from '@/lib/featureFlags'

export function useFeatureFlag(flag: FeatureFlag): boolean {
  return isFeatureEnabled(flag)
}
