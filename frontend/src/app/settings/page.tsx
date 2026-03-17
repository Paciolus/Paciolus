'use client'

/**
 * Settings Hub Page - Sprint 48
 *
 * Landing page for settings that directs users to either:
 * - Profile Settings (personal account info)
 * - Practice Settings (business configuration)
 */

import { useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { FeatureGate } from '@/components/shared/FeatureGate'
import { fadeUp, staggerContainerTight } from '@/lib/motion'

export default function SettingsHubPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuthSession()

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
    <main id="main-content" className="min-h-screen bg-surface-page">
      {/* Main Content */}
      <div className="pt-8 pb-16 px-6">
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
          <motion.div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" variants={staggerContainerTight} initial="hidden" animate="visible">
            {/* Profile Settings Card */}
            <motion.div
              variants={fadeUp}
              whileHover={{ y: -4 }}
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
              variants={fadeUp}
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

            {/* Billing Settings Card */}
            <motion.div
              variants={fadeUp}
              whileHover={{ y: -4 }}
            >
              <Link
                href="/settings/billing"
                className="block bg-surface-card border border-theme rounded-2xl p-6 shadow-theme-card hover:shadow-theme-card-hover hover:border-sage-500/50 transition-all group"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-sage-50 rounded-xl flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                    <svg className="w-6 h-6 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-serif font-semibold text-content-primary group-hover:text-sage-600 transition-colors">
                      Billing & Subscription
                    </h2>
                    <p className="text-content-tertiary text-sm font-sans">
                      Plan & payment management
                    </p>
                  </div>
                </div>
                <ul className="space-y-2 text-sm text-content-secondary font-sans">
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Current plan & usage
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Upgrade or downgrade
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                    Payment method
                  </li>
                </ul>
              </Link>
            </motion.div>
            {/* Team Dashboard Card — Professional+ */}
            <FeatureGate feature="admin_dashboard" hidden>
              <motion.div
                variants={fadeUp}
                whileHover={{ y: -4 }}
              >
                <Link
                  href="/settings/admin-dashboard"
                  className="block bg-surface-card border border-theme rounded-2xl p-6 shadow-theme-card hover:shadow-theme-card-hover hover:border-sage-500/50 transition-all group"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-sage-50 rounded-xl flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                      <svg className="w-6 h-6 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-lg font-serif font-semibold text-content-primary group-hover:text-sage-600 transition-colors">
                        Team Dashboard
                      </h2>
                      <p className="text-content-tertiary text-sm font-sans">
                        Professional+
                      </p>
                    </div>
                  </div>
                  <ul className="space-y-2 text-sm text-content-secondary font-sans">
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Team usage metrics
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Tool adoption
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Activity export
                    </li>
                  </ul>
                </Link>
              </motion.div>
            </FeatureGate>

            {/* PDF Branding Card — Enterprise */}
            <FeatureGate feature="custom_branding" hidden>
              <motion.div
                variants={fadeUp}
                whileHover={{ y: -4 }}
              >
                <Link
                  href="/settings/branding"
                  className="block bg-surface-card border border-theme rounded-2xl p-6 shadow-theme-card hover:shadow-theme-card-hover hover:border-sage-500/50 transition-all group"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-sage-50 rounded-xl flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                      <svg className="w-6 h-6 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-lg font-serif font-semibold text-content-primary group-hover:text-sage-600 transition-colors">
                        PDF Branding
                      </h2>
                      <p className="text-content-tertiary text-sm font-sans">
                        Enterprise
                      </p>
                    </div>
                  </div>
                  <ul className="space-y-2 text-sm text-content-secondary font-sans">
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Custom header & footer
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Logo upload
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Memo customization
                    </li>
                  </ul>
                </Link>
              </motion.div>
            </FeatureGate>

            {/* Export Sharing Card — Professional+ */}
            <FeatureGate feature="export_sharing" hidden>
              <motion.div
                variants={fadeUp}
                whileHover={{ y: -4 }}
              >
                <Link
                  href="/settings/shares"
                  className="block bg-surface-card border border-theme rounded-2xl p-6 shadow-theme-card hover:shadow-theme-card-hover hover:border-sage-500/50 transition-all group"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-sage-50 rounded-xl flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                      <svg className="w-6 h-6 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-lg font-serif font-semibold text-content-primary group-hover:text-sage-600 transition-colors">
                        Export Sharing
                      </h2>
                      <p className="text-content-tertiary text-sm font-sans">
                        Professional+
                      </p>
                    </div>
                  </div>
                  <ul className="space-y-2 text-sm text-content-secondary font-sans">
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Active share links
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      48h expiry
                    </li>
                    <li className="flex items-center gap-2">
                      <span className="w-1.5 h-1.5 bg-content-tertiary rounded-full"></span>
                      Revoke access
                    </li>
                  </ul>
                </Link>
              </motion.div>
            </FeatureGate>
          </motion.div>
        </div>
      </div>
    </main>
  )
}
