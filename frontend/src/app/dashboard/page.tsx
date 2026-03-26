'use client'

/**
 * Authenticated Dashboard — "Mission Control"
 *
 * Sprint 579: Redesigned from TB-centric launcher to tool-agnostic
 * mission control. Shows:
 * - Welcome header with platform-wide summary
 * - Stat cards: Tool Runs Today, Clients, Active Workspaces, Last Activity
 * - Quick Launch grid: pinned/favorite tools with browse-all link
 * - Unified activity feed across all 12+ tools
 * - Active workspace progress (when applicable)
 */

import { useState, useEffect, useCallback, type ReactNode } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { WelcomeModal } from '@/components/shared/WelcomeModal'
import { Reveal } from '@/components/ui/Reveal'
import { apiGet, apiPut } from '@/utils/apiClient'
import { fadeUp, staggerContainerTight } from '@/lib/motion'

/* ─── Types ─────────────────────────────────────────────────────────── */

interface DashboardStats {
  total_clients: number
  assessments_today: number
  last_assessment_date: string | null
  total_assessments: number
  tool_runs_today: number
  total_tool_runs: number
  active_workspaces: number
  tools_used: number
}

interface ToolActivityItem {
  id: number
  tool_name: string
  tool_label: string
  filename: string | null
  record_count: number | null
  summary: Record<string, unknown> | null
  created_at: string
}

interface UserPreferences {
  favorite_tools: string[]
}

/* ─── Tool Catalog (shared with /tools page) ─────────────────────── */

interface ToolDef {
  key: string
  label: string
  href: string
  description: string
  category: 'Core Analysis' | 'Testing Suite' | 'Advanced'
  icon: 'chart' | 'upload' | 'shield' | 'calculator' | 'search' | 'banknotes' | 'receipt' | 'clock' | 'cube' | 'truck' | 'building' | 'box' | 'percentage'
}

const TOOLS: ToolDef[] = [
  { key: 'trial_balance', label: 'TB Diagnostics', href: '/tools/trial-balance', description: 'Ratio analysis, anomaly detection, lead sheets', category: 'Core Analysis', icon: 'chart' },
  { key: 'multi_period', label: 'Multi-Period', href: '/tools/multi-period', description: 'Trend analysis across reporting periods', category: 'Core Analysis', icon: 'clock' },
  { key: 'bank_reconciliation', label: 'Bank Rec', href: '/tools/bank-rec', description: 'Bank-to-book reconciliation testing', category: 'Core Analysis', icon: 'banknotes' },
  { key: 'three_way_match', label: 'Three-Way Match', href: '/tools/three-way-match', description: 'PO, receipt, and invoice matching', category: 'Core Analysis', icon: 'receipt' },
  { key: 'journal_entry_testing', label: 'JE Testing', href: '/tools/journal-entry-testing', description: '19-test battery: Benford, fraud indicators', category: 'Testing Suite', icon: 'shield' },
  { key: 'ap_testing', label: 'AP Testing', href: '/tools/ap-testing', description: 'Duplicate payments, vendor anomalies', category: 'Testing Suite', icon: 'calculator' },
  { key: 'revenue_testing', label: 'Revenue Testing', href: '/tools/revenue-testing', description: 'ASC 606 / IFRS 15 contract analysis', category: 'Testing Suite', icon: 'banknotes' },
  { key: 'ar_aging', label: 'AR Aging', href: '/tools/ar-aging', description: 'Receivables aging and collectibility', category: 'Testing Suite', icon: 'clock' },
  { key: 'payroll_testing', label: 'Payroll Testing', href: '/tools/payroll-testing', description: 'Ghost employees, rate anomalies', category: 'Testing Suite', icon: 'calculator' },
  { key: 'fixed_asset_testing', label: 'Fixed Assets', href: '/tools/fixed-assets', description: 'Depreciation, impairment, disposals', category: 'Testing Suite', icon: 'building' },
  { key: 'inventory_testing', label: 'Inventory Testing', href: '/tools/inventory-testing', description: 'Valuation, obsolescence, cutoff', category: 'Testing Suite', icon: 'box' },
  { key: 'statistical_sampling', label: 'Stat Sampling', href: '/tools/statistical-sampling', description: 'ISA 530 sample design and evaluation', category: 'Advanced', icon: 'percentage' },
  { key: 'flux_analysis', label: 'Flux Analysis', href: '/flux', description: 'Account-level variance analysis', category: 'Advanced', icon: 'search' },
]

