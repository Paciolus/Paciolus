/**
 * Feature Flag Registry — Sprint 406: Phase LVII
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
  | 'INTELLIGENCE_WATERMARK'
  | 'FORMAT_ODS'

const FLAG_REGISTRY: Record<FeatureFlag, boolean> = {
  /** Web Audio API tones on upload/success/error/export */
  SONIFICATION: true,
  /** AI-style contextual messages in InsightRail */
  INSIGHT_MICROCOPY: true,
  /** "Paciolus Intelligence" stamp on PDF exports */
  INTELLIGENCE_WATERMARK: true,
  /** ODS file format upload support (Sprint 436 — off by default) */
  FORMAT_ODS: false,
}

/**
 * Check whether a feature flag is enabled.
 * Returns false for unknown keys (type-safe at compile time,
 * runtime guard for dynamic strings).
 */
export function isFeatureEnabled(flag: FeatureFlag): boolean {
  return FLAG_REGISTRY[flag] ?? false
}
