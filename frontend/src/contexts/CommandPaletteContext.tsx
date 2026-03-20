'use client'

/**
 * CommandPaletteContext — Split into state + actions contexts
 *
 * CommandPaletteStateContext   — isOpen, recentIds (volatile, changes on open/close)
 * CommandPaletteActionsContext — stable callbacks + memoized command list
 *
 * Backward-compatible useCommandPaletteContext() merges both.
 *
 * Recency persisted to sessionStorage (command IDs only — Zero-Storage compliant).
 * Global Cmd+K listener via direct document.addEventListener (NOT useKeyboardShortcuts,
 * because meta+K must fire even when focused on an input field).
 */

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  useMemo,
  type ReactNode,
} from 'react'
import type { PaletteCommand } from '@/types/commandPalette'
import { trackEvent } from '@/utils/telemetry'
import { BASE_COMMANDS } from '@/lib/commandRegistry'

const RECENCY_KEY = 'paciolus_recent_commands'
const MAX_RECENT = 10

// =============================================================================
// Sub-context types
// =============================================================================

interface CommandPaletteStateContextType {
  isOpen: boolean
  recentIds: string[]
}

interface CommandPaletteActionsContextType {
  openPalette: (source?: string) => void
  closePalette: () => void
  registerCommands: (scopeId: string, commands: PaletteCommand[]) => void
  unregisterCommands: (scopeId: string) => void
  recordRecentCommand: (id: string) => void
  getAllCommands: () => PaletteCommand[]
}

// Combined type (backward compatibility)
interface CommandPaletteContextType
  extends CommandPaletteStateContextType,
    CommandPaletteActionsContextType {}

// =============================================================================
// Contexts
// =============================================================================

const CommandPaletteStateContext = createContext<CommandPaletteStateContextType | null>(null)
const CommandPaletteActionsContext = createContext<CommandPaletteActionsContextType | null>(null)

// =============================================================================
// Helpers
// =============================================================================

function loadRecentIds(): string[] {
  if (typeof window === 'undefined') return []
  try {
    const raw = sessionStorage.getItem(RECENCY_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
      return parsed.slice(0, MAX_RECENT)
    }
    return []
  } catch {
    return []
  }
}

function saveRecentIds(ids: string[]): void {
  if (typeof window === 'undefined') return
  try {
    sessionStorage.setItem(RECENCY_KEY, JSON.stringify(ids.slice(0, MAX_RECENT)))
  } catch {
    // sessionStorage unavailable — non-critical
  }
}

// =============================================================================
// Provider
// =============================================================================

export function CommandPaletteProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [recentIds, setRecentIds] = useState<string[]>(loadRecentIds)
  const scopedCommandsRef = useRef<Map<string, PaletteCommand[]>>(new Map())
  const [scopedCommandsVersion, setScopedCommandsVersion] = useState(0)

  // Global Cmd+K listener — must fire even from input fields
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        e.stopPropagation()
        setIsOpen(prev => {
          const next = !prev
          if (next) {
            trackEvent('palette_open', { source: 'keyboard' })
          }
          return next
        })
      }
    }

    document.addEventListener('keydown', handleKeyDown, { capture: true })
    return () => {
      document.removeEventListener('keydown', handleKeyDown, { capture: true })
    }
  }, [])

  const openPalette = useCallback((source?: string) => {
    setIsOpen(true)
    trackEvent('palette_open', { source: source ?? 'unknown' })
  }, [])

  const closePalette = useCallback(() => {
    setIsOpen(false)
  }, [])

  const registerCommands = useCallback((scopeId: string, commands: PaletteCommand[]) => {
    scopedCommandsRef.current.set(scopeId, commands)
    setScopedCommandsVersion(v => v + 1)
  }, [])

  const unregisterCommands = useCallback((scopeId: string) => {
    scopedCommandsRef.current.delete(scopeId)
    setScopedCommandsVersion(v => v + 1)
  }, [])

  const recordRecentCommand = useCallback((id: string) => {
    setRecentIds(prev => {
      const next = [id, ...prev.filter(existing => existing !== id)].slice(0, MAX_RECENT)
      saveRecentIds(next)
      return next
    })
  }, [])

  // Memoized command list — recomputed only when scoped commands change
  const allCommands = useMemo((): PaletteCommand[] => {
    const scoped: PaletteCommand[] = []
    for (const commands of scopedCommandsRef.current.values()) {
      scoped.push(...commands)
    }
    return [...BASE_COMMANDS, ...scoped]
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scopedCommandsVersion])

  const getAllCommands = useCallback((): PaletteCommand[] => allCommands, [allCommands])

  // --- Memoized context values ---
  const stateValue = useMemo<CommandPaletteStateContextType>(() => ({
    isOpen,
    recentIds,
  }), [isOpen, recentIds])

  const actionsValue = useMemo<CommandPaletteActionsContextType>(() => ({
    openPalette,
    closePalette,
    registerCommands,
    unregisterCommands,
    recordRecentCommand,
    getAllCommands,
  }), [openPalette, closePalette, registerCommands, unregisterCommands, recordRecentCommand, getAllCommands])

  return (
    <CommandPaletteActionsContext.Provider value={actionsValue}>
      <CommandPaletteStateContext.Provider value={stateValue}>
        {children}
      </CommandPaletteStateContext.Provider>
    </CommandPaletteActionsContext.Provider>
  )
}

// =============================================================================
// Granular hooks
// =============================================================================

export function useCommandPaletteState(): CommandPaletteStateContextType {
  const ctx = useContext(CommandPaletteStateContext)
  if (!ctx) {
    throw new Error('useCommandPaletteState must be used within CommandPaletteProvider')
  }
  return ctx
}

export function useCommandPaletteActions(): CommandPaletteActionsContextType {
  const ctx = useContext(CommandPaletteActionsContext)
  if (!ctx) {
    throw new Error('useCommandPaletteActions must be used within CommandPaletteProvider')
  }
  return ctx
}

// =============================================================================
// Backward-compatible combined hook
// =============================================================================

export function useCommandPaletteContext(): CommandPaletteContextType {
  const state = useContext(CommandPaletteStateContext)
  const actions = useContext(CommandPaletteActionsContext)
  if (!state || !actions) {
    throw new Error('useCommandPaletteContext must be used within CommandPaletteProvider')
  }
  return { ...state, ...actions }
}
