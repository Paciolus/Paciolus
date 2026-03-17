'use client'

/**
 * ShareExportModal — Sprint 545c
 *
 * Modal for creating a share link for an export. Copies link to clipboard.
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { fadeScale } from '@/lib/motion'

interface ShareExportModalProps {
  isOpen: boolean
  onClose: () => void
  onShare: (tool: string, format: string, data: string) => Promise<string | null>
  tool: string
  format: string
  exportData: string
}

export function ShareExportModal({
  isOpen,
  onClose,
  onShare,
  tool,
  format,
  exportData,
}: ShareExportModalProps) {
  const [shareUrl, setShareUrl] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  async function handleCreate() {
    setIsCreating(true)
    const result = await onShare(tool, format, exportData)
    if (result) {
      const url = `${window.location.origin}/shared/${result}`
      setShareUrl(url)
    }
    setIsCreating(false)
  }

  async function handleCopy() {
    if (!shareUrl) return
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback for older browsers
      const input = document.createElement('input')
      input.value = shareUrl
      document.body.appendChild(input)
      input.select()
      document.execCommand('copy')
      document.body.removeChild(input)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  function handleClose() {
    setShareUrl(null)
    setCopied(false)
    onClose()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-obsidian-900/50"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            variants={fadeScale}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative z-10 bg-surface-card border border-theme rounded-2xl p-6 shadow-xl max-w-md w-full mx-4"
          >
            <h2 className="text-xl font-serif font-semibold text-content-primary mb-2">
              Share Export
            </h2>
            <p className="text-content-secondary text-sm font-sans mb-6">
              Create a shareable link for this {format.toUpperCase()} export. Links expire after 48 hours.
            </p>

            {!shareUrl ? (
              <button
                onClick={handleCreate}
                disabled={isCreating}
                className="w-full px-5 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCreating ? 'Creating...' : 'Create Share Link'}
              </button>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    readOnly
                    value={shareUrl}
                    className="flex-1 bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-mono text-content-primary"
                  />
                  <button
                    onClick={handleCopy}
                    className="px-4 py-2 bg-sage-600 text-white rounded-lg font-sans text-sm font-medium hover:bg-sage-700 transition-colors whitespace-nowrap"
                  >
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                <p className="text-content-tertiary text-xs font-sans">
                  Anyone with this link can access the export for 48 hours.
                </p>
              </div>
            )}

            <button
              onClick={handleClose}
              className="mt-4 w-full px-5 py-2.5 border border-theme rounded-lg font-sans font-medium text-content-secondary hover:bg-surface-input transition-colors"
            >
              {shareUrl ? 'Done' : 'Cancel'}
            </button>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
