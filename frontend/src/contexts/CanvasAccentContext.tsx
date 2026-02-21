'use client'

/**
 * CanvasAccentContext — lightweight context for tool accent state
 *
 * Provides { accentState, setAccentState } to tool pages.
 * Wrapped in tools/layout.tsx. Tools call setAccentState()
 * when their upload hook status changes.
 * Tools that don't call it get 'idle' by default.
 */

import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { AccentState } from '@/components/shared/IntelligenceCanvas'

interface CanvasAccentContextValue {
  accentState: AccentState
  setAccentState: (state: AccentState) => void
}

const CanvasAccentContext = createContext<CanvasAccentContextValue | null>(null)

export function CanvasAccentProvider({ children }: { children: ReactNode }) {
  const [accentState, setAccentStateRaw] = useState<AccentState>('idle')

  const setAccentState = useCallback((state: AccentState) => {
    setAccentStateRaw(state)
  }, [])

  return (
    <CanvasAccentContext.Provider value={{ accentState, setAccentState }}>
      {children}
    </CanvasAccentContext.Provider>
  )
}

/**
 * Hook for tool pages to read/write accent state.
 * Returns null-safe — pages outside CanvasAccentProvider get idle defaults.
 */
export function useCanvasAccent(): CanvasAccentContextValue {
  const ctx = useContext(CanvasAccentContext)
  if (!ctx) {
    return { accentState: 'idle', setAccentState: () => {} }
  }
  return ctx
}
