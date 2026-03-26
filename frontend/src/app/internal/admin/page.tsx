'use client'

/**
 * Internal Admin Console — Customer List Page
 * Sprint 590: Superadmin CRM
 *
 * Paginated, searchable, filterable customer list.
 */

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { Reveal } from '@/components/ui/Reveal'
import { useInternalAdmin } from '@/hooks/useInternalAdmin'

const PLAN_OPTIONS = ['', 'solo', 'professional', 'enterprise']
const STATUS_OPTIONS = ['', 'active', 'trialing', 'past_due', 'canceled']

export default function InternalAdminPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading, user } = useAuthSession()
  const { customers, isLoading, error, fetchCustomers } = useInternalAdmin()

  const [search, setSearch] = useState('')
  const [planFilter, setPlanFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(0)
  const pageSize = 25

  const loadCustomers = useCallback(() => {
    const params: Record<string, string> = {
      offset: String(page * pageSize),
      limit: String(pageSize),
      sort_by: 'created_at',
      sort_dir: 'desc',
    }
    if (search) params.search = search
    if (planFilter) params.plan = planFilter
    if (statusFilter) params.status = statusFilter
    fetchCustomers(params)
  }, [page, search, planFilter, statusFilter, fetchCustomers, pageSize])

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      loadCustomers()
    }
  }, [isAuthenticated, loadCustomers])

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  const totalPages = customers ? Math.ceil(customers.total / pageSize) : 0

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="pt-8 pb-16 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <Reveal>
            <h1 className="text-2xl font-serif font-bold text-content-primary mb-2">
              Customer Console
            </h1>
            <p className="text-content-secondary font-sans text-sm mb-6">
              Internal admin — manage all customer accounts, billing, and usage.
            </p>
          </Reveal>

          {/* Filters */}
          <Reveal delay={0.06}>
            <div className="bg-surface-card border border-theme rounded-xl p-4 mb-6">
              <div className="flex flex-wrap gap-3 items-end">
                <div className="flex-1 min-w-[200px]">
                  <label htmlFor="admin-search" className="block text-xs font-sans text-content-tertiary mb-1">Search</label>
                  <input
                    id="admin-search"
                    type="text"
                    name="search"
                    autoComplete="off"
                    placeholder="Email or org name..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary placeholder:text-content-muted"
                  />
                </div>
                <div>
                  <label htmlFor="admin-plan-filter" className="block text-xs font-sans text-content-tertiary mb-1">Plan</label>
                  <select
                    id="admin-plan-filter"
                    value={planFilter}
                    onChange={e => setPlanFilter(e.target.value)}
                    className="px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary"
                  >
                    {PLAN_OPTIONS.map(p => (
                      <option key={p} value={p}>{p || 'All Plans'}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="admin-status-filter" className="block text-xs font-sans text-content-tertiary mb-1">Status</label>
                  <select
                    id="admin-status-filter"
                    value={statusFilter}
                    onChange={e => setStatusFilter(e.target.value)}
                    className="px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-primary"
                  >
                    {STATUS_OPTIONS.map(s => (
                      <option key={s} value={s}>{s || 'All Statuses'}</option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={() => { setPage(0); loadCustomers() }}
                  className="px-4 py-2 bg-sage-600 text-white rounded-lg font-sans font-medium text-sm hover:bg-sage-700 transition-colors"
                >
                  Search
                </button>
              </div>
            </div>
          </Reveal>

          {/* Error */}
          {error && (
            <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-xl p-4 mb-6 text-sm font-sans">
              {error}
            </div>
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
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Org / Email</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Plan</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Status</th>
                        <th className="text-right py-3 px-4 text-content-tertiary font-medium">MRR</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Signup</th>
                        <th className="text-left py-3 px-4 text-content-tertiary font-medium">Last Active</th>
                        <th className="text-right py-3 px-4 text-content-tertiary font-medium">Uploads</th>
                      </tr>
                    </thead>
                    <tbody>
                      {customers?.items.map(c => (
                        <tr
                          key={c.user_id}
                          role="button"
                          tabIndex={0}
                          onClick={() => router.push(`/internal/admin/customers/${c.org_id ?? c.user_id}`)}
                          onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') router.push(`/internal/admin/customers/${c.org_id ?? c.user_id}`) }}
                          className="border-b border-theme hover:bg-surface-input/30 cursor-pointer transition-colors"
                        >
                          <td className="py-3 px-4">
                            <div className="text-content-primary font-medium">{c.org_name || c.owner_name || '—'}</div>
                            <div className="text-content-tertiary text-xs">{c.owner_email}</div>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                              c.plan === 'enterprise' ? 'bg-obsidian-100 text-obsidian-700' :
                              c.plan === 'professional' ? 'bg-sage-100 text-sage-700' :
                              c.plan === 'solo' ? 'bg-oatmeal-200 text-obsidian-600' :
                              'bg-surface-input text-content-tertiary'
                            }`}>
                              {c.plan}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                              c.status === 'active' ? 'bg-sage-100 text-sage-700' :
                              c.status === 'trialing' ? 'bg-oatmeal-200 text-obsidian-600' :
                              c.status === 'past_due' ? 'bg-clay-100 text-clay-700' :
                              c.status === 'canceled' ? 'bg-clay-50 text-clay-600' :
                              'bg-surface-input text-content-tertiary'
                            }`}>
                              {c.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-content-primary">
                            ${c.mrr.toFixed(2)}
                          </td>
                          <td className="py-3 px-4 text-content-secondary text-xs">
                            {c.signup_date ? new Date(c.signup_date).toLocaleDateString() : '—'}
                          </td>
                          <td className="py-3 px-4 text-content-secondary text-xs">
                            {c.last_login ? new Date(c.last_login).toLocaleDateString() : 'Never'}
                          </td>
                          <td className="py-3 px-4 text-right font-mono text-content-primary">
                            {c.uploads_this_period}
                          </td>
                        </tr>
                      ))}
                      {(!customers?.items.length) && (
                        <tr>
                          <td colSpan={7} className="py-12 text-center text-content-tertiary">
                            No customers found.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-theme">
                  <span className="text-xs text-content-tertiary font-sans">
                    {customers?.total ?? 0} total customers
                  </span>
                  <div className="flex gap-2">
                    <button
                      disabled={page === 0}
                      onClick={() => setPage(p => Math.max(0, p - 1))}
                      className="px-3 py-1 border border-theme rounded text-sm font-sans disabled:opacity-40 hover:bg-surface-input transition-colors"
                    >
                      Prev
                    </button>
                    <span className="px-3 py-1 text-sm text-content-secondary font-sans">
                      {page + 1} / {totalPages}
                    </span>
                    <button
                      disabled={page >= totalPages - 1}
                      onClick={() => setPage(p => p + 1)}
                      className="px-3 py-1 border border-theme rounded text-sm font-sans disabled:opacity-40 hover:bg-surface-input transition-colors"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          </Reveal>

          {/* Nav links */}
          <Reveal delay={0.18}>
            <div className="mt-6 flex gap-4">
              <button
                onClick={() => router.push('/internal/admin/audit-log')}
                className="px-4 py-2 border border-theme rounded-lg text-sm font-sans text-content-secondary hover:bg-surface-input transition-colors"
              >
                View Audit Log
              </button>
            </div>
          </Reveal>
        </div>
      </div>
    </main>
  )
}
