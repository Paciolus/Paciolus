'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspaceContext, type WorkspaceView } from '@/contexts/WorkspaceContext';
import { ProfileDropdown } from '@/components/auth';
import { useCommandPalette } from '@/hooks/useCommandPalette';

/**
 * CommandBar — Sprint 385: Phase LII Foundation
 *
 * Top navigation bar for the unified workspace shell.
 * Dark theme (matching ToolNav pattern via data-theme="dark").
 *
 * Left: Logo + brand text
 * Center: Tab nav — "Client Portfolio" | "Diagnostic Workspace"
 * Right: Search trigger (Cmd+K hint) + ProfileDropdown
 */

const TABS: { key: WorkspaceView; label: string; href: string }[] = [
  { key: 'portfolio', label: 'Client Portfolio', href: '/portfolio' },
  { key: 'engagements', label: 'Diagnostic Workspace', href: '/engagements' },
];

export function CommandBar() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const { currentView, activeClient } = useWorkspaceContext();
  const { openPalette } = useCommandPalette();

  return (
    <nav
      data-theme="dark"
      className="fixed top-0 w-full bg-obsidian-900/90 backdrop-blur-lg border-b border-obsidian-600/30 z-50"
    >
      <div className="max-w-[1440px] mx-auto px-6 py-3 flex items-center justify-between">
        {/* Left: Logo + brand */}
        <div className="flex items-center gap-3 min-w-0">
          <Link href="/" className="flex items-center gap-3 group shrink-0">
            <div className="relative">
              <Image
                src="/PaciolusLogo_DarkBG.png"
                alt="Paciolus"
                width={370}
                height={510}
                priority
                className="h-9 w-auto max-h-9 object-contain transition-all duration-300 group-hover:logo-glow"
                style={{ imageRendering: 'crisp-edges' }}
              />
              <div className="absolute inset-0 bg-sage-500/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10" />
            </div>
            <span className="text-lg font-bold font-serif text-oatmeal-200 tracking-tight group-hover:text-oatmeal-100 transition-colors hidden sm:block">
              Paciolus
            </span>
          </Link>

          {/* Breadcrumb (when client selected) */}
          {activeClient && (
            <div className="hidden md:flex items-center gap-2 ml-4 pl-4 border-l border-obsidian-600/30 min-w-0">
              <span className="text-xs font-sans text-oatmeal-500 shrink-0">
                {currentView === 'portfolio' ? 'Portfolio' : 'Workspace'}
              </span>
              <svg className="w-3 h-3 text-oatmeal-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <span className="text-xs font-sans text-oatmeal-300 truncate">
                {activeClient.name}
              </span>
            </div>
          )}
        </div>

        {/* Center: Tab nav */}
        <div className="hidden sm:flex items-center gap-1">
          {TABS.map((tab) => {
            const isActive = currentView === tab.key;
            return (
              <Link
                key={tab.key}
                href={tab.href}
                className={`
                  px-4 py-1.5 text-sm font-sans rounded-lg transition-colors
                  ${isActive
                    ? 'text-sage-400 bg-sage-500/10'
                    : 'text-oatmeal-400 hover:text-oatmeal-200 hover:bg-obsidian-700/50'
                  }
                `}
              >
                {tab.label}
                {isActive && (
                  <span className="block h-0.5 bg-sage-400/50 rounded-full mt-0.5" />
                )}
              </Link>
            );
          })}
        </div>

        {/* Right: Search + Profile */}
        <div className="flex items-center gap-3">
          {/* Search trigger */}
          <button
            onClick={() => openPalette('button')}
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 text-xs font-sans text-oatmeal-500 bg-obsidian-800/60 border border-obsidian-600/30 rounded-lg hover:text-oatmeal-300 hover:border-obsidian-500/40 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span>Search</span>
            <kbd className="ml-1 px-1.5 py-0.5 text-[10px] font-mono bg-obsidian-700/60 border border-obsidian-600/30 rounded-sm">
              {typeof navigator !== 'undefined' && /Mac/.test(navigator.userAgent) ? '\u2318' : 'Ctrl'}+K
            </kbd>
          </button>

          {/* Profile dropdown */}
          <div className="pl-3 border-l border-obsidian-600/30">
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
  );
}
