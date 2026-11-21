/**
 * Feature Flag Registry
 *
 * Static boolean flag registry for premium features.
 * Follows the USE_BESPOKE_ICONS pattern from constants.ts but with
 * a typed, centralized lookup via isFeatureEnabled().
 *
 * All flags default OFF — features are muted by default.
 * Toggle to true to enable during development or for specific builds.
 */

export type FeatureFlag =
  | 'SONIFICATION'
  | 'INSIGHT_MICROCOPY'

const FLAG_REGISTRY: Record<FeatureFlag, boolean> = {
  /** Web Audio API tones on upload/success/error/export */
  SONIFICATION: true,
  /** AI-style contextual messages in InsightRail */
  INSIGHT_MICROCOPY: true,
  // Sprint 891 (16D): INTELLIGENCE_WATERMARK (nothing read it) and FORMAT_ODS (enabled formats now come
  // from the backend's GET /upload/capabilities) were removed.
}

/**
 * Check whether a feature flag is enabled.
 * Returns false for unknown keys (type-safe at compile time,
 * runtime guard for dynamic strings).
 */
export function isFeatureEnabled(flag: FeatureFlag): boolean {
  return FLAG_REGISTRY[flag] ?? false
}
