'use client'

import { motion } from 'framer-motion'
import type { APDataQuality } from '@/types/apTesting'

function qualityColor(score: number): string {
  if (score >= 90) return 'text-sage-400'
  if (score >= 70) return 'text-oatmeal-300'
  return 'text-clay-400'
}

function qualityLabel(score: number): string {
  if (score >= 90) return 'Excellent'
  if (score >= 70) return 'Good'
  if (score >= 50) return 'Fair'
  return 'Poor'
}

interface APDataQualityBadgeProps {
  quality: APDataQuality
}

export function APDataQualityBadge({ quality }: APDataQualityBadgeProps) {
  const color = qualityColor(quality.completeness_score)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-serif text-sm text-oatmeal-300">Data Quality</h3>
        <div className="flex items-center gap-2">
          <span className={`font-mono text-lg ${color}`}>
            {quality.completeness_score.toFixed(0)}%
          </span>
          <span className="text-oatmeal-600 text-xs font-sans">
            {qualityLabel(quality.completeness_score)}
          </span>
        </div>
      </div>

      {/* Quality bar */}
      <div className="w-full h-2 bg-obsidian-700 rounded-full overflow-hidden mb-4">
        <motion.div
          className={`h-full rounded-full ${quality.completeness_score >= 90 ? 'bg-sage-500' : quality.completeness_score >= 70 ? 'bg-oatmeal-400' : 'bg-clay-500'}`}
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
              <span className="font-sans text-xs text-oatmeal-500 capitalize">
                {field.replace(/_/g, ' ')}
              </span>
              <span className={`font-mono text-xs ${rate >= 0.9 ? 'text-sage-500' : rate >= 0.5 ? 'text-oatmeal-400' : 'text-clay-500'}`}>
                {(rate * 100).toFixed(0)}%
              </span>
            </div>
          ))
        }
      </div>

      {/* Issues */}
      {quality.detected_issues.length > 0 && (
        <div className="mt-3 pt-3 border-t border-obsidian-600/20">
          {quality.detected_issues.map((issue, i) => (
            <p key={i} className="font-sans text-xs text-oatmeal-500 mt-1">
              <span className="text-clay-500 mr-1">!</span> {issue}
            </p>
          ))}
        </div>
      )}

      <p className="font-sans text-xs text-oatmeal-600 mt-3">
        {quality.total_rows.toLocaleString()} payments analyzed
      </p>
    </motion.div>
  )
}
