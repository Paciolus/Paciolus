/**
 * Sprint 237: EngagementContext tests
 */
import React from 'react'
import { renderHook, act } from '@testing-library/react'

const mockGetEngagement = jest.fn()
const mockGetToolRuns = jest.fn()
const mockGetMateriality = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('next/navigation', () => ({
  useSearchParams: jest.fn(() => ({
    get: jest.fn(() => null),
    toString: jest.fn(() => ''),
  })),
  useRouter: jest.fn(() => ({
    replace: jest.fn(),
  })),
  usePathname: jest.fn(() => '/tools'),
}))

jest.mock('@/hooks/useEngagement', () => ({
  useEngagement: jest.fn(() => ({
    getEngagement: mockGetEngagement,
    getToolRuns: mockGetToolRuns,
    getMateriality: mockGetMateriality,
  })),
}))

import {
  EngagementProvider,
  useEngagementContext,
  useOptionalEngagementContext,
} from '@/contexts/EngagementContext'

describe('EngagementContext', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockGetEngagement.mockResolvedValue(null)
    mockGetToolRuns.mockResolvedValue([])
    mockGetMateriality.mockResolvedValue(null)
  })

  it('throws when useEngagementContext is used outside provider', () => {
    // Suppress console.error for expected throw
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      renderHook(() => useEngagementContext())
    }).toThrow('useEngagementContext must be used within an EngagementProvider')

    spy.mockRestore()
  })

  it('provides context values inside provider', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <EngagementProvider>{children}</EngagementProvider>
    )

    const { result } = renderHook(() => useEngagementContext(), { wrapper })

    expect(result.current.activeEngagement).toBeNull()
    expect(result.current.toolRuns).toEqual([])
    expect(result.current.materiality).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.toastMessage).toBeNull()
    expect(typeof result.current.selectEngagement).toBe('function')
    expect(typeof result.current.clearEngagement).toBe('function')
    expect(typeof result.current.refreshToolRuns).toBe('function')
    expect(typeof result.current.triggerLinkToast).toBe('function')
    expect(typeof result.current.dismissToast).toBe('function')
  })

  it('selectEngagement loads engagement data', async () => {
    const mockEngagement = { id: 1, client_name: 'Acme', status: 'active' }
    const mockRuns = [{ id: 1, tool_name: 'TB Diagnostics' }]
    const mockMat = { overall: 50000, performance: 37500, trivial: 2500 }

    mockGetEngagement.mockResolvedValue(mockEngagement)
    mockGetToolRuns.mockResolvedValue(mockRuns)
    mockGetMateriality.mockResolvedValue(mockMat)

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <EngagementProvider>{children}</EngagementProvider>
    )

    const { result } = renderHook(() => useEngagementContext(), { wrapper })

    await act(async () => {
      await result.current.selectEngagement(1)
    })

    expect(result.current.activeEngagement).toEqual(mockEngagement)
    expect(result.current.toolRuns).toEqual(mockRuns)
    expect(result.current.materiality).toEqual(mockMat)
  })

  it('clearEngagement resets state', async () => {
    const mockEngagement = { id: 1, client_name: 'Acme', status: 'active' }
    mockGetEngagement.mockResolvedValue(mockEngagement)
    mockGetToolRuns.mockResolvedValue([])
    mockGetMateriality.mockResolvedValue(null)

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <EngagementProvider>{children}</EngagementProvider>
    )

    const { result } = renderHook(() => useEngagementContext(), { wrapper })

    await act(async () => { await result.current.selectEngagement(1) })
    expect(result.current.activeEngagement).toBeDefined()

    act(() => { result.current.clearEngagement() })

    expect(result.current.activeEngagement).toBeNull()
    expect(result.current.toolRuns).toEqual([])
    expect(result.current.materiality).toBeNull()
  })

  it('useOptionalEngagementContext returns null outside provider', () => {
    const { result } = renderHook(() => useOptionalEngagementContext())
    expect(result.current).toBeNull()
  })

  it('useOptionalEngagementContext returns context with engagementId inside provider', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <EngagementProvider>{children}</EngagementProvider>
    )

    const { result } = renderHook(() => useOptionalEngagementContext(), { wrapper })

    expect(result.current).not.toBeNull()
    expect(result.current!.engagementId).toBeNull() // No active engagement
    expect(typeof result.current!.selectEngagement).toBe('function')
  })

  it('dismissToast clears toast message', async () => {
    const mockEngagement = { id: 1, client_name: 'Acme', status: 'active' }
    mockGetEngagement.mockResolvedValue(mockEngagement)
    mockGetToolRuns.mockResolvedValue([])
    mockGetMateriality.mockResolvedValue(null)

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <EngagementProvider>{children}</EngagementProvider>
    )

    const { result } = renderHook(() => useEngagementContext(), { wrapper })

    // Select engagement first (triggerLinkToast requires activeEngagement)
    await act(async () => { await result.current.selectEngagement(1) })

    act(() => { result.current.triggerLinkToast('TB Diagnostics') })
    expect(result.current.toastMessage).toBe('TB Diagnostics results linked to workspace')

    act(() => { result.current.dismissToast() })
    expect(result.current.toastMessage).toBeNull()
  })
})
