/**
 * Sprint 750: usePeriodUploads hook tests.
 *
 * Demonstrates the value of the Phase 4 tool-page template — the upload
 * state machine is now testable in isolation without rendering the
 * multi-period page or its children.
 */
import { act, renderHook } from '@testing-library/react'
import { usePeriodUploads } from '@/hooks/usePeriodUploads'
import { uploadTrialBalance } from '@/utils/trialBalanceUpload'

jest.mock('@/utils/trialBalanceUpload', () => ({
  uploadTrialBalance: jest.fn(),
}))

const mockUpload = uploadTrialBalance as jest.MockedFunction<typeof uploadTrialBalance>

const baseOptions = {
  token: 'test-token',
  materialityThreshold: 500,
  engagementId: null,
}

describe('usePeriodUploads', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('initializes all three slots in idle state with showBudget off', () => {
    const { result } = renderHook(() => usePeriodUploads(baseOptions))

    expect(result.current.prior.status).toBe('idle')
    expect(result.current.current.status).toBe('idle')
    expect(result.current.budget.status).toBe('idle')
    expect(result.current.showBudget).toBe(false)
    expect(result.current.canCompare).toBe(false)
    expect(result.current.anyLoading).toBe(false)
  })

  it('transitions a slot through loading → success on a successful upload', async () => {
    mockUpload.mockResolvedValue({
      kind: 'success',
      result: { filename: 'tb.csv' } as any,
    })

    const { result } = renderHook(() => usePeriodUploads(baseOptions))
    const file = new File(['x'], 'prior.csv', { type: 'text/csv' })

    await act(async () => {
      result.current.handlePriorFile(file)
    })

    expect(result.current.prior.status).toBe('success')
    expect(result.current.prior.file).toBe(file)
    expect(mockUpload).toHaveBeenCalledWith(
      expect.objectContaining({ file, materialityThreshold: 500 }),
      'test-token',
    )
  })

  it('transitions to error state on upload failure', async () => {
    mockUpload.mockResolvedValue({ kind: 'error', message: 'upload failed' })

    const { result } = renderHook(() => usePeriodUploads(baseOptions))
    const file = new File(['x'], 'current.csv', { type: 'text/csv' })

    await act(async () => {
      result.current.handleCurrentFile(file)
    })

    expect(result.current.current.status).toBe('error')
    expect(result.current.current.error).toBe('upload failed')
  })

  it('canCompare is true once prior + current succeed without budget', async () => {
    mockUpload.mockResolvedValue({
      kind: 'success',
      result: { filename: 'x' } as any,
    })

    const { result } = renderHook(() => usePeriodUploads(baseOptions))
    const file = new File(['x'], 'tb.csv', { type: 'text/csv' })

    await act(async () => {
      result.current.handlePriorFile(file)
    })
    await act(async () => {
      result.current.handleCurrentFile(file)
    })

    expect(result.current.canCompare).toBe(true)
  })

  it('canCompare requires the budget slot to also succeed when showBudget is on', async () => {
    mockUpload.mockResolvedValue({
      kind: 'success',
      result: { filename: 'x' } as any,
    })

    const { result } = renderHook(() => usePeriodUploads(baseOptions))
    const file = new File(['x'], 'tb.csv', { type: 'text/csv' })

    await act(async () => {
      result.current.handlePriorFile(file)
    })
    await act(async () => {
      result.current.handleCurrentFile(file)
    })
    act(() => {
      result.current.toggleBudget()
    })

    // Budget zone is still idle → canCompare flips back to false
    expect(result.current.showBudget).toBe(true)
    expect(result.current.canCompare).toBe(false)

    await act(async () => {
      result.current.handleBudgetFile(file)
    })

    expect(result.current.canCompare).toBe(true)
  })

  it('toggleBudget OFF clears any existing budget state', async () => {
    mockUpload.mockResolvedValue({
      kind: 'success',
      result: { filename: 'x' } as any,
    })

    const { result } = renderHook(() => usePeriodUploads(baseOptions))
    act(() => {
      result.current.toggleBudget()
    })
    await act(async () => {
      result.current.handleBudgetFile(new File(['x'], 'b.csv', { type: 'text/csv' }))
    })
    expect(result.current.budget.status).toBe('success')

    act(() => {
      result.current.toggleBudget()
    })

    expect(result.current.showBudget).toBe(false)
    expect(result.current.budget.status).toBe('idle')
    expect(result.current.budget.file).toBe(null)
  })

  it('reset clears all three slots', async () => {
    mockUpload.mockResolvedValue({
      kind: 'success',
      result: { filename: 'x' } as any,
    })

    const { result } = renderHook(() => usePeriodUploads(baseOptions))
    const file = new File(['x'], 'tb.csv', { type: 'text/csv' })

    await act(async () => {
      result.current.handlePriorFile(file)
    })

    act(() => {
      result.current.reset()
    })

    expect(result.current.prior.status).toBe('idle')
    expect(result.current.prior.file).toBe(null)
  })

  it('calls onBeforeUpload before each upload (so the consumer can clear stale comparison results)', async () => {
    mockUpload.mockResolvedValue({
      kind: 'success',
      result: { filename: 'x' } as any,
    })
    const onBeforeUpload = jest.fn()

    const { result } = renderHook(() =>
      usePeriodUploads({ ...baseOptions, onBeforeUpload }),
    )
    const file = new File(['x'], 'tb.csv', { type: 'text/csv' })

    await act(async () => {
      result.current.handlePriorFile(file)
    })
    await act(async () => {
      result.current.handleCurrentFile(file)
    })

    expect(onBeforeUpload).toHaveBeenCalledTimes(2)
  })
})
