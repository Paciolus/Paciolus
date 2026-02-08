'use client'

import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { ProfileDropdown } from '@/components/auth'

export type ToolKey = 'tb-diagnostics' | 'multi-period' | 'je-testing' | 'ap-testing' | 'bank-rec' | 'payroll-testing' | 'three-way-match'

const TOOLS: { key: ToolKey; label: string; href: string }[] = [
  { key: 'tb-diagnostics', label: 'TB Diagnostics', href: '/tools/trial-balance' },
  { key: 'multi-period', label: 'Multi-Period', href: '/tools/multi-period' },
  { key: 'je-testing', label: 'JE Testing', href: '/tools/journal-entry-testing' },
  { key: 'ap-testing', label: 'AP Testing', href: '/tools/ap-testing' },
  { key: 'bank-rec', label: 'Bank Rec', href: '/tools/bank-rec' },
  { key: 'payroll-testing', label: 'Payroll Testing', href: '/tools/payroll-testing' },
  { key: 'three-way-match', label: 'Three-Way Match', href: '/tools/three-way-match' },
]

interface ToolNavProps {
  currentTool: ToolKey
  showBrandText?: boolean
}

/**
 * Shared navigation bar for all tool pages.
 * Highlights the active tool, renders auth controls.
 *
 * Sprint 81: Extracted from 5 duplicated inline navbars.
 */
export function ToolNav({ currentTool, showBrandText }: ToolNavProps) {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()

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
          {TOOLS.map(tool =>
            tool.key === currentTool ? (
              <span key={tool.key} className="text-sm font-sans text-sage-400 border-b border-sage-400/50">
                {tool.label}
              </span>
            ) : (
              <Link
                key={tool.key}
                href={tool.href}
                className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
              >
                {tool.label}
              </Link>
            )
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
