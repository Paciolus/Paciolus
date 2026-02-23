/**
 * useRegisterCommands — Sprint 396: Phase LV
 *
 * Registration hook for scoped commands. Registers on mount,
 * unregisters on unmount. Commands update when the array reference changes.
 */

import { useEffect, useRef } from 'react'
import { useCommandPaletteContext } from '@/contexts/CommandPaletteContext'
import type { PaletteCommand } from '@/types/commandPalette'

export function useRegisterCommands(scopeId: string, commands: PaletteCommand[]): void {
  const { registerCommands, unregisterCommands } = useCommandPaletteContext()
  const scopeIdRef = useRef(scopeId)

  useEffect(() => {
    scopeIdRef.current = scopeId
  }, [scopeId])

  useEffect(() => {
    const id = scopeIdRef.current
    if (commands.length > 0) {
      registerCommands(id, commands)
    }
    return () => {
      unregisterCommands(id)
    }
  }, [commands, registerCommands, unregisterCommands])
}
