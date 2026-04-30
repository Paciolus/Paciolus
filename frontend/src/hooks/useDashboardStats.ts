/**
 * Dashboard stats hook (Sprint 751).
 *
 * Fetches `/dashboard/stats` once on mount, exposes a `retry` action,
 * and surfaces explicit `loading` / `error` flags so the dashboard's
 * stat cards can render skeletons / error banners cleanly.
 *
 * Per ADR-017: workflow hook with a narrow API. The page composes this
 * with `useActivityFeed` and `useUserPreferences` rather than carrying
 * the fetch logic inline.
 */
'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiGet } from '@/utils/apiClient'

export interface DashboardStats {
  total_clients: number
  assessments_today: number
  last_assessment_date: string | null
  total_assessments: number
  tool_runs_today: number
  total_tool_runs: number
  active_workspaces: number
  tools_used: number
}

export interface UseDashboardStatsReturn {
  stats: DashboardStats | null
  loading: boolean
  error: boolean
  retry: () => void
}

export interface UseDashboardStatsOptions {
  /** Called with a user-facing message when the fetch fails. The page
   *  consumer typically pipes this to `useToast().error`. */
  onError?: (message: string) => void
}

export function useDashboardStats(
  token: string | null,
  options: UseDashboardStatsOptions = {},
): UseDashboardStatsReturn {
  const { onError } = options
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchStats = useCallback(() => {
    if (!token) return
    setError(false)
    setLoading(true)
    apiGet<DashboardStats>('/dashboard/stats', token)
      .then(res => {
        if (res.data) setStats(res.data)
      })
      .catch(() => {
        setError(true)
        onError?.('Failed to load dashboard stats')
      })
      .finally(() => setLoading(false))
  }, [token, onError])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return { stats, loading, error, retry: fetchStats }
}
