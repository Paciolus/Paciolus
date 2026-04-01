'use client'

/**
 * Admin Dashboard Page — Sprint 545a
 *
 * Team overview metrics, tool usage table, team activity with filters, CSV export.
 * Professional+ tier (gated by FeatureGate).
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { FeatureGate } from '@/components/shared/FeatureGate'
import { Reveal } from '@/components/ui/Reveal'
import { useAdminDashboard } from '@/hooks/useAdminDashboard'

export default function AdminDashboardPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuthSession()
  const {
    overview,
    teamActivity,
    memberUsage,
    isLoading,
    error,
    fetchOverview,
    fetchTeamActivity,
    fetchUsageByMember,
    exportActivityCsv,
  } = useAdminDashboard()

  const [daysFilter, setDaysFilter] = useState(30)
  const [toolFilter, setToolFilter] = useState('')
  const [memberFilter, setMemberFilter] = useState('')
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      fetchOverview()
      fetchTeamActivity(daysFilter)
      fetchUsageByMember()
    }
  }, [isAuthenticated, fetchOverview, fetchTeamActivity, fetchUsageByMember, daysFilter])

  function handleApplyFilters() {
    fetchTeamActivity(
      daysFilter,
      toolFilter || undefined,
      memberFilter || undefined,
    )
  }

  async function handleExport() {
    setExporting(true)
    await exportActivityCsv()
    setExporting(false)
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="pt-8 pb-16 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Breadcrumb + Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 text-content-tertiary text-sm font-sans mb-4">
              <Link href="/" className="hover:text-content-secondary transition-colors">Home</Link>
              <span>/</span>
              <Link href="/settings" className="hover:text-content-secondary transition-colors">Settings</Link>
              <span>/</span>
              <span className="text-content-secondary">Team Dashboard</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
              Team Dashboard
            </h1>
            <p className="text-content-secondary font-sans">
              Monitor team usage, activity, and tool adoption.
            </p>
          </div>

          <FeatureGate feature="admin_dashboard">
            {/* Error Banner */}
            {error && (
              <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-6 text-sm font-sans" role="alert">
                {error}
              </div>
            )}

            {/* Overview Cards */}
            <Reveal className="mb-8">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Total Members', value: overview?.total_members ?? '—' },
                  { label: 'Uploads (30d)', value: overview?.total_uploads_30d ?? '—' },
                  { label: 'Active (30d)', value: overview?.active_members_30d ?? '—' },
                  { label: 'Top Tool', value: overview?.top_tool ?? '—' },
                ].map(card => (
                  <div key={card.label} className="bg-surface-card border border-theme rounded-xl p-4">
                    <p className="text-content-tertiary text-xs font-sans mb-1">{card.label}</p>
                    <p className="text-2xl font-mono font-semibold text-content-primary">
                      {card.value}
                    </p>
                  </div>
                ))}
              </div>
            </Reveal>

            {/* Member Usage Table */}
            <Reveal delay={0.06} className="mb-8">
              <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
                Usage by Member
              </h2>
              <div className="bg-surface-card border border-theme rounded-xl overflow-hidden">
                <table className="w-full text-sm font-sans">
                  <thead>
                    <tr className="border-b border-theme bg-surface-input/50">
                      <th className="text-left px-4 py-3 font-medium text-content-secondary">Email</th>
                      <th className="text-right px-4 py-3 font-medium text-content-secondary">Uploads (30d)</th>
                      <th className="text-left px-4 py-3 font-medium text-content-secondary">Top Tool</th>
                      <th className="text-left px-4 py-3 font-medium text-content-secondary">Last Active</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading && !memberUsage.length ? (
                      <tr><td colSpan={4} className="px-4 py-8 text-center text-content-muted">Loading...</td></tr>
                    ) : memberUsage.length === 0 ? (
                      <tr><td colSpan={4} className="px-4 py-8 text-center text-content-muted">No usage data yet.</td></tr>
                    ) : (
                      memberUsage.map(m => (
                        <tr key={m.user_id} className="border-b border-theme last:border-0">
                          <td className="px-4 py-3 text-content-primary">{m.email}</td>
                          <td className="px-4 py-3 text-right font-mono text-content-primary">{m.uploads_30d}</td>
                          <td className="px-4 py-3 text-content-secondary">{m.top_tool ?? '—'}</td>
                          <td className="px-4 py-3 text-content-tertiary">
                            {m.last_active ? new Date(m.last_active).toLocaleDateString() : '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Reveal>

            {/* Team Activity */}
            <Reveal delay={0.12}>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-serif font-semibold text-content-primary">
                  Team Activity
                </h2>
                <button
                  onClick={handleExport}
                  disabled={exporting}
                  className="px-4 py-2 border border-theme rounded-lg font-sans text-sm font-medium text-content-secondary hover:bg-surface-input transition-colors disabled:opacity-50"
                >
                  {exporting ? 'Exporting...' : 'Export CSV'}
                </button>
              </div>

              {/* Filters */}
              <div className="flex flex-wrap gap-3 mb-4">
                <select
                  value={daysFilter}
                  onChange={e => setDaysFilter(Number(e.target.value))}
                  className="bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={30}>Last 30 days</option>
                  <option value={90}>Last 90 days</option>
                </select>
                <input
                  type="text"
                  placeholder="Filter by tool..."
                  value={toolFilter}
                  onChange={e => setToolFilter(e.target.value)}
                  className="bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder:text-content-muted"
                />
                <input
                  type="text"
                  placeholder="Filter by member..."
                  value={memberFilter}
                  onChange={e => setMemberFilter(e.target.value)}
                  className="bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder:text-content-muted"
                />
                <button
                  onClick={handleApplyFilters}
                  className="px-4 py-2 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm font-medium hover:bg-sage-700 transition-colors"
                >
                  Apply
                </button>
              </div>

              {/* Activity Table */}
              <div className="bg-surface-card border border-theme rounded-xl overflow-hidden">
                <table className="w-full text-sm font-sans">
                  <thead>
                    <tr className="border-b border-theme bg-surface-input/50">
                      <th className="text-left px-4 py-3 font-medium text-content-secondary">Member</th>
                      <th className="text-left px-4 py-3 font-medium text-content-secondary">Tool</th>
                      <th className="text-right px-4 py-3 font-medium text-content-secondary">Records</th>
                      <th className="text-left px-4 py-3 font-medium text-content-secondary">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading && !teamActivity.length ? (
                      <tr><td colSpan={4} className="px-4 py-8 text-center text-content-muted">Loading...</td></tr>
                    ) : teamActivity.length === 0 ? (
                      <tr><td colSpan={4} className="px-4 py-8 text-center text-content-muted">No activity in this period.</td></tr>
                    ) : (
                      teamActivity.map(a => (
                        <tr key={a.id} className="border-b border-theme last:border-0">
                          <td className="px-4 py-3 text-content-primary">{a.member_email}</td>
                          <td className="px-4 py-3 text-content-secondary">{a.tool_name}</td>
                          <td className="px-4 py-3 text-right font-mono text-content-primary">{a.record_count.toLocaleString()}</td>
                          <td className="px-4 py-3 text-content-tertiary">
                            {new Date(a.timestamp).toLocaleDateString()}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Reveal>
          </FeatureGate>
        </div>
      </div>
    </main>
  )
}
