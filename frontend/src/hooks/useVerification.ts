'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useAuth } from '@/context/AuthContext'

/**
 * useVerification — Sprint 58
 *
 * Reusable hook for resend verification + countdown timer logic.
 * Used by VerificationBanner and verification-pending page.
 */

export interface UseVerificationReturn {
  cooldownSeconds: number
  canResend: boolean
  isResending: boolean
  resendError: string | null
  resendSuccess: boolean
  resend: () => Promise<void>
}

export function useVerification(): UseVerificationReturn {
  const { resendVerification, checkVerificationStatus } = useAuth()
  const [cooldownSeconds, setCooldownSeconds] = useState(0)
  const [isResending, setIsResending] = useState(false)
  const [resendError, setResendError] = useState<string | null>(null)
  const [resendSuccess, setResendSuccess] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Countdown timer
  useEffect(() => {
    if (cooldownSeconds <= 0) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    intervalRef.current = setInterval(() => {
      setCooldownSeconds(prev => {
        if (prev <= 1) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [cooldownSeconds])

  // Initialize cooldown from server on mount
  useEffect(() => {
    let cancelled = false
    const fetchStatus = async () => {
      const status = await checkVerificationStatus()
      if (!cancelled && status && status.resend_cooldown_seconds > 0) {
        setCooldownSeconds(status.resend_cooldown_seconds)
      }
    }
    fetchStatus()
    return () => { cancelled = true }
  }, [checkVerificationStatus])

  const resend = useCallback(async () => {
    setIsResending(true)
    setResendError(null)
    setResendSuccess(false)

    const result = await resendVerification()

    if (result.success) {
      setResendSuccess(true)
      // Default 2-minute cooldown
      setCooldownSeconds(120)
    } else {
      setResendError(result.error || 'Failed to resend')
      // On rate limit, fetch accurate cooldown from server
      const status = await checkVerificationStatus()
      if (status && status.resend_cooldown_seconds > 0) {
        setCooldownSeconds(status.resend_cooldown_seconds)
      }
    }

    setIsResending(false)
  }, [resendVerification, checkVerificationStatus])

  return {
    cooldownSeconds,
    canResend: cooldownSeconds <= 0,
    isResending,
    resendError,
    resendSuccess,
    resend,
  }
}
