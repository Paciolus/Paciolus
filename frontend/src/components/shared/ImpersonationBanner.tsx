'use client'

/**
 * Impersonation Banner — Sprint 590
 *
 * Persistent top banner shown when viewing as a customer.
 * Cannot be dismissed. Shows target email, time remaining, and end session button.
 */

import { useEffect, useState } from 'react'

export function ImpersonationBanner() {
  const [isImpersonating, setIsImpersonating] = useState(false)
  const [email, setEmail] = useState('')
  const [timeRemaining, setTimeRemaining] = useState('')

  useEffect(() => {
    if (typeof window === 'undefined') return undefined

    const token = sessionStorage.getItem('impersonation_token')
    const storedEmail = sessionStorage.getItem('impersonation_email')
    const expires = sessionStorage.getItem('impersonation_expires')

    if (!token || !storedEmail || !expires) return undefined

    setIsImpersonating(true)
    setEmail(storedEmail)

    const interval = setInterval(() => {
      const remaining = new Date(expires).getTime() - Date.now()
      if (remaining <= 0) {
        endSession()
        return
      }
      const minutes = Math.floor(remaining / 60000)
      const seconds = Math.floor((remaining % 60000) / 1000)
      setTimeRemaining(`${minutes}:${seconds.toString().padStart(2, '0')}`)
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  function endSession() {
    if (typeof window === 'undefined') return
    sessionStorage.removeItem('impersonation_token')
    sessionStorage.removeItem('impersonation_email')
    sessionStorage.removeItem('impersonation_expires')
    setIsImpersonating(false)
    window.location.href = '/internal/admin'
  }

  if (!isImpersonating) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-clay-600 text-white py-2 px-4 flex items-center justify-center gap-4 text-sm font-sans shadow-lg">
      <span>
        You are viewing as <strong>{email}</strong> — Read-only mode — {timeRemaining} remaining
      </span>
      <button
        onClick={endSession}
        className="px-3 py-1 bg-white text-clay-700 rounded font-medium hover:bg-clay-50 transition-colors"
      >
        End Session
      </button>
    </div>
  )
}