const DEFAULT_FAVORITES = ['trial_balance', 'journal_entry_testing', 'ap_testing', 'revenue_testing', 'payroll_testing', 'fixed_asset_testing']

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

function getToolIcon(iconKey: string) {
  const icons: Record<string, ReactNode> = {
    chart: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />,
    upload: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />,
    shield: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />,
    calculator: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25V13.5zm0 2.25h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25V18zm2.498-6.75h.007v.008h-.007v-.008zm0 2.25h.007v.008h-.007V13.5zm0 2.25h.007v.008h-.007v-.008zm0 2.25h.007v.008h-.007V18zm2.504-6.75h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V13.5zm0 2.25h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V18zm2.498-6.75h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V13.5zM8.25 6h7.5v2.25h-7.5V6zM12 2.25c-1.892 0-3.758.11-5.593.322C5.307 2.7 4.5 3.65 4.5 4.757V19.5a2.25 2.25 0 002.25 2.25h10.5a2.25 2.25 0 002.25-2.25V4.757c0-1.108-.806-2.057-1.907-2.185A48.507 48.507 0 0012 2.25z" />,
    search: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />,
    banknotes: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />,
    receipt: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />,
    clock: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />,
    cube: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9" />,
    truck: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.029-.504 1.029-1.125v-3.026a3 3 0 00-.879-2.121l-3.024-3.024A3 3 0 0014.226 8.25H14.25M3.375 14.25h4.875" />,
    building: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />,
    box: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />,
    percentage: <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6.75 6.75h.75v.75h-.75v-.75zm9.75 9.75h.75v.75h-.75v-.75zM5.25 18.75l13.5-13.5" />,
  }
  return (
    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      {icons[iconKey] || icons.cube}
    </svg>
  )
}

/* ─── Component ─────────────────────────────────────────────────────── */

export default function DashboardPage() {
  const router = useRouter()
  const { user, token, isAuthenticated, isLoading: authLoading } = useAuthSession()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [activity, setActivity] = useState<ToolActivityItem[]>([])
  const [favorites, setFavorites] = useState<string[]>(DEFAULT_FAVORITES)
  const [statsLoading, setStatsLoading] = useState(true)
  const [activityLoading, setActivityLoading] = useState(true)

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

    apiGet<ToolActivityItem[]>('/activity/tool-feed?limit=8', token)
      .then(res => { if (res.data) setActivity(res.data) })
      .catch(() => {})
      .finally(() => setActivityLoading(false))

    apiGet<UserPreferences>('/settings/preferences', token)
      .then(res => { if (res.data?.favorite_tools?.length) setFavorites(res.data.favorite_tools) })
      .catch(() => {})
  }, [token])

  const toggleFavorite = useCallback(
    async (toolKey: string) => {
      if (!token) return
      const next = favorites.includes(toolKey)
        ? favorites.filter(k => k !== toolKey)
        : [...favorites, toolKey]
      setFavorites(next)
      try {
        await apiPut('/settings/preferences', token, { favorite_tools: next })
      } catch {
        // Revert on failure
        setFavorites(favorites)
      }
    },
    [token, favorites]
  )

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

  const favoritedTools = TOOLS.filter(t => favorites.includes(t.key))
  const displayTools = favoritedTools.length > 0 ? favoritedTools : TOOLS.slice(0, 6)

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
                      {getToolIcon(tool.icon)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="font-sans font-semibold text-sm text-content-primary">{tool.label}</h3>
                      <p className="text-xs font-sans text-content-tertiary mt-0.5 line-clamp-2">{tool.description}</p>
                    </div>
                  </Link>
                  <button
                    onClick={(e) => { e.preventDefault(); toggleFavorite(tool.key) }}
                    className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center rounded-md opacity-0 group-hover:opacity-100 transition-opacity hover:bg-oatmeal-100"
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
                <h3 className="font-sans font-semibold text-sm text-content-primary">Portfolio &amp; Workspaces</h3>
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

            {activityLoading ? (
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
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-sage-600 text-white rounded-xl font-sans text-sm font-bold hover:bg-sage-700 transition-colors shadow-theme-card"
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
                  const tool = TOOLS.find(t => t.key === item.tool_name)
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
                        {getToolIcon(tool?.icon || 'cube')}
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
