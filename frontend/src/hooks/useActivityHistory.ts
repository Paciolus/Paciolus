/**
 * Paciolus Activity History Hook
 * Phase 2 Refactor: Extracted from history page
 *
 * Handles fetching diagnostic history from API with localStorage fallback.
 *
 * ZERO-STORAGE: Only metadata is stored, never financial data.
 */

import { useEffect, useState, useCallback, useRef } from 'react'
import { useAuth } from '@/context/AuthContext'
import { apiGet, isAuthError, prefetch } from '@/utils'
import type { AuditActivity, ActivityHistoryResponse } from '@/types/history'
import {
  HISTORY_STORAGE_KEY,
  HISTORY_VERSION,
  mapActivityLogToAuditActivity,
} from '@/types/history'

interface UseActivityHistoryOptions {
  /** Number of items per page (default: 50) */
  pageSize?: number
  /** Initial page number (default: 1) */
  initialPage?: number
  /** Whether to auto-fetch on mount (default: true) */
  autoFetch?: boolean
}

interface UseActivityHistoryReturn {
  /** List of activity entries */
  activities: AuditActivity[]
  /** Loading state */
  isLoading: boolean
  /** Error message if fetch failed */
  error: string | null
  /** Total count of activities */
  totalCount: number
  /** Current page number */
  page: number
  /** Total number of pages */
  totalPages: number
  /** Whether there's a next page */
  hasNextPage: boolean
  /** Whether there's a previous page */
  hasPrevPage: boolean
  /** Refetch the history data */
  refetch: () => Promise<void>
  /** Go to a specific page */
  setPage: (page: number) => void
  /** Go to next page */
  nextPage: () => void
  /** Go to previous page */
  prevPage: () => void
}

/**
 * Hook for fetching and managing activity history.
 *
 * @example
 * const { activities, isLoading, error, refetch } = useActivityHistory()
 *
 * @example
 * // With pagination
 * const { activities, page, setPage, totalCount } = useActivityHistory({
 *   pageSize: 20,
 *   initialPage: 1,
 * })
 */
export function useActivityHistory(
  options: UseActivityHistoryOptions = {}
): UseActivityHistoryReturn {
  const { pageSize = 50, initialPage = 1, autoFetch = true } = options

  const [activities, setActivities] = useState<AuditActivity[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(initialPage)

  const { isAuthenticated, token, isLoading: authLoading } = useAuth()

  // Track if prefetch has been triggered to avoid duplicate prefetches
  const prefetchedPages = useRef<Set<number>>(new Set())

  // Load from localStorage as fallback
  const loadFromLocalStorage = useCallback(() => {
    try {
      const stored = localStorage.getItem(HISTORY_STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        if (parsed.version === HISTORY_VERSION) {
          const localActivities = parsed.activities || []
          setActivities(localActivities)
          setTotalCount(localActivities.length)
        }
      }
    } catch (err) {
      console.error('Failed to load from localStorage:', err)
    }
  }, [])

  // Fetch history from API
  const fetchHistory = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      if (isAuthenticated && token) {
        // Authenticated: Fetch from backend API
        const { data, status, ok } = await apiGet<ActivityHistoryResponse>(
          `/activity/history?page=${page}&page_size=${pageSize}`,
          token
        )

        if (ok && data) {
          const mappedActivities = data.activities.map(mapActivityLogToAuditActivity)
          setActivities(mappedActivities)
          setTotalCount(data.total_count)
        } else if (isAuthError(status)) {
          // Token expired or invalid, fall back to localStorage
          loadFromLocalStorage()
        } else {
          throw new Error('Failed to fetch history')
        }
      } else {
        // Not authenticated: Load from localStorage
        loadFromLocalStorage()
      }
    } catch (err) {
      console.error('Failed to load audit history:', err)
      setError('Failed to load history. Showing local data.')
      loadFromLocalStorage()
    } finally {
      setIsLoading(false)
    }
  }, [isAuthenticated, token, page, pageSize, loadFromLocalStorage])

  // Auto-fetch on mount and when dependencies change
  useEffect(() => {
    if (authLoading || !autoFetch) return
    fetchHistory()
  }, [authLoading, autoFetch, fetchHistory])

  // Calculate pagination info
  const totalPages = Math.ceil(totalCount / pageSize)
  const hasNextPage = page < totalPages
  const hasPrevPage = page > 1

  // Prefetch next page after current page loads (with delay)
  useEffect(() => {
    if (!isAuthenticated || !token || isLoading || !hasNextPage) return

    const nextPage = page + 1

    // Skip if already prefetched
    if (prefetchedPages.current.has(nextPage)) return

    // Prefetch after a short delay (user is likely reading current page)
    const timer = setTimeout(() => {
      prefetchedPages.current.add(nextPage)
      prefetch<ActivityHistoryResponse>(
        `/activity/history?page=${nextPage}&page_size=${pageSize}`,
        token
      )
    }, 2000) // 2 second delay

    return () => clearTimeout(timer)
  }, [isAuthenticated, token, isLoading, hasNextPage, page, pageSize])

  // Navigation helpers
  const nextPage = useCallback(() => {
    if (hasNextPage) {
      setPage(p => p + 1)
    }
  }, [hasNextPage])

  const prevPage = useCallback(() => {
    if (hasPrevPage) {
      setPage(p => p - 1)
    }
  }, [hasPrevPage])

  return {
    activities,
    isLoading,
    error,
    totalCount,
    page,
    totalPages,
    hasNextPage,
    hasPrevPage,
    refetch: fetchHistory,
    setPage,
    nextPage,
    prevPage,
  }
}
