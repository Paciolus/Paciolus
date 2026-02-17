'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import Image from 'next/image'

interface User {
  email: string
}

interface ProfileDropdownProps {
  user: User
  onLogout: () => void
}

interface NavItem {
  href: string
  label: string
  icon: string
}

const TOOL_ITEMS: NavItem[] = [
  { href: '/tools/trial-balance', label: 'TB Diagnostics', icon: 'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z' },
  { href: '/tools/multi-period', label: 'Multi-Period Comparison', icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4' },
  { href: '/tools/journal-entry-testing', label: 'JE Testing', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
]

const NAV_ITEMS: NavItem[] = [
  { href: '/portfolio', label: 'Client Portfolio', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
  { href: '/history', label: 'Diagnostic History', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
  { href: '/settings/profile', label: 'Profile Settings', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
  { href: '/settings/practice', label: 'Practice Settings', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' },
]

function NavMenuItem({ item, onClick }: { item: NavItem; onClick: () => void }) {
  return (
    <Link
      href={item.href}
      onClick={onClick}
      className="w-full px-4 py-2 text-left hover:bg-obsidian-700/50 transition-colors block"
    >
      <div className="flex items-center gap-3 px-2">
        <svg className="w-5 h-5 text-oatmeal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
        </svg>
        <span className="font-sans text-sm text-oatmeal-300">{item.label}</span>
      </div>
    </Link>
  )
}

const dropdownVariants = {
  hidden: { opacity: 0, y: -8, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { type: 'spring' as const, stiffness: 400, damping: 25 },
  },
  exit: { opacity: 0, y: -8, scale: 0.95, transition: { duration: 0.15 } },
}

export function ProfileDropdown({ user, onLogout }: ProfileDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const displayEmail = user.email.length > 24
    ? user.email.slice(0, 21) + '...'
    : user.email

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') setIsOpen(false)
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [])

  const handleLogout = () => {
    setIsOpen(false)
    onLogout()
  }

  const closeMenu = () => setIsOpen(false)

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
        <div className="w-8 h-8 rounded-full bg-sage-500/20 border border-sage-500/40 flex items-center justify-center">
          <span className="text-sage-400 font-sans font-bold text-sm">
            {user.email.charAt(0).toUpperCase()}
          </span>
        </div>
        <svg
          className={`w-4 h-4 text-oatmeal-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
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
            {/* Header */}
            <div className="px-4 py-4 border-b border-obsidian-700 bg-obsidian-700/30">
              <div className="flex items-center gap-3 mb-3">
                <Image
                  src="/PaciolusLogo_LightBG.png"
                  alt="Paciolus"
                  width={370}
                  height={510}
                  className="h-8 w-auto object-contain"
                  style={{ imageRendering: 'crisp-edges' }}
                />
                <div className="h-6 w-px bg-obsidian-600"></div>
                <span className="text-sm font-serif font-bold text-oatmeal-300">Vault Access</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-sage-500/20 border border-sage-500/40 flex items-center justify-center flex-shrink-0">
                  <span className="text-sage-400 font-sans font-bold">
                    {user.email.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="text-oatmeal-200 font-sans font-medium text-sm">Welcome back</p>
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
                  <span className="text-sage-300 text-xs font-sans font-medium">Zero-Storage Active</span>
                </div>
              </div>

              {/* Tools Section */}
              <div className="px-4 py-1">
                <span className="text-oatmeal-500 text-xs font-sans font-medium uppercase tracking-wider px-2">Tools</span>
              </div>
              {TOOL_ITEMS.map(item => (
                <NavMenuItem key={item.href} item={item} onClick={closeMenu} />
              ))}

              <div className="my-2 border-t border-obsidian-700"></div>

              {NAV_ITEMS.map(item => (
                <NavMenuItem key={item.href} item={item} onClick={closeMenu} />
              ))}

              <div className="my-2 border-t border-obsidian-700"></div>

              {/* Logout */}
              <button
                onClick={handleLogout}
                className="w-full px-4 py-2 text-left hover:bg-obsidian-700/50 transition-colors"
              >
                <div className="flex items-center gap-3 px-2">
                  <svg className="w-5 h-5 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  <span className="font-sans text-sm text-clay-400">Sign out</span>
                </div>
              </button>
            </div>

            {/* Footer */}
            <div className="px-4 py-3 border-t border-obsidian-700 bg-obsidian-700/30">
              <p className="text-oatmeal-500 text-xs font-sans text-center">
                Paciolus v1.2.0 - Built for Financial Professionals
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ProfileDropdown
