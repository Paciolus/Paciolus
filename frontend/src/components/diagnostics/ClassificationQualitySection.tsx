'use client'

import { useState } from 'react'

interface ClassificationIssue {
  account_number: string
  account_name: string
  issue_type: string
  description: string
  severity: string
  confidence: number
  category: string
  suggested_action: string
}

interface ClassificationQualityData {
  issues: ClassificationIssue[]
  quality_score: number
  issue_counts: Record<string, number>
  total_issues: number
}

interface ClassificationQualitySectionProps {
  data: ClassificationQualityData
}

const ISSUE_TYPE_LABELS: Record<string, string> = {
  duplicate_number: 'Duplicate Numbers',
  orphan_account: 'Orphan Accounts',
  unclassified: 'Unclassified',
  number_gap: 'Number Gaps',
  inconsistent_naming: 'Naming Issues',
  sign_anomaly: 'Sign Anomalies',
}

const ISSUE_TYPE_ICONS: Record<string, string> = {
  duplicate_number: '#',
  orphan_account: '?',
  unclassified: '!',
  number_gap: '...',
  inconsistent_naming: 'Aa',
  sign_anomaly: '+/-',
}

const SEVERITY_COLORS: Record<string, string> = {
  high: 'bg-clay-50 text-clay-700 border-clay-200',
  medium: 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300',
  low: 'bg-oatmeal-50 text-content-secondary border-oatmeal-200',
}

function getScoreColor(score: number): string {
  if (score >= 90) return 'text-sage-600'
  if (score >= 70) return 'text-oatmeal-700'
  return 'text-clay-600'
}

function getScoreBg(score: number): string {
  if (score >= 90) return 'bg-sage-50 border-sage-200'
  if (score >= 70) return 'bg-oatmeal-100 border-oatmeal-300'
  return 'bg-clay-50 border-clay-200'
}

export function ClassificationQualitySection({ data }: ClassificationQualitySectionProps) {
  const [expanded, setExpanded] = useState(false)
  const [activeType, setActiveType] = useState<string | null>(null)

  if (data.total_issues === 0 && data.quality_score >= 100) {
    return (
      <div className="bg-surface-card border border-theme rounded-xl p-6 shadow-theme-card">
        <div className="flex items-center justify-between">
          <h3 className="font-serif text-sm text-content-primary">Chart of Accounts Quality</h3>
          <div className={`px-3 py-1 rounded-full border ${getScoreBg(data.quality_score)}`}>
            <span className={`font-mono text-sm font-medium ${getScoreColor(data.quality_score)}`}>
              {data.quality_score.toFixed(0)}%
            </span>
          </div>
        </div>
        <p className="font-sans text-xs text-content-tertiary mt-2">
          No structural issues detected in the chart of accounts.
        </p>
      </div>
    )
  }

  // Group issues by type
  const issuesByType: Record<string, ClassificationIssue[]> = {}
  for (const issue of data.issues) {
    const key = issue.issue_type
    if (!issuesByType[key]) issuesByType[key] = []
    issuesByType[key].push(issue)
  }

  const typeKeys = Object.keys(issuesByType)
  const displayType = activeType || typeKeys[0] || null
  const displayIssues = displayType ? (issuesByType[displayType] || []) : []

  return (
    <div className="bg-surface-card border border-theme rounded-xl overflow-hidden shadow-theme-card">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-surface-card-secondary transition-colors"
      >
        <div className="flex items-center gap-3">
          <h3 className="font-serif text-sm text-content-primary">Chart of Accounts Quality</h3>
          <div className={`px-3 py-1 rounded-full border ${getScoreBg(data.quality_score)}`}>
            <span className={`font-mono text-sm font-medium ${getScoreColor(data.quality_score)}`}>
              {data.quality_score.toFixed(0)}%
            </span>
          </div>
          {data.total_issues > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-clay-50 border border-clay-200 text-xs font-sans text-clay-700">
              {data.total_issues} issue{data.total_issues !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <svg
          className={`w-5 h-5 text-content-tertiary transform transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-theme">
          {/* Issue Type Tabs */}
          <div className="flex flex-wrap gap-2 px-6 py-3 border-b border-theme">
            {typeKeys.map(type => (
              <button
                key={type}
                onClick={() => setActiveType(type)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-sans transition-colors ${
                  displayType === type
                    ? 'bg-sage-50 border border-sage-200 text-sage-700'
                    : 'bg-surface-card-secondary border border-theme text-content-tertiary hover:text-content-secondary'
                }`}
              >
                <span className="font-mono text-[10px] opacity-60">
                  {ISSUE_TYPE_ICONS[type] || '?'}
                </span>
                {ISSUE_TYPE_LABELS[type] || type}
                <span className="ml-1 opacity-60">({data.issue_counts[type] || 0})</span>
              </button>
            ))}
          </div>

          {/* Issue List */}
          <div className="px-6 py-3 max-h-[320px] overflow-y-auto">
            {displayIssues.length === 0 ? (
              <p className="text-center text-sm font-sans text-content-tertiary py-4">
                Select an issue type to view details.
              </p>
            ) : (
              <div className="space-y-2">
                {displayIssues.slice(0, 20).map((issue, idx) => (
                  <div
                    key={idx}
                    className="flex items-start justify-between gap-4 py-2 border-b border-theme-divider last:border-b-0"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {issue.account_number && (
                          <span className="font-mono text-xs text-content-secondary">{issue.account_number}</span>
                        )}
                        <span className="font-sans text-sm text-content-primary truncate">{issue.account_name}</span>
                      </div>
                      <p className="font-sans text-xs text-content-secondary mt-0.5">{issue.description}</p>
                      <p className="font-sans text-xs text-content-tertiary mt-0.5 italic">{issue.suggested_action}</p>
                    </div>
                    <span className={`inline-block px-1.5 py-0.5 rounded border text-xs font-sans whitespace-nowrap ${SEVERITY_COLORS[issue.severity] || SEVERITY_COLORS.low}`}>
                      {issue.severity}
                    </span>
                  </div>
                ))}
                {displayIssues.length > 20 && (
                  <p className="text-xs font-sans text-content-tertiary text-center pt-1">
                    + {displayIssues.length - 20} more
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
