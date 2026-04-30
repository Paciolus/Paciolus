/**
 * Sprint 751: useUserPreferences hook tests.
 *
 * Pins the optimistic-update-with-revert contract for `toggleFavorite`:
 * the favorite list flips immediately and reverts on PUT failure.
 */
import { act, renderHook, waitFor } from '@testing-library/react'
import { useUserPreferences } from '@/hooks/useUserPreferences'
import { DEFAULT_FAVORITES } from '@/content/dashboard-tools'

const mockApiGet = jest.fn()
const mockApiPut = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
}))

describe('useUserPreferences', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('starts with DEFAULT_FAVORITES until the GET resolves', () => {
    mockApiGet.mockResolvedValue({ ok: true, status: 200, data: { favorite_tools: ['x'] } })
    const { result } = renderHook(() => useUserPreferences('tok'))
    expect(result.current.favorites).toEqual(DEFAULT_FAVORITES)
  })

  it('hydrates favorites from /settings/preferences when non-empty', async () => {
    mockApiGet.mockResolvedValue({
      ok: true,
      status: 200,
      data: { favorite_tools: ['trial_balance', 'ar_aging'] },
    })
    const { result } = renderHook(() => useUserPreferences('tok'))
    await waitFor(() => expect(result.current.favorites).toEqual(['trial_balance', 'ar_aging']))
  })

  it('keeps DEFAULT_FAVORITES when the server returns an empty list', async () => {
    mockApiGet.mockResolvedValue({ ok: true, status: 200, data: { favorite_tools: [] } })
    const { result } = renderHook(() => useUserPreferences('tok'))
    // Wait a tick — fetch resolves but should not overwrite defaults.
    await waitFor(() => expect(mockApiGet).toHaveBeenCalled())
    expect(result.current.favorites).toEqual(DEFAULT_FAVORITES)
  })

  it('does not fetch when token is null', () => {
    renderHook(() => useUserPreferences(null))
    expect(mockApiGet).not.toHaveBeenCalled()
  })

  it('toggleFavorite adds a key and PUTs the new list', async () => {
    mockApiGet.mockResolvedValue({
      ok: true,
      status: 200,
      data: { favorite_tools: ['a'] },
    })
    mockApiPut.mockResolvedValue({ ok: true })
    const { result } = renderHook(() => useUserPreferences('tok'))
    await waitFor(() => expect(result.current.favorites).toEqual(['a']))

    await act(async () => {
      await result.current.toggleFavorite('b')
    })

    expect(result.current.favorites).toEqual(['a', 'b'])
    expect(mockApiPut).toHaveBeenCalledWith(
      '/settings/preferences',
      'tok',
      { favorite_tools: ['a', 'b'] },
    )
  })

  it('toggleFavorite removes an existing key', async () => {
    mockApiGet.mockResolvedValue({
      ok: true,
      status: 200,
      data: { favorite_tools: ['a', 'b'] },
    })
    mockApiPut.mockResolvedValue({ ok: true })
    const { result } = renderHook(() => useUserPreferences('tok'))
    await waitFor(() => expect(result.current.favorites).toEqual(['a', 'b']))

    await act(async () => {
      await result.current.toggleFavorite('a')
    })

    expect(result.current.favorites).toEqual(['b'])
  })

  it('reverts the optimistic toggle when the PUT fails', async () => {
    mockApiGet.mockResolvedValue({
      ok: true,
      status: 200,
      data: { favorite_tools: ['a'] },
    })
    mockApiPut.mockRejectedValue(new Error('persist failed'))
    const { result } = renderHook(() => useUserPreferences('tok'))
    await waitFor(() => expect(result.current.favorites).toEqual(['a']))

    await act(async () => {
      await result.current.toggleFavorite('b')
    })

    // After the rejected PUT, favorites should be back to ['a'].
    expect(result.current.favorites).toEqual(['a'])
  })

  it('toggleFavorite no-ops when token is null', async () => {
    const { result } = renderHook(() => useUserPreferences(null))
    await act(async () => {
      await result.current.toggleFavorite('x')
    })
    expect(mockApiPut).not.toHaveBeenCalled()
  })
})
