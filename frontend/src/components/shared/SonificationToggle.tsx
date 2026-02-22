'use client'

/**
 * SonificationToggle — Sprint 407: Phase LVII
 *
 * Small speaker icon button for toggling data sonification.
 * Only renders when SONIFICATION feature flag is enabled.
 * Uses content-tertiary/sage-500 colors per Oat & Obsidian mandate.
 */

import { useSonification } from '@/hooks/useSonification'

export function SonificationToggle() {
  const { isMuted, toggleMute, enabled } = useSonification()

  if (!enabled) return null

  return (
    <button
      onClick={toggleMute}
      aria-label={isMuted ? 'Enable data sonification' : 'Mute data sonification'}
      title={isMuted ? 'Sound off' : 'Sound on'}
      className={`
        w-8 h-8 flex items-center justify-center rounded-lg
        transition-colors duration-150
        ${isMuted
          ? 'text-content-tertiary hover:text-content-secondary'
          : 'text-sage-500 hover:text-sage-600'
        }
        bg-surface-card/80 backdrop-blur-sm border border-theme
        hover:bg-surface-card
      `}
    >
      {isMuted ? (
        // Speaker muted icon
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
        </svg>
      ) : (
        // Speaker active icon
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M15.536 8.464a5 5 0 010 7.072M18.364 5.636a9 9 0 010 12.728" />
        </svg>
      )}
    </button>
  )
}
