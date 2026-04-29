'use client'

/**
 * Authenticated Dashboard — "Mission Control"
 *
 * Sprint 579: Redesigned from TB-centric launcher to tool-agnostic mission control.
 * Sprint 751: Decomposed per ADR-017 — composition root over useDashboardStats +
 * useActivityFeed + useUserPreferences. Tool catalog moved to
 * `content/dashboard-tools.ts`; SVG paths moved to `components/dashboard/ToolIcon.tsx`.
 */

import { useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useToast } from '@/contexts/ToastContext'
import { ToolIcon } from '@/components/dashboard/ToolIcon'
import { WelcomeModal } from '@/components/shared/WelcomeModal'
import { Reveal } from '@/components/ui/Reveal'
import { useActivityFeed, useDashboardStats, useUserPreferences } from '@/hooks'
import { DASHBOARD_TOOLS } from '@/content/dashboard-tools'
import { fadeUp, staggerContainerTight } from '@/lib/motion'

/* ─── Helpers ───────────────────────────────────────────────────────── */

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

/* ─── Component ─────────────────────────────────────────────────────── */

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const { error: toastError } = useToast()

  const { stats, loading: statsLoading, error: statsError, retry: retryStats } =
    useDashboardStats(token, { onError: toastError })
  const { activity, loading: activityLoading, error: activityError, retry: retryActivity } =
    useActivityFeed(token, { onError: toastError })
  const { favorites, toggleFavorite } = useUserPreferences(token, { onError: toastError })

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

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

  // Contextual summary line — platform-wide
  const summaryParts: string[] = []
  if (stats && stats.total_clients > 0) summaryParts.push(`${stats.total_clients} client${stats.total_clients === 1 ? '' : 's'}`)
  if (stats && stats.tools_used > 0) summaryParts.push(`${stats.tools_used} tool${stats.tools_used === 1 ? '' : 's'} used`)
  if (stats && stats.active_workspaces > 0) summaryParts.push(`${stats.active_workspaces} active workspace${stats.active_workspaces === 1 ? '' : 's'}`)
  const summaryLine = summaryParts.length > 0 ? summaryParts.join(' \u00B7 ') : 'Get started by launching any diagnostic tool below'

  const favoritedTools = DASHBOARD_TOOLS.filter(t => favorites.includes(t.key))
  const displayTools = favoritedTools.length > 0 ? favoritedTools : DASHBOARD_TOOLS.slice(0, 6)

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      {/* Subtle accent strip below toolbar */}
      <div className="h-[2px] bg-gradient-to-r from-transparent via-sage-500/20 to-transparent" />

      <div className="max-w-6xl mx-auto px-6 pt-8 pb-16">
        {/* Welcome Header */}
        <Reveal>
          <div className="mb-8">
            <p className="text-sm font-sans text-content-tertiary mb-1">{todayStr}</p>
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
              Welcome back, <span className="text-sage-600">{displayName}</span>
            </h1>
            <p className="text-sm font-sans text-content-secondary mt-1.5">{summaryLine}</p>
          </div>
        </Reveal>

        {/* Stat Cards — 4-column platform-wide stats */}
        {statsError && (
          <div className="theme-card p-4 mb-4 flex items-center justify-between border-clay-500/30 bg-clay-50/10">
            <p className="text-sm font-sans text-clay-600">Dashboard stats unavailable</p>
            <button onClick={retryStats} className="text-sm font-sans font-medium text-sage-600 hover:text-sage-700 transition-colors">
              Retry
            </button>
          </div>
        )}
        <Reveal delay={0.05}>
          <motion.div
            variants={staggerContainerTight}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10"
          >
            {/* Tool Runs Today */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Runs Today</p>
                <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
              {statsLoading ? (
                <div className="h-8 w-12 bg-oatmeal-200 rounded animate-pulse" />
              ) : (
                <p className={`font-mono text-2xl font-bold ${(stats?.tool_runs_today ?? 0) > 0 ? 'text-content-primary' : 'text-content-tertiary'}`}>
                  {stats?.tool_runs_today ?? stats?.assessments_today ?? 0}
                </p>
              )}
            </motion.div>

            {/* Total Clients */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Clients</p>
                <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
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

            {/* Active Workspaces */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Workspaces</p>
                <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                  </svg>
                </div>
              </div>
              {statsLoading ? (
                <div className="h-8 w-12 bg-oatmeal-200 rounded animate-pulse" />
              ) : (
                <p className={`font-mono text-2xl font-bold ${(stats?.active_workspaces ?? 0) > 0 ? 'text-content-primary' : 'text-content-tertiary'}`}>
                  {stats?.active_workspaces ?? 0}
                </p>
              )}
            </motion.div>

            {/* Last Activity */}
            <motion.div variants={fadeUp} className="theme-card p-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-sans text-content-tertiary uppercase tracking-wider">Last Activity</p>
                <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
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

        {/* Quick Launch — Favorite tools grid */}
        <Reveal delay={0.1}>
          <div className="mb-10">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-serif text-lg font-bold text-content-primary">Quick Launch</h2>
              <Link
                href="/tools"
                className="text-sm font-sans font-medium text-sage-600 hover:text-sage-700 transition-colors"
              >
                Browse All Tools &rarr;
              </Link>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {displayTools.map(tool => (
                <div key={tool.key} className="relative group">
                  <Link
                    href={tool.href}
                    className="theme-card p-4 flex items-start gap-3 hover:shadow-theme-card-hover transition-all block h-full"
                  >
                    <div className="w-9 h-9 rounded-lg bg-sage-50 text-sage-600 flex items-center justify-center flex-shrink-0 group-hover:bg-sage-100 transition-colors">
                      <ToolIcon iconKey={tool.icon} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-serif font-semibold text-sm text-content-primary">{tool.label}</h3>
                      <p className="text-xs font-sans text-content-tertiary mt-0.5 line-clamp-2">{tool.description}</p>
                    </div>
                  </Link>
                  <button
                    onClick={(e) => { e.preventDefault(); toggleFavorite(tool.key) }}
                    className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center rounded-md opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity hover:bg-oatmeal-100"
                    aria-label={favorites.includes(tool.key) ? 'Remove from favorites' : 'Add to favorites'}
                    title={favorites.includes(tool.key) ? 'Remove from favorites' : 'Add to favorites'}
                  >
                    <svg
                      className={`w-3.5 h-3.5 ${favorites.includes(tool.key) ? 'text-sage-600 fill-sage-600' : 'text-content-tertiary'}`}
                      fill={favorites.includes(tool.key) ? 'currentColor' : 'none'}
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Quick Access: Portfolio (now includes workspaces) */}
        <Reveal delay={0.12}>
          <div className="mb-10">
            <Link
              href="/portfolio"
              className="theme-card p-5 group hover:shadow-theme-card-hover transition-shadow block"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="w-9 h-9 rounded-lg bg-sage-50 text-sage-600 flex items-center justify-center group-hover:bg-sage-100 transition-colors">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
                  </svg>
                </div>
                <h3 className="font-serif font-semibold text-sm text-content-primary">Portfolio &amp; Workspaces</h3>
              </div>
              <p className="text-xs font-sans text-content-secondary">Manage your clients and their diagnostic workspaces</p>
            </Link>
          </div>
        </Reveal>

        {/* Recent Activity — Multi-tool unified feed */}
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

            {activityError ? (
              <div className="theme-card p-6 text-center">
                <p className="text-sm font-sans text-clay-600 mb-3">Failed to load activity feed</p>
                <button onClick={retryActivity} className="text-sm font-sans font-medium text-sage-600 hover:text-sage-700 transition-colors">
                  Retry
                </button>
              </div>
            ) : activityLoading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="theme-card p-4 animate-pulse">
                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 bg-oatmeal-200 rounded-lg" />
                      <div className="flex-1">
                        <div className="h-4 w-40 bg-oatmeal-200 rounded mb-1.5" />
                        <div className="h-3 w-24 bg-oatmeal-200 rounded" />
                      </div>
                      <div className="h-3 w-16 bg-oatmeal-200 rounded" />
                    </div>
                  </div>
                ))}
              </div>
            ) : activity.length === 0 ? (
              <div className="theme-card p-10 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-oatmeal-100 border border-oatmeal-200 flex items-center justify-center">
                  <svg className="w-8 h-8 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7v4m0 0l-2-2m2 2l2-2" />
                  </svg>
                </div>
                <p className="text-content-primary font-sans font-medium mb-1">No activity yet</p>
                <p className="text-content-tertiary font-sans text-sm mb-5 max-w-xs mx-auto">
                  Your diagnostic history will appear here once you run any tool.
                </p>
                <Link
                  href="/tools"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-sage-600 text-oatmeal-50 rounded-xl font-sans text-sm font-bold hover:bg-sage-700 transition-colors shadow-theme-card"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />
                  </svg>
                  Explore Tools
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {activity.map(item => {
                  const tool = DASHBOARD_TOOLS.find(t => t.key === item.tool_name)
                  const anomalyCount = typeof item.summary?.anomaly_count === 'number' ? (item.summary.anomaly_count as number) : 0
                  const rowLabel = item.record_count != null ? `${item.record_count.toLocaleString()} rows` : null

                  // Build a unique primary title: filename first, then a generated summary
                  const primaryTitle = item.filename
                    || [rowLabel, anomalyCount > 0 ? `${anomalyCount} anomalies` : null, item.summary?.was_balanced === false ? 'Out of Balance' : item.summary?.was_balanced === true ? 'Balanced' : null].filter(Boolean).join(' · ')
                    || 'Analysis complete'

                  return (
                    <div
                      key={item.id}
                      className="theme-card p-4 flex items-center gap-4 hover:shadow-theme-card-hover transition-shadow"
                    >
                      <div className="w-8 h-8 rounded-lg bg-sage-50 text-sage-600 flex items-center justify-center flex-shrink-0">
                        <ToolIcon iconKey={tool?.icon || 'cube'} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-sans text-sm font-medium text-content-primary truncate">{primaryTitle}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs font-sans font-medium px-2 py-0.5 rounded-full bg-oatmeal-100 text-content-secondary border border-oatmeal-200">
                            {item.tool_label}
                          </span>
                          {item.filename && rowLabel && (
                            <span className="text-xs font-sans text-content-tertiary">{rowLabel}</span>
                          )}
                          {item.summary?.was_balanced === true && (
                            <span className="text-xs font-sans font-medium px-1.5 py-0.5 rounded-full bg-sage-50 text-sage-700 border border-sage-200">Balanced</span>
                          )}
                          {item.summary?.was_balanced === false && (
                            <span className="text-xs font-sans font-medium px-1.5 py-0.5 rounded-full bg-clay-50 text-clay-700 border border-clay-200">Out of Balance</span>
                          )}
                          {item.filename && anomalyCount > 0 && (
                            <span className="text-xs font-sans text-clay-600">
                              {anomalyCount} anomalies
                            </span>
                          )}
                        </div>
                      </div>
                      <span className="text-xs font-sans text-content-tertiary flex-shrink-0">
                        {formatRelativeTime(item.created_at)}
                      </span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </Reveal>
      </div>

      {/* First-run onboarding — Sprint 583 */}
      <WelcomeModal />
    </main>
  )
}
