'use client'

/**
 * Internal Admin Console Hook — Sprint 590
 *
 * Data fetching and admin actions for the superadmin customer console.
 */

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import type {
  CustomerListResponse,
  CustomerDetail,
  AdminActionResponse,
  ImpersonationResponse,
  AuditLogResponse,
} from '@/types/internalAdmin'
import { apiGet, apiPost } from '@/utils/apiClient'

interface InternalAdminState {
  customers: CustomerListResponse | null
  customerDetail: CustomerDetail | null
  auditLog: AuditLogResponse | null
  isLoading: boolean
  error: string | null
}

export function useInternalAdmin() {
  const { token } = useAuthSession()
  const [state, setState] = useState<InternalAdminState>({
    customers: null,
    customerDetail: null,
    auditLog: null,
    isLoading: false,
    error: null,
  })

  const fetchCustomers = useCallback(async (params?: Record<string, string>) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    const { data, ok, error } = await apiGet<CustomerListResponse>(`/internal/admin/customers/${qs}`, token)
    if (ok && data) {
      setState(prev => ({ ...prev, customers: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: error ?? 'Failed to fetch customers', isLoading: false }))
    return null
  }, [token])

  const fetchCustomerDetail = useCallback(async (orgId: number) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const { data, ok, error } = await apiGet<CustomerDetail>(`/internal/admin/customers/${orgId}`, token)
    if (ok && data) {
      setState(prev => ({ ...prev, customerDetail: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: error ?? 'Failed to fetch customer detail', isLoading: false }))
    return null
  }, [token])

  const planOverride = useCallback(async (orgId: number, body: { new_plan: string; reason: string; effective_immediately: boolean }) => {
    const { data, ok, error } = await apiPost<AdminActionResponse>(`/internal/admin/customers/${orgId}/plan-override`, token, body)
    if (ok && data) return data
    throw new Error(error ?? 'Failed to override plan')
  }, [token])

  const extendTrial = useCallback(async (orgId: number, body: { days: number; reason: string }) => {
    const { data, ok, error } = await apiPost<AdminActionResponse>(`/internal/admin/customers/${orgId}/extend-trial`, token, body)
    if (ok && data) return data
    throw new Error(error ?? 'Failed to extend trial')
  }, [token])

  const issueCredit = useCallback(async (orgId: number, body: { amount_cents: number; reason: string }) => {
    const { data, ok, error } = await apiPost<AdminActionResponse>(`/internal/admin/customers/${orgId}/credit`, token, body)
    if (ok && data) return data
    throw new Error(error ?? 'Failed to issue credit')
  }, [token])

  const issueRefund = useCallback(async (orgId: number, body: { payment_intent_id: string; amount_cents: number; reason: string }) => {
    const { data, ok, error } = await apiPost<AdminActionResponse>(`/internal/admin/customers/${orgId}/refund`, token, body)
    if (ok && data) return data
    throw new Error(error ?? 'Failed to issue refund')
  }, [token])

  const forceCancel = useCallback(async (orgId: number, body: { reason: string; immediate: boolean }) => {
    const { data, ok, error } = await apiPost<AdminActionResponse>(`/internal/admin/customers/${orgId}/cancel`, token, body)
    if (ok && data) return data
    throw new Error(error ?? 'Failed to cancel subscription')
  }, [token])

  const impersonate = useCallback(async (orgId: number) => {
    const { data, ok, error } = await apiPost<ImpersonationResponse>(`/internal/admin/customers/${orgId}/impersonate`, token, {})
    if (ok && data) return data
    throw new Error(error ?? 'Failed to start impersonation')
  }, [token])

  const revokeSessions = useCallback(async (orgId: number) => {
    const { data, ok, error } = await apiPost<AdminActionResponse>(`/internal/admin/customers/${orgId}/revoke-sessions`, token, {})
    if (ok && data) return data
    throw new Error(error ?? 'Failed to revoke sessions')
  }, [token])

  const fetchAuditLog = useCallback(async (params?: Record<string, string>) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    const { data, ok, error } = await apiGet<AuditLogResponse>(`/internal/admin/audit-log${qs}`, token)
    if (ok && data) {
      setState(prev => ({ ...prev, auditLog: data, isLoading: false }))
      return data
    }
    setState(prev => ({ ...prev, error: error ?? 'Failed to fetch audit log', isLoading: false }))
    return null
  }, [token])

  return {
    ...state,
    fetchCustomers,
    fetchCustomerDetail,
    planOverride,
    extendTrial,
    issueCredit,
    issueRefund,
    forceCancel,
    impersonate,
    revokeSessions,
    fetchAuditLog,
  }
}
