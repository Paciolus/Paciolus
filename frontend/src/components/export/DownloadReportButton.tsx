'use client'

import { useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { AuditResult } from '@/types/diagnostic'
import { apiDownload, downloadBlob } from '@/utils/apiClient'
import { RESOLVE_ENTER } from '@/utils/motionTokens'

interface DownloadReportButtonProps {
  auditResult: AuditResult
  filename: string
  disabled?: boolean
  token?: string | null
}


/**
 * DownloadReportButton - Sprint 18 Export Component
 *
 * Premium "Export Diagnostic Summary" button with animated loading state.
 * Follows Oat & Obsidian design system.
 *
 * Features:
 * - Animated loading state ("Generating Diagnostic Summary...")
 * - Framer-motion transitions
 * - Triggers browser download on completion
 *
 * Sprint 18 Terminology: "Download Report" → "Export Diagnostic Summary"
 */
export function DownloadReportButton({
  auditResult,
  filename,
  disabled = false,
  token,
}: DownloadReportButtonProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const clearTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const markComplete = useCallback(() => {
    setIsComplete(true)
    if (clearTimerRef.current) clearTimeout(clearTimerRef.current)
    clearTimerRef.current = setTimeout(() => {
      setIsComplete(false)
      clearTimerRef.current = null
    }, 1500)
  }, [])

  const handleDownload = async () => {
    if (isGenerating || isComplete || disabled) return

    setIsGenerating(true)
    setError(null)

    try {
      // Prepare the request body
      const requestBody = {
        ...auditResult,
        filename,
      }

      const { blob, filename: downloadFilename, error: downloadError, ok } = await apiDownload(
        '/export/pdf',
        token ?? null,
        { method: 'POST', body: requestBody as Record<string, unknown> }
      )

      if (!ok || !blob) {
        throw new Error(downloadError || 'Failed to generate report')
      }

      downloadBlob(blob, downloadFilename || 'Paciolus_Report.pdf')
      markComplete()

    } catch (err) {
      console.error('PDF generation error:', err)
      setError(err instanceof Error ? err.message : 'Failed to generate report')
    } finally {
      setIsGenerating(false)
    }
  }

  // Animation variants
  const buttonVariants = {
    idle: { scale: 1 },
    hover: { scale: 1.02 },
    tap: { scale: 0.98 },
  }

  const spinnerVariants = {
    animate: {
      rotate: 360,
      transition: {
        duration: 1,
        repeat: Infinity,
        ease: 'linear' as const,
      },
    },
  }

  const textVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 },
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <motion.button
        onClick={handleDownload}
        disabled={disabled || isGenerating}
        variants={buttonVariants}
        initial="idle"
        whileHover={!disabled && !isGenerating ? 'hover' : 'idle'}
        whileTap={!disabled && !isGenerating ? 'tap' : 'idle'}
        className={`
          relative flex items-center justify-center gap-3 px-6 py-3 rounded-xl
          font-sans font-medium text-sm
          transition-colors duration-200
          ${disabled || isGenerating
            ? 'bg-surface-card-secondary text-content-disabled cursor-not-allowed'
            : 'bg-sage-600 text-white hover:bg-sage-500 shadow-sm hover:shadow-md'
          }
        `}
      >
        <AnimatePresence mode="wait">
          {isGenerating ? (
            <motion.div
              key="generating"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3"
            >
              {/* Spinning loader */}
              <motion.svg
                variants={spinnerVariants}
                animate="animate"
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </motion.svg>

              <motion.span
                variants={textVariants}
                initial="initial"
                animate="animate"
                className="min-w-[180px]"
              >
                Generating Diagnostic Summary...
              </motion.span>
            </motion.div>
          ) : isComplete ? (
            <motion.div
              key="complete"
              variants={RESOLVE_ENTER}
              initial="initial"
              animate="animate"
              exit="exit"
              className="flex items-center gap-3"
            >
              {/* Checkmark icon */}
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
                  d="M5 13l4 4L19 7"
                />
              </svg>

              <span>Downloaded</span>
            </motion.div>
          ) : (
            <motion.div
              key="idle"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3"
            >
              {/* PDF icon */}
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
                  d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>

              <span>Export Diagnostic Summary</span>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {/* Error message */}
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="text-theme-error-text text-xs font-sans"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Subtle hint */}
      {!isGenerating && !error && (
        <p className="text-content-tertiary text-xs font-sans">
          Zero-Storage: Summary generated on-demand, never stored
        </p>
      )}
    </div>
  )
}

export default DownloadReportButton
