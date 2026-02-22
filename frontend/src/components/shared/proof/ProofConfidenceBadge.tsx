'use client'

import type { ProofConfidenceLevel } from '@/types/proof'

// =============================================================================
// Confidence badge styling per level
// =============================================================================

const BADGE_STYLES: Record<ProofConfidenceLevel, { bg: string; text: string; border: string; label: string }> = {
  strong: { bg: 'bg-sage-50', text: 'text-sage-700', border: 'border-sage-200', label: 'Strong' },
  adequate: { bg: 'bg-sage-50/60', text: 'text-sage-600', border: 'border-sage-200/60', label: 'Adequate' },
  limited: { bg: 'bg-oatmeal-100', text: 'text-oatmeal-700', border: 'border-oatmeal-300', label: 'Limited' },
  insufficient: { bg: 'bg-clay-50', text: 'text-clay-700', border: 'border-clay-200', label: 'Insufficient' },
}

// =============================================================================
// Component
// =============================================================================

export interface ProofConfidenceBadgeProps {
  level: ProofConfidenceLevel
  narrative?: string
}

export function ProofConfidenceBadge({ level, narrative }: ProofConfidenceBadgeProps) {
  const style = BADGE_STYLES[level]

  return (
    <div className={`${style.bg} border ${style.border} rounded-lg p-3`}>
      <div className="flex items-center gap-2 mb-1">
        <span className={`font-serif text-xs font-medium ${style.text}`}>
          Confidence: {style.label}
        </span>
      </div>
      {narrative && (
        <p className="font-sans text-xs text-content-secondary leading-relaxed">
          {narrative}
        </p>
      )}
    </div>
  )
}
