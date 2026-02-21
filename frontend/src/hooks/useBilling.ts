/**
 * Billing hook — Sprint 368.
 *
 * Wraps billing API calls. Follows existing hook patterns (useAdjustments, etc.).
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { apiGet, apiPost } from '@/utils/apiClient'

export interface SubscriptionInfo {
  id: number | null
  tier: string
  status: string
  billing_interval: string | null
  current_period_start: string | null
  current_period_end: string | null
  cancel_at_period_end: boolean
}

export interface UsageInfo {
  diagnostics_used: number
  diagnostics_limit: number
  clients_used: number
  clients_limit: number
  tier: string
}

interface BillingState {
  subscription: SubscriptionInfo | null
  usage: UsageInfo | null
  isLoading: boolean
  error: string | null
}

export function useBilling() {
  const { token } = useAuth()
  const [state, setState] = useState<BillingState>({
    subscription: null,
    usage: null,
    isLoading: false,
    error: null,
  })

  const fetchSubscription = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiGet<SubscriptionInfo>('/billing/subscription', token)
    if (ok && data) {
      setState(prev => ({ ...prev, subscription: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to fetch subscription', isLoading: false }))
    return null
  }, [token])

  const fetchUsage = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error: apiError } = await apiGet<UsageInfo>('/billing/usage', token)
    if (ok && data) {
      setState(prev => ({ ...prev, usage: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to fetch usage', isLoading: false }))
    return null
  }, [token])

  const createCheckoutSession = useCallback(async (
    tier: string,
    interval: string,
    successUrl: string,
    cancelUrl: string,
  ): Promise<string | null> => {
    const { data, ok, error: apiError } = await apiPost<{ checkout_url: string }>(
      '/billing/create-checkout-session',
      token,
      { tier, interval, success_url: successUrl, cancel_url: cancelUrl },
    )
    if (ok && data) {
      return data.checkout_url
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to create checkout session' }))
    return null
  }, [token])

  const cancelSubscription = useCallback(async (): Promise<boolean> => {
    const { ok, error: apiError } = await apiPost<{ message: string }>('/billing/cancel', token, {})
    if (ok) {
      setState(prev => ({
        ...prev,
        subscription: prev.subscription ? { ...prev.subscription, cancel_at_period_end: true } : null,
      }))
      return true
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to cancel subscription' }))
    return false
  }, [token])

  const reactivateSubscription = useCallback(async (): Promise<boolean> => {
    const { ok, error: apiError } = await apiPost<{ message: string }>('/billing/reactivate', token, {})
    if (ok) {
      setState(prev => ({
        ...prev,
        subscription: prev.subscription ? { ...prev.subscription, cancel_at_period_end: false } : null,
      }))
      return true
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to reactivate subscription' }))
    return false
  }, [token])

  const getPortalUrl = useCallback(async (): Promise<string | null> => {
    const { data, ok, error: apiError } = await apiGet<{ portal_url: string }>('/billing/portal-session', token)
    if (ok && data) {
      return data.portal_url
    }
    setState(prev => ({ ...prev, error: apiError ?? 'Failed to get portal URL' }))
    return null
  }, [token])

  return {
    ...state,
    fetchSubscription,
    fetchUsage,
    createCheckoutSession,
    cancelSubscription,
    reactivateSubscription,
    getPortalUrl,
  }
}
