/**
 * Sprint 235: createTestingHook factory tests
 */
import { renderHook } from '@testing-library/react'

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', user: { is_verified: true } })),
}))
jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))
jest.mock('@/utils/apiClient', () => ({
  getCsrfToken: jest.fn(() => null),
}))

import { createTestingHook } from '@/hooks/createTestingHook'

describe('createTestingHook', () => {
  it('creates a hook function', () => {
    const useTestHook = createTestingHook({
      endpoint: '/audit/test',
      toolName: 'Test Tool',
    })
    expect(typeof useTestHook).toBe('function')
  })

  it('created hook returns audit upload interface', () => {
    const useTestHook = createTestingHook<{ score: number }>({
      endpoint: '/audit/test',
      toolName: 'Test Tool',
    })

    const { result } = renderHook(() => useTestHook())

    expect(result.current).toHaveProperty('status', 'idle')
    expect(result.current).toHaveProperty('result', null)
    expect(result.current).toHaveProperty('error', '')
    expect(typeof result.current.run).toBe('function')
    expect(typeof result.current.reset).toBe('function')
  })

  it('created hook starts in idle state', () => {
    const useTestHook = createTestingHook<{ data: string }>({
      endpoint: '/audit/custom',
      toolName: 'Custom Tool',
    })

    const { result } = renderHook(() => useTestHook())

    expect(result.current.status).toBe('idle')
    expect(result.current.result).toBeNull()
    expect(result.current.error).toBe('')
  })

  it('accepts custom buildFormData', () => {
    const customBuild = jest.fn((...files: File[]) => {
      const fd = new FormData()
      files.forEach((f, i) => fd.append(`file_${i}`, f))
      return fd
    })

    const useTestHook = createTestingHook({
      endpoint: '/audit/multi',
      toolName: 'Multi File Tool',
      buildFormData: customBuild,
    })

    expect(typeof useTestHook).toBe('function')

    const { result } = renderHook(() => useTestHook())
    expect(result.current.status).toBe('idle')
  })
})
