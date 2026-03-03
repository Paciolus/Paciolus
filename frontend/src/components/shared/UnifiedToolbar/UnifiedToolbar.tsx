'use client'

/**
 * UnifiedToolbar — Sprint 475
 *
 * Single light-themed toolbar replacing ToolNav, CommandBar, and all
 * standalone page navs. Marble-textured oatmeal background, "Tools"
 * mega-dropdown trigger, direct nav links, Cmd+K search, ProfileDropdown.
 *
 * Mobile: Collapses to hamburger with slide-out drawer.
 */

import { useState, useCallback } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { ProfileDropdown } from '@/components/auth/ProfileDropdown'
import { BrandIcon } from '@/components/shared/BrandIcon'
import { useCommandPalette } from '@/hooks/useCommandPalette'
import { MegaDropdown } from './MegaDropdown'
import { TOOLBAR_NAV, TOOL_COLUMNS, ACCOUNT_NAV, ALL_TOOL_HREFS, TIER_BADGE_STYLES } from './toolbarConfig'

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
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()
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

  return (
    <nav
      className="fixed top-0 w-full toolbar-marble bg-oatmeal-100/95 backdrop-blur-lg border-b border-oatmeal-300/60 z-50"
      style={{ height: 'var(--toolbar-height, 56px)' }}
    >
      <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
        {/* Left: Logo */}
        <Link href="/dashboard" className="flex items-center gap-3 group flex-shrink-0">
          <Image
            src="/PaciolusLogo_LightBG.png"
            alt="Paciolus"
            width={370}
            height={510}
            priority
            className="h-9 w-auto max-h-9 object-contain"
            style={{ imageRendering: 'crisp-edges' }}
          />
          <span className="text-lg font-bold font-serif text-obsidian-800 tracking-tight hidden sm:block">
            Paciolus
          </span>
        </Link>

        {/* Center: Desktop nav */}
        <div className="hidden md:flex items-center gap-1 ml-8">
          {/* Tools dropdown trigger */}
          <div className="relative">
            <button
              onClick={() => setMegaOpen(o => !o)}
              aria-expanded={megaOpen}
              aria-haspopup="menu"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-sans font-medium transition-colors ${
                megaOpen || isToolActive
                  ? 'text-sage-700 bg-sage-50'
                  : 'text-obsidian-700 hover:text-obsidian-900 hover:bg-oatmeal-200/60'
              }`}
            >
              Tools
              <BrandIcon
                name="chevron-down"
                className={`w-3.5 h-3.5 transition-transform duration-200 ${megaOpen ? 'rotate-180' : ''}`}
              />
            </button>
            <MegaDropdown isOpen={megaOpen} onClose={closeMega} />
          </div>

          {/* Direct nav links */}
          {TOOLBAR_NAV.map(item => (
            <Link
              key={item.href}
              href={item.href}
              className={`px-3 py-2 rounded-lg text-sm font-sans font-medium transition-colors ${
                isActive(item.href)
                  ? 'text-sage-700 bg-sage-50'
                  : 'text-obsidian-700 hover:text-obsidian-900 hover:bg-oatmeal-200/60'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>

        {/* Right: Search + Profile */}
        <div className="flex items-center gap-3">
          {/* Cmd+K search trigger */}
          <button
            onClick={() => openPalette('button')}
            className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 text-xs font-sans text-obsidian-500 bg-oatmeal-200/60 border border-oatmeal-300/50 rounded-lg hover:text-obsidian-700 hover:bg-oatmeal-200 hover:border-oatmeal-300 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <kbd className="text-[10px] font-mono bg-white/60 border border-oatmeal-300/40 rounded-sm px-1 py-0.5">
              {typeof navigator !== 'undefined' && /Mac/.test(navigator.userAgent) ? '\u2318' : 'Ctrl'}+K
            </kbd>
          </button>

          {/* Profile / Sign In */}
          <div className="hidden md:block">
            {authLoading ? null : isAuthenticated && user ? (
              <ProfileDropdown user={user} onLogout={logout} />
            ) : (
              <Link
                href="/login"
                className="text-sm font-sans font-medium text-obsidian-700 hover:text-sage-700 transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(o => !o)}
            className="md:hidden flex flex-col justify-center items-center w-9 h-9 gap-[5px] rounded-lg hover:bg-oatmeal-200/60 transition-colors"
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
              {/* Tool columns in mobile — stacked */}
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
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium leading-none border ${TIER_BADGE_STYLES[item.tier]}`}>
                          {item.tier}
                        </span>
                      </Link>
                    ))}
                  </div>
                </motion.div>
              ))}

              {/* Account nav in mobile */}
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

              {/* Auth section in mobile */}
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
                      className="block px-3 py-2.5 text-center rounded-lg text-sm font-sans font-medium text-white bg-sage-600 hover:bg-sage-700 transition-colors"
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
