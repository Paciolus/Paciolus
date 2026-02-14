'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/contexts/AuthContext'
import { useFormValidation, commonValidators } from '@/hooks'
import VaultTransition from '@/components/VaultTransition'

/**
 * Obsidian Vault Login Page - Day 13
 *
 * Design: "Secure Vault" visual metaphor with premium Oat & Obsidian styling.
 * Zero-Storage Promise badge prominently displayed to reinforce trust.
 *
 * Refactored: Now uses useFormValidation hook for form state management
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */

type LoginFormValues = {
  email: string
  password: string
  rememberMe: boolean
}

const initialValues: LoginFormValues = {
  email: '',
  password: '',
  rememberMe: false,
}

export default function LoginPage() {
  const router = useRouter()
  const { login, user, isAuthenticated, isLoading: authLoading } = useAuth()

  // Server-side error (from failed login attempt)
  const [serverError, setServerError] = useState('')

  // Vault transition state
  const [showVaultTransition, setShowVaultTransition] = useState(false)
  const [pendingRedirect, setPendingRedirect] = useState<string | null>(null)

  const handleVaultComplete = useCallback(() => {
    if (pendingRedirect) {
      router.push(pendingRedirect)
    }
  }, [pendingRedirect, router])

  // Form state via useFormValidation hook
  const {
    values,
    isSubmitting,
    setValue,
    handleSubmit,
  } = useFormValidation<LoginFormValues>({
    initialValues,
    validationRules: {
      email: [
        commonValidators.required('Email is required'),
        commonValidators.email('Please enter a valid email'),
      ],
      password: [
        commonValidators.required('Password is required'),
      ],
    },
    onSubmit: async (formValues) => {
      setServerError('')

      const result = await login({
        email: formValues.email,
        password: formValues.password,
        rememberMe: formValues.rememberMe,
      })

      if (result.success) {
        // Check for stored redirect path
        const redirectPath = sessionStorage.getItem('paciolus_redirect') || '/'
        sessionStorage.removeItem('paciolus_redirect')
        // Trigger vault transition instead of immediate redirect
        setPendingRedirect(redirectPath)
        setShowVaultTransition(true)
      } else {
        setServerError(result.error || 'Invalid email or password')
      }
    },
  })

  // Redirect if already authenticated (no transition for auto-redirects)
  useEffect(() => {
    if (!authLoading && isAuthenticated && !showVaultTransition) {
      const redirectPath = sessionStorage.getItem('paciolus_redirect') || '/'
      sessionStorage.removeItem('paciolus_redirect')
      router.push(redirectPath)
    }
  }, [isAuthenticated, authLoading, router, showVaultTransition])

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring' as const,
        stiffness: 300,
        damping: 24,
      },
    },
  }

  const vaultIconVariants = {
    hidden: { scale: 0.8, opacity: 0, rotateY: -15 },
    visible: {
      scale: 1,
      opacity: 1,
      rotateY: 0,
      transition: {
        type: 'spring' as const,
        stiffness: 200,
        damping: 20,
        delay: 0.2,
      },
    },
  }

  return (
    <>
      {/* Vault Crack Transition — plays on login success */}
      {showVaultTransition && (
        <VaultTransition
          userName={user?.name || user?.email?.split('@')[0]}
          onComplete={handleVaultComplete}
        />
      )}

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Vault Card */}
        <motion.div
          className="bg-obsidian-800 border border-obsidian-600 rounded-2xl shadow-2xl overflow-hidden"
          variants={itemVariants}
        >
          {/* Header with Vault Icon */}
          <div className="px-8 pt-8 pb-6 text-center border-b border-obsidian-700">
            {/* Vault Icon */}
            <motion.div
              className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-obsidian-700 border border-obsidian-500 flex items-center justify-center"
              variants={vaultIconVariants}
            >
              <svg
                className="w-10 h-10 text-sage-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </motion.div>

            <motion.h1
              className="text-2xl font-serif font-bold text-oatmeal-200 mb-2"
              variants={itemVariants}
            >
              Obsidian Vault
            </motion.h1>

            <motion.p
              className="text-oatmeal-400 font-sans text-sm"
              variants={itemVariants}
            >
              Secure access to your audit workspace
            </motion.p>
          </div>

          {/* Zero-Storage Badge */}
          <motion.div
            className="px-8 py-4 bg-obsidian-700/30 border-b border-obsidian-700"
            variants={itemVariants}
          >
            <div className="flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse"></div>
              <span className="text-sage-300 text-sm font-sans font-medium">
                Zero-Storage Promise
              </span>
              <div className="group relative">
                <button
                  type="button"
                  aria-label="What is Zero-Storage?"
                  className="w-4 h-4 rounded-full bg-obsidian-600 text-oatmeal-400 text-xs flex items-center justify-center hover:bg-obsidian-500 transition-colors"
                >
                  ?
                </button>
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-obsidian-900 border border-obsidian-500 rounded-lg text-xs text-oatmeal-300 w-56 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 font-sans">
                  Your trial balance data never touches our servers. Credentials are stored securely, but your financial data is processed entirely in-memory.
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-obsidian-500"></div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Login Form */}
          <motion.form
            onSubmit={handleSubmit}
            className="px-8 py-6 space-y-5"
            variants={itemVariants}
          >
            {/* Server Error Message */}
            {serverError && (
              <motion.div
                className="p-4 rounded-lg bg-clay-500/10 border border-clay-500/30"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div className="flex items-center gap-3">
                  <svg
                    className="w-5 h-5 text-clay-400 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <p className="text-clay-300 text-sm font-sans">{serverError}</p>
                </div>
              </motion.div>
            )}

            {/* Email Input */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-sans font-medium text-oatmeal-300 mb-2"
              >
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg
                    className="w-5 h-5 text-oatmeal-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                    />
                  </svg>
                </div>
                <input
                  type="email"
                  id="email"
                  value={values.email}
                  onChange={(e) => setValue('email', e.target.value)}
                  placeholder="you@company.com"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-obsidian-900 border border-obsidian-500 rounded-xl text-oatmeal-200 placeholder-oatmeal-500 font-sans focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-sans font-medium text-oatmeal-300 mb-2"
              >
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg
                    className="w-5 h-5 text-oatmeal-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                </div>
                <input
                  type="password"
                  id="password"
                  value={values.password}
                  onChange={(e) => setValue('password', e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-obsidian-900 border border-obsidian-500 rounded-xl text-oatmeal-200 placeholder-oatmeal-500 font-sans focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent transition-all"
                />
              </div>
            </div>

            {/* Remember Me & Forgot Password Row */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer">
                <div
                  className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                    values.rememberMe
                      ? 'bg-sage-500 border-sage-500'
                      : 'border-oatmeal-500/50 hover:border-oatmeal-400'
                  }`}
                  onClick={() => setValue('rememberMe', !values.rememberMe)}
                >
                  {values.rememberMe && (
                    <svg className="w-3 h-3 text-obsidian-900" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
                <input
                  type="checkbox"
                  checked={values.rememberMe}
                  onChange={(e) => setValue('rememberMe', e.target.checked)}
                  className="sr-only"
                />
                <span className="text-sm text-oatmeal-400 font-sans">Remember me</span>
              </label>

              <button
                type="button"
                className="text-sm text-oatmeal-500 hover:text-oatmeal-400 font-sans transition-colors cursor-not-allowed"
                disabled
                title="Coming soon"
              >
                Forgot password?
              </button>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full py-3 rounded-xl font-sans font-bold transition-all transform ${
                isSubmitting
                  ? 'bg-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                  : 'bg-sage-500 hover:bg-sage-400 text-obsidian-900 hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-oatmeal-400/30 border-t-oatmeal-400 rounded-full animate-spin"></div>
                  Unlocking Vault...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"
                    />
                  </svg>
                  Enter Vault
                </span>
              )}
            </button>
          </motion.form>

          {/* Footer - Register Link */}
          <motion.div
            className="px-8 py-5 bg-obsidian-700/30 border-t border-obsidian-700 text-center"
            variants={itemVariants}
          >
            <p className="text-oatmeal-400 text-sm font-sans">
              New to Paciolus?{' '}
              <Link
                href="/register"
                className="text-sage-400 hover:text-sage-300 font-medium transition-colors"
              >
                Create an account
              </Link>
            </p>
          </motion.div>
        </motion.div>

      </motion.div>
    </>
  )
}
