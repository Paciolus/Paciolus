/**
 * Sprint 236: useEngagement hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useEngagement } from '@/hooks/useEngagement'

const mockApiGet = jest.fn()
const mockApiPost = jest.fn()
const mockApiPut = jest.fn()
const mockApiDelete = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}))

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
  isAuthError: jest.fn(() => false),
}))


const mockUseAuth = useAuth as jest.Mock

const mockEngagement = {
  id: 1, client_id: 1, client_name: 'Acme', period: 'FY2025',
  status: 'active', materiality_threshold: 50000, created_at: '2026-01-01',
}

describe('useEngagement', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
    mockApiGet.mockResolvedValue({
      ok: true,
      data: { engagements: [mockEngagement], total_count: 1, page: 1 },
    })
  })

  it('initializes with empty engagements', () => {
    const { result } = renderHook(() => useEngagement({ autoFetch: false }))
    expect(result.current.engagements).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('fetchEngagements calls API', async () => {
    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    await act(async () => { await result.current.fetchEngagements() })

    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('/engagements'),
      'test-token',
      { skipCache: true }
    )
    expect(result.current.engagements).toEqual([mockEngagement])
  })

  it('createEngagement calls POST', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: { id: 2, ...mockEngagement } })

    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    let created: unknown
    await act(async () => {
      created = await result.current.createEngagement({
        client_id: 1, period: 'FY2025', materiality_threshold: 50000,
      })
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/engagements',
      'test-token',
      expect.objectContaining({ client_id: 1 })
    )
    expect(created).toBeDefined()
  })

  it('updateEngagement calls PUT', async () => {
    mockApiPut.mockResolvedValue({ ok: true, data: { ...mockEngagement, status: 'completed' } })

    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    await act(async () => {
      await result.current.updateEngagement(1, { status: 'completed' })
    })

    expect(mockApiPut).toHaveBeenCalledWith(
      '/engagements/1',
      'test-token',
      expect.objectContaining({ status: 'completed' })
    )
  })

  it('getEngagement fetches single engagement', async () => {
    mockApiGet.mockResolvedValueOnce({ ok: true, data: mockEngagement })

    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    let engagement: unknown
    await act(async () => {
      engagement = await result.current.getEngagement(1)
    })

    expect(engagement).toEqual(mockEngagement)
  })

  it('getToolRuns fetches tool runs for engagement', async () => {
    const mockRuns = [{ id: 1, tool_name: 'TB Diagnostics', run_at: '2026-01-15' }]
    mockApiGet.mockResolvedValueOnce({ ok: true, data: mockRuns })

    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    let runs: unknown
    await act(async () => {
      runs = await result.current.getToolRuns(1)
    })

    expect(runs).toEqual(mockRuns)
  })

  it('getMateriality fetches materiality cascade', async () => {
    const mockMateriality = { overall: 50000, performance: 37500, trivial: 2500 }
    mockApiGet.mockResolvedValueOnce({ ok: true, data: mockMateriality })

    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    let materiality: unknown
    await act(async () => {
      materiality = await result.current.getMateriality(1)
    })

    expect(materiality).toEqual(mockMateriality)
  })

  it('sets error on failed fetch', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Unauthorized', status: 401 })

    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    await act(async () => { await result.current.fetchEngagements() })

    expect(result.current.error).toBeTruthy()
  })

  it('does nothing when not authenticated', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() => useEngagement({ autoFetch: false }))

    await act(async () => { await result.current.fetchEngagements() })

    expect(mockApiGet).not.toHaveBeenCalled()
  })
})
