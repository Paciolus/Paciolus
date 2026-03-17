/**
 * useBranding Hook Tests — Sprint 545b
 */

import { renderHook, act } from '@testing-library/react'
import { useBranding } from '@/hooks/useBranding'

// Mock auth context
const mockToken = 'test-token'
jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({ token: mockToken, isAuthenticated: true }),
}))

// Mock API client
const mockApiGet = jest.fn()
const mockApiPut = jest.fn()
const mockApiPost = jest.fn()
const mockApiDelete = jest.fn()
jest.mock('@/utils/apiClient', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPut: (...args: unknown[]) => mockApiPut(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
}))

const mockBranding = {
  header_text: 'Smith CPA',
  footer_text: 'Confidential',
  logo_url: null,
}

describe('useBranding', () => {
  beforeEach(() => {
    mockApiGet.mockReset()
    mockApiPut.mockReset()
    mockApiPost.mockReset()
    mockApiDelete.mockReset()
  })

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useBranding())
    expect(result.current.branding).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('fetchBranding sets branding data', async () => {
    mockApiGet.mockResolvedValueOnce({ data: mockBranding, ok: true })

    const { result } = renderHook(() => useBranding())

    await act(async () => {
      await result.current.fetchBranding()
    })

    expect(result.current.branding).toEqual(mockBranding)
    expect(mockApiGet).toHaveBeenCalledWith('/branding/', mockToken)
  })

  it('updateBranding sends header and footer', async () => {
    const updated = { ...mockBranding, header_text: 'New Header' }
    mockApiPut.mockResolvedValueOnce({ data: updated, ok: true })

    const { result } = renderHook(() => useBranding())

    await act(async () => {
      const ok = await result.current.updateBranding('New Header', 'Confidential')
      expect(ok).toBe(true)
    })

    expect(result.current.branding).toEqual(updated)
    expect(mockApiPut).toHaveBeenCalledWith('/branding/', mockToken, {
      header_text: 'New Header',
      footer_text: 'Confidential',
    })
  })

  it('uploadLogo sends FormData', async () => {
    const withLogo = { ...mockBranding, logo_url: '/logos/test.png' }
    mockApiPost.mockResolvedValueOnce({ data: withLogo, ok: true })

    const { result } = renderHook(() => useBranding())
    const file = new File(['fake-image'], 'logo.png', { type: 'image/png' })

    await act(async () => {
      const ok = await result.current.uploadLogo(file)
      expect(ok).toBe(true)
    })

    expect(result.current.branding?.logo_url).toBe('/logos/test.png')
    const [endpoint, token, body] = mockApiPost.mock.calls[0]
    expect(endpoint).toBe('/branding/logo')
    expect(token).toBe(mockToken)
    expect(body).toBeInstanceOf(FormData)
  })

  it('deleteLogo clears logo_url', async () => {
    // First set branding with logo
    const withLogo = { ...mockBranding, logo_url: '/logos/test.png' }
    mockApiGet.mockResolvedValueOnce({ data: withLogo, ok: true })

    const { result } = renderHook(() => useBranding())

    await act(async () => {
      await result.current.fetchBranding()
    })
    expect(result.current.branding?.logo_url).toBe('/logos/test.png')

    // Now delete
    mockApiDelete.mockResolvedValueOnce({ ok: true })

    await act(async () => {
      const ok = await result.current.deleteLogo()
      expect(ok).toBe(true)
    })

    expect(result.current.branding?.logo_url).toBeNull()
  })

  it('handles fetch error', async () => {
    mockApiGet.mockResolvedValueOnce({ data: null, ok: false, error: 'Not found' })

    const { result } = renderHook(() => useBranding())

    await act(async () => {
      await result.current.fetchBranding()
    })

    expect(result.current.error).toBe('Not found')
    expect(result.current.branding).toBeNull()
  })
})
