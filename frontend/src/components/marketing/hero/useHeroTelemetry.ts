'use client'

import { useCallback, useEffect, useState } from 'react'
import { trackEvent } from '@/utils/telemetry'

/** Hero CTA telemetry (Sprint 861: the film's step events went with the film). */
export function useHeroTelemetry() {
  const trackCtaClick = useCallback((cta: string) => {
    trackEvent('hero_cta_click', { cta })
  }, [])

  return { trackCtaClick }
}

/** Hydration guard — auth-dependent CTAs render only after mount. */
export function useHasMounted() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  return mounted
}
