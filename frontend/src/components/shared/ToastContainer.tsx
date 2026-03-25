'use client'

/**
 * ToastContainer — Sprint 582: Global Toast Notification System
 *
 * Renders toast notifications in bottom-right corner.
 * Uses framer-motion for enter/exit animations.
 * Follows Oat & Obsidian design tokens.
 */

import { motion, AnimatePresence } from 'framer-motion'
import { useToast, type ToastType } from '@/contexts/ToastContext'

const TOAST_STYLES: Record<ToastType, { bg: string; border: string; icon: string; text: string }> = {
  success: {
    bg: 'bg-sage-50',
    border: 'border-sage-200',
    icon: 'text-sage-600',
    text: 'text-sage-800',
  },
  error: {
    bg: 'bg-clay-50',
    border: 'border-clay-200',
    icon: 'text-clay-600',
    text: 'text-clay-800',
  },
  info: {
    bg: 'bg-oatmeal-50',
    border: 'border-oatmeal-300',
    icon: 'text-obsidian-500',
    text: 'text-obsidian-700',
  },
}

const TOAST_ICONS: Record<ToastType, React.ReactNode> = {
  success: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  info: (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
}

export function ToastContainer() {
  const { toasts, removeToast } = useToast()

  return (
    <div
      aria-live="polite"
      aria-label="Notifications"
      className="fixed bottom-6 right-6 z-[80] flex flex-col-reverse gap-2 max-w-sm w-full pointer-events-none"
    >
      <AnimatePresence mode="popLayout">
        {toasts.map(toast => {
          const style = TOAST_STYLES[toast.type]
          return (
            <motion.div
              key={toast.id}
              layout
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ type: 'spring' as const, stiffness: 400, damping: 30 }}
              role="status"
              className={`pointer-events-auto ${style.bg} border ${style.border} rounded-xl px-4 py-3 shadow-lg flex items-start gap-3`}
            >
              <div className={`flex-shrink-0 mt-0.5 ${style.icon}`}>
                {TOAST_ICONS[toast.type]}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-sans font-medium ${style.text}`}>
                  {toast.title}
                </p>
                {toast.description && (
                  <p className={`text-xs font-sans mt-0.5 ${style.text} opacity-75`}>
                    {toast.description}
                  </p>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className={`flex-shrink-0 p-1 rounded-lg hover:bg-obsidian-900/5 transition-colors ${style.icon}`}
                aria-label="Dismiss notification"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
