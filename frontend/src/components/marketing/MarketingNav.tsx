'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useAuth } from '@/contexts/AuthContext'
import { ProfileDropdown } from '@/components/auth'

const navLinks = [
  { label: 'Platform', href: '/#tools' },
  { label: 'Pricing', href: '/pricing' },
  { label: 'Trust', href: '/trust' },
  { label: 'About', href: '/about' },
  { label: 'Contact', href: '/contact' },
]

/**
 * Shared marketing navigation bar for public pages.
 * Simplified nav (5 links) vs homepage tool nav (11 links).
 * Dark themed, fixed position, auth-aware.
 */
export function MarketingNav() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav className={`fixed top-0 w-full backdrop-blur-lg border-b z-50 transition-all duration-300 ${
      scrolled
        ? 'bg-obsidian-900/95 border-obsidian-600/40 shadow-lg shadow-obsidian-900/50'
        : 'bg-obsidian-900/60 border-obsidian-600/20'
    }`}>
      <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <Image
            src="/PaciolusLogo_DarkBG.png"
            alt="Paciolus"
            width={370}
            height={510}
            className="h-10 w-auto max-h-10 object-contain"
          />
        </Link>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              {link.label}
            </Link>
          ))}
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

        {/* Mobile Hamburger */}
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
          aria-expanded={mobileOpen}
          aria-label="Toggle navigation menu"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-obsidian-600/30 bg-obsidian-900/95 backdrop-blur-lg">
          <div className="px-6 py-4 space-y-3">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="block text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors py-2"
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-3 border-t border-obsidian-600/30">
              {authLoading ? null : isAuthenticated && user ? (
                <ProfileDropdown user={user} onLogout={logout} />
              ) : (
                <Link
                  href="/login"
                  onClick={() => setMobileOpen(false)}
                  className="block text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors py-2"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}
