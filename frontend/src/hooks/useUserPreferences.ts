/**
 * User preferences hook (Sprint 751).
 *
 * Fetches `/settings/preferences` on mount, exposes a `toggleFavorite`
 * action that optimistically updates local state and PUTs the new list.
 * Reverts and reports when the save fails (Sprint 890: a resolved `ok: false`
 * is a failure too), and ignores a late response from an older request.
 *
 * Per ADR-017: this is a workflow hook with a narrow API. The dashboard
 * page composes it alongside `useDashboardStats` + `useActivityFeed`
 * rather than carrying preferences fetch + persist logic inline.
 */
'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
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
  const [favorites, setFavorites] = useState<string[]>(DEFAULT_FAVORITES)

  // Sprint 890 (15A): callers pass an inline onError; keep the latest in a ref so the
  // fetch effect does not re-run (and refetch) on every render.
  const onErrorRef = useRef(options.onError)
  useEffect(() => {
    onErrorRef.current = options.onError
  })

  // The list the server last confirmed, the list on screen, and a counter so a late
  // response from an older request can never undo a newer change.
  const confirmedRef = useRef<string[]>(DEFAULT_FAVORITES)
  const currentRef = useRef<string[]>(DEFAULT_FAVORITES)
  const changeSeqRef = useRef(0)

  const show = useCallback((list: string[]) => {
    currentRef.current = list
    setFavorites(list)
  }, [])

  useEffect(() => {
    if (!token) return
    const seqAtLoad = changeSeqRef.current
    apiGet<UserPreferencesResponse>('/settings/preferences', token)
      .then(res => {
        if (!res.ok) {
          onErrorRef.current?.('Failed to load preferences')
          return
        }
        if (changeSeqRef.current !== seqAtLoad) return // the user changed something meanwhile
        if (res.data?.favorite_tools?.length) {
          confirmedRef.current = res.data.favorite_tools
          show(res.data.favorite_tools)
        }
      })
      .catch(() => {
        onErrorRef.current?.('Failed to load preferences')
      })
  }, [token, show])

  const toggleFavorite = useCallback(
    async (toolKey: string) => {
      if (!token) return
      const previous = currentRef.current
      const next = previous.includes(toolKey)
        ? previous.filter(k => k !== toolKey)
        : [...previous, toolKey]
      const seq = ++changeSeqRef.current

      // Optimistic update — UI flips immediately, revert if the save fails.
      show(next)
      let saved = false
      try {
        const res = await apiPut('/settings/preferences', token, { favorite_tools: next })
        saved = Boolean(res?.ok)
      } catch {
        saved = false
      }
      if (seq !== changeSeqRef.current) {
        // A newer change was made; its own response decides. Remember a success only.
        if (saved) confirmedRef.current = next
        return
      }
      if (saved) {
        confirmedRef.current = next
      } else {
        show(confirmedRef.current)
        onErrorRef.current?.('Failed to save preferences')
      }
    },
    [token, show],
  )

  return { favorites, toggleFavorite }
}
