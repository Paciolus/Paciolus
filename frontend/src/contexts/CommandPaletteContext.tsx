'use client'

/**
 * CommandPaletteContext — Sprint 396: Phase LV
 *
 * Global context for the universal command palette.
 * Manages open/close state, scoped command registration, and recency tracking.
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
  type ReactNode,
} from 'react'
import type { PaletteCommand } from '@/types/commandPalette'
import { BASE_COMMANDS } from '@/lib/commandRegistry'
import { trackEvent } from '@/utils/telemetry'

const RECENCY_KEY = 'paciolus_recent_commands'
const MAX_RECENT = 10

interface CommandPaletteContextType {
  isOpen: boolean
  openPalette: (source?: string) => void
  closePalette: () => void
  registerCommands: (scopeId: string, commands: PaletteCommand[]) => void
  unregisterCommands: (scopeId: string) => void
  recordRecentCommand: (id: string) => void
  getAllCommands: () => PaletteCommand[]
  recentIds: string[]
}

const CommandPaletteContext = createContext<CommandPaletteContextType | null>(null)

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

export function CommandPaletteProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [recentIds, setRecentIds] = useState<string[]>(loadRecentIds)
  const scopedCommandsRef = useRef<Map<string, PaletteCommand[]>>(new Map())

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
  }, [])

  const unregisterCommands = useCallback((scopeId: string) => {
    scopedCommandsRef.current.delete(scopeId)
  }, [])

  const recordRecentCommand = useCallback((id: string) => {
    setRecentIds(prev => {
      const next = [id, ...prev.filter(existing => existing !== id)].slice(0, MAX_RECENT)
      saveRecentIds(next)
      return next
    })
  }, [])

  const getAllCommands = useCallback((): PaletteCommand[] => {
    const scoped: PaletteCommand[] = []
    for (const commands of scopedCommandsRef.current.values()) {
      scoped.push(...commands)
    }
    return [...BASE_COMMANDS, ...scoped]
  }, [])

  return (
    <CommandPaletteContext.Provider
      value={{
        isOpen,
        openPalette,
        closePalette,
        registerCommands,
        unregisterCommands,
        recordRecentCommand,
        getAllCommands,
        recentIds,
      }}
    >
      {children}
    </CommandPaletteContext.Provider>
  )
}

export function useCommandPaletteContext(): CommandPaletteContextType {
  const ctx = useContext(CommandPaletteContext)
  if (!ctx) {
    throw new Error('useCommandPaletteContext must be used within CommandPaletteProvider')
  }
  return ctx
}
