'use client'

import { motion } from 'framer-motion'
import type { JECompositeScore, JERiskTier } from '@/types/jeTesting'
import { RISK_TIER_COLORS, RISK_TIER_LABELS } from '@/types/jeTesting'

const tierGradients: Record<JERiskTier, string> = {
  low: 'from-sage-500/20 to-sage-500/5',
  elevated: 'from-oatmeal-500/15 to-oatmeal-500/5',
  moderate: 'from-clay-500/10 to-clay-500/5',
  high: 'from-clay-500/20 to-clay-500/5',
  critical: 'from-clay-500/30 to-clay-500/10',
}

interface JEScoreCardProps {
  score: JECompositeScore
}

export function JEScoreCard({ score }: JEScoreCardProps) {
  const tier = score.risk_tier
  const colors = RISK_TIER_COLORS[tier]
  const gradient = tierGradients[tier]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, type: 'spring' as const }}
      className={`relative overflow-hidden rounded-2xl border ${colors.border} bg-gradient-to-br ${gradient} p-8`}
    >
      <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
        {/* Score Circle */}
        <div className="relative flex-shrink-0">
          <svg width="140" height="140" viewBox="0 0 140 140">
            <circle
              cx="70" cy="70" r="60"
              fill="none" stroke="currentColor"
              className="text-obsidian-700"
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
            <span className="text-oatmeal-500 text-xs font-sans">/ 100</span>
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 text-center md:text-left">
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${colors.bg} border ${colors.border} mb-3`}>
            <div className={`w-2 h-2 rounded-full ${tier === 'low' ? 'bg-sage-400' : tier === 'elevated' ? 'bg-oatmeal-400' : 'bg-clay-400'}`} />
            <span className={`text-sm font-sans font-medium ${colors.text}`}>
              {RISK_TIER_LABELS[tier]}
            </span>
          </div>

          <h3 className="font-serif text-xl text-oatmeal-100 mb-1">
            Composite Risk Score
          </h3>
          <p className="font-sans text-oatmeal-500 text-sm mb-4">
            {score.tests_run} tests analyzed {score.total_entries.toLocaleString()} journal entries
          </p>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <span className="font-mono text-lg text-oatmeal-200">{score.total_flagged.toLocaleString()}</span>
              <p className="text-oatmeal-500 text-xs font-sans">Flagged</p>
            </div>
            <div>
              <span className="font-mono text-lg text-oatmeal-200">{(score.flag_rate * 100).toFixed(1)}%</span>
              <p className="text-oatmeal-500 text-xs font-sans">Flag Rate</p>
            </div>
            <div>
              <span className="font-mono text-lg text-clay-400">{score.flags_by_severity.high}</span>
              <span className="font-mono text-sm text-oatmeal-400"> / {score.flags_by_severity.medium}</span>
              <span className="font-mono text-sm text-oatmeal-600"> / {score.flags_by_severity.low}</span>
              <p className="text-oatmeal-500 text-xs font-sans">H / M / L</p>
            </div>
          </div>
        </div>
      </div>

      {/* Top findings */}
      {score.top_findings.length > 0 && (
        <div className="mt-6 pt-6 border-t border-obsidian-600/30">
          <h4 className="font-sans text-xs text-oatmeal-500 uppercase tracking-wider mb-3">Top Findings</h4>
          <div className="space-y-1.5">
            {score.top_findings.slice(0, 3).map((finding, i) => (
              <p key={i} className="font-sans text-sm text-oatmeal-300">
                <span className="text-oatmeal-600 mr-2">{i + 1}.</span>
                {finding}
              </p>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
