'use client'

import { type ReactNode } from 'react'
import { motion } from 'framer-motion'
import type { TestingRiskTier } from '@/types/testingShared'
import { TESTING_RISK_TIER_COLORS, TESTING_RISK_TIER_LABELS } from '@/types/testingShared'
import { TIMING, EASE } from '@/utils/motionTokens'

const TIER_LEFT_BORDER: Record<TestingRiskTier, string> = {
  low: 'border-l-sage-500',
  elevated: 'border-l-oatmeal-500',
  moderate: 'border-l-clay-400',
  high: 'border-l-clay-500',
  critical: 'border-l-clay-600',
}

const TIER_DOT_COLOR: Record<TestingRiskTier, string> = {
  low: 'bg-sage-500',
  elevated: 'bg-oatmeal-500',
  moderate: 'bg-clay-500',
  high: 'bg-clay-500',
  critical: 'bg-clay-500',
}

export interface TestingScoreCardProps {
  score: number
  risk_tier: TestingRiskTier
  tests_run: number
  total_entries: number
  total_flagged: number
  flag_rate: number
  flags_by_severity: { high: number; medium: number; low: number }
  top_findings: string[]
  entity_label: string
  title?: string
  extra_content?: ReactNode
  /** Override the subtitle line below the title */
  subtitle_override?: ReactNode
  /** Override the 3-column stats grid */
  stats_override?: ReactNode
  /** Custom renderer for top findings (e.g. Payroll structured findings) */
  findings_renderer?: (findings: string[]) => ReactNode
}

export function TestingScoreCard({
  score,
  risk_tier,
  tests_run,
  total_entries,
  total_flagged,
  flag_rate,
  flags_by_severity,
  top_findings,
  entity_label,
  title = 'Composite Risk Score',
  extra_content,
  subtitle_override,
  stats_override,
  findings_renderer,
}: TestingScoreCardProps) {
  const colors = TESTING_RISK_TIER_COLORS[risk_tier]
  const borderAccent = TIER_LEFT_BORDER[risk_tier]
  const dotColor = TIER_DOT_COLOR[risk_tier]

  const isHighRisk = risk_tier === 'high' || risk_tier === 'critical'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={isHighRisk
        ? { duration: TIMING.settle, ease: EASE.emphasis }
        : { duration: 0.5, type: 'spring' as const }
      }
      className={`relative overflow-hidden rounded-2xl bg-surface-card border border-theme border-l-4 ${borderAccent} p-8 shadow-theme-card`}
    >
      <div className="flex flex-col md:flex-row items-center md:items-start gap-8">
        {/* Score Circle */}
        <div className="relative flex-shrink-0">
          <svg width="140" height="140" viewBox="0 0 140 140">
            <circle
              cx="70" cy="70" r="60"
              fill="none" stroke="currentColor"
              className="text-oatmeal-300"
              strokeWidth="8"
            />
            <motion.circle
              cx="70" cy="70" r="60"
              fill="none"
              className={colors.text}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 60}`}
              strokeDashoffset={2 * Math.PI * 60 * (1 - score / 100)}
              initial={{ strokeDashoffset: 2 * Math.PI * 60 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 60 * (1 - score / 100) }}
              transition={{ duration: 1.2, ease: 'easeOut' as const }}
              transform="rotate(-90 70 70)"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              className={`type-num-xl ${colors.text}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
            >
              {score.toFixed(0)}
            </motion.span>
            <span className="text-content-secondary text-xs font-sans">/ 100</span>
          </div>
        </div>

        {/* Details */}
        <div className="flex-1 text-center md:text-left">
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full ${colors.bg} border ${colors.border} mb-3`}>
            <div className={`w-2 h-2 rounded-full ${dotColor}`} />
            <span className={`text-sm font-sans font-medium ${colors.text}`}>
              {TESTING_RISK_TIER_LABELS[risk_tier]}
            </span>
          </div>

          <h3 className="font-serif text-xl text-content-primary mb-1">
            {title}
          </h3>

          {subtitle_override ?? (
            <p className="font-sans text-content-secondary text-sm mb-4">
              {tests_run} tests analyzed {total_entries.toLocaleString()} {entity_label}
            </p>
          )}

          {stats_override ?? (
            <div className="grid grid-cols-3 gap-4">
              <div>
                <span className="type-num text-content-primary">{total_flagged.toLocaleString()}</span>
                <p className="text-content-secondary text-xs font-sans">Flagged</p>
              </div>
              <div>
                <span className="type-num text-content-primary">{(flag_rate * 100).toFixed(1)}%</span>
                <p className="text-content-secondary text-xs font-sans">Flag Rate</p>
              </div>
              <div>
                <span className="type-num text-clay-600">{flags_by_severity.high}</span>
                <span className="type-num-sm text-content-secondary"> / {flags_by_severity.medium}</span>
                <span className="type-num-sm text-content-tertiary"> / {flags_by_severity.low}</span>
                <p className="text-content-secondary text-xs font-sans">H / M / L</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Extra content slot (before findings) */}
      {extra_content}

      {/* Top findings */}
      {top_findings.length > 0 && (
        <div className="mt-6 pt-6 border-t border-theme-divider">
          <h4 className="font-sans text-xs text-content-secondary uppercase tracking-wider mb-3">Top Findings</h4>
          {findings_renderer ? (
            findings_renderer(top_findings)
          ) : (
            <div className="space-y-1.5">
              {top_findings.slice(0, 3).map((finding, i) => (
                <p key={i} className="font-sans text-sm text-content-primary">
                  <span className="text-content-tertiary mr-2">{i + 1}.</span>
                  {finding}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </motion.div>
  )
}
