/**
 * Sprint 890 (CEO brief 15C): a testing-tool response missing a required key is reported as an
 * error, not cast to its type and rendered.
 */
import { act, renderHook } from '@testing-library/react'
import { createTestingHook } from '@/hooks/createTestingHook'

const mockUploadFetch = jest.fn()
jest.mock('@/utils/uploadTransport', () => ({
  uploadFetch: (...args: unknown[]) => mockUploadFetch(...args),
}))
jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({ token: 'test-token', user: { is_verified: true } })),
}))
jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))
const mockToastError = jest.fn()
jest.mock('@/contexts/ToastContext', () => ({
  useToast: () => ({ error: mockToastError, success: jest.fn() }),
}))

const useJE = createTestingHook<{ composite_score: unknown; test_results: unknown[] }>({
  endpoint: '/audit/journal-entries',
  toolName: 'JE tests',
})

beforeEach(() => jest.clearAllMocks())

it('a response without composite_score ends in an error state', async () => {
  mockUploadFetch.mockResolvedValue({ ok: true, status: 200, data: { test_results: [] } })
  const { result } = renderHook(() => useJE())
  await act(async () => {
    await result.current.run(new File(['a'], 'gl.csv'))
  })
  expect(result.current.status).toBe('error')
  expect(result.current.result).toBeNull()
  expect(mockToastError).toHaveBeenCalled()
})

it('a complete response succeeds', async () => {
  mockUploadFetch.mockResolvedValue({ ok: true, status: 200, data: { composite_score: {}, test_results: [] } })
  const { result } = renderHook(() => useJE())
  await act(async () => {
    await result.current.run(new File(['a'], 'gl.csv'))
  })
  expect(result.current.status).toBe('success')
})
