'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import type { PreFlightReport, PreFlightIssue, PreFlightColumnQuality } from '@/types/preflight'

interface PreFlightSummaryProps {
  report: PreFlightReport
  onProceed: () => void
  onExportPDF: () => void
  onExportCSV: () => void
}

function scoreColor(score: number): string {
  if (score >= 80) return 'text-sage-600'
  if (score >= 50) return 'text-oatmeal-600'
  return 'text-clay-600'
}

function scoreBarColor(score: number): string {
  if (score >= 80) return 'bg-sage-500'
  if (score >= 50) return 'bg-oatmeal-400'
  return 'bg-clay-500'
}

function severityBadge(severity: string): string {
  switch (severity) {
    case 'high': return 'bg-clay-50 text-clay-700 border-clay-200'
    case 'medium': return 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300'
    case 'low': return 'bg-sage-50 text-sage-700 border-sage-200'
    default: return 'bg-oatmeal-50 text-content-secondary border-oatmeal-200'
  }
}

function statusIcon(status: string): string {
  switch (status) {
    case 'found': return '✓'
    case 'low_confidence': return '?'
    case 'missing': return '✕'
    default: return '—'
  }
}

function statusColor(status: string): string {
  switch (status) {
    case 'found': return 'text-sage-600'
    case 'low_confidence': return 'text-oatmeal-600'
    case 'missing': return 'text-clay-600'
    default: return 'text-content-secondary'
  }
}

const SEVERITY_ORDER: Record<string, number> = { high: 0, medium: 1, low: 2 }

function sortBySeverity(issues: PreFlightIssue[]): PreFlightIssue[] {
  return [...issues].sort((a, b) =>
    (SEVERITY_ORDER[a.severity] ?? 3) - (SEVERITY_ORDER[b.severity] ?? 3)
  )
}

export function PreFlightSummary({ report, onProceed, onExportPDF, onExportCSV }: PreFlightSummaryProps) {
  const [expandedIssue, setExpandedIssue] = useState<number | null>(null)
  const sortedIssues = sortBySeverity(report.issues)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      {/* Readiness Score Card */}
      <div className="theme-card p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-serif text-lg text-content-primary">Data Readiness</h3>
          <span className={`font-mono text-2xl font-bold ${scoreColor(report.readiness_score)}`}>
            {report.readiness_score.toFixed(0)}
          </span>
        </div>

        <div className="w-full h-3 bg-oatmeal-100 rounded-full overflow-hidden mb-2">
          <motion.div
            className={`h-full rounded-full ${scoreBarColor(report.readiness_score)}`}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: report.readiness_score / 100 }}
            style={{ transformOrigin: 'left' }}
            transition={{ duration: 0.8, ease: 'easeOut' as const }}
          />
        </div>

        <div className="flex items-center justify-between text-sm">
          <span className={`font-sans font-medium ${scoreColor(report.readiness_score)}`}>
            {report.readiness_label}
          </span>
          <span className="font-sans text-content-tertiary">
            {report.row_count.toLocaleString()} rows &middot; {report.column_count} columns
          </span>
        </div>
      </div>

      {/* Column Detection Grid */}
      {report.columns.length > 0 && (
        <div className="theme-card p-5">
          <h4 className="font-serif text-sm text-content-primary mb-3">Column Detection</h4>
          <div className="grid grid-cols-3 gap-3">
            {report.columns.map((col: PreFlightColumnQuality) => (
              <div
                key={col.role}
                className="flex items-center gap-2 p-2 rounded-lg bg-surface-card-secondary"
              >
                <span className={`font-mono text-base ${statusColor(col.status)}`}>
                  {statusIcon(col.status)}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-sans text-xs text-content-secondary capitalize">{col.role}</p>
                  <p className="font-mono text-xs text-content-primary truncate">
                    {col.detected_name || 'Not found'}
                  </p>
                </div>
                <span className="font-mono text-xs text-content-tertiary">
                  {(col.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues List */}
      {sortedIssues.length > 0 && (
        <div className="theme-card p-5">
          <h4 className="font-serif text-sm text-content-primary mb-3">
            Issues ({sortedIssues.length})
          </h4>
          <div className="space-y-2">
            {sortedIssues.map((issue: PreFlightIssue, idx: number) => (
              <div key={idx} className="border border-theme-divider rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedIssue(expandedIssue === idx ? null : idx)}
                  className="w-full flex items-center gap-3 p-3 text-left hover:bg-surface-card-secondary transition-colors"
                >
                  <span className={`inline-flex px-2 py-0.5 rounded-sm text-xs font-sans font-medium border ${severityBadge(issue.severity)}`}>
                    {issue.severity.toUpperCase()}
                  </span>
                  <span className="font-sans text-sm text-content-primary flex-1">{issue.message}</span>
                  <svg
                    className={`w-4 h-4 text-content-tertiary transition-transform ${expandedIssue === idx ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {expandedIssue === idx && (
                  <div className="px-3 pb-3 pt-1 border-t border-theme-divider bg-surface-card-secondary">
                    <p className="font-sans text-xs text-content-secondary">{issue.remediation}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No issues */}
      {sortedIssues.length === 0 && (
        <div className="theme-card p-5 text-center">
          <p className="font-sans text-sm text-sage-600">No data quality issues detected.</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={onExportPDF}
            className="px-3 py-1.5 text-xs font-sans font-medium text-content-secondary border border-theme-divider rounded-lg hover:bg-surface-card-secondary transition-colors"
          >
            Export PDF
          </button>
          <button
            onClick={onExportCSV}
            className="px-3 py-1.5 text-xs font-sans font-medium text-content-secondary border border-theme-divider rounded-lg hover:bg-surface-card-secondary transition-colors"
          >
            Export CSV
          </button>
        </div>
        <button
          onClick={onProceed}
          className="px-5 py-2 text-sm font-sans font-semibold text-white bg-sage-600 hover:bg-sage-700 rounded-lg transition-colors"
        >
          Proceed to Full Analysis
        </button>
      </div>
    </motion.div>
  )
}
