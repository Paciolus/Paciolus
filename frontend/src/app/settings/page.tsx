'use client'

/**
 * Settings Hub Page - Sprint 48
 *
 * Landing page for settings that directs users to either:
 * - Profile Settings (personal account info)
 * - Practice Settings (business configuration)
 */

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/context/AuthContext'

export default function SettingsHubPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuth()

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-surface-page">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-surface-card backdrop-blur-md border-b border-theme z-50">
        <div className="max-w-4xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
            />
            <span className="text-xl font-bold font-serif text-content-primary tracking-tight">
              Paciolus
            </span>
          </Link>
          <span className="text-content-secondary text-sm font-sans">
            Settings
          </span>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-24 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 text-content-tertiary text-sm font-sans mb-4">
              <Link href="/" className="hover:text-content-secondary transition-colors">Home</Link>
              <span>/</span>
              <span className="text-content-secondary">Settings</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
              Settings
            </h1>
            <p className="text-content-secondary font-sans">
              Manage your account and practice configuration.
            </p>
          </div>

          {/* Settings Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Profile Settings Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              whileHover={{ y: -4 }}
              transition={{ duration: 0.2 }}
            >
              <Link
                href="/settings/profile"
                className="block bg-surface-card border border-theme rounded-2xl p-6 shadow-theme-card hover:shadow-theme-card-hover hover:border-sage-500/50 transition-all group"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-sage-50 rounded-xl flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                    <svg className="w-6 h-6 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-serif font-semibold text-content-primary group-hover:text-sage-600 transition-colors">
                      Profile Settings
                    </h2>
                    <p className="text-content-tertiary text-sm font-sans">
                      Personal account info
                    </p>
                  </div>
                </div>
                <ul className="space-y-2 text-sm text-content-secondary font-sans">
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Display name
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Email address
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Password
                  </li>
                </ul>
              </Link>
            </motion.div>

            {/* Practice Settings Card */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              whileHover={{ y: -4 }}
            >
              <Link
                href="/settings/practice"
                className="block bg-surface-card border border-theme rounded-2xl p-6 shadow-theme-card hover:shadow-theme-card-hover hover:border-sage-500/50 transition-all group"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-sage-50 rounded-xl flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                    <svg className="w-6 h-6 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-serif font-semibold text-content-primary group-hover:text-sage-600 transition-colors">
                      Practice Settings
                    </h2>
                    <p className="text-content-tertiary text-sm font-sans">
                      Business configuration
                    </p>
                  </div>
                </div>
                <ul className="space-y-2 text-sm text-content-secondary font-sans">
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Materiality formulas
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Weighted thresholds
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Export preferences
                  </li>
                </ul>
              </Link>
            </motion.div>
          </div>
        </div>
      </div>
    </main>
  )
}
