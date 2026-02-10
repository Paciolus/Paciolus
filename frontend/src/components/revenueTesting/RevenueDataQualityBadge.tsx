'use client'

import { motion } from 'framer-motion'
import type { RevenueDataQuality } from '@/types/revenueTesting'

function qualityColor(score: number): string {
  if (score >= 90) return 'text-sage-600'
  if (score >= 70) return 'text-content-primary'
  return 'text-clay-600'
}

function qualityLabel(score: number): string {
  if (score >= 90) return 'Excellent'
  if (score >= 70) return 'Good'
  if (score >= 50) return 'Fair'
  return 'Poor'
}

interface RevenueDataQualityBadgeProps {
  quality: RevenueDataQuality
}

export function RevenueDataQualityBadge({ quality }: RevenueDataQualityBadgeProps) {
  const color = qualityColor(quality.completeness_score)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-surface-card border border-theme rounded-xl p-5 shadow-theme-card"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-serif text-sm text-content-primary">Data Quality</h3>
        <div className="flex items-center gap-2">
          <span className={`font-mono text-lg ${color}`}>
            {quality.completeness_score.toFixed(0)}%
          </span>
          <span className="text-content-tertiary text-xs font-sans">
            {qualityLabel(quality.completeness_score)}
          </span>
        </div>
      </div>

      {/* Quality bar */}
      <div className="w-full h-2 bg-oatmeal-100 rounded-full overflow-hidden mb-4">
        <motion.div
          className={`h-full rounded-full ${quality.completeness_score >= 90 ? 'bg-sage-500' : quality.completeness_score >= 70 ? 'bg-oatmeal-500' : 'bg-clay-500'}`}
          initial={{ width: 0 }}
          animate={{ width: `${quality.completeness_score}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' as const }}
        />
      </div>

      {/* Field fill rates */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
        {Object.entries(quality.field_fill_rates)
          .sort(([, a], [, b]) => b - a)
          .map(([field, rate]) => (
            <div key={field} className="flex items-center justify-between">
              <span className="font-sans text-xs text-content-secondary capitalize">
                {field.replace(/_/g, ' ')}
              </span>
              <span className={`font-mono text-xs ${rate >= 0.9 ? 'text-sage-600' : rate >= 0.5 ? 'text-content-secondary' : 'text-clay-600'}`}>
                {(rate * 100).toFixed(0)}%
              </span>
            </div>
          ))
        }
      </div>

      {/* Issues */}
      {quality.detected_issues.length > 0 && (
        <div className="mt-3 pt-3 border-t border-theme-divider">
          {quality.detected_issues.map((issue, i) => (
            <p key={i} className="font-sans text-xs text-content-secondary mt-1">
              <span className="text-clay-600 mr-1">!</span> {issue}
            </p>
          ))}
        </div>
      )}

      <p className="font-sans text-xs text-content-tertiary mt-3">
        {quality.total_rows.toLocaleString()} revenue entries analyzed
      </p>
    </motion.div>
  )
}
