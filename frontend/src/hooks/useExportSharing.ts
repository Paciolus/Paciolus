/**
 * Export Sharing Hook — Sprint 545c
 *
 * Manage share links for exports (Professional+ tier).
 */

'use client'

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import type { ExportShareInfo } from '@/types/exportSharing'
import { apiGet, apiPost, apiDelete } from '@/utils/apiClient'

interface ExportSharingState {
  shares: ExportShareInfo[]
  isLoading: boolean
  error: string | null
}

export function useExportSharing() {
  const { token } = useAuthSession()
  const [state, setState] = useState<ExportSharingState>({
    shares: [],
    isLoading: false,
    error: null,
  })

  const listShares = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiGet<ExportShareInfo[]>('/export-sharing/', token)
    if (ok && data) {
      setState(prev => ({ ...prev, shares: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to fetch shares', isLoading: false }))
    return null
  }, [token])

  const createShare = useCallback(async (
    tool: string,
    format: string,
    b64data: string,
  ): Promise<ExportShareInfo | null> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiPost<ExportShareInfo>(
      '/export-sharing/create',
      token,
      { tool, format, data: b64data },
    )
    if (ok && data) {
      setState(prev => ({
        ...prev,
        shares: [data, ...prev.shares],
        isLoading: false,
      }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to create share', isLoading: false }))
    return null
  }, [token])

  const revokeShare = useCallback(async (shareToken: string): Promise<boolean> => {
    const { ok, error: apiError } = await apiDelete(`/export-sharing/${shareToken}`, token)
    if (ok) {
      setState(prev => ({
        ...prev,
        shares: prev.shares.filter(s => s.token !== shareToken),
      }))
      return true
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to revoke share' }))
    return false
  }, [token])

  return {
    ...state,
    listShares,
    createShare,
    revokeShare,
  }
}
