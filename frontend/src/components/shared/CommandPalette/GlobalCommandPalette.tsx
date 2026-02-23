'use client'

/**
 * GlobalCommandPalette — Sprint 397: Phase LV
 *
 * Universal command palette rendered in providers.tsx, conditionally visible
 * when isOpen && isAuthenticated. Always dark themed (data-theme="dark")
 * matching ToolNav/CommandBar dark visual anchor pattern.
 *
 * Features:
 * - Fuzzy search across all commands (static + scoped)
 * - Grouped results by category
 * - Arrow Up/Down keyboard navigation, Enter to execute, Escape to close
 * - Recency tracking (sessionStorage, Zero-Storage compliant)
 * - Guard status: tier_blocked → navigate to /pricing, unverified → /verification-pending
 * - Focus trap (WCAG compliance)
 * - framer-motion enter/exit animation
 * - Telemetry: palette_open, palette_select, palette_dismiss, palette_empty_search
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { useCommandPaletteContext } from '@/contexts/CommandPaletteContext'
import { useFocusTrap } from '@/hooks/useFocusTrap'
import type { ScoredCommand, CommandCategory } from '@/types/commandPalette'
import { trackEvent } from '@/utils/telemetry'
import { scoreAndFilterCommands, COMMAND_HREFS } from '@/lib/commandRegistry'
import { CommandGroup } from './CommandGroup'
import { EmptyState } from './EmptyState'

const CATEGORY_ORDER: { key: CommandCategory; label: string }[] = [
  { key: 'tool', label: 'Tools' },
  { key: 'navigation', label: 'Navigation' },
  { key: 'workspace', label: 'Workspaces' },
  { key: 'action', label: 'Actions' },
  { key: 'settings', label: 'Settings' },
]

export function GlobalCommandPalette() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()
  const {
    isOpen,
    closePalette,
    getAllCommands,
    recentIds,
    recordRecentCommand,
  } = useCommandPaletteContext()

  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const containerRef = useFocusTrap(isOpen, closePalette)

  // Score and filter commands
  const allCommands = useMemo(() => {
    if (!isOpen) return []
    return getAllCommands()
  }, [isOpen, getAllCommands])

  const scored = useMemo(() => {
    return scoreAndFilterCommands(allCommands, query, recentIds, user ?? null)
  }, [allCommands, query, recentIds, user])

  // Group by category
  const groups = useMemo(() => {
    return CATEGORY_ORDER.map(cat => ({
      ...cat,
      items: scored.filter(sc => sc.command.category === cat.key),
    })).filter(g => g.items.length > 0)
  }, [scored])

  // Flat list for keyboard navigation
  const flatItems = useMemo(() => {
    const items: ScoredCommand[] = []
    for (const group of groups) {
      items.push(...group.items)
    }
    return items
  }, [groups])

  // Reset on open/query change
  useEffect(() => {
    setSelectedIndex(0)
  }, [query])

  useEffect(() => {
    if (isOpen) {
      setQuery('')
      setSelectedIndex(0)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [isOpen])

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return
    const items = listRef.current.querySelectorAll('[data-result-item]')
    const item = items[selectedIndex]
    if (item) {
      item.scrollIntoView({ block: 'nearest' })
    }
  }, [selectedIndex])

  const handleSelect = useCallback((index: number) => {
    const sc = flatItems[index]
    if (!sc) return

    if (sc.guardStatus === 'tier_blocked') {
      closePalette()
      router.push('/pricing')
      trackEvent('palette_select', { command: sc.command.id, blocked: 'tier' })
      return
    }

    if (sc.guardStatus === 'unverified') {
      closePalette()
      router.push('/verification-pending')
      trackEvent('palette_select', { command: sc.command.id, blocked: 'unverified' })
      return
    }

    recordRecentCommand(sc.command.id)
    trackEvent('palette_select', { command: sc.command.id, query })
    closePalette()

    // Execute: use href lookup if available, otherwise call action
    const href = COMMAND_HREFS[sc.command.id]
    if (href) {
      router.push(href)
    } else {
      sc.command.action()
    }
  }, [flatItems, closePalette, router, recordRecentCommand, query])

  const handleDismiss = useCallback(() => {
    trackEvent('palette_dismiss', { query_length: query.length })
    closePalette()
  }, [closePalette, query])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => Math.min(prev + 1, flatItems.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => Math.max(prev - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      handleSelect(selectedIndex)
    } else if (e.key === 'Escape') {
      e.preventDefault()
      handleDismiss()
    }
  }, [flatItems.length, selectedIndex, handleSelect, handleDismiss])

  // Track empty searches
  useEffect(() => {
    if (query.length >= 3 && flatItems.length === 0) {
      trackEvent('palette_empty_search', { query })
    }
  }, [query, flatItems.length])

  if (!isOpen || !isAuthenticated) return null

  // Compute flat offsets for each group
  let runningOffset = 0

  return (
    <AnimatePresence>
      <div
        data-theme="dark"
        className="fixed inset-0 z-[70] flex items-start justify-center pt-[15vh]"
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-obsidian-900/60 backdrop-blur-sm"
          onClick={handleDismiss}
        />

        {/* Palette panel */}
        <motion.div
          ref={containerRef}
          initial={{ opacity: 0, scale: 0.95 as const, y: -10 }}
          animate={{ opacity: 1, scale: 1 as const, y: 0 }}
          exit={{ opacity: 0, scale: 0.95 as const, y: -10 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-lg bg-obsidian-800 rounded-xl border border-obsidian-600/40 shadow-xl overflow-hidden"
          role="dialog"
          aria-label="Command palette"
          onKeyDown={handleKeyDown}
        >
          {/* Search input */}
          <div className="px-4 py-3 border-b border-obsidian-600/30 flex items-center gap-3">
            <svg className="w-4 h-4 text-oatmeal-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent text-sm font-sans text-oatmeal-200 placeholder:text-oatmeal-500 outline-none"
            />
            <kbd className="text-[10px] font-mono text-oatmeal-500 px-1.5 py-0.5 bg-obsidian-700/60 border border-obsidian-600/30 rounded">
              Esc
            </kbd>
          </div>

          {/* Results */}
          <div ref={listRef} className="max-h-[50vh] overflow-y-auto">
            {flatItems.length === 0 ? (
              <EmptyState query={query} />
            ) : (
              <>
                {groups.map(group => {
                  const offset = runningOffset
                  runningOffset += group.items.length
                  return (
                    <CommandGroup
                      key={group.key}
                      category={group.key}
                      label={group.label}
                      items={group.items}
                      selectedIndex={selectedIndex}
                      flatOffset={offset}
                      onSelect={handleSelect}
                      onHover={setSelectedIndex}
                    />
                  )
                })}
              </>
            )}
          </div>

          {/* Footer hints */}
          <div className="px-4 py-2 border-t border-obsidian-600/30 bg-obsidian-800/80 flex items-center gap-4">
            <span className="text-[9px] font-sans text-oatmeal-500 flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-obsidian-700/60 rounded border border-obsidian-600/30 text-[8px] font-mono">{'\u2191\u2193'}</kbd>
              Navigate
            </span>
            <span className="text-[9px] font-sans text-oatmeal-500 flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-obsidian-700/60 rounded border border-obsidian-600/30 text-[8px] font-mono">{'\u21B5'}</kbd>
              Select
            </span>
            <span className="text-[9px] font-sans text-oatmeal-500 flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-obsidian-700/60 rounded border border-obsidian-600/30 text-[8px] font-mono">Esc</kbd>
              Close
            </span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
