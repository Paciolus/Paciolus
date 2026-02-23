/**
 * Sprint 271: useStatisticalSampling hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useStatisticalSampling } from '@/hooks/useStatisticalSampling'

const mockFetch = jest.fn()
global.fetch = mockFetch

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({ token: 'test-token', user: { is_verified: true } })),
}))

jest.mock('@/contexts/EngagementContext', () => ({
  useOptionalEngagementContext: jest.fn(() => null),
}))

jest.mock('@/utils/apiClient', () => ({
  getCsrfToken: jest.fn(() => 'csrf-token'),
}))

jest.mock('@/utils/constants', () => ({
  API_URL: 'http://localhost:8000',
}))


const mockUseAuth = useAuth as jest.Mock

describe('useStatisticalSampling', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseAuth.mockReturnValue({ token: 'test-token', user: { is_verified: true } })
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ method: 'mus', population_size: 100, actual_sample_size: 10, selected_items: [] }),
    })
  })

  it('initializes with idle status for both phases', () => {
    const { result } = renderHook(() => useStatisticalSampling())
    expect(result.current.designStatus).toBe('idle')
    expect(result.current.designResult).toBeNull()
    expect(result.current.designError).toBe('')
    expect(result.current.evalStatus).toBe('idle')
    expect(result.current.evalResult).toBeNull()
    expect(result.current.evalError).toBe('')
  })

  it('runDesign calls /audit/sampling/design with FormData', async () => {
    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'population.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      stratification_threshold: null,
      sample_size_override: null,
    }

    await act(async () => {
      await result.current.runDesign(file, config)
    })

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/audit/sampling/design',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    )
    expect(result.current.designStatus).toBe('success')
    expect(result.current.designResult).toBeTruthy()
  })

  it('runDesign sets error on API failure', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Invalid parameters' }),
    })

    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'population.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      stratification_threshold: null,
      sample_size_override: null,
    }

    await act(async () => {
      await result.current.runDesign(file, config)
    })

    expect(result.current.designStatus).toBe('error')
    expect(result.current.designError).toBe('Invalid parameters')
  })

  it('runDesign handles 401 unauthorized', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Unauthorized' }),
    })

    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'population.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      stratification_threshold: null,
      sample_size_override: null,
    }

    await act(async () => {
      await result.current.runDesign(file, config)
    })

    expect(result.current.designStatus).toBe('error')
    expect(result.current.designError).toContain('sign in')
  })

  it('runDesign handles network error', async () => {
    mockFetch.mockRejectedValue(new Error('Network failure'))

    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'population.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      stratification_threshold: null,
      sample_size_override: null,
    }

    await act(async () => {
      await result.current.runDesign(file, config)
    })

    expect(result.current.designStatus).toBe('error')
    expect(result.current.designError).toContain('Network error')
  })

  it('runDesign blocks unverified users', async () => {
    mockUseAuth.mockReturnValue({ token: 'test-token', user: { is_verified: false } })

    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'population.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      stratification_threshold: null,
      sample_size_override: null,
    }

    await act(async () => {
      await result.current.runDesign(file, config)
    })

    expect(mockFetch).not.toHaveBeenCalled()
    expect(result.current.designStatus).toBe('error')
    expect(result.current.designError).toContain('verify your email')
  })

  it('runEvaluation calls /audit/sampling/evaluate', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({
        method: 'mus',
        conclusion: 'pass',
        conclusion_detail: 'UEL within tolerance',
        errors: [],
      }),
    })

    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'sample.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      population_value: 1000000,
      sample_size: 50,
      sampling_interval: 20000,
    }

    await act(async () => {
      await result.current.runEvaluation(file, config)
    })

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/audit/sampling/evaluate',
      expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      })
    )
    expect(result.current.evalStatus).toBe('success')
    expect(result.current.evalResult).toBeTruthy()
  })

  it('resetDesign clears design state', async () => {
    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'population.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      stratification_threshold: null,
      sample_size_override: null,
    }

    await act(async () => {
      await result.current.runDesign(file, config)
    })
    expect(result.current.designStatus).toBe('success')

    act(() => {
      result.current.resetDesign()
    })
    expect(result.current.designStatus).toBe('idle')
    expect(result.current.designResult).toBeNull()
  })

  it('resetEvaluation clears evaluation state', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ method: 'mus', conclusion: 'pass', errors: [] }),
    })

    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'sample.csv', { type: 'text/csv' })
    const config = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      population_value: 1000000,
      sample_size: 50,
      sampling_interval: null,
    }

    await act(async () => {
      await result.current.runEvaluation(file, config)
    })
    expect(result.current.evalStatus).toBe('success')

    act(() => {
      result.current.resetEvaluation()
    })
    expect(result.current.evalStatus).toBe('idle')
    expect(result.current.evalResult).toBeNull()
  })

  it('design and evaluation states are independent', async () => {
    const { result } = renderHook(() => useStatisticalSampling())

    const file = new File(['test'], 'population.csv', { type: 'text/csv' })
    const designConfig = {
      method: 'mus' as const,
      confidence_level: 0.95,
      tolerable_misstatement: 50000,
      expected_misstatement: 0,
      stratification_threshold: null,
      sample_size_override: null,
    }

    // Run design
    await act(async () => {
      await result.current.runDesign(file, designConfig)
    })

    expect(result.current.designStatus).toBe('success')
    expect(result.current.evalStatus).toBe('idle') // eval unaffected

    // Reset design doesn't affect eval
    act(() => {
      result.current.resetDesign()
    })
    expect(result.current.designStatus).toBe('idle')
    expect(result.current.evalStatus).toBe('idle')
  })
})
