'use client'

/**
 * MegaDropdown — Sprint 475
 *
 * 4-column click-triggered dropdown for the UnifiedToolbar.
 * Columns: Core Analysis | Testing Suite | Advanced | Account
 * Focus trap, Escape close, arrow key navigation.
 */

import { useRef, useEffect, useCallback, useState, type KeyboardEvent } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import { fadeScale } from '@/lib/motion'
import {
  TOOL_COLUMNS,
  ACCOUNT_NAV,
  TIER_BADGE_STYLES,
  type ToolItem,
  type NavItem,
} from './toolbarConfig'

interface MegaDropdownProps {
  isOpen: boolean
  onClose: () => void
}

export function MegaDropdown({ isOpen, onClose }: MegaDropdownProps) {
  const panelRef = useRef<HTMLDivElement>(null)
  const pathname = usePathname()
  const [focusIndex, setFocusIndex] = useState(-1)

  // Collect all focusable items for keyboard nav
  const allItems = useRef<HTMLAnchorElement[]>([])

  const collectRefs = useCallback(() => {
    if (!panelRef.current) return
    allItems.current = Array.from(
      panelRef.current.querySelectorAll<HTMLAnchorElement>('a[role="menuitem"]')
    )
  }, [])

  // Close on Escape + click-outside
  useEffect(() => {
    if (!isOpen) return

    function handleEscape(e: globalThis.KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('keydown', handleEscape)
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, onClose])

  // Reset focus index when opening
  useEffect(() => {
    if (isOpen) {
      setFocusIndex(-1)
      // Collect refs after render
      requestAnimationFrame(collectRefs)
    }
  }, [isOpen, collectRefs])

  // Focus management
  useEffect(() => {
    if (focusIndex >= 0 && allItems.current[focusIndex]) {
      allItems.current[focusIndex].focus()
    }
  }, [focusIndex])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      collectRefs()
      const total = allItems.current.length
      if (!total) return

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setFocusIndex(i => (i + 1) % total)
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setFocusIndex(i => (i - 1 + total) % total)
      } else if (e.key === 'Home') {
        e.preventDefault()
        setFocusIndex(0)
      } else if (e.key === 'End') {
        e.preventDefault()
        setFocusIndex(total - 1)
      }
    },
    [collectRefs]
  )

  function isActive(href: string) {
    return pathname === href || pathname.startsWith(href + '/')
  }

  function renderToolItem(item: ToolItem) {
    const active = isActive(item.href)
    const badgeStyle = TIER_BADGE_STYLES[item.tier]

    return (
      <Link
        key={item.href}
        href={item.href}
        role="menuitem"
        onClick={onClose}
        className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-sans transition-colors ${
          active
            ? 'text-sage-700 bg-sage-50 font-medium'
            : 'text-content-primary hover:bg-oatmeal-100/80 hover:text-obsidian-800'
        }`}
      >
        <span className="flex-1">{item.label}</span>
        <span
          className={`px-1.5 py-0.5 rounded text-[10px] font-medium leading-none border ${badgeStyle}`}
        >
          {item.tier}
        </span>
      </Link>
    )
  }

  function renderNavItem(item: NavItem) {
    const active = isActive(item.href)

    return (
      <div key={item.href}>
        {item.dividerAbove && (
          <div className="border-t border-oatmeal-200/60 my-2" />
        )}
        <Link
          href={item.href}
          role="menuitem"
          onClick={onClose}
          className={`block px-3 py-2 rounded-lg text-sm font-sans transition-colors ${
            active
              ? 'text-sage-700 bg-sage-50 font-medium'
              : 'text-content-primary hover:bg-oatmeal-100/80 hover:text-obsidian-800'
          }`}
        >
          {item.label}
        </Link>
      </div>
    )
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          role="menu"
          aria-label="Tools and navigation"
          variants={fadeScale}
          initial="hidden"
          animate="visible"
          exit="exit"
          onKeyDown={handleKeyDown}
          className="fixed left-1/2 -translate-x-1/2 w-[min(calc(100vw-2rem),64rem)] bg-white/95 backdrop-blur-xl border border-oatmeal-200/80 rounded-2xl shadow-theme-elevated z-50 overflow-hidden"
          style={{ transformOrigin: 'top center', top: 'calc(var(--toolbar-height, 56px) + 4px)' }}
        >
          <div className="grid grid-cols-4 gap-0 p-5">
            {/* Tool columns */}
            {TOOL_COLUMNS.map((col, colIdx) => (
              <div
                key={col.heading}
                className={`px-3 ${colIdx < TOOL_COLUMNS.length - 1 ? 'border-r border-oatmeal-200/50' : ''}`}
              >
                <h3 className="font-serif text-xs font-semibold text-content-secondary uppercase tracking-wider mb-3 px-3">
                  {col.heading}
                </h3>
                <div className="space-y-0.5">
                  {col.items.map(renderToolItem)}
                </div>
              </div>
            ))}

            {/* Account column */}
            <div className="px-3 border-l border-oatmeal-200/50">
              <h3 className="font-serif text-xs font-semibold text-content-secondary uppercase tracking-wider mb-3 px-3">
                Account
              </h3>
              <div className="space-y-0.5">
                {ACCOUNT_NAV.map(renderNavItem)}
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
