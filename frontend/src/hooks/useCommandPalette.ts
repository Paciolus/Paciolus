/**
 * useCommandPalette — Sprint 396: Phase LV
 *
 * Consumer hook for the command palette. Provides open/close controls
 * without exposing full context internals.
 */

import { useCommandPaletteContext } from '@/contexts/CommandPaletteContext'

export function useCommandPalette() {
  const { isOpen, openPalette, closePalette } = useCommandPaletteContext()
  return { isOpen, openPalette, closePalette }
}
