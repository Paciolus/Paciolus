'use client'

/**
 * CancelModal — Sprint 374.
 *
 * Cancellation confirmation with end-date display.
 */

import { useState } from 'react'

interface CancelModalProps {
  isOpen: boolean
  periodEnd: string | null
  onConfirm: () => Promise<boolean>
  onClose: () => void
}

export function CancelModal({ isOpen, periodEnd, onConfirm, onClose }: CancelModalProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

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
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-surface-card border border-theme rounded-lg p-6 max-w-md w-full">
        <h2 className="font-serif text-xl text-content-primary mb-4">Cancel Subscription</h2>

        <p className="text-content-secondary font-sans mb-4">
          Are you sure you want to cancel your subscription?
        </p>

        {endDate && (
          <div className="bg-oatmeal-100 border border-theme rounded-lg p-4 mb-4">
            <p className="text-sm text-content-secondary font-sans">
              You will continue to have access to your current plan until{' '}
              <span className="font-medium text-content-primary">{endDate}</span>.
              After that, your account will revert to the Free plan.
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
            Keep Plan
          </button>
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="flex-1 py-2.5 bg-clay-600 text-white rounded-lg font-sans font-medium hover:bg-clay-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Canceling...' : 'Cancel Subscription'}
          </button>
        </div>
      </div>
    </div>
  )
}
