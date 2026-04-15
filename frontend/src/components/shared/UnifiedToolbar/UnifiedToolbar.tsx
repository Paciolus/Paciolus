'use client'

/**
 * UnifiedToolbar — Sprint 499
 *
 * Three-zone toolbar following professional SaaS conventions (Figma/Linear/Stripe):
 *   Zone 1 — Left (Identity): Logo only
 *   Zone 2 — Center (Primary Nav): Icon+label links, Tools mega-dropdown
 *   Zone 3 — Right (User/System): Icon-only search, settings, avatar
 *
 * Background preserved: marble-textured oatmeal with glassmorphism.
 * Mobile: Collapses to hamburger with slide-out drawer.
 */

import { useState, useCallback } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { ProfileDropdown } from '@/components/auth/ProfileDropdown'
import { BrandIcon } from '@/components/shared/BrandIcon'
import { useCommandPalette } from '@/hooks/useCommandPalette'
import { MegaDropdown } from './MegaDropdown'
import { TOOLBAR_NAV, TOOL_COLUMNS, ACCOUNT_NAV, ALL_TOOL_HREFS } from './toolbarConfig'

/** framer-motion variants for mobile drawer */
const drawerContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.04, delayChildren: 0.05 },
  },
  exit: { opacity: 0, transition: { duration: 0.15 } },
} as const

const drawerItemVariants = {
  hidden: { opacity: 0, x: -12 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.2 } },
  exit: { opacity: 0, x: -12 },
} as const

