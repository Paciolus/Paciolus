'use client'

import { useState, useMemo, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { useFormValidation, commonValidators } from '@/hooks'

/**
 * Obsidian Vault Registration Page - Day 13
 *
 * Design: Same vault aesthetic as login with password strength indicator.
 * Zero-Storage Promise badge reinforces trust messaging.
 *
 * Refactored: Now uses useFormValidation hook for form state management
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */

interface PasswordStrength {
  score: number // 0-5
  label: string
  color: string
  requirements: {
    length: boolean
    uppercase: boolean
    lowercase: boolean
    number: boolean
    special: boolean
  }
}

function calculatePasswordStrength(password: string): PasswordStrength {
  const requirements = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  }

  const score = Object.values(requirements).filter(Boolean).length

  const labels = ['Very Weak', 'Weak', 'Fair', 'Strong', 'Very Strong']
  const colors = ['clay-500', 'clay-400', 'oatmeal-400', 'sage-400', 'sage-500']

  return {
    score,
    label: labels[score - 1] || 'Very Weak',
    color: colors[score - 1] || 'clay-500',
    requirements,
  }
}

type RegisterFormValues = {
  email: string
  password: string
  confirmPassword: string
  acceptTerms: boolean
}

const initialValues: RegisterFormValues = {
  email: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
}

