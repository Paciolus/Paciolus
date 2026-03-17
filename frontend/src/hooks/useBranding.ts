/**
 * Branding Hook — Sprint 545b
 *
 * CRUD operations for PDF branding configuration (Enterprise tier).
 */

'use client'

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import type { BrandingConfig } from '@/types/branding'
import { apiGet, apiPut, apiPost, apiDelete } from '@/utils/apiClient'

interface BrandingState {
  branding: BrandingConfig | null
  isLoading: boolean
  error: string | null
}

export function useBranding() {
  const { token } = useAuth()
  const [state, setState] = useState<BrandingState>({
    branding: null,
    isLoading: false,
    error: null,
  })

  const fetchBranding = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiGet<BrandingConfig>('/branding/', token)
    if (ok && data) {
      setState(prev => ({ ...prev, branding: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to fetch branding', isLoading: false }))
    return null
  }, [token])

  const updateBranding = useCallback(async (header: string, footer: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiPut<BrandingConfig>('/branding/', token, {
      header_text: header,
      footer_text: footer,
    })
    if (ok && data) {
      setState(prev => ({ ...prev, branding: data, isLoading: false }))
      return true
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to update branding', isLoading: false }))
    return false
  }, [token])

  const uploadLogo = useCallback(async (file: File): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const formData = new FormData()
    formData.append('logo', file)
    const { data, ok, error: apiError } = await apiPost<BrandingConfig>('/branding/logo', token, formData)
    if (ok && data) {
      setState(prev => ({ ...prev, branding: data, isLoading: false }))
      return true
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to upload logo', isLoading: false }))
    return false
  }, [token])

  const deleteLogo = useCallback(async (): Promise<boolean> => {
    const { ok, error: apiError } = await apiDelete('/branding/logo', token)
    if (ok) {
      setState(prev => ({
        ...prev,
        branding: prev.branding ? { ...prev.branding, logo_url: null } : null,
      }))
      return true
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to delete logo' }))
    return false
  }, [token])

  return {
    ...state,
    fetchBranding,
    updateBranding,
    uploadLogo,
    deleteLogo,
  }
}