export function UnifiedToolbar() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuthSession()
  const { openPalette } = useCommandPalette()
  const pathname = usePathname()
  const [megaOpen, setMegaOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const closeMobile = useCallback(() => setMobileOpen(false), [])
  const closeMega = useCallback(() => setMegaOpen(false), [])

  const isToolActive = ALL_TOOL_HREFS.some(
    href => pathname === href || pathname.startsWith(href + '/')
  )

  function isActive(href: string) {
    return pathname === href || pathname.startsWith(href + '/')
  }

  /** Shared class builder for Zone 2 nav items — bottom-border active indicator */
  function navItemClass(active: boolean) {
    return `flex items-center gap-1.5 px-3 h-full text-sm font-sans transition-colors border-b-2 ${
      active
        ? 'border-sage-600 text-sage-700 font-semibold'
        : 'border-transparent text-obsidian-500 hover:text-obsidian-700'
    }`
  }

  const isMac = typeof navigator !== 'undefined' && /Mac/.test(navigator.userAgent)

  return (
    <nav
      aria-label="Primary navigation"
      className="fixed top-0 w-full toolbar-marble bg-oatmeal-100/95 backdrop-blur-lg border-b border-oatmeal-300/60 z-50"
      style={{ height: 'var(--toolbar-height, 56px)' }}
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:bg-sage-600 focus:text-oatmeal-50 focus:rounded-lg focus:text-sm focus:font-sans focus:font-medium"
      >
        Skip to main content
      </a>
      <div className="max-w-7xl mx-auto px-6 h-full flex items-center">
        {/* ═══ Zone 1 — Left: Identity ═══ */}
        <div className="w-[120px] flex-shrink-0">
          <Link href="/dashboard" className="flex items-center">
            <Image
              src="/PaciolusLogo_LightBG.png"
              alt="Paciolus"
              width={370}
              height={510}
              priority
              className="h-8 w-auto max-h-8 object-contain"
              style={{ imageRendering: 'crisp-edges' }}
            />
          </Link>
        </div>

        {/* ═══ Zone 2 — Center: Primary Nav ═══ */}
        <div className="hidden md:flex flex-1 items-center justify-center h-full gap-1">
          {/* Dashboard — first (highest frequency) */}
          <Link href="/dashboard" className={navItemClass(isActive('/dashboard'))}>
            <BrandIcon name="bar-chart" className="w-4 h-4" />
            <span>Dashboard</span>
          </Link>

          {/* Tools mega-dropdown trigger */}
          <div className="relative h-full">
            <button
              onClick={() => setMegaOpen(o => !o)}
              aria-expanded={megaOpen}
              aria-haspopup="menu"
              className={navItemClass(megaOpen || isToolActive)}
            >
              <BrandIcon name="cube" className="w-4 h-4" />
              <span>Tools</span>
              <BrandIcon
                name="chevron-down"
                className={`w-3 h-3 transition-transform duration-200 ${megaOpen ? 'rotate-180' : ''}`}
              />
            </button>
            <MegaDropdown isOpen={megaOpen} onClose={closeMega} />
          </div>

          {/* Workspaces, Portfolio, History */}
          {TOOLBAR_NAV.filter(item => item.href !== '/dashboard').map(item => (
            <Link
              key={item.href}
              href={item.href}
              className={navItemClass(isActive(item.href))}
            >
              {item.icon && <BrandIcon name={item.icon} className="w-4 h-4" />}
              <span>{item.label}</span>
            </Link>
          ))}
        </div>

        {/* ═══ Zone 3 — Right: User/System ═══ */}
        <div className="hidden md:flex items-center gap-1 w-[120px] justify-end flex-shrink-0">
          {/* Search — icon-only */}
          <button
            onClick={() => openPalette('button')}
            title={`Search (${isMac ? '\u2318' : 'Ctrl'}+K)`}
            aria-label="Open command palette"
            className="w-9 h-9 flex items-center justify-center rounded-lg text-obsidian-400 hover:text-obsidian-600 hover:bg-oatmeal-200/60 transition-colors"
          >
            <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>

          {/* Settings — icon-only */}
          <Link
            href="/settings"
            title="Settings"
            aria-label="Settings"
            className="w-9 h-9 flex items-center justify-center rounded-lg text-obsidian-400 hover:text-obsidian-600 hover:bg-oatmeal-200/60 transition-colors"
          >
            <BrandIcon name="sliders" className="w-[18px] h-[18px]" />
          </Link>

          {/* Profile avatar / Sign In — icon-only */}
          {authLoading ? null : isAuthenticated && user ? (
            <ProfileDropdown user={user} onLogout={logout} />
          ) : (
            <Link
              href="/login"
              title="Sign In"
              aria-label="Sign in"
              className="w-9 h-9 flex items-center justify-center rounded-lg text-obsidian-400 hover:text-obsidian-600 hover:bg-oatmeal-200/60 transition-colors"
            >
              <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </Link>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen(o => !o)}
          className="md:hidden ml-auto flex flex-col justify-center items-center w-9 h-9 gap-[5px] rounded-lg hover:bg-oatmeal-200/60 transition-colors"
          aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={mobileOpen}
        >
          <span
            className={`block w-5 h-[2px] bg-obsidian-700 rounded-full transition-transform duration-200 ${
              mobileOpen ? 'rotate-45 translate-y-[7px]' : ''
            }`}
          />
          <span
            className={`block w-5 h-[2px] bg-obsidian-700 rounded-full transition-all duration-200 ${
              mobileOpen ? 'opacity-0 scale-x-0' : ''
            }`}
          />
          <span
            className={`block w-5 h-[2px] bg-obsidian-700 rounded-full transition-transform duration-200 ${
              mobileOpen ? '-rotate-45 -translate-y-[7px]' : ''
            }`}
          />
        </button>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            variants={drawerContainerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="md:hidden fixed inset-x-0 top-[var(--toolbar-height,56px)] bottom-0 bg-oatmeal-50/98 backdrop-blur-xl overflow-y-auto z-40"
          >
            <div className="px-6 py-4 space-y-6">
              {/* Navigation links with icons */}
              <motion.div variants={drawerItemVariants}>
                <h3 className="font-serif text-xs font-semibold text-content-secondary uppercase tracking-wider mb-2">
                  Navigation
                </h3>
                <div className="space-y-1">
                  {TOOLBAR_NAV.map(item => (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={closeMobile}
                      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-sans transition-colors ${
                        isActive(item.href)
                          ? 'text-sage-700 bg-sage-50 font-medium'
                          : 'text-content-primary hover:bg-oatmeal-100'
                      }`}
                    >
                      {item.icon && <BrandIcon name={item.icon} className="w-4 h-4" />}
                      <span>{item.label}</span>
                    </Link>
                  ))}
                </div>
              </motion.div>

              {/* Tool columns — stacked */}
              {TOOL_COLUMNS.map(col => (
                <motion.div key={col.heading} variants={drawerItemVariants}>
                  <h3 className="font-serif text-xs font-semibold text-content-secondary uppercase tracking-wider mb-2">
                    {col.heading}
                  </h3>
                  <div className="space-y-1">
                    {col.items.map(item => (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={closeMobile}
                        className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-sans transition-colors ${
                          isActive(item.href)
                            ? 'text-sage-700 bg-sage-50 font-medium'
                            : 'text-content-primary hover:bg-oatmeal-100'
                        }`}
                      >
                        <span>{item.label}</span>
                      </Link>
                    ))}
                  </div>
                </motion.div>
              ))}

              {/* Account nav */}
              <motion.div variants={drawerItemVariants}>
                <h3 className="font-serif text-xs font-semibold text-content-secondary uppercase tracking-wider mb-2">
                  Account
                </h3>
                <div className="space-y-1">
                  {ACCOUNT_NAV.map(item => (
                    <div key={item.href}>
                      {item.dividerAbove && (
                        <div className="border-t border-oatmeal-200/60 my-2" />
                      )}
                      <Link
                        href={item.href}
                        onClick={closeMobile}
                        className={`block px-3 py-2.5 rounded-lg text-sm font-sans transition-colors ${
                          isActive(item.href)
                            ? 'text-sage-700 bg-sage-50 font-medium'
                            : 'text-content-primary hover:bg-oatmeal-100'
                        }`}
                      >
                        {item.label}
                      </Link>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Auth section */}
              <motion.div variants={drawerItemVariants} className="pt-2 border-t border-oatmeal-200/60">
                {authLoading ? null : isAuthenticated && user ? (
                  <div className="space-y-3">
                    <div className="flex items-center gap-3 px-3">
                      <div className="w-8 h-8 rounded-full bg-sage-500/20 border border-sage-500/40 flex items-center justify-center">
                        <span className="text-sm font-sans font-medium text-sage-700">
                          {user.email.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <span className="text-sm text-content-secondary font-sans truncate">
                        {user.email}
                      </span>
                    </div>
                    <button
                      onClick={() => { closeMobile(); logout() }}
                      className="w-full px-3 py-2.5 text-left rounded-lg text-sm font-sans text-clay-600 hover:bg-clay-50 transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Link
                      href="/login"
                      onClick={closeMobile}
                      className="block px-3 py-2.5 text-center rounded-lg text-sm font-sans font-medium text-obsidian-700 border border-oatmeal-300 hover:bg-oatmeal-100 transition-colors"
                    >
                      Sign In
                    </Link>
                    <Link
                      href="/register"
                      onClick={closeMobile}
                      className="block px-3 py-2.5 text-center rounded-lg text-sm font-sans font-medium text-oatmeal-50 bg-sage-600 hover:bg-sage-700 transition-colors"
                    >
                      Start Free Trial
                    </Link>
                  </div>
                )}
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
