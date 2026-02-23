'use client'

import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { ProfileDropdown } from '@/components/auth'
import { BrandIcon } from '@/components/shared/BrandIcon'
import { useCommandPalette } from '@/hooks/useCommandPalette'

export type ToolKey = 'tb-diagnostics' | 'multi-period' | 'je-testing' | 'ap-testing' | 'bank-rec' | 'payroll-testing' | 'three-way-match' | 'revenue-testing' | 'ar-aging' | 'fixed-assets' | 'inventory-testing' | 'statistical-sampling'

const TOOLS: { key: ToolKey; label: string; href: string }[] = [
  { key: 'tb-diagnostics', label: 'TB Diagnostics', href: '/tools/trial-balance' },
  { key: 'multi-period', label: 'Multi-Period', href: '/tools/multi-period' },
  { key: 'je-testing', label: 'JE Testing', href: '/tools/journal-entry-testing' },
  { key: 'ap-testing', label: 'AP Testing', href: '/tools/ap-testing' },
  { key: 'bank-rec', label: 'Bank Rec', href: '/tools/bank-rec' },
  { key: 'payroll-testing', label: 'Payroll', href: '/tools/payroll-testing' },
  { key: 'three-way-match', label: 'Three-Way Match', href: '/tools/three-way-match' },
  { key: 'revenue-testing', label: 'Revenue', href: '/tools/revenue-testing' },
  { key: 'ar-aging', label: 'AR Aging', href: '/tools/ar-aging' },
  { key: 'fixed-assets', label: 'Fixed Assets', href: '/tools/fixed-assets' },
  { key: 'inventory-testing', label: 'Inventory', href: '/tools/inventory-testing' },
  { key: 'statistical-sampling', label: 'Sampling', href: '/tools/statistical-sampling' },
]

/** Number of tools shown inline before overflow dropdown */
const INLINE_COUNT = 6

interface ToolNavProps {
  currentTool: ToolKey
  showBrandText?: boolean
}

/**
 * Shared navigation bar for all tool pages.
 * Shows first INLINE_COUNT tools inline, remaining in a "More" dropdown.
 *
 * Sprint 81: Extracted from 5 duplicated inline navbars.
 * Sprint 111: Overflow dropdown for 9+ tools.
 */
export function ToolNav({ currentTool, showBrandText }: ToolNavProps) {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()
  const { openPalette } = useCommandPalette()
  const [moreOpen, setMoreOpen] = useState(false)
  const moreRef = useRef<HTMLDivElement>(null)

  const inlineTools = TOOLS.slice(0, INLINE_COUNT)
  const overflowTools = TOOLS.slice(INLINE_COUNT)
  const currentInOverflow = overflowTools.some(t => t.key === currentTool)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreOpen(false)
      }
    }
    function handleEscapeKey(e: globalThis.KeyboardEvent) {
      if (e.key === 'Escape') setMoreOpen(false)
    }
    if (!moreOpen) return
      document.addEventListener('mousedown', handleClickOutside)
      document.addEventListener('keydown', handleEscapeKey)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
        document.removeEventListener('keydown', handleEscapeKey)
      }
  }, [moreOpen])

  const handleMoreKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      setMoreOpen(o => !o)
    } else if (e.key === 'Escape') {
      setMoreOpen(false)
    }
  }, [])

  function renderToolLink(tool: { key: ToolKey; label: string; href: string }, isDropdown = false) {
    const isCurrent = tool.key === currentTool
    if (isCurrent) {
      return (
        <span
          key={tool.key}
          className={`text-sm font-sans text-sage-400 ${isDropdown ? 'block px-3 py-1.5 bg-sage-500/10 rounded-lg' : 'border-b border-sage-400/50'}`}
        >
          {tool.label}
        </span>
      )
    }
    return (
      <Link
        key={tool.key}
        href={tool.href}
        onClick={() => setMoreOpen(false)}
        {...(isDropdown ? { role: 'menuitem' as const } : {})}
        className={`text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors ${isDropdown ? 'block px-3 py-1.5 rounded-lg hover:bg-obsidian-700/50' : ''}`}
      >
        {tool.label}
      </Link>
    )
  }

  return (
    <nav data-theme="dark" className="fixed top-0 w-full bg-obsidian-900/90 backdrop-blur-lg border-b border-obsidian-600/30 z-50">
      <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-3 group">
          {showBrandText ? (
            <>
              <div className="relative">
                <Image
                  src="/PaciolusLogo_DarkBG.png"
                  alt="Paciolus"
                  width={370}
                  height={510}
                  priority
                  className="h-10 w-auto max-h-10 object-contain transition-all duration-300 group-hover:logo-glow"
                  style={{ imageRendering: 'crisp-edges' }}
                />
                <div className="absolute inset-0 bg-sage-500/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10" />
              </div>
              <span className="text-xl font-bold font-serif text-oatmeal-200 tracking-tight group-hover:text-oatmeal-100 transition-colors">
                Paciolus
              </span>
            </>
          ) : (
            <Image
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              width={370}
              height={510}
              priority
              className="h-10 w-auto max-h-10 object-contain"
            />
          )}
        </Link>
        <div className="flex items-center gap-4">
          {inlineTools.map(tool => renderToolLink(tool))}

          {overflowTools.length > 0 && (
            <div ref={moreRef} className="relative">
              <button
                onClick={() => setMoreOpen(o => !o)}
                onKeyDown={handleMoreKeyDown}
                aria-expanded={moreOpen}
                aria-haspopup="menu"
                className={`text-sm font-sans transition-colors ${
                  currentInOverflow
                    ? 'text-sage-400 border-b border-sage-400/50'
                    : 'text-oatmeal-400 hover:text-oatmeal-200'
                }`}
              >
                More{currentInOverflow ? ` (${TOOLS.find(t => t.key === currentTool)?.label})` : ''}
                <BrandIcon name="chevron-down" className={`inline-block w-3 h-3 ml-1 transition-transform ${moreOpen ? 'rotate-180' : ''}`} />
              </button>
              {moreOpen && (
                <div role="menu" aria-label="Additional tools" className="absolute top-full right-0 mt-2 w-48 bg-obsidian-800 border border-obsidian-600/40 rounded-xl shadow-xl py-2 space-y-0.5">
                  {overflowTools.map(tool => renderToolLink(tool, true))}
                </div>
              )}
            </div>
          )}

          <Link
            href="/engagements"
            className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
          >
            Workspaces
          </Link>

          {/* Search trigger — Sprint 398 */}
          <button
            onClick={() => openPalette('button')}
            className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 text-xs font-sans text-oatmeal-500 bg-obsidian-800/60 border border-obsidian-600/30 rounded-lg hover:text-oatmeal-300 hover:border-obsidian-500/40 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <kbd className="text-[10px] font-mono bg-obsidian-700/60 border border-obsidian-600/30 rounded px-1 py-0.5">
              {typeof navigator !== 'undefined' && /Mac/.test(navigator.userAgent) ? '\u2318' : 'Ctrl'}+K
            </kbd>
          </button>

          <div className="ml-4 pl-4 border-l border-obsidian-600/30">
            {authLoading ? null : isAuthenticated && user ? (
              <ProfileDropdown user={user} onLogout={logout} />
            ) : (
              <Link
                href="/login"
                className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
