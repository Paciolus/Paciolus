/**
 * Sprint 276: useVerification hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { useAuth } from '@/contexts/AuthContext'
import { useVerification } from '@/hooks/useVerification'

const mockResendVerification = jest.fn()
const mockCheckVerificationStatus = jest.fn()

jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(() => ({
    resendVerification: mockResendVerification,
    checkVerificationStatus: mockCheckVerificationStatus,
  })),
}))


const mockUseAuth = useAuth as jest.Mock

describe('useVerification', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    jest.useRealTimers()
    mockUseAuth.mockReturnValue({
      resendVerification: mockResendVerification,
      checkVerificationStatus: mockCheckVerificationStatus,
    })
    mockResendVerification.mockResolvedValue({ success: true })
    mockCheckVerificationStatus.mockResolvedValue({ resend_cooldown_seconds: 0 })
  })

  it('initializes with 0 cooldown and canResend=true', async () => {
    const { result } = renderHook(() => useVerification())

    // Wait for mount effect (checkVerificationStatus)
    await act(async () => {})

    expect(result.current.cooldownSeconds).toBe(0)
    expect(result.current.canResend).toBe(true)
    expect(result.current.isResending).toBe(false)
    expect(result.current.resendError).toBeNull()
    expect(result.current.resendSuccess).toBe(false)
  })

  it('resend calls resendVerification', async () => {
    const { result } = renderHook(() => useVerification())

    await act(async () => {})

    await act(async () => {
      await result.current.resend()
    })

    expect(mockResendVerification).toHaveBeenCalled()
  })

  it('successful resend sets cooldown to 120 and resendSuccess=true', async () => {
    mockResendVerification.mockResolvedValue({ success: true })

    const { result } = renderHook(() => useVerification())

    await act(async () => {})

    await act(async () => {
      await result.current.resend()
    })

    expect(result.current.resendSuccess).toBe(true)
    expect(result.current.cooldownSeconds).toBe(120)
    expect(result.current.canResend).toBe(false)
    expect(result.current.isResending).toBe(false)
  })

  it('failed resend sets resendError', async () => {
    mockResendVerification.mockResolvedValue({ success: false, error: 'Rate limited' })
    mockCheckVerificationStatus.mockResolvedValue({ resend_cooldown_seconds: 45 })

    const { result } = renderHook(() => useVerification())

    await act(async () => {})

    await act(async () => {
      await result.current.resend()
    })

    expect(result.current.resendError).toBe('Rate limited')
    expect(result.current.resendSuccess).toBe(false)
    expect(result.current.isResending).toBe(false)
  })

  it('canResend is false when cooldown > 0', async () => {
    mockResendVerification.mockResolvedValue({ success: true })

    const { result } = renderHook(() => useVerification())

    await act(async () => {})

    await act(async () => {
      await result.current.resend()
    })

    // cooldown was set to 120
    expect(result.current.cooldownSeconds).toBe(120)
    expect(result.current.canResend).toBe(false)
  })

  it('countdown decrements over time', async () => {
    jest.useFakeTimers()
    mockCheckVerificationStatus.mockResolvedValue({ resend_cooldown_seconds: 3 })

    const { result } = renderHook(() => useVerification())

    // Wait for mount effect to initialize cooldown from server
    await act(async () => {
      await Promise.resolve()
    })

    expect(result.current.cooldownSeconds).toBe(3)
    expect(result.current.canResend).toBe(false)

    // Advance 1 second
    await act(async () => {
      jest.advanceTimersByTime(1000)
    })
    expect(result.current.cooldownSeconds).toBe(2)

    // Advance another second
    await act(async () => {
      jest.advanceTimersByTime(1000)
    })
    expect(result.current.cooldownSeconds).toBe(1)

    // Advance to zero
    await act(async () => {
      jest.advanceTimersByTime(1000)
    })
    expect(result.current.cooldownSeconds).toBe(0)
    expect(result.current.canResend).toBe(true)

    jest.useRealTimers()
  })

  it('initializes cooldown from server on mount', async () => {
    mockCheckVerificationStatus.mockResolvedValue({ resend_cooldown_seconds: 60 })

    const { result } = renderHook(() => useVerification())

    await act(async () => {})

    expect(mockCheckVerificationStatus).toHaveBeenCalled()
    expect(result.current.cooldownSeconds).toBe(60)
    expect(result.current.canResend).toBe(false)
  })

  it('failed resend fetches accurate cooldown from server', async () => {
    mockResendVerification.mockResolvedValue({ success: false, error: 'Too many requests' })
    mockCheckVerificationStatus.mockResolvedValue({ resend_cooldown_seconds: 90 })

    const { result } = renderHook(() => useVerification())

    // Wait for initial mount
    await act(async () => {})

    await act(async () => {
      await result.current.resend()
    })

    // After failure, it should have called checkVerificationStatus again
    // Once on mount + once on failure = 2 total calls
    expect(mockCheckVerificationStatus).toHaveBeenCalledTimes(2)
    expect(result.current.cooldownSeconds).toBe(90)
    expect(result.current.resendError).toBe('Too many requests')
  })
})
