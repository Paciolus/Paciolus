/**
 * Admin Dashboard Hook — Sprint 545a
 *
 * Fetches team overview, activity, and usage data for the admin dashboard.
 * Professional+ tier only (gated by FeatureGate on the page level).
 */

'use client'

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import type { AdminOverview, TeamActivity, MemberUsage } from '@/types/adminDashboard'
import { apiGet } from '@/utils/apiClient'
import { apiDownload, downloadBlob } from '@/utils/downloadAdapter'

interface AdminDashboardState {
  overview: AdminOverview | null
  teamActivity: TeamActivity[]
  memberUsage: MemberUsage[]
  isLoading: boolean
  error: string | null
}

export function useAdminDashboard() {
  const { token } = useAuthSession()
  const [state, setState] = useState<AdminDashboardState>({
    overview: null,
    teamActivity: [],
    memberUsage: [],
    isLoading: false,
    error: null,
  })

  const fetchOverview = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiGet<AdminOverview>('/admin/overview', token)
    if (ok && data) {
      setState(prev => ({ ...prev, overview: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to fetch overview', isLoading: false }))
    return null
  }, [token])

  const fetchTeamActivity = useCallback(async (
    days?: number,
    tool?: string,
    member?: string,
  ) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const params = new URLSearchParams()
    if (days) params.append('days', String(days))
    if (tool) params.append('tool', tool)
    if (member) params.append('member', member)
    const qs = params.toString()
    const url = `/admin/team-activity${qs ? `?${qs}` : ''}`

    const { data, ok, error: apiError } = await apiGet<TeamActivity[]>(url, token)
    if (ok && data) {
      setState(prev => ({ ...prev, teamActivity: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to fetch team activity', isLoading: false }))
    return null
  }, [token])

  const fetchUsageByMember = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiGet<MemberUsage[]>('/admin/usage-by-member', token)
    if (ok && data) {
      setState(prev => ({ ...prev, memberUsage: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to fetch usage data', isLoading: false }))
    return null
  }, [token])

  const exportActivityCsv = useCallback(async () => {
    const { blob, filename, ok } = await apiDownload('/admin/export-activity-csv', token)
    if (ok && blob) {
      downloadBlob(blob, filename ?? 'team-activity.csv')
      return true
    }
    setState(prev => ({ ...prev, error: 'Failed to export activity CSV' }))
    return false
  }, [token])

  return {
    ...state,
    fetchOverview,
    fetchTeamActivity,
    fetchUsageByMember,
    exportActivityCsv,
  }
}
