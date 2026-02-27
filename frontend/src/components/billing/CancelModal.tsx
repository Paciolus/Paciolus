'use client'

/**
 * CancelModal — Sprint 374.
 *
 * Cancellation confirmation with end-date display.
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MODAL_OVERLAY_VARIANTS, MODAL_CONTENT_VARIANTS } from '@/utils/themeUtils'

interface CancelModalProps {
  isOpen: boolean
  periodEnd: string | null
  status?: string
  onConfirm: () => Promise<boolean>
  onClose: () => void
}

export function CancelModal({ isOpen, periodEnd, status, onConfirm, onClose }: CancelModalProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const isTrialing = status === 'trialing'

  const endDate = periodEnd
    ? new Date(periodEnd).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null

  async function handleConfirm() {
    setIsLoading(true)
    setError(null)
    const success = await onConfirm()
    setIsLoading(false)
    if (success) {
      onClose()
    } else {
      setError('Failed to cancel subscription. Please try again.')
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <motion.div
            variants={MODAL_OVERLAY_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-xs"
            onClick={onClose}
          />
          <motion.div
            variants={MODAL_CONTENT_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative bg-surface-card border border-theme rounded-lg p-6 max-w-md w-full"
          >
        <h2 className="font-serif text-xl text-content-primary mb-4">
          {isTrialing ? 'Cancel Trial' : 'Cancel Subscription'}
        </h2>

        <p className="text-content-secondary font-sans mb-4">
          {isTrialing
            ? 'Are you sure you want to cancel your free trial? You will not be charged.'
            : 'Are you sure you want to cancel your subscription?'}
        </p>

        {endDate && !isTrialing && (
          <div className="bg-oatmeal-100 border border-theme rounded-lg p-4 mb-4">
            <p className="text-sm text-content-secondary font-sans">
              You will continue to have access to your current plan until{' '}
              <span className="font-medium text-content-primary">{endDate}</span>.
              After that, you will lose access to paid features.
            </p>
          </div>
        )}

        {isTrialing && (
          <div className="bg-oatmeal-100 border border-theme rounded-lg p-4 mb-4">
            <p className="text-sm text-content-secondary font-sans">
              Your trial will be canceled and you will lose access to paid features immediately.
              No payment method will be charged.
            </p>
          </div>
        )}

        {error && (
          <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-4 text-sm" role="alert">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 py-2.5 border border-theme rounded-lg font-sans font-medium text-content-secondary hover:bg-surface-input transition-colors disabled:opacity-50"
          >
            {isTrialing ? 'Keep Trial' : 'Keep Plan'}
          </button>
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="flex-1 py-2.5 bg-clay-600 text-white rounded-lg font-sans font-medium hover:bg-clay-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Canceling...' : isTrialing ? 'Cancel Trial' : 'Cancel Subscription'}
          </button>
        </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
