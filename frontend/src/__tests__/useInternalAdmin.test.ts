/**
 * Sprint 652: useInternalAdmin hook tests — covers the admin surface
 * (superadmin customer console). Happy + error paths for each major
 * action since these write paths have real-world consequences
 * (plan overrides, refunds, revocations).
 */
import { renderHook, act } from '@testing-library/react'
import { useInternalAdmin } from '@/hooks/useInternalAdmin'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ token: 'admin-tok' }),
}))

jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}))

const customerListData = {
  customers: [{ org_id: 1, name: 'Acme', plan: 'solo' }],
  total: 1,
}

describe('useInternalAdmin', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('starts empty and not loading', () => {
    const { result } = renderHook(() => useInternalAdmin())
    expect(result.current.customers).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetchCustomers: happy path stores the list', async () => {
    mockApiGet.mockResolvedValue({ ok: true, data: customerListData })
    const { result } = renderHook(() => useInternalAdmin())

    await act(async () => {
      const rows = await result.current.fetchCustomers({ plan: 'solo' })
      expect(rows).toEqual(customerListData)
    })

    expect(mockApiGet).toHaveBeenCalledWith('/internal/admin/customers/?plan=solo', 'admin-tok')
    expect(result.current.customers).toEqual(customerListData)
  })

  it('fetchCustomers: error path sets error and leaves state unchanged', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Not permitted' })
    const { result } = renderHook(() => useInternalAdmin())

    await act(async () => {
      const rows = await result.current.fetchCustomers()
      expect(rows).toBeNull()
    })

    expect(result.current.customers).toBeNull()
    expect(result.current.error).toBe('Not permitted')
  })

  it('fetchCustomerDetail: happy path stores detail', async () => {
    const detail = { org_id: 1, name: 'Acme', billing: { plan: 'solo' } }
    mockApiGet.mockResolvedValue({ ok: true, data: detail })

    const { result } = renderHook(() => useInternalAdmin())
    await act(async () => {
      await result.current.fetchCustomerDetail(1)
    })

    expect(mockApiGet).toHaveBeenCalledWith('/internal/admin/customers/1', 'admin-tok')
    expect(result.current.customerDetail).toEqual(detail)
  })

  it('planOverride: returns response on success', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: { applied: true } })
    const { result } = renderHook(() => useInternalAdmin())

    await act(async () => {
      const res = await result.current.planOverride(1, {
        new_plan: 'professional',
        reason: 'manual',
        effective_immediately: true,
      })
      expect(res).toEqual({ applied: true })
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/internal/admin/customers/1/plan-override',
      'admin-tok',
      { new_plan: 'professional', reason: 'manual', effective_immediately: true },
    )
  })

  it('planOverride: throws on failure so callers surface the error', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'boom' })
    const { result } = renderHook(() => useInternalAdmin())

    await expect(
      result.current.planOverride(1, { new_plan: 'x', reason: '', effective_immediately: false }),
    ).rejects.toThrow('boom')
  })

  it('impersonate: returns the token payload on success', async () => {
    const payload = { impersonation_token: 'imp-123', expires_in: 900 }
    mockApiPost.mockResolvedValue({ ok: true, data: payload })

    const { result } = renderHook(() => useInternalAdmin())
    await act(async () => {
      const res = await result.current.impersonate(1)
      expect(res).toEqual(payload)
    })

    expect(mockApiPost).toHaveBeenCalledWith('/internal/admin/customers/1/impersonate', 'admin-tok', {})
  })

  it('fetchAuditLog: forwards filters and stores log', async () => {
    const auditLog = { entries: [{ id: 1, action: 'PLAN_OVERRIDE' }], total: 1 }
    mockApiGet.mockResolvedValue({ ok: true, data: auditLog })

    const { result } = renderHook(() => useInternalAdmin())
    await act(async () => {
      await result.current.fetchAuditLog({ action: 'PLAN_OVERRIDE' })
    })

    expect(mockApiGet).toHaveBeenCalledWith('/internal/admin/audit-log?action=PLAN_OVERRIDE', 'admin-tok')
    expect(result.current.auditLog).toEqual(auditLog)
  })

  it('revokeSessions: throws the server message on failure', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'already offline' })
    const { result } = renderHook(() => useInternalAdmin())

    await expect(result.current.revokeSessions(42)).rejects.toThrow('already offline')
  })
})
