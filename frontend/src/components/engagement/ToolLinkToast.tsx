'use client'

/**
 * ToolLinkToast — Sprint 103: Tool-Engagement Integration
 *
 * Floating toast (bottom-right) that appears when a tool run
 * is successfully linked to a diagnostic workspace.
 *
 * Guardrail: "Results linked to [Workspace Name]" — never "audit findings linked"
 */

import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface ToolLinkToastProps {
  message: string | null
  onDismiss: () => void
}

export function ToolLinkToast({ message, onDismiss }: ToolLinkToastProps) {
  useEffect(() => {
    if (!message) return

    const timer = setTimeout(onDismiss, 4000)
    return () => clearTimeout(timer)
  }, [message, onDismiss])

  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          transition={{ duration: 0.25, ease: 'easeOut' as const }}
          className="fixed bottom-6 right-6 z-50"
        >
          <div data-theme="dark" className="bg-obsidian-800 border border-sage-500/30 rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 max-w-sm">
            <div className="w-2 h-2 bg-sage-400 rounded-full flex-shrink-0" />
            <span className="text-sage-300 text-sm font-sans">{message}</span>
            <button
              onClick={onDismiss}
              className="text-oatmeal-500 hover:text-oatmeal-300 transition-colors flex-shrink-0"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
