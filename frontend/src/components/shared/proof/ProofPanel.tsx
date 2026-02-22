'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { ProofSummary, ProofTestDetail } from '@/types/proof'
import { ProofTraceBar } from './ProofTraceBar'
import { ProofConfidenceBadge } from './ProofConfidenceBadge'

// =============================================================================
// Test detail table row
// =============================================================================

const STATUS_INDICATOR: Record<ProofTestDetail['status'], { icon: string; color: string; label: string }> = {
  clear: { icon: '\u25CF', color: 'text-sage-500', label: 'clear' },
  flagged: { icon: '\u25B2', color: 'text-oatmeal-600', label: 'flagged' },
  skipped: { icon: '\u2014', color: 'text-oatmeal-400', label: 'skipped' },
}

function TestDetailRow({ detail }: { detail: ProofTestDetail }) {
  const indicator = STATUS_INDICATOR[detail.status]

  return (
    <tr className="border-b border-oatmeal-200/50 last:border-b-0">
      <td className="py-1.5 pr-3 font-sans text-xs text-content-primary">{detail.testName}</td>
      <td className="py-1.5 pr-3">
        <span className={`font-sans text-xs ${indicator.color}`}>
          {indicator.icon} {indicator.label}
        </span>
      </td>
      <td className="py-1.5 type-num-xs text-content-secondary text-right">
        {detail.status === 'skipped' ? '\u2014' : detail.flaggedCount}
      </td>
    </tr>
  )
}

// =============================================================================
// ProofPanel — Collapsible detail view
// =============================================================================

export interface ProofPanelProps {
  proof: ProofSummary
  defaultExpanded?: boolean
}

export function ProofPanel({ proof, defaultExpanded = false }: ProofPanelProps) {
  const [expanded, setExpanded] = useState(defaultExpanded)

  return (
    <div className="border border-oatmeal-200 rounded-xl overflow-hidden">
      {/* Toggle header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 bg-surface-card hover:bg-surface-card-secondary transition-colors text-left"
        aria-expanded={expanded}
        aria-controls="proof-panel-content"
      >
        <span className="font-serif text-sm text-content-primary">Evidence Trace</span>
        <svg
          className={`w-4 h-4 text-content-tertiary transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expandable content */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            id="proof-panel-content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' as const }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4">
              {/* Trace bar */}
              <ProofTraceBar testDetails={proof.testDetails} />

              {/* Test detail table */}
              {proof.testDetails.length > 0 && (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-oatmeal-300">
                        <th className="py-1.5 pr-3 text-left font-sans text-xs font-medium text-content-secondary">Test</th>
                        <th className="py-1.5 pr-3 text-left font-sans text-xs font-medium text-content-secondary">Status</th>
                        <th className="py-1.5 text-right font-sans text-xs font-medium text-content-secondary">Flagged</th>
                      </tr>
                    </thead>
                    <tbody>
                      {proof.testDetails.map((detail) => (
                        <TestDetailRow key={detail.testKey} detail={detail} />
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Confidence badge */}
              <ProofConfidenceBadge
                level={proof.overallLevel}
                narrative={proof.narrativeCopy}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
