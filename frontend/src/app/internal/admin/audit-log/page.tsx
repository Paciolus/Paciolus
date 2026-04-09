'use client'

/**
 * Internal Admin — Audit Log Page
 * Sprint 590: Superadmin CRM
 *
 * Paginated admin action audit trail.
 */

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { Reveal } from '@/components/ui/Reveal'
import { useInternalAdmin } from '@/hooks/useInternalAdmin'

const ACTION_TYPES = [
  '',
  'plan_override',
  'trial_extension',
  'credit_issued',
  'refund_issued',
  'force_cancel',
  'impersonation_start',
  'impersonation_end',
  'session_revoke',
]

export default function AuditLogPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuthSession()
  const { auditLog, isLoading, error, fetchAuditLog } = useInternalAdmin()

  const [actionFilter, setActionFilter] = useState('')
  const [page, setPage] = useState(0)
  const pageSize = 50

  const load = useCallback(() => {
    const params: Record<string, string> = {
      offset: String(page * pageSize),
      limit: String(pageSize),
    }
    if (actionFilter) params.action_type = actionFilter
    fetchAuditLog(params)
  }, [page, actionFilter, fetchAuditLog, pageSize])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push('/login')
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) load()
  }, [isAuthenticated, load])

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  const totalPages = auditLog ? Math.ceil(auditLog.total / pageSize) : 0

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="pt-8 pb-16 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Breadcrumb */}
          <button onClick={() => router.push('/internal/admin')} className="text-sage-600 font-sans text-sm hover:underline mb-4 block">
            ← Back to customers
          </button>

          <Reveal>
            <h1 className="text-2xl font-serif font-bold text-content-primary mb-6">Admin Audit Log</h1>
          </Reveal>

          {/* Filter */}
          <Reveal delay={0.06}>
            <div className="bg-surface-card border border-theme rounded-xl p-4 mb-6">
              <div className="flex gap-3 items-end">
                <div>
                  <label htmlFor="audit-action-filter" className="block text-xs font-sans text-content-tertiary mb-1">Action Type</label>
                  <select
                    id="audit-action-filter"
                    value={actionFilter}
                    onChange={e => { setActionFilter(e.target.value); setPage(0) }}
                    className="px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary"
                  >
                    {ACTION_TYPES.map(a => (
                      <option key={a} value={a}>{a || 'All Actions'}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </Reveal>

          {error && (
            <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-xl p-4 mb-6 text-sm font-sans">{error}</div>
          )}

          {/* Table */}
          <Reveal delay={0.12}>
            <div className="bg-surface-card border border-theme rounded-xl overflow-hidden">
              {isLoading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="w-8 h-8 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm font-sans">
                    <thead>
                      <tr className="border-b border-theme bg-surface-input/50">
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Timestamp</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Admin</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Action</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Target</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditLog?.items.map(entry => {
                        let details = ''
                        if (entry.details_json) {
                          try {
                            const d = JSON.parse(entry.details_json)
                            details = d.reason || JSON.stringify(d).slice(0, 80)
                          } catch {
                            details = entry.details_json.slice(0, 80)
                          }
                        }

                        return (
                          <tr key={entry.id} className="border-b border-theme last:border-0">
                            <td className="py-3 px-4 text-content-secondary text-xs whitespace-nowrap">
                              {new Date(entry.created_at).toLocaleString()}
                            </td>
                            <td className="py-3 px-4 text-content-primary">{entry.admin_email || `User #${entry.admin_user_id}`}</td>
                            <td className="py-3 px-4">
                              <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-surface-input text-content-primary">
                                {entry.action_type}
                              </span>
                            </td>
                            <td className="py-3 px-4 font-mono text-content-secondary text-xs">
                              {entry.target_org_id ? `Org #${entry.target_org_id}` : entry.target_user_id ? `User #${entry.target_user_id}` : '—'}
                            </td>
                            <td className="py-3 px-4 text-content-tertiary text-xs max-w-[200px] truncate">{details}</td>
                          </tr>
                        )
                      })}
                      {(!auditLog?.items.length) && (
                        <tr>
                          <td colSpan={5} className="py-12 text-center text-content-tertiary">No audit entries.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-theme">
                  <span className="text-xs text-content-tertiary font-sans">{auditLog?.total ?? 0} total entries</span>
                  <div className="flex gap-2">
                    <button disabled={page === 0} onClick={() => setPage(p => Math.max(0, p - 1))} className="px-3 py-1 border border-theme rounded text-sm font-sans disabled:opacity-40 hover:bg-surface-input transition-colors">Prev</button>
                    <span className="px-3 py-1 text-sm text-content-secondary font-sans">{page + 1} / {totalPages}</span>
                    <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)} className="px-3 py-1 border border-theme rounded text-sm font-sans disabled:opacity-40 hover:bg-surface-input transition-colors">Next</button>
                  </div>
                </div>
              )}
            </div>
          </Reveal>
        </div>
      </div>
    </main>
  )
}
