/**
 * Sprint 886 (review OUT-16): the trial balance page tells the server how it set
 * the materiality threshold — the pre-filled default (saved firm setting or the
 * Paciolus default), the engagement's performance materiality, or the user's own
 * entry — so every export names the real origin instead of "manual".
 */
import { act, renderHook } from '@testing-library/react'
import { useTrialBalanceUpload } from '@/hooks/useTrialBalanceUpload'
import { uploadTrialBalance } from '@/utils/trialBalanceUpload'

const mockEngagement = { current: null as null | Record<string, unknown> }
const mockSettings = { current: { practiceSettings: null as unknown, isLoading: false } }

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ user: { is_verified: true }, isAuthenticated: true, token: 't' }),
}))
jest.mock('@/contexts/EngagementContext', () => ({ useOptionalEngagementContext: () => mockEngagement.current }))
jest.mock('@/contexts/MappingContext', () => ({
  useMappings: () => ({ getOverridesForApi: () => ({}), setAccountTypes: jest.fn() }),
}))
jest.mock('@/hooks/useSettings', () => ({ useSettings: () => mockSettings.current }))
jest.mock('@/utils', () => ({ apiPost: jest.fn() }))
jest.mock('@/utils/trialBalanceUpload', () => ({
  uploadTrialBalance: jest.fn().mockResolvedValue({ kind: 'error', message: 'stop' }),
}))

const file = new File(['a'], 'tb.csv', { type: 'text/csv' })
const sentOrigin = () => (uploadTrialBalance as jest.Mock).mock.calls.at(-1)[0].materialityOrigin

beforeEach(() => {
  ;(uploadTrialBalance as jest.Mock).mockClear()
  mockEngagement.current = null
  mockSettings.current = { practiceSettings: null, isLoading: false }
})

it('sends "default" for the pre-filled Paciolus default', async () => {
  const { result } = renderHook(() => useTrialBalanceUpload())
  await act(async () => { await result.current.runAudit(file, result.current.materialityThreshold) })
  expect(result.current.materialityThreshold).toBe(500)
  expect(sentOrigin()).toBe('default')
})

it('sends "default" for a threshold pre-filled from the saved firm setting', async () => {
  mockSettings.current = {
    practiceSettings: { default_materiality: { type: 'fixed', value: 2500 }, show_immaterial_by_default: false },
    isLoading: false,
  }
  const { result } = renderHook(() => useTrialBalanceUpload())
  expect(result.current.materialityThreshold).toBe(2500)
  await act(async () => { await result.current.runAudit(file, result.current.materialityThreshold) })
  expect(sentOrigin()).toBe('default')
})

it("sends \"engagement\" for the engagement's performance materiality", async () => {
  mockEngagement.current = {
    engagementId: 7, materiality: { performance_materiality: 1500 },
    refreshToolRuns: jest.fn(), triggerLinkToast: jest.fn(),
  }
  const { result } = renderHook(() => useTrialBalanceUpload())
  expect(result.current.materialityThreshold).toBe(1500)
  await act(async () => { await result.current.runAudit(file, result.current.materialityThreshold) })
  expect(sentOrigin()).toBe('engagement')
})

it('sends "entered" once the user types a figure, even over an engagement pre-fill', async () => {
  mockEngagement.current = {
    engagementId: 7, materiality: { performance_materiality: 1500 },
    refreshToolRuns: jest.fn(), triggerLinkToast: jest.fn(),
  }
  const { result } = renderHook(() => useTrialBalanceUpload())
  act(() => result.current.setMaterialityThreshold(750))
  await act(async () => { await result.current.runAudit(file, 750) })
  expect(sentOrigin()).toBe('entered')
})
