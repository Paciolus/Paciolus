'use client'

/**
 * Authenticated Dashboard — Sprint 475
 *
 * First page logged-in users see. Shows:
 * - Welcome header with date
 * - Stat cards (analyses today, total clients, last activity)
 * - Quick action cards (Upload TB, Portfolio, Workspaces)
 * - Recent activity feed
 *
 * Adapts WorkspaceHeader/QuickActionsBar/RecentHistoryMini from TB page
 * into light-themed dashboard components.
 */

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
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

const QUICK_ACTIONS = [
  {
    label: 'Upload Trial Balance',
    href: '/tools/trial-balance',
    description: 'Run diagnostics on a new trial balance',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
  },
  {
    label: 'Portfolio',
    href: '/portfolio',
    description: 'View and manage your clients',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
      </svg>
    ),
  },
  {
    label: 'Workspaces',
    href: '/engagements',
    description: 'Manage diagnostic workspaces',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
      </svg>
    ),
  },
] as const

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, isAuthenticated, isLoading: authLoading } = useAuth()
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

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="max-w-5xl mx-auto px-6 pt-8 pb-16">
        {/* Welcome Header */}
        <Reveal>
          <div className="mb-8">
            <p className="text-sm font-sans text-content-tertiary mb-1">{todayStr}</p>
            <h1 className="text-2xl font-serif font-bold text-content-primary">
              Welcome back, <span className="text-sage-600">{displayName}</span>
            </h1>
          </div>
        </Reveal>

        {/* Stat Cards */}
        <Reveal delay={0.05}>
          <motion.div
            variants={staggerContainerTight}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10"
          >
            {/* Analyses Today */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider mb-2">Analyses Today</p>
              {statsLoading ? (
                <div className="h-8 w-12 bg-oatmeal-200 rounded animate-pulse" />
              ) : (
                <p className="type-num text-2xl font-bold text-content-primary">{stats?.assessments_today ?? 0}</p>
              )}
            </motion.div>

            {/* Total Clients */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider mb-2">Clients</p>
              {statsLoading ? (
                <div className="h-8 w-12 bg-oatmeal-200 rounded animate-pulse" />
              ) : (
                <p className="type-num text-2xl font-bold text-content-primary">{stats?.total_clients ?? 0}</p>
              )}
            </motion.div>

            {/* Last Activity */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider mb-2">Last Activity</p>
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

        {/* Quick Actions */}
        <Reveal delay={0.1}>
          <div className="mb-10">
            <h2 className="font-serif text-lg font-bold text-content-primary mb-4">Quick Actions</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {QUICK_ACTIONS.map(action => (
                <Link
                  key={action.href}
                  href={action.href}
                  className="theme-card p-5 group hover:shadow-theme-card-hover transition-shadow"
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-9 h-9 rounded-lg bg-sage-50 text-sage-600 flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                      {action.icon}
                    </div>
                    <h3 className="font-sans font-semibold text-sm text-content-primary">{action.label}</h3>
                  </div>
                  <p className="text-xs font-sans text-content-secondary">{action.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Recent Activity */}
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
              <div className="theme-card p-8 text-center">
                <p className="text-content-secondary font-sans text-sm mb-3">No analyses yet</p>
                <Link
                  href="/tools/trial-balance"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-sage-600 text-white rounded-lg font-sans text-sm font-medium hover:bg-sage-700 transition-colors"
                >
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
