'use client'

import { useState, useEffect, useCallback } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { ProfileDropdown } from '@/components/auth'

/**
 * MarketingNav — Sprint 338 Redesign
 *
 * Premium marketing navigation with strategic link architecture:
 * - Solutions: Platform + Pricing (what we sell)
 * - Company: About + Approach + Contact (who we are)
 * - Trust: Trust & Security (why trust us)
 *
 * Features:
 * - Scroll-triggered backdrop intensification
 * - Underline-slide hover on desktop links
 * - Smooth mobile drawer with staggered links
 * - Auth-aware: ProfileDropdown when logged in, Sign In + Get Started when not
 */

interface NavLink {
  label: string
  href: string
}

const NAV_LINKS: NavLink[] = [
  { label: 'Platform', href: '/#tools' },
  { label: 'Demo', href: '/demo' },
  { label: 'Pricing', href: '/pricing' },
  { label: 'About', href: '/about' },
  { label: 'Trust', href: '/trust' },
  { label: 'Contact', href: '/contact' },
]

const mobileItemVariants = {
  hidden: { opacity: 0, x: -12 },
  visible: { opacity: 1, x: 0 },
}

const mobileContainerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.04, delayChildren: 0.05 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
}

export function MarketingNav() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const closeMobile = useCallback(() => setMobileOpen(false), [])

  return (
    <nav
      className={`fixed top-0 w-full z-50 transition-all duration-500 ${
        scrolled
          ? 'bg-obsidian-900/95 backdrop-blur-xl border-b border-obsidian-500/30 shadow-lg shadow-obsidian-900/60'
          : 'bg-obsidian-900/40 backdrop-blur-md border-b border-transparent'
      }`}
    >
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 shrink-0 group">
            <Image
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              width={370}
              height={510}
              className="h-9 w-auto max-h-9 object-contain transition-opacity group-hover:opacity-80"
            />
            <span className="text-lg font-serif font-semibold text-oatmeal-100 tracking-wide transition-opacity group-hover:opacity-80">
              Paciolus
            </span>
          </Link>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="relative px-3 py-2 text-sm font-sans text-oatmeal-400 hover:text-oatmeal-100 transition-colors duration-200 group"
              >
                {link.label}
                {/* Underline slide */}
                <span className="absolute bottom-0.5 left-3 right-3 h-px bg-sage-500 scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
              </Link>
            ))}

            {/* Auth Section */}
            <div className="ml-3 pl-4 border-l border-obsidian-500/30 flex items-center gap-3">
              {!authLoading && isAuthenticated && user ? (
                <ProfileDropdown user={user} onLogout={logout} />
              ) : (
                <>
                  <Link
                    href="/login"
                    className="px-4 py-1.5 text-sm font-sans font-medium text-oatmeal-200 rounded-lg bg-obsidian-700/50 backdrop-blur-md border border-oatmeal-200/10 shadow-lg shadow-black/30 hover:bg-obsidian-600/60 hover:border-oatmeal-200/20 hover:shadow-xl hover:shadow-black/40 transition-all duration-200"
                    style={{ boxShadow: 'inset 0 1px 0 0 rgba(255,255,255,0.06), 0 4px 12px -2px rgba(0,0,0,0.3)' }}
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/register"
                    className="px-4 py-1.5 text-sm font-sans font-medium text-white rounded-lg bg-sage-600/70 backdrop-blur-md border border-sage-400/20 shadow-lg shadow-sage-900/30 hover:bg-sage-500/80 hover:border-sage-400/30 hover:shadow-xl hover:shadow-sage-900/40 transition-all duration-200"
                    style={{ boxShadow: 'inset 0 1px 0 0 rgba(255,255,255,0.1), 0 4px 12px -2px rgba(74,124,89,0.3)' }}
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Mobile Hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden relative w-10 h-10 flex items-center justify-center text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            aria-expanded={mobileOpen}
            aria-label="Toggle navigation menu"
          >
            <div className="w-5 h-4 relative flex flex-col justify-between">
              <span
                className={`block h-px bg-current transform transition-all duration-300 origin-center ${
                  mobileOpen ? 'rotate-45 translate-y-[7.5px]' : ''
                }`}
              />
              <span
                className={`block h-px bg-current transition-all duration-200 ${
                  mobileOpen ? 'opacity-0 scale-x-0' : 'opacity-100'
                }`}
              />
              <span
                className={`block h-px bg-current transform transition-all duration-300 origin-center ${
                  mobileOpen ? '-rotate-45 -translate-y-[7.5px]' : ''
                }`}
              />
            </div>
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            variants={mobileContainerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="md:hidden border-t border-obsidian-500/30 bg-obsidian-900/98 backdrop-blur-xl"
          >
            <div className="px-6 py-5 space-y-1">
              {NAV_LINKS.map((link) => (
                <motion.div key={link.href} variants={mobileItemVariants}>
                  <Link
                    href={link.href}
                    onClick={closeMobile}
                    className="block px-3 py-2.5 text-sm font-sans text-oatmeal-400 hover:text-oatmeal-100 hover:bg-obsidian-800/50 rounded-lg transition-colors"
                  >
                    {link.label}
                  </Link>
                </motion.div>
              ))}

              {/* Auth in mobile */}
              <motion.div
                variants={mobileItemVariants}
                className="pt-3 mt-2 border-t border-obsidian-500/30"
              >
                {!authLoading && isAuthenticated && user ? (
                  <ProfileDropdown user={user} onLogout={logout} />
                ) : (
                  <div className="space-y-2">
                    <Link
                      href="/login"
                      onClick={closeMobile}
                      className="block text-center px-3 py-2.5 text-sm font-sans font-medium text-oatmeal-200 rounded-lg bg-obsidian-700/50 backdrop-blur-md border border-oatmeal-200/10 shadow-lg shadow-black/30 hover:bg-obsidian-600/60 hover:border-oatmeal-200/20 transition-all duration-200"
                      style={{ boxShadow: 'inset 0 1px 0 0 rgba(255,255,255,0.06), 0 4px 12px -2px rgba(0,0,0,0.3)' }}
                    >
                      Sign In
                    </Link>
                    <Link
                      href="/register"
                      onClick={closeMobile}
                      className="block text-center px-3 py-2.5 text-sm font-sans font-medium text-white rounded-lg bg-sage-600/70 backdrop-blur-md border border-sage-400/20 shadow-lg shadow-sage-900/30 hover:bg-sage-500/80 hover:border-sage-400/30 transition-all duration-200"
                      style={{ boxShadow: 'inset 0 1px 0 0 rgba(255,255,255,0.1), 0 4px 12px -2px rgba(74,124,89,0.3)' }}
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
