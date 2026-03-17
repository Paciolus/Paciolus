// Telemetry hook: all analytics event calls, keyed to animation state transitions.
'use client'

import { useCallback } from 'react'
import { trackEvent } from '@/utils/telemetry'
import type { FilmStep, OnStepChange } from './useHeroAnimation'

/**
 * Encapsulates all hero-film telemetry in a single hook.
 *
 * Returns:
 * - `onStepChange` — fire when the scrubber reaches a new step
 * - `trackCtaClick` — fire when a CTA button is clicked
 */
export function useHeroTelemetry() {
  const onStepChange: OnStepChange = useCallback((step: FilmStep) => {
    trackEvent('hero_step_reached', { step })
  }, [])

  const trackCtaClick = useCallback((cta: string) => {
    trackEvent('hero_cta_click', { cta })
  }, [])

  return { onStepChange, trackCtaClick }
}
