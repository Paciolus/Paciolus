'use client'

/**
 * ShareExportModal — Sprint 545c / Sprint 593
 *
 * Modal for creating a share link for an export. Copies link to clipboard.
 * Sprint 593: Passcode protection, single-use mode, tier-based TTL messaging.
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { fadeScale } from '@/lib/motion'

interface ShareExportModalProps {
  isOpen: boolean
  onClose: () => void
  onShare: (tool: string, format: string, data: string, options?: { passcode?: string; singleUse?: boolean }) => Promise<string | null>
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
  const [passcode, setPasscode] = useState('')
  const [singleUse, setSingleUse] = useState(false)

  async function handleCreate() {
    setIsCreating(true)
    const options: { passcode?: string; singleUse?: boolean } = {}
    if (passcode.length >= 4) options.passcode = passcode
    if (singleUse) options.singleUse = true
    const result = await onShare(tool, format, exportData, Object.keys(options).length > 0 ? options : undefined)
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
    setPasscode('')
    setSingleUse(false)
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
            role="dialog"
            aria-modal="true"
            aria-labelledby="share-export-title"
            variants={fadeScale}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative z-10 bg-surface-card border border-theme rounded-2xl p-6 shadow-xl max-w-md w-full mx-4"
          >
            <h2 id="share-export-title" className="text-xl font-serif font-semibold text-content-primary mb-2">
              Share Export
            </h2>
            <p className="text-content-secondary text-sm font-sans mb-4">
              Create a shareable link for this {format.toUpperCase()} export. Links expire based on your plan.
            </p>

            {!shareUrl ? (
              <div className="space-y-4">
                {/* Passcode input */}
                <div>
                  <label htmlFor="share-passcode" className="block text-xs font-sans font-medium text-content-secondary mb-1">
                    Passcode (optional, min 4 characters)
                  </label>
                  <input
                    id="share-passcode"
                    type="text"
                    value={passcode}
                    onChange={(e) => setPasscode(e.target.value)}
                    placeholder="Enter a passcode..."
                    className="w-full bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder:text-content-muted"
                  />
                </div>

                {/* Single-use checkbox */}
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={singleUse}
                    onChange={(e) => setSingleUse(e.target.checked)}
                    className="rounded border-theme text-sage-600 focus:ring-sage-500"
                  />
                  <span className="text-sm font-sans text-content-secondary">
                    Single-use link (expires after first download)
                  </span>
                </label>

                <button
                  onClick={handleCreate}
                  disabled={isCreating || (passcode.length > 0 && passcode.length < 4)}
                  className="w-full px-5 py-2.5 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isCreating ? 'Creating...' : 'Create Share Link'}
                </button>
              </div>
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
                    className="px-4 py-2 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm font-medium hover:bg-sage-700 transition-colors whitespace-nowrap"
                  >
                    {copied ? 'Copied!' : 'Copy'}
                  </button>
                </div>
                {passcode.length >= 4 && (
                  <p className="text-clay-600 text-xs font-sans">
                    This link is passcode-protected. Share the passcode separately for security.
                  </p>
                )}
                <p className="text-content-tertiary text-xs font-sans">
                  Anyone with this link{passcode.length >= 4 ? ' and the passcode' : ''} can access the export.
                  {singleUse ? ' This link will expire after the first download.' : ''}
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
