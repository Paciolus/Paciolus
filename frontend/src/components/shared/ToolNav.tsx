'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { ProfileDropdown } from '@/components/auth'

export type ToolKey = 'tb-diagnostics' | 'multi-period' | 'je-testing' | 'ap-testing' | 'bank-rec' | 'payroll-testing' | 'three-way-match' | 'revenue-testing' | 'ar-aging' | 'fixed-assets' | 'inventory-testing'

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
    if (moreOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [moreOpen])

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
        className={`text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors ${isDropdown ? 'block px-3 py-1.5 rounded-lg hover:bg-obsidian-700/50' : ''}`}
      >
        {tool.label}
      </Link>
    )
  }

  return (
    <nav className="fixed top-0 w-full bg-obsidian-900/90 backdrop-blur-lg border-b border-obsidian-600/30 z-50">
      <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
        <Link href="/" className="flex items-center gap-3 group">
          {showBrandText ? (
            <>
              <div className="relative">
                <img
                  src="/PaciolusLogo_DarkBG.png"
                  alt="Paciolus"
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
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
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
                className={`text-sm font-sans transition-colors ${
                  currentInOverflow
                    ? 'text-sage-400 border-b border-sage-400/50'
                    : 'text-oatmeal-400 hover:text-oatmeal-200'
                }`}
              >
                More{currentInOverflow ? ` (${TOOLS.find(t => t.key === currentTool)?.label})` : ''}
                <svg className={`inline-block w-3 h-3 ml-1 transition-transform ${moreOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {moreOpen && (
                <div className="absolute top-full right-0 mt-2 w-48 bg-obsidian-800 border border-obsidian-600/40 rounded-xl shadow-xl py-2 space-y-0.5">
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
