/**
 * Sprint 276: useCurrencyRates hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useCurrencyRates } from '@/hooks/useCurrencyRates'

const mockApiFetch = jest.fn()
const mockApiPost = jest.fn()
const mockApiDelete = jest.fn()
const mockGetCsrfToken = jest.fn(() => 'csrf-token')

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token' })),
}))

jest.mock('@/utils/apiClient', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
  getCsrfToken: (...args: unknown[]) => mockGetCsrfToken(...args),
}))


const mockUseAuth = useAuth as jest.Mock

const mockRateStatus = {
  has_rates: true,
  rate_count: 3,
  presentation_currency: 'USD',
  currency_pairs: ['EUR/USD', 'GBP/USD', 'JPY/USD'],
}

const mockUploadResult = {
  rate_count: 3,
  presentation_currency: 'USD',
  currency_pairs: ['EUR/USD', 'GBP/USD', 'JPY/USD'],
  uploaded_at: '2026-02-17T00:00:00Z',
}

const mockSingleRateResult = {
  from_currency: 'EUR',
  to_currency: 'USD',
  rate: '1.0850',
  presentation_currency: 'USD',
  total_rates: 4,
}

describe('useCurrencyRates', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token' })
  })

  it('initializes with null status and idle upload', () => {
    const { result } = renderHook(() => useCurrencyRates())
    expect(result.current.rateStatus).toBeNull()
    expect(result.current.uploadStatus).toBe('idle')
    expect(result.current.error).toBe('')
  })

  it('refreshStatus calls apiFetch and sets rateStatus', async () => {
    mockApiFetch.mockResolvedValue({ ok: true, data: mockRateStatus })

    const { result } = renderHook(() => useCurrencyRates())

    await act(async () => {
      await result.current.refreshStatus()
    })

    expect(mockApiFetch).toHaveBeenCalledWith('/audit/currency-rates', 'test-token')
    expect(result.current.rateStatus).toEqual(mockRateStatus)
  })

  it('uploadRateTable creates FormData and calls apiPost', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockUploadResult })

    const { result } = renderHook(() => useCurrencyRates())
    const file = new File(['from,to,rate\nEUR,USD,1.085'], 'rates.csv', { type: 'text/csv' })

    await act(async () => {
      await result.current.uploadRateTable(file, 'USD')
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/currency-rates',
      'test-token',
      expect.any(FormData)
    )
    // Verify FormData contents
    const formData = (mockApiPost as jest.Mock).mock.calls[0][2] as FormData
    expect(formData.get('file')).toEqual(file)
    expect(formData.get('presentation_currency')).toBe('USD')
  })

  it('uploadRateTable sets success status on success', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockUploadResult })

    const { result } = renderHook(() => useCurrencyRates())
    const file = new File(['data'], 'rates.csv')

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.uploadRateTable(file, 'USD')
    })

    expect(success).toBe(true)
    expect(result.current.uploadStatus).toBe('success')
    expect(result.current.rateStatus).toEqual({
      has_rates: true,
      rate_count: 3,
      presentation_currency: 'USD',
      currency_pairs: ['EUR/USD', 'GBP/USD', 'JPY/USD'],
    })
  })

  it('uploadRateTable sets error on failure', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'Invalid CSV format' })

    const { result } = renderHook(() => useCurrencyRates())
    const file = new File(['bad data'], 'rates.csv')

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.uploadRateTable(file, 'USD')
    })

    expect(success).toBe(false)
    expect(result.current.uploadStatus).toBe('error')
    expect(result.current.error).toBe('Invalid CSV format')
  })

  it('addSingleRate calls apiPost with uppercased currencies', async () => {
    mockApiPost.mockResolvedValue({ ok: true, data: mockSingleRateResult })

    const { result } = renderHook(() => useCurrencyRates())

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.addSingleRate('eur', 'usd', '1.0850', 'usd')
    })

    expect(mockApiPost).toHaveBeenCalledWith(
      '/audit/currency-rate',
      'test-token',
      expect.objectContaining({
        from_currency: 'EUR',
        to_currency: 'USD',
        rate: '1.0850',
        presentation_currency: 'USD',
      })
    )
    expect(success).toBe(true)
    expect(result.current.rateStatus).toEqual({
      has_rates: true,
      rate_count: 4,
      presentation_currency: 'USD',
      currency_pairs: [],
    })
  })

  it('addSingleRate handles error', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: 'Duplicate rate' })

    const { result } = renderHook(() => useCurrencyRates())

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.addSingleRate('EUR', 'USD', '1.085')
    })

    expect(success).toBe(false)
    expect(result.current.error).toBe('Duplicate rate')
  })

  it('clearRates calls apiDelete and resets state', async () => {
    mockApiDelete.mockResolvedValue({ ok: true })
    mockApiFetch.mockResolvedValue({ ok: true, data: mockRateStatus })

    const { result } = renderHook(() => useCurrencyRates())

    // First populate status
    await act(async () => {
      await result.current.refreshStatus()
    })
    expect(result.current.rateStatus).not.toBeNull()

    let success: boolean | undefined
    await act(async () => {
      success = await result.current.clearRates()
    })

    expect(mockApiDelete).toHaveBeenCalledWith('/audit/currency-rates', 'test-token')
    expect(success).toBe(true)
    expect(result.current.rateStatus).toBeNull()
    expect(result.current.uploadStatus).toBe('idle')
    expect(result.current.error).toBe('')
  })

  it('error message is set correctly on upload default fallback', async () => {
    mockApiPost.mockResolvedValue({ ok: false, error: '' })

    const { result } = renderHook(() => useCurrencyRates())
    const file = new File(['data'], 'rates.csv')

    await act(async () => {
      await result.current.uploadRateTable(file, 'USD')
    })

    expect(result.current.error).toBe('Failed to upload rate table')
  })
})
