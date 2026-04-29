/**
 * Activity feed hook (Sprint 751).
 *
 * Fetches `/activity/tool-feed?limit=N` once on mount, exposes `retry`,
 * tracks `loading` / `error` for the dashboard's "Recent Activity"
 * section.
 */
'use client'

import { useCallback, useEffect, useState } from 'react'
import { apiGet } from '@/utils/apiClient'

export interface ToolActivityItem {
  id: number
  tool_name: string
  tool_label: string
  filename: string | null
  record_count: number | null
  summary: Record<string, unknown> | null
  created_at: string
}

export interface UseActivityFeedReturn {
  activity: ToolActivityItem[]
  loading: boolean
  error: boolean
  retry: () => void
}

export interface UseActivityFeedOptions {
  /** Items requested from `/activity/tool-feed?limit=`. Default: 8. */
  limit?: number
  onError?: (message: string) => void
}

export function useActivityFeed(
  token: string | null,
  options: UseActivityFeedOptions = {},
): UseActivityFeedReturn {
  const { limit = 8, onError } = options
  const [activity, setActivity] = useState<ToolActivityItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchActivity = useCallback(() => {
    if (!token) return
    setError(false)
    setLoading(true)
    apiGet<ToolActivityItem[]>(`/activity/tool-feed?limit=${limit}`, token)
      .then(res => {
        if (res.data) setActivity(res.data)
      })
      .catch(() => {
        setError(true)
        onError?.('Failed to load activity feed')
      })
      .finally(() => setLoading(false))
  }, [token, limit, onError])

  useEffect(() => {
    fetchActivity()
  }, [fetchActivity])

  return { activity, loading, error, retry: fetchActivity }
}
