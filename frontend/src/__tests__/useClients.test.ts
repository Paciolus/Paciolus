/**
 * Sprint 236: useClients hook tests
 */
import { renderHook, act } from '@testing-library/react'

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

import { useClients } from '@/hooks/useClients'
import { useAuth } from '@/contexts/AuthContext'

const mockUseAuth = useAuth as jest.Mock

const mockClient = { id: 1, name: 'Acme Corp', industry: 'technology', fiscal_year_end: '12-31' }

describe('useClients', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', isAuthenticated: true })
    mockApiGet.mockResolvedValue({
      ok: true,
      data: { clients: [mockClient], total_count: 1, page: 1 },
    })
  })

  it('initializes with empty clients and loading state', () => {
    const { result } = renderHook(() => useClients({ autoFetch: false }))
    expect(result.current.clients).toEqual([])
    expect(result.current.error).toBeNull()
  })

  it('fetchClients calls API and populates clients', async () => {
    const { result } = renderHook(() => useClients({ autoFetch: false }))

    await act(async () => { await result.current.fetchClients() })

    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining('/clients'),
      'test-token'
    )
    expect(result.current.clients).toEqual([mockClient])
    expect(result.current.totalCount).toBe(1)
  })

  it('createClient calls POST and refreshes list', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: { id: 2, name: 'New Client' } })

    const { result } = renderHook(() => useClients({ autoFetch: false }))

    await act(async () => {
      await result.current.createClient({ name: 'New Client', industry: 'healthcare', fiscal_year_end: '06-30' })
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/clients',
      'test-token',
      expect.objectContaining({ name: 'New Client' })
    )
  })

  it('updateClient calls PUT', async () => {
    mockApiPut.mockResolvedValue({ ok: true, data: { ...mockClient, name: 'Updated' } })

    const { result } = renderHook(() => useClients({ autoFetch: false }))

    await act(async () => {
      await result.current.updateClient(1, { name: 'Updated' })
    })

    expect(mockApiPut).toHaveBeenCalledWith(
      '/clients/1',
      'test-token',
      expect.objectContaining({ name: 'Updated' })
    )
  })

  it('deleteClient calls DELETE', async () => {
    mockApiDelete.mockResolvedValue({ ok: true })

    const { result } = renderHook(() => useClients({ autoFetch: false }))

    await act(async () => {
      await result.current.deleteClient(1)
    })

    expect(mockApiDelete).toHaveBeenCalledWith('/clients/1', 'test-token')
  })

  it('getClient fetches single client', async () => {
    mockApiGet.mockResolvedValueOnce({ ok: true, data: mockClient })

    const { result } = renderHook(() => useClients({ autoFetch: false }))

    let client: unknown
    await act(async () => {
      client = await result.current.getClient(1)
    })

    expect(client).toEqual(mockClient)
    expect(mockApiGet).toHaveBeenCalledWith(
      '/clients/1',
      'test-token'
    )
  })

  it('sets error on failed fetch', async () => {
    mockApiGet.mockResolvedValue({ ok: false, error: 'Server error', status: 500 })

    const { result } = renderHook(() => useClients({ autoFetch: false }))

    await act(async () => { await result.current.fetchClients() })

    expect(result.current.error).toBe('Server error')
  })

  it('provides industries list when autoFetch is enabled', async () => {
    mockApiGet
      .mockResolvedValueOnce({
        ok: true,
        data: { clients: [], total_count: 0, page: 1 },
      })
      .mockResolvedValueOnce({
        ok: true,
        data: [{ value: 'technology', label: 'Technology' }],
      })

    const { result } = renderHook(() => useClients({ autoFetch: true }))

    // Wait for both fetchClients and fetchIndustries to complete
    await act(async () => {})

    expect(result.current.industries.length).toBeGreaterThan(0)
  })

  it('does nothing when not authenticated', async () => {
    mockUseAuth.mockReturnValue({ token: null, isAuthenticated: false })

    const { result } = renderHook(() => useClients({ autoFetch: false }))

    await act(async () => { await result.current.fetchClients() })

    expect(mockApiGet).not.toHaveBeenCalled()
  })
})
