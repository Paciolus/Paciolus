'use client'

import { motion } from 'framer-motion'
import type { FACompositeScore, FARiskTier } from '@/types/fixedAssetTesting'
import { FA_RISK_TIER_COLORS, FA_RISK_TIER_LABELS } from '@/types/fixedAssetTesting'

const tierBorderAccent: Record<FARiskTier, string> = {
  low: 'border-l-sage-500',
  elevated: 'border-l-oatmeal-500',
  moderate: 'border-l-clay-400',
  high: 'border-l-clay-500',
  critical: 'border-l-clay-600',
}

interface FixedAssetScoreCardProps {
  score: FACompositeScore
}

export function FixedAssetScoreCard({ score }: FixedAssetScoreCardProps) {
  const tier = score.risk_tier
  const colors = FA_RISK_TIER_COLORS[tier]
  const borderAccent = tierBorderAccent[tier]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, type: 'spring' as const }}
      className={`bg-surface-card border border-theme border-l-4 ${borderAccent} rounded-2xl p-8 shadow-theme-card`}
    >
      <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
        {/* Score Circle */}
        <div className="relative flex-shrink-0">
          <svg width="140" height="140" viewBox="0 0 140 140">
            <circle
              cx="70" cy="70" r="60"
              fill="none" stroke="currentColor"
              className="text-oatmeal-200"
              strokeWidth="8"
            />
            <motion.circle
              cx="70" cy="70" r="60"
              fill="none"
              className={colors.text}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 60}`}
              strokeDashoffset={2 * Math.PI * 60 * (1 - score.score / 100)}
              initial={{ strokeDashoffset: 2 * Math.PI * 60 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 60 * (1 - score.score / 100) }}
              transition={{ duration: 1.2, ease: 'easeOut' as const }}
              transform="rotate(-90 70 70)"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className={`font-mono text-3xl font-bold ${colors.text}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              {score.score.toFixed(0)}
            </motion.span>
            <span className="text-content-secondary text-xs font-sans">/ 100</span>
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 text-center md:text-left">
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${colors.bg} border ${colors.border} mb-3`}>
            <div className={`w-2 h-2 rounded-full ${tier === 'low' ? 'bg-sage-500' : tier === 'elevated' ? 'bg-oatmeal-500' : 'bg-clay-500'}`} />
            <span className={`text-sm font-sans font-medium ${colors.text}`}>
              {FA_RISK_TIER_LABELS[tier]}
            </span>
          </div>

          <h3 className="font-serif text-xl text-content-primary mb-1">
            Fixed Asset Risk Score
          </h3>
          <p className="font-sans text-content-secondary text-sm mb-4">
            {score.tests_run} tests analyzed {score.total_entries.toLocaleString()} fixed asset entries
          </p>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <span className="font-mono text-lg text-content-primary">{score.total_flagged.toLocaleString()}</span>
              <p className="text-content-secondary text-xs font-sans">Flagged</p>
            </div>
            <div>
              <span className="font-mono text-lg text-content-primary">{(score.flag_rate * 100).toFixed(1)}%</span>
              <p className="text-content-secondary text-xs font-sans">Flag Rate</p>
            </div>
            <div>
              <span className="font-mono text-lg text-clay-600">{score.flags_by_severity.high}</span>
              <span className="font-mono text-sm text-content-secondary"> / {score.flags_by_severity.medium}</span>
              <span className="font-mono text-sm text-content-tertiary"> / {score.flags_by_severity.low}</span>
              <p className="text-content-secondary text-xs font-sans">H / M / L</p>
            </div>
          </div>
        </div>
      </div>

      {/* Top findings */}
      {score.top_findings.length > 0 && (
        <div className="mt-6 pt-6 border-t border-theme">
          <h4 className="font-sans text-xs text-content-secondary uppercase tracking-wider mb-3">Top Findings</h4>
          <div className="space-y-1.5">
            {score.top_findings.slice(0, 3).map((finding, i) => (
              <p key={i} className="font-sans text-sm text-content-primary">
                <span className="text-content-tertiary mr-2">{i + 1}.</span>
                {finding}
              </p>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
