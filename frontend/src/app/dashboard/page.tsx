'use client'

/**
 * Authenticated Dashboard — Sprint 566 (Design Enrichment)
 *
 * First page logged-in users see. Shows:
 * - Welcome header with date + contextual summary
 * - Stat cards with icons and contextual styling
 * - Quick action cards (Upload TB hero + Portfolio/Workspaces secondary)
 * - Recent activity feed with enhanced empty state
 *
 * Sprint 566 changes: D1 (stat icons), D2 (hero Upload TB),
 * D3 (larger header), D4 (accent strip), D5 (enhanced empty activity),
 * X1 (max-w-6xl), X2 (visual motif below toolbar)
 */

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { Reveal } from '@/components/ui/Reveal'
import { apiGet } from '@/utils/apiClient'
import { fadeUp, staggerContainerTight } from '@/lib/motion'

interface DashboardStats {
  total_clients: number
  assessments_today: number
  last_assessment_date: string | null
  total_assessments: number
}

interface HistoryItem {
  id: number
  filename: string
  created_at: string
  was_balanced: boolean
  record_count: number
  anomaly_count: number
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [statsLoading, setStatsLoading] = useState(true)
  const [historyLoading, setHistoryLoading] = useState(true)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (!token) return

    apiGet<DashboardStats>('/dashboard/stats', token)
      .then(res => { if (res.data) setStats(res.data) })
      .catch(() => {})
      .finally(() => setStatsLoading(false))

