'use client'

/**
 * SoD analysis results — Sprint 689b.
 *
 * Renders headline counters, per-user risk summary, and per-conflict
 * detail list. Styled to match the Paciolus Oat & Obsidian palette.
 */

import type { SODAnalysisResponse, SODRiskTier, SODSeverity } from '@/types/sod'

const SEVERITY_STYLES: Record<SODSeverity, string> = {
  high: 'bg-clay-100 text-clay-700 border-clay-200',
  medium: 'bg-oatmeal-200 text-obsidian-700 border-obsidian-200',
  low: 'bg-sage-50 text-sage-700 border-sage-200',
}

const RISK_TIER_STYLES: Record<SODRiskTier, string> = {
  high: 'bg-clay-600 text-oatmeal-50',
  moderate: 'bg-obsidian-600 text-oatmeal-50',
  low: 'bg-sage-600 text-oatmeal-50',
}

interface SODResultsProps {
  result: SODAnalysisResponse
}

export function SODResults({ result }: SODResultsProps) {
  const { conflicts, user_summaries, rules_evaluated, users_evaluated, users_with_conflicts, high_risk_users } = result

  return (
    <div className="space-y-6">
      {/* Headline counters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Counter label="Users evaluated" value={users_evaluated} />
        <Counter label="Rules evaluated" value={rules_evaluated} />
        <Counter label="Users with conflicts" value={users_with_conflicts} tone={users_with_conflicts > 0 ? 'warn' : 'ok'} />
        <Counter label="High-risk users" value={high_risk_users} tone={high_risk_users > 0 ? 'bad' : 'ok'} />
      </div>

      {/* User risk summary */}
      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Per-User Risk Summary</h3>
        {user_summaries.length === 0 ? (
          <p className="font-sans text-sm text-content-tertiary">No users in input.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-sans">
              <thead>
                <tr className="border-b border-theme text-left text-xs uppercase tracking-wider text-content-tertiary">
                  <th className="py-2 pr-3">User</th>
                  <th className="py-2 px-3 text-right">Conflicts</th>
                  <th className="py-2 px-3 text-right">High</th>
                  <th className="py-2 px-3 text-right">Med</th>
                  <th className="py-2 px-3 text-right">Low</th>
                  <th className="py-2 px-3 text-right">Score</th>
                  <th className="py-2 pl-3">Tier</th>
                </tr>
              </thead>
              <tbody>
                {user_summaries.map(s => (
                  <tr key={s.user_id} className="border-b border-theme/40 last:border-0">
                    <td className="py-2 pr-3">
                      <div className="font-medium text-content-primary">{s.user_name}</div>
                      <div className="font-mono text-xs text-content-tertiary">{s.user_id}</div>
                    </td>
                    <td className="py-2 px-3 text-right font-mono">{s.conflict_count}</td>
                    <td className="py-2 px-3 text-right font-mono text-clay-700">{s.high_severity_count}</td>
                    <td className="py-2 px-3 text-right font-mono">{s.medium_severity_count}</td>
                    <td className="py-2 px-3 text-right font-mono text-sage-700">{s.low_severity_count}</td>
                    <td className="py-2 px-3 text-right font-mono">{s.risk_score.toFixed(2)}</td>
                    <td className="py-2 pl-3">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-sans font-medium ${RISK_TIER_STYLES[s.risk_tier]}`}>
                        {s.risk_tier}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Conflict detail */}
      <section className="theme-card p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">
          Conflict Detail <span className="font-sans text-sm text-content-tertiary">({conflicts.length})</span>
        </h3>
        {conflicts.length === 0 ? (
          <p className="font-sans text-sm text-content-tertiary">No SoD conflicts detected across the supplied matrices.</p>
        ) : (
          <ul className="space-y-3">
            {conflicts.map((c, idx) => (
              <li key={`${c.user_id}-${c.rule_code}-${idx}`} className="border border-theme rounded-lg p-4">
                <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
                  <div>
                    <div className="font-serif text-content-primary">
                      {c.rule_code} &mdash; {c.rule_title}
                    </div>
                    <div className="font-sans text-xs text-content-tertiary mt-1">
                      {c.user_name} <span className="font-mono">({c.user_id})</span>
                    </div>
                  </div>
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-sans font-medium border ${SEVERITY_STYLES[c.severity]}`}>
                    {c.severity}
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-sans text-content-secondary mb-2">
                  <div>
                    <span className="text-content-tertiary">Triggering permissions: </span>
                    <span className="font-mono">{c.triggering_permissions.join(', ') || '—'}</span>
                  </div>
                  <div>
                    <span className="text-content-tertiary">Via roles: </span>
                    <span className="font-mono">{c.triggering_roles.join(', ') || '—'}</span>
                  </div>
                </div>
                {c.mitigation && (
                  <p className="text-xs font-sans text-content-secondary">
                    <span className="text-content-tertiary">Mitigation: </span>{c.mitigation}
                  </p>
                )}
                {c.rationale && (
                  <p className="text-xs font-sans text-content-tertiary mt-1 italic">{c.rationale}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

interface CounterProps {
  label: string
  value: number
  tone?: 'ok' | 'warn' | 'bad'
}

function Counter({ label, value, tone = 'ok' }: CounterProps) {
  const toneClass =
    tone === 'bad'
      ? 'text-clay-700'
      : tone === 'warn'
        ? 'text-obsidian-700'
        : 'text-sage-700'
  return (
    <div className="theme-card p-4">
      <div className="text-xs font-sans uppercase tracking-wider text-content-tertiary mb-1">{label}</div>
      <div className={`font-mono text-2xl ${toneClass}`}>{value}</div>
    </div>
  )
}
