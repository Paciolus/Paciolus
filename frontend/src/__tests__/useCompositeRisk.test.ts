/**
 * Sprint 688: useCompositeRisk hook tests.
 *
 * Pins the POST /composite-risk/profile contract: request body is forwarded
 * as-is, success hydrates `result`, error paths surface an error string.
 */
import { renderHook, act } from '@testing-library/react'
import { useCompositeRisk } from '@/hooks/useCompositeRisk'
import type {
  CompositeRiskProfileRequest,
  CompositeRiskProfileResponse,
} from '@/types/compositeRisk'

const mockApiPost = jest.fn()

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ token: 'tok-crsp' }),
}))

jest.mock('@/utils/apiClient', () => ({
  apiPost: (...args: unknown[]) => mockApiPost(...args),
}))

const samplePayload: CompositeRiskProfileRequest = {
  account_assessments: [
    {
      account_name: 'Revenue',
      assertion: 'existence',
      inherent_risk: 'high',
      control_risk: 'moderate',
      fraud_risk_factor: true,
      auditor_notes: 'Significant revenue concentration',
    },
  ],
  going_concern_indicators_triggered: 2,
}

const sampleResponse: CompositeRiskProfileResponse = {
  account_assessments: [
    {
      account_name: 'Revenue',
      assertion: 'existence',
      inherent_risk: 'high',
      control_risk: 'moderate',
      combined_risk: 'high',
      fraud_risk_factor: true,
      auditor_notes: 'Significant revenue concentration',
    },
  ],
  testing_scores: {},
  going_concern_indicators_triggered: 2,
  high_risk_accounts: 1,
  fraud_risk_accounts: 1,
  total_assessments: 1,
  risk_distribution: { low: 0, moderate: 0, elevated: 0, high: 1 },
  overall_risk_tier: 'high',
  disclaimer: 'Auditor judgment required.',
}

describe('useCompositeRisk', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('starts idle', () => {
    const { result } = renderHook(() => useCompositeRisk())
    expect(result.current.status).toBe('idle')
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBe('')
  })

  it('buildProfile: success hydrates result and forwards token + body', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: sampleResponse })
    const { result } = renderHook(() => useCompositeRisk())

    await act(async () => {
      await result.current.buildProfile(samplePayload)
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/composite-risk/profile',
      'tok-crsp',
      samplePayload,
    )
    expect(result.current.status).toBe('success')
    expect(result.current.result).toEqual(sampleResponse)
    expect(result.current.error).toBe('')
  })

  it('buildProfile: error path surfaces error and clears result', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'Invalid assertion' })
    const { result } = renderHook(() => useCompositeRisk())

    await act(async () => {
      await result.current.buildProfile(samplePayload)
    })

    expect(result.current.status).toBe('error')
    expect(result.current.error).toBe('Invalid assertion')
    expect(result.current.result).toBeNull()
  })

  it('reset returns to idle', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: sampleResponse })
    const { result } = renderHook(() => useCompositeRisk())

    await act(async () => {
      await result.current.buildProfile(samplePayload)
    })
    expect(result.current.status).toBe('success')

    act(() => {
      result.current.reset()
    })
    expect(result.current.status).toBe('idle')
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBe('')
  })
})