    apiGet<HistoryItem[]>('/activity/recent?limit=5', token)
      .then(res => { if (res.data) setHistory(res.data) })
      .catch(() => {})
      .finally(() => setHistoryLoading(false))
  }, [token])

  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })

  const displayName = user?.name || user?.email?.split('@')[0] || 'there'

  // Contextual summary line
  const summaryParts: string[] = []
  if (stats && stats.total_clients > 0) summaryParts.push(`${stats.total_clients} client${stats.total_clients === 1 ? '' : 's'}`)
  if (stats && stats.total_assessments > 0) summaryParts.push(`${stats.total_assessments} total analyses`)
  const summaryLine = summaryParts.length > 0 ? summaryParts.join(' \u00B7 ') : 'Upload a trial balance to get started'

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      {/* X2: Subtle accent strip below toolbar */}
      <div className="h-[2px] bg-gradient-to-r from-transparent via-sage-500/20 to-transparent" />

      <div className="max-w-6xl mx-auto px-6 pt-8 pb-16">
        {/* Welcome Header — D3: enlarged */}
        <Reveal>
          <div className="mb-8">
            <p className="text-sm font-sans text-content-tertiary mb-1">{todayStr}</p>
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
              Welcome back, <span className="text-sage-600">{displayName}</span>
            </h1>
            <p className="text-sm font-sans text-content-secondary mt-1.5">{summaryLine}</p>
          </div>
        </Reveal>

        {/* Stat Cards — D1: icons + contextual styling */}
        <Reveal delay={0.05}>
          <motion.div
            variants={staggerContainerTight}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10"
          >
            {/* Analyses Today */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Analyses Today</p>
                <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
              {statsLoading ? (
                <div className="h-8 w-12 bg-oatmeal-200 rounded animate-pulse" />
              ) : (
                <p className={`font-mono text-2xl font-bold ${(stats?.assessments_today ?? 0) > 0 ? 'text-content-primary' : 'text-content-tertiary'}`}>
                  {stats?.assessments_today ?? 0}
                </p>
              )}
            </motion.div>

            {/* Total Clients */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Clients</p>
                <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                  </svg>
                </div>
              </div>
              {statsLoading ? (
                <div className="h-8 w-12 bg-oatmeal-200 rounded animate-pulse" />
              ) : (
                <p className={`font-mono text-2xl font-bold ${(stats?.total_clients ?? 0) > 0 ? 'text-content-primary' : 'text-content-tertiary'}`}>
                  {stats?.total_clients ?? 0}
                </p>
              )}
            </motion.div>

            {/* Last Activity */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Last Activity</p>
                <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              {statsLoading ? (
                <div className="h-8 w-20 bg-oatmeal-200 rounded animate-pulse" />
              ) : (
                <p className="text-sm font-sans text-content-secondary">
                  {stats?.last_assessment_date
                    ? formatRelativeTime(stats.last_assessment_date)
                    : 'No activity yet'}
                </p>
              )}
            </motion.div>
          </motion.div>
        </Reveal>

        {/* Quick Actions — D2: Upload TB as hero, others as secondary row */}
        <Reveal delay={0.1}>
          <div className="mb-10">
            <h2 className="font-serif text-lg font-bold text-content-primary mb-4">Quick Actions</h2>

            {/* Hero: Upload Trial Balance */}
            <Link
              href="/tools/trial-balance"
              className="block mb-4 group"
            >
              <div className="theme-card p-6 bg-sage-50/50 border-sage-200 hover:shadow-theme-card-hover transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-sage-100 text-sage-600 flex items-center justify-center group-hover:bg-sage-200 transition-colors">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="font-sans font-bold text-base text-content-primary">Upload Trial Balance</h3>
                    <p className="text-sm font-sans text-content-secondary mt-0.5">Run diagnostics on a new trial balance &mdash; ratio analysis, anomaly detection, and lead sheets</p>
                  </div>
                  <svg className="w-5 h-5 text-content-tertiary group-hover:text-sage-600 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </Link>

            {/* Secondary: Portfolio + Workspaces */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                href="/portfolio"
                className="theme-card p-5 group hover:shadow-theme-card-hover transition-shadow"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-9 h-9 rounded-lg bg-sage-50 text-sage-600 flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
                    </svg>
                  </div>
                  <h3 className="font-sans font-semibold text-sm text-content-primary">Portfolio</h3>
                </div>
                <p className="text-xs font-sans text-content-secondary">View and manage your clients</p>
              </Link>

              <Link
                href="/engagements"
                className="theme-card p-5 group hover:shadow-theme-card-hover transition-shadow"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-9 h-9 rounded-lg bg-sage-50 text-sage-600 flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                    </svg>
                  </div>
                  <h3 className="font-sans font-semibold text-sm text-content-primary">Workspaces</h3>
                </div>
                <p className="text-xs font-sans text-content-secondary">Manage diagnostic workspaces</p>
              </Link>
            </div>
          </div>
        </Reveal>

        {/* Recent Activity — D5: enhanced empty state */}
        <Reveal delay={0.15}>
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-serif text-lg font-bold text-content-primary">Recent Activity</h2>
              <Link
                href="/history"
                className="text-sm font-sans font-medium text-sage-600 hover:text-sage-700 transition-colors"
              >
                View All History &rarr;
              </Link>
            </div>

            {historyLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="theme-card p-4 animate-pulse">
                    <div className="flex items-center gap-4">
                      <div className="h-4 w-32 bg-oatmeal-200 rounded" />
                      <div className="h-4 w-20 bg-oatmeal-200 rounded" />
                      <div className="ml-auto h-4 w-16 bg-oatmeal-200 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : history.length === 0 ? (
              <div className="theme-card p-10 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-oatmeal-100 border border-oatmeal-200 flex items-center justify-center">
                  <svg className="w-8 h-8 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7v4m0 0l-2-2m2 2l2-2" />
                  </svg>
                </div>
                <p className="text-content-primary font-sans font-medium mb-1">No analyses yet</p>
                <p className="text-content-tertiary font-sans text-sm mb-5 max-w-xs mx-auto">
                  Your diagnostic history will appear here once you upload and analyze a trial balance.
                </p>
                <Link
                  href="/tools/trial-balance"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-sage-600 text-white rounded-xl font-sans text-sm font-bold hover:bg-sage-700 transition-colors shadow-theme-card"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                  </svg>
                  Upload your first trial balance
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {history.map(item => (
                  <div
                    key={item.id}
                    className="theme-card p-4 flex items-center gap-4 hover:shadow-theme-card-hover transition-shadow"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-sans text-sm text-content-primary truncate">{item.filename}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className={`text-xs font-sans font-medium px-2 py-0.5 rounded-full ${
                          item.was_balanced
                            ? 'bg-sage-50 text-sage-700 border border-sage-200'
                            : 'bg-clay-50 text-clay-700 border border-clay-200'
                        }`}>
                          {item.was_balanced ? 'Balanced' : 'Out of Balance'}
                        </span>
                        <span className="text-xs font-sans text-content-tertiary">
                          {item.record_count} rows
                        </span>
                        {item.anomaly_count > 0 && (
                          <span className="text-xs font-sans text-clay-600">
                            {item.anomaly_count} anomalies
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="text-xs font-sans text-content-tertiary flex-shrink-0">
                      {formatRelativeTime(item.created_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Reveal>
      </div>
    </main>
  )
}
