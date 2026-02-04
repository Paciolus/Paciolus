'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'

interface User {
  email: string
}

interface ProfileDropdownProps {
  user: User
  onLogout: () => void
}

/**
 * ProfileDropdown - Day 13 Navbar Component
 *
 * Premium dropdown for logged-in users following Oat & Obsidian design.
 * Features Paciolus logo, user greeting, and logout option.
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function ProfileDropdown({ user, onLogout }: ProfileDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Truncate long emails for display
  const displayEmail = user.email.length > 24
    ? user.email.slice(0, 21) + '...'
    : user.email

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Close dropdown on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  const handleLogout = () => {
    setIsOpen(false)
    onLogout()
  }

  // Animation variants
  const dropdownVariants = {
    hidden: {
      opacity: 0,
      y: -8,
      scale: 0.95,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: 'spring' as const,
        stiffness: 400,
        damping: 25,
      },
    },
    exit: {
      opacity: 0,
      y: -8,
      scale: 0.95,
      transition: {
        duration: 0.15,
      },
    },
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-all ${
          isOpen
            ? 'bg-obsidian-700 border border-sage-500/50'
            : 'hover:bg-obsidian-700/50 border border-transparent'
        }`}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {/* User Avatar */}
        <div className="w-8 h-8 rounded-full bg-sage-500/20 border border-sage-500/40 flex items-center justify-center">
          <span className="text-sage-400 font-sans font-bold text-sm">
            {user.email.charAt(0).toUpperCase()}
          </span>
        </div>

        {/* Chevron */}
        <svg
          className={`w-4 h-4 text-oatmeal-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className="absolute right-0 mt-2 w-72 bg-obsidian-800 border border-obsidian-600 rounded-xl shadow-2xl overflow-hidden z-50"
            variants={dropdownVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            {/* Header with Logo */}
            <div className="px-4 py-4 border-b border-obsidian-700 bg-obsidian-700/30">
              <div className="flex items-center gap-3 mb-3">
                <img
                  src="/PaciolusLogo_LightBG.png"
                  alt="Paciolus"
                  className="h-8 w-auto object-contain"
                  style={{ imageRendering: 'crisp-edges' }}
                />
                <div className="h-6 w-px bg-obsidian-600"></div>
                <span className="text-sm font-serif font-bold text-oatmeal-300">
                  Vault Access
                </span>
              </div>

              {/* User Greeting */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-sage-500/20 border border-sage-500/40 flex items-center justify-center flex-shrink-0">
                  <span className="text-sage-400 font-sans font-bold">
                    {user.email.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="text-oatmeal-200 font-sans font-medium text-sm">
                    Welcome back
                  </p>
                  <p className="text-oatmeal-500 font-sans text-sm truncate" title={user.email}>
                    {displayEmail}
                  </p>
                </div>
              </div>
            </div>

            {/* Menu Items */}
            <div className="py-2">
              {/* Zero-Storage Badge */}
              <div className="px-4 py-2 mb-1">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-sage-500/10 border border-sage-500/20">
                  <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse"></div>
                  <span className="text-sage-300 text-xs font-sans font-medium">
                    Zero-Storage Active
                  </span>
                </div>
              </div>

              {/* Client Portfolio Link (Sprint 17) */}
              <Link
                href="/portfolio"
                onClick={() => setIsOpen(false)}
                className="w-full px-4 py-2 text-left hover:bg-obsidian-700/50 transition-colors block"
              >
                <div className="flex items-center gap-3 px-2">
                  <svg
                    className="w-5 h-5 text-oatmeal-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
                    />
                  </svg>
                  <span className="font-sans text-sm text-oatmeal-300">Client Portfolio</span>
                </div>
              </Link>

              {/* Diagnostic History Link (Sprint 18) */}
              <Link
                href="/history"
                onClick={() => setIsOpen(false)}
                className="w-full px-4 py-2 text-left hover:bg-obsidian-700/50 transition-colors block"
              >
                <div className="flex items-center gap-3 px-2">
                  <svg
                    className="w-5 h-5 text-oatmeal-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span className="font-sans text-sm text-oatmeal-300">Diagnostic History</span>
                </div>
              </Link>

              {/* Settings Link (Sprint 21) */}
              <Link
                href="/settings"
                onClick={() => setIsOpen(false)}
                className="w-full px-4 py-2 text-left hover:bg-obsidian-700/50 transition-colors block"
              >
                <div className="flex items-center gap-3 px-2">
                  <svg
                    className="w-5 h-5 text-oatmeal-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <span className="font-sans text-sm text-oatmeal-300">Practice Settings</span>
                </div>
              </Link>

              {/* Divider */}
              <div className="my-2 border-t border-obsidian-700"></div>

              {/* Logout Button */}
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2 text-left hover:bg-obsidian-700/50 transition-colors"
              >
                <div className="flex items-center gap-3 px-2">
                  <svg
                    className="w-5 h-5 text-clay-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  <span className="font-sans text-sm text-clay-400">
                    Sign out
                  </span>
                </div>
              </button>
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-obsidian-700 bg-obsidian-700/30">
              <p className="text-oatmeal-600 text-xs font-sans text-center">
                Paciolus v0.16.0 - Built for Financial Professionals
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ProfileDropdown
