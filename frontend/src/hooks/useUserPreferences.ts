/**
 * User preferences hook (Sprint 751).
 *
 * Fetches `/settings/preferences` on mount, exposes a `toggleFavorite`
 * action that optimistically updates local state and PUTs the new list.
 * Reverts on PUT failure.
 *
 * Per ADR-017: this is a workflow hook with a narrow API. The dashboard
 * page composes it alongside `useDashboardStats` + `useActivityFeed`
 * rather than carrying preferences fetch + persist logic inline.
 */
'use client'

import { useCallback, useEffect, useState } from 'react'
import { DEFAULT_FAVORITES } from '@/content/dashboard-tools'
import { apiGet, apiPut } from '@/utils/apiClient'

interface UserPreferencesResponse {
  favorite_tools: string[]
}

export interface UseUserPreferencesReturn {
  /** Tool keys currently favorited (falls back to DEFAULT_FAVORITES). */
  favorites: string[]
  /** Optimistically toggle membership; reverts on PUT failure. */
  toggleFavorite: (toolKey: string) => Promise<void>
}

export interface UseUserPreferencesOptions {
  onError?: (message: string) => void
}

export function useUserPreferences(
  token: string | null,
  options: UseUserPreferencesOptions = {},
): UseUserPreferencesReturn {
  const { onError } = options
  const [favorites, setFavorites] = useState<string[]>(DEFAULT_FAVORITES)

  useEffect(() => {
    if (!token) return
    apiGet<UserPreferencesResponse>('/settings/preferences', token)
      .then(res => {
        if (res.data?.favorite_tools?.length) setFavorites(res.data.favorite_tools)
      })
      .catch(() => {
        onError?.('Failed to load preferences')
      })
  }, [token, onError])

  const toggleFavorite = useCallback(
    async (toolKey: string) => {
      if (!token) return
      const previous = favorites
      const next = previous.includes(toolKey)
        ? previous.filter(k => k !== toolKey)
        : [...previous, toolKey]

      // Optimistic update — UI flips immediately, revert if the PUT fails.
      setFavorites(next)
      try {
        await apiPut('/settings/preferences', token, { favorite_tools: next })
      } catch {
        setFavorites(previous)
      }
    },
    [token, favorites],
  )

  return { favorites, toggleFavorite }
}
