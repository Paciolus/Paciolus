'use client'

import { useCallback, useEffect, useRef } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { PdfPreviewResult } from '@/types/pdf'

interface PdfExtractionPreviewProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  previewResult: PdfPreviewResult
}

const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
}

const modalVariants = {
  hidden: { opacity: 0, scale: 0.95, y: 20 },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { type: 'spring' as const, damping: 25, stiffness: 300 },
  },
  exit: { opacity: 0, scale: 0.95, y: 20, transition: { duration: 0.15 } },
}

function getConfidenceColor(value: number): string {
  if (value >= 0.6) return 'bg-sage-500'
  if (value >= 0.4) return 'bg-oatmeal-500'
  return 'bg-clay-500'
}

function getConfidenceTextColor(value: number): string {
  if (value >= 0.6) return 'text-sage-600'
  if (value >= 0.4) return 'text-oatmeal-600'
  return 'text-clay-600'
}

function getConfidenceLabel(value: number): string {
  if (value >= 0.8) return 'High'
  if (value >= 0.6) return 'Good'
  if (value >= 0.4) return 'Fair'
  return 'Low'
}

function MetricBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100)
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 text-xs text-content-secondary font-sans shrink-0">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-surface-card-secondary overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${getConfidenceColor(value)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`w-10 type-num-xs text-right ${getConfidenceTextColor(value)}`}>
        {pct}%
      </span>
    </div>
  )
}

export function PdfExtractionPreview({
  isOpen,
  onClose,
  onConfirm,
  previewResult,
}: PdfExtractionPreviewProps) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  // Focus trap: auto-focus confirm button on open
  useEffect(() => {
    if (isOpen && confirmRef.current) {
      confirmRef.current.focus()
    }
  }, [isOpen])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    },
    [onClose],
  )

  const passesGate = previewResult.passes_quality_gate

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          variants={overlayVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          onKeyDown={handleKeyDown}
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-obsidian-900/80 backdrop-blur-xs"
            onClick={onClose}
            role="presentation"
          />

          {/* Modal */}
          <motion.div
            className="relative w-full max-w-xl bg-surface-card rounded-2xl shadow-elevated border border-theme overflow-hidden"
            variants={modalVariants}
            role="dialog"
            aria-modal="true"
            aria-labelledby="pdf-preview-title"
          >
            {/* Header */}
            <div className="px-6 pt-6 pb-4 border-b border-theme">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-sage-500/10 flex items-center justify-center">
                  <svg className="w-5 h-5 text-sage-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                  </svg>
                </div>
                <div>
                  <h2 id="pdf-preview-title" className="font-serif text-lg text-content-primary">
                    PDF Extraction Preview
                  </h2>
                  <p className="text-xs text-content-secondary font-sans">
                    {previewResult.filename} &middot; {previewResult.page_count} page{previewResult.page_count !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            </div>

            {/* Quality Metrics */}
            <div className="px-6 py-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-sans text-content-primary font-medium">
                  Extraction Quality
                </span>
                <span className={`text-sm font-mono font-semibold ${getConfidenceTextColor(previewResult.extraction_confidence)}`}>
                  {Math.round(previewResult.extraction_confidence * 100)}% &middot; {getConfidenceLabel(previewResult.extraction_confidence)}
                </span>
              </div>
              <MetricBar label="Headers" value={previewResult.header_confidence} />
              <MetricBar label="Numeric data" value={previewResult.numeric_density} />
              <MetricBar label="Row consistency" value={previewResult.row_consistency} />
            </div>

            {/* Remediation Hints (when quality gate fails) */}
            {!passesGate && previewResult.remediation_hints.length > 0 && (
              <div className="mx-6 mb-4 p-3 rounded-lg border-l-4 border-clay-500 bg-clay-500/5">
                <p className="text-xs font-sans text-clay-600 font-medium mb-1">
                  Quality below threshold
                </p>
                {previewResult.remediation_hints.map((hint, i) => (
                  <p key={i} className="text-xs font-sans text-content-secondary mt-1">
                    {hint}
                  </p>
                ))}
              </div>
            )}

            {/* Sample Data Table */}
            {previewResult.column_names.length > 0 && previewResult.sample_rows.length > 0 && (
              <div className="px-6 pb-4">
                <p className="text-xs text-content-secondary font-sans mb-2">
                  Sample data ({previewResult.sample_rows.length} row{previewResult.sample_rows.length !== 1 ? 's' : ''})
                </p>
                <div className="overflow-x-auto rounded-lg border border-theme">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="bg-surface-card-secondary">
                        {previewResult.column_names.map((col, i) => (
                          <th key={i} className="px-3 py-2 text-left font-sans font-medium text-content-secondary whitespace-nowrap">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewResult.sample_rows.map((row, rowIdx) => (
                        <tr key={rowIdx} className="border-t border-theme">
                          {previewResult.column_names.map((col, colIdx) => (
                            <td key={colIdx} className="px-3 py-1.5 font-mono text-content-primary whitespace-nowrap">
                              {row[col] ?? ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Footer Actions */}
            <div className="px-6 py-4 border-t border-theme flex items-center justify-between">
              <p className="text-xs text-content-tertiary font-sans">
                {previewResult.tables_found} table{previewResult.tables_found !== 1 ? 's' : ''} detected
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-sans text-content-secondary border border-theme rounded-lg
                    hover:bg-surface-card-secondary transition-colors"
                >
                  Cancel
                </button>
                <button
                  ref={confirmRef}
                  type="button"
                  onClick={onConfirm}
                  disabled={!passesGate}
                  className={`px-4 py-2 text-sm font-sans rounded-lg transition-colors ${
                    passesGate
                      ? 'bg-sage-500 text-white hover:bg-sage-600'
                      : 'bg-surface-card-secondary text-content-tertiary cursor-not-allowed'
                  }`}
                >
                  Proceed
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