export default function RegisterPage() {
  const router = useRouter()
  const { register, isAuthenticated, isLoading: authLoading } = useAuth()

  // Server-side error (from failed registration attempt)
  const [serverError, setServerError] = useState('')

  // Form state via useFormValidation hook
  const {
    values,
    isSubmitting,
    isValid,
    setValue,
    handleSubmit,
  } = useFormValidation<RegisterFormValues>({
    initialValues,
    validationRules: {
      email: [
        commonValidators.required('Email is required'),
        commonValidators.email('Please enter a valid email'),
      ],
      password: [
        commonValidators.required('Password is required'),
        commonValidators.minLength(8, 'Password must be at least 8 characters'),
        {
          test: (value) => {
            if (typeof value !== 'string') return true
            const strength = calculatePasswordStrength(value)
            return strength.score >= 3
          },
          message: 'Please choose a stronger password',
        },
      ],
      confirmPassword: [
        commonValidators.required('Please confirm your password'),
        commonValidators.matches<RegisterFormValues>('password', 'Passwords do not match'),
      ],
      acceptTerms: [
        {
          test: (value) => value === true,
          message: 'Please accept the terms of service',
        },
      ],
    },
    onSubmit: async (formValues) => {
      setServerError('')

      const result = await register({
        email: formValues.email,
        password: formValues.password,
      })

      if (result.success) {
        router.push('/verification-pending?email=' + encodeURIComponent(formValues.email))
      } else {
        setServerError(result.error || 'Registration failed. Please try again.')
      }
    },
  })

  // Password strength for UI display (separate from validation)
  const passwordStrength = useMemo(
    () => calculatePasswordStrength(values.password),
    [values.password]
  )

  // Computed: do passwords match (for UI indicator)
  const passwordsMatch = values.password === values.confirmPassword && values.confirmPassword.length > 0

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      router.push('/')
    }
  }, [isAuthenticated, authLoading, router])

  // Button disabled state
  const isButtonDisabled = isSubmitting || !values.acceptTerms || !passwordsMatch || passwordStrength.score < 3

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
            {/* Vault Icon - with key symbol for registration */}
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
                  d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                />
              </svg>
            </motion.div>

            <motion.h1
              className="text-2xl font-serif font-bold text-oatmeal-200 mb-2"
              variants={itemVariants}
            >
              Create Your Vault
            </motion.h1>

            <motion.p
              className="text-oatmeal-400 font-sans text-sm"
              variants={itemVariants}
            >
              Join Paciolus for secure trial balance auditing
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
                Zero-Storage Architecture
              </span>
            </div>
            <p className="text-oatmeal-500 text-xs font-sans text-center mt-2">
              Your financial data is never stored. Only credentials are saved securely.
            </p>
          </motion.div>

          {/* Registration Form */}
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
                  placeholder="Create a strong password"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-obsidian-900 border border-obsidian-500 rounded-xl text-oatmeal-200 placeholder-oatmeal-500 font-sans focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent transition-all"
                />
              </div>

              {/* Password Strength Indicator */}
              {values.password.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-3 space-y-2"
                >
                  {/* Strength Bar */}
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <div
                        key={level}
                        className={`h-1.5 flex-1 rounded-full transition-all ${
                          level <= passwordStrength.score
                            ? level <= 2
                              ? 'bg-clay-500'
                              : level <= 3
                              ? 'bg-oatmeal-400'
                              : 'bg-sage-500'
                            : 'bg-obsidian-600'
                        }`}
                      />
                    ))}
                  </div>

                  {/* Strength Label */}
                  <div className="flex justify-between items-center">
                    <span
                      className={`text-xs font-sans font-medium ${
                        passwordStrength.score <= 2
                          ? 'text-clay-400'
                          : passwordStrength.score === 3
                          ? 'text-oatmeal-300'
                          : 'text-sage-400'
                      }`}
                    >
                      {passwordStrength.label}
                    </span>
                  </div>

                  {/* Requirements Checklist */}
                  <div className="grid grid-cols-2 gap-1 text-xs font-sans">
                    <div className={`flex items-center gap-1 ${passwordStrength.requirements.length ? 'text-sage-400' : 'text-oatmeal-500'}`}>
                      {passwordStrength.requirements.length ? (
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" strokeWidth={2} />
                        </svg>
                      )}
                      8+ characters
                    </div>
                    <div className={`flex items-center gap-1 ${passwordStrength.requirements.uppercase ? 'text-sage-400' : 'text-oatmeal-500'}`}>
                      {passwordStrength.requirements.uppercase ? (
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" strokeWidth={2} />
                        </svg>
                      )}
                      Uppercase
                    </div>
                    <div className={`flex items-center gap-1 ${passwordStrength.requirements.lowercase ? 'text-sage-400' : 'text-oatmeal-500'}`}>
                      {passwordStrength.requirements.lowercase ? (
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" strokeWidth={2} />
                        </svg>
                      )}
                      Lowercase
                    </div>
                    <div className={`flex items-center gap-1 ${passwordStrength.requirements.number ? 'text-sage-400' : 'text-oatmeal-500'}`}>
                      {passwordStrength.requirements.number ? (
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" strokeWidth={2} />
                        </svg>
                      )}
                      Number
                    </div>
                    <div className={`flex items-center gap-1 col-span-2 ${passwordStrength.requirements.special ? 'text-sage-400' : 'text-oatmeal-500'}`}>
                      {passwordStrength.requirements.special ? (
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <circle cx="12" cy="12" r="10" strokeWidth={2} />
                        </svg>
                      )}
                      Special character (!@#$%^&*)
                    </div>
                  </div>
                </motion.div>
              )}
            </div>

            {/* Confirm Password Input */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-sans font-medium text-oatmeal-300 mb-2"
              >
                Confirm Password
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
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                <input
                  type="password"
                  id="confirmPassword"
                  value={values.confirmPassword}
                  onChange={(e) => setValue('confirmPassword', e.target.value)}
                  placeholder="Confirm your password"
                  required
                  className={`w-full pl-12 pr-10 py-3 bg-obsidian-900 border rounded-xl text-oatmeal-200 placeholder-oatmeal-500 font-sans focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent transition-all ${
                    values.confirmPassword.length > 0
                      ? passwordsMatch
                        ? 'border-sage-500'
                        : 'border-clay-500'
                      : 'border-obsidian-500'
                  }`}
                />
                {values.confirmPassword.length > 0 && (
                  <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                    {passwordsMatch ? (
                      <svg className="w-5 h-5 text-sage-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5 text-clay-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                )}
              </div>
              {values.confirmPassword.length > 0 && !passwordsMatch && (
                <p className="mt-2 text-xs text-clay-400 font-sans">
                  Passwords do not match
                </p>
              )}
            </div>

            {/* Terms Acceptance */}
            <div>
              <label className="flex items-start gap-3 cursor-pointer">
                <div
                  className={`mt-0.5 w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                    values.acceptTerms
                      ? 'bg-sage-500 border-sage-500'
                      : 'border-oatmeal-500/50 hover:border-oatmeal-400'
                  }`}
                  onClick={() => setValue('acceptTerms', !values.acceptTerms)}
                >
                  {values.acceptTerms && (
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
                  checked={values.acceptTerms}
                  onChange={(e) => setValue('acceptTerms', e.target.checked)}
                  className="sr-only"
                  required
                />
                <span className="text-sm text-oatmeal-400 font-sans">
                  I agree to the{' '}
                  <a
                    href="/terms"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sage-400 hover:text-sage-300 underline transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Terms of Service
                  </a>
                  {' '}and{' '}
                  <a
                    href="/privacy"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sage-400 hover:text-sage-300 underline transition-colors"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Privacy Policy
                  </a>
                </span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isButtonDisabled}
              className={`w-full py-3 rounded-xl font-sans font-bold transition-all transform ${
                isButtonDisabled
                  ? 'bg-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                  : 'bg-sage-500 hover:bg-sage-400 text-obsidian-900 hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-oatmeal-400/30 border-t-oatmeal-400 rounded-full animate-spin"></div>
                  Creating Your Vault...
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
                      d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                    />
                  </svg>
                  Create My Vault
                </span>
              )}
            </button>
          </motion.form>

          {/* Footer - Login Link */}
          <motion.div
            className="px-8 py-5 bg-obsidian-700/30 border-t border-obsidian-700 text-center"
            variants={itemVariants}
          >
            <p className="text-oatmeal-400 text-sm font-sans">
              Already have a vault?{' '}
              <Link
                href="/login"
                className="text-sage-400 hover:text-sage-300 font-medium transition-colors"
              >
                Sign in
              </Link>
            </p>
          </motion.div>
        </motion.div>

    </motion.div>
  )
}
