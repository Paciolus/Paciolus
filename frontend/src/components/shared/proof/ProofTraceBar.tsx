'use client'

import type { ProofTestDetail } from '@/types/proof'

// =============================================================================
// ProofTraceBar — Segmented horizontal bar showing test proportions
// =============================================================================

export interface ProofTraceBarProps {
  testDetails: ProofTestDetail[]
}

export function ProofTraceBar({ testDetails }: ProofTraceBarProps) {
  const total = testDetails.length
  if (total === 0) return null

  const clear = testDetails.filter((t) => t.status === 'clear').length
  const flagged = testDetails.filter((t) => t.status === 'flagged').length
  const skipped = testDetails.filter((t) => t.status === 'skipped').length

  const clearPct = (clear / total) * 100
  const flaggedPct = (flagged / total) * 100
  const skippedPct = (skipped / total) * 100

  return (
    <div>
      {/* Segmented bar */}
      <div className="flex h-2.5 rounded-full overflow-hidden bg-oatmeal-200" role="img" aria-label={`Test results: ${clear} clear, ${flagged} flagged, ${skipped} skipped out of ${total}`}>
        {clearPct > 0 && (
          <div
            className="bg-sage-500 transition-all duration-300"
            style={{ width: `${clearPct}%` }}
          />
        )}
        {flaggedPct > 0 && (
          <div
            className="bg-oatmeal-500 transition-all duration-300"
            style={{ width: `${flaggedPct}%` }}
          />
        )}
        {skippedPct > 0 && (
          <div
            className="bg-oatmeal-300 transition-all duration-300"
            style={{ width: `${skippedPct}%` }}
          />
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-1.5">
        <span className="flex items-center gap-1 text-xs font-sans text-content-secondary">
          <span className="inline-block w-2 h-2 rounded-full bg-sage-500" />
          clear: {clear}
        </span>
        <span className="flex items-center gap-1 text-xs font-sans text-content-secondary">
          <span className="inline-block w-2 h-2 rounded-full bg-oatmeal-500" />
          flagged: {flagged}
        </span>
        {skipped > 0 && (
          <span className="flex items-center gap-1 text-xs font-sans text-content-secondary">
            <span className="inline-block w-2 h-2 rounded-full bg-oatmeal-300" />
            skipped: {skipped}
          </span>
        )}
      </div>
    </div>
  )
}
