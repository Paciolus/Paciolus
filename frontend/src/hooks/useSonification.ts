/**
 * useSonification — Sprint 407: Phase LVII
 *
 * React hook for data sonification. Checks feature flag + reduced motion.
 * Returns no-op functions when disabled.
 */

import { useCallback, useState } from 'react'
import { useFeatureFlag } from './useFeatureFlag'
import { useReducedMotion } from './useReducedMotion'
import { playTone as enginePlayTone, isMuted, setMuted, type ToneName } from '@/lib/sonification'

export interface UseSonificationReturn {
  playTone: (name: ToneName) => void
  isMuted: boolean
  toggleMute: () => void
  enabled: boolean
}

export function useSonification(): UseSonificationReturn {
  const flagOn = useFeatureFlag('SONIFICATION')
  const { prefersReducedMotion } = useReducedMotion()
  const [muted, setMutedState] = useState(() => isMuted())

  const enabled = flagOn && !prefersReducedMotion

  const play = useCallback((name: ToneName) => {
    if (!enabled) return
    enginePlayTone(name)
  }, [enabled])

  const toggleMute = useCallback(() => {
    const next = !muted
    setMuted(next)
    setMutedState(next)
  }, [muted])

  return {
    playTone: play,
    isMuted: muted,
    toggleMute,
    enabled,
  }
}
