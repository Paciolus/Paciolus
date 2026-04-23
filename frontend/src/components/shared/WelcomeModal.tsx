'use client'

/**
 * WelcomeModal — Sprint 583: First-Run Onboarding Experience
 *
 * 3-step onboarding guide for new users landing on the dashboard.
 * Shows once per user (completion stored in localStorage).
 * Follows Oat & Obsidian design tokens.
 *
 * Steps:
 * 1. Upload a trial balance (core action)
 * 2. Explore your diagnostic tools (18 tools)
 * 3. Export audit-ready memos (deliverable)
 */

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { fadeScale } from '@/lib/motion'

const ONBOARDING_KEY = 'paciolus_onboarding_complete'

interface Step {
  title: string
  description: string
  icon: React.ReactNode
  cta: string
  href: string
}

const STEPS: Step[] = [
  {
    title: 'Upload a Trial Balance',
    description: 'Start by uploading any trial balance file — CSV, Excel, or 8 other formats. Your data is processed in-memory and never stored.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
    cta: 'Upload Now',
    href: '/tools/trial-balance',
  },
  {
    title: 'Run Diagnostic Tools',
    description: '12 specialized testing tools — from Journal Entry Testing (19 fraud indicators) to Revenue Testing (ASC 606/IFRS 15). Each produces actionable findings.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
      </svg>
    ),
    cta: 'Browse Tools',
    href: '/tools',
  },
  {
    title: 'Export Audit-Ready Memos',
    description: 'Generate PDF memos aligned with PCAOB and ISA standards, plus Excel and CSV exports. Professional deliverables in seconds.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
    cta: 'Get Started',
    href: '/tools/trial-balance',
  },
]

interface WelcomeModalProps {
  /** Force show for testing/demo purposes. */
  forceShow?: boolean
}

export function WelcomeModal({ forceShow = false }: WelcomeModalProps) {
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    if (forceShow) {
      setIsOpen(true)
      return undefined
    }
    try {
      const completed = localStorage.getItem(ONBOARDING_KEY)
      if (!completed) {
        // Small delay so the dashboard renders first
        const timer = setTimeout(() => setIsOpen(true), 800)
        return () => clearTimeout(timer)
      }
    } catch {
      // localStorage unavailable — skip onboarding
    }
    return undefined
  }, [forceShow])

  const handleComplete = useCallback(() => {
    setIsOpen(false)
    try {
      localStorage.setItem(ONBOARDING_KEY, 'true')
    } catch {
      // localStorage unavailable — ignore
    }
  }, [])

  const handleStepAction = useCallback(() => {
    handleComplete()
    const step = STEPS[currentStep]
    if (step) router.push(step.href)
  }, [handleComplete, router, currentStep])

  const handleNext = useCallback(() => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      handleStepAction()
    }
  }, [currentStep, handleStepAction])

  const step = STEPS[currentStep] ?? STEPS[0]!

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-center justify-center p-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-obsidian-900/70 backdrop-blur-xs"
            onClick={handleComplete}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Modal */}
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="welcome-title"
            variants={fadeScale}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative bg-surface-card rounded-2xl border border-theme shadow-2xl w-full max-w-lg overflow-hidden"
          >
            {/* Progress indicator */}
            <div className="px-6 pt-6 flex items-center gap-2">
              {STEPS.map((_, i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                    i <= currentStep ? 'bg-sage-500' : 'bg-oatmeal-200'
                  }`}
                />
              ))}
            </div>

            {/* Content */}
            <div className="px-6 pt-6 pb-4 text-center">
              {currentStep === 0 && (
                <p className="text-xs font-sans font-medium text-sage-600 uppercase tracking-wider mb-2">
                  Welcome to Paciolus
                </p>
              )}
              <div className="w-16 h-16 mx-auto mb-5 rounded-2xl bg-sage-50 border border-sage-200 flex items-center justify-center text-sage-600">
                {step.icon}
              </div>
              <h2 id="welcome-title" className="text-2xl font-serif font-bold text-content-primary mb-3">
                {step.title}
              </h2>
              <p className="text-sm font-sans text-content-secondary leading-relaxed max-w-sm mx-auto">
                {step.description}
              </p>
            </div>

            {/* Step indicator */}
            <p className="text-center text-xs font-sans text-content-tertiary mb-4">
              Step {currentStep + 1} of {STEPS.length}
            </p>

            {/* Actions */}
            <div className="px-6 pb-6 flex gap-3">
              <button
                onClick={handleComplete}
                className="flex-1 py-3 border border-theme rounded-xl font-sans text-sm font-medium text-content-secondary hover:bg-surface-input transition-colors"
              >
                Skip
              </button>
              <button
                onClick={handleNext}
                className="flex-1 py-3 bg-sage-600 text-oatmeal-50 rounded-xl font-sans text-sm font-bold hover:bg-sage-700 transition-colors"
              >
                {currentStep === STEPS.length - 1 ? step.cta : 'Next'}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
