/**
 * Sprint 872: a refused identical re-run can be run again as-is.
 *
 * POST /audit/trial-balance answers 409 when the same file is sent with the same
 * settings within 5 minutes. The hook marks that as a duplicate and
 * forceRerunAudit() repeats the refused request with force_resubmit=true.
 */
import { renderHook, act } from '@testing-library/react'
import { useTrialBalanceUpload } from '@/hooks/useTrialBalanceUpload'

jest.mock('@/contexts/MappingContext', () => ({
  useMappings: jest.fn(() => ({ getOverridesForApi: () => ({}), initializeFromAudit: jest.fn() })),
}))
jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({ user: { id: 1, is_verified: true }, token: 't', isAuthenticated: true })),
}))
jest.mock('@/contexts/EngagementContext', () => ({ useOptionalEngagementContext: jest.fn(() => null) }))
jest.mock('@/hooks/useSettings', () => ({ useSettings: jest.fn(() => ({ practiceSettings: null, isLoading: false })) }))
jest.mock('@/utils', () => ({ apiPost: jest.fn(() => Promise.resolve()) }))
jest.mock('@/utils/constants', () => ({ API_URL: 'http://localhost:8000' }))
jest.mock('@/utils/apiClient', () => ({ getCsrfToken: jest.fn(() => 'csrf') }))

const mockFetch = jest.fn()
global.fetch = mockFetch

const conflict = {
  ok: false,
  status: 409,
  json: async () => ({
    code: 'CONFLICT',
    message: "This file ('tb.csv') matches a previous submission ... re-submit with force_resubmit=true.",
    detail: { error: 'duplicate_submission' },
  }),
}
const success = {
  ok: true,
  status: 200,
  json: async () => ({
    status: 'success', balanced: true, total_debits: 1, total_credits: 1, difference: 0, row_count: 2,
    message: 'Balanced', abnormal_balances: [], has_risk_alerts: false, materiality_threshold: 250,
    material_count: 0, immaterial_count: 0,
  }),
}

const sentForm = (call: number): FormData => mockFetch.mock.calls[call][1].body as FormData

describe('useTrialBalanceUpload duplicate handling', () => {
  beforeEach(() => mockFetch.mockReset())

  it('marks a 409 as a duplicate and re-runs the same request with force_resubmit', async () => {
    mockFetch.mockResolvedValueOnce(conflict).mockResolvedValueOnce(success)
    const { result } = renderHook(() => useTrialBalanceUpload())
    const file = new File(['a,b\n'], 'tb.csv', { type: 'text/csv' })

    await act(async () => {
      await result.current.runAudit(file, 250, false, null, null, 'preflight-tok')
    })
    expect(result.current.auditStatus).toBe('error')
    expect(result.current.isDuplicate).toBe(true)
    expect(result.current.auditError).not.toMatch(/force_resubmit/)
    expect(sentForm(0).get('force_resubmit')).toBeNull()

    await act(async () => {
      result.current.forceRerunAudit()
    })
    expect(mockFetch).toHaveBeenCalledTimes(2)
    const rerun = sentForm(1)
    expect(rerun.get('force_resubmit')).toBe('true')
    expect(rerun.get('materiality_threshold')).toBe('250')
    expect(rerun.get('file')).toBeInstanceOf(File)
    expect(rerun.get('preflight_token')).toBeNull() // single-use; not resent
    expect(result.current.auditStatus).toBe('success')
    expect(result.current.isDuplicate).toBe(false)
  })

  it('other failures are not marked as duplicates', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500, json: async () => ({ message: 'boom' }) })
    const { result } = renderHook(() => useTrialBalanceUpload())
    await act(async () => {
      await result.current.runAudit(new File(['a'], 'tb.csv'), 0)
    })
    expect(result.current.auditStatus).toBe('error')
    expect(result.current.isDuplicate).toBe(false)
  })
})
