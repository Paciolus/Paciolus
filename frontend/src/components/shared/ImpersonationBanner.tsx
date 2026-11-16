'use client'

/**
 * Impersonation Banner — Sprint 590
 *
 * Persistent top banner shown when viewing as a customer.
 * Cannot be dismissed. Shows target email, time remaining, and end session button.
 *
 * Sprint 840: "End Session" revokes the token server-side before discarding
 * it, so the token does not stay valid for its full 15 minutes.
 *
 * Sprint 872 (AZ-13): the token and the customer's email are held in memory
 * only (`lib/impersonationState`); logout clears them and a reload loses them.
 */

import { useEffect, useRef, useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { apiPost } from '@/utils/apiClient'
import { clearImpersonation, getImpersonation, useImpersonation } from '@/lib/impersonationState'

export function ImpersonationBanner() {
  const { token: adminToken } = useAuthSession()
  // A ref, so the 1-second timer effect below never has to restart for a token refresh.
  const adminTokenRef = useRef(adminToken)
  adminTokenRef.current = adminToken
  // Sprint 872 (AZ-13): held in memory only — never in browser storage.
  const impersonation = useImpersonation()
  const [timeRemaining, setTimeRemaining] = useState('')
  const [endError, setEndError] = useState<string | null>(null)

  const expiresAt = impersonation?.expiresAt
  useEffect(() => {
    if (!expiresAt) return undefined
    setEndError(null)

    const tick = () => {
      const remaining = new Date(expiresAt).getTime() - Date.now()
      if (remaining <= 0) {
        clearInterval(interval)
        void endSession()
        return
      }
      const minutes = Math.floor(remaining / 60000)
      const seconds = Math.floor((remaining % 60000) / 1000)
      setTimeRemaining(`${minutes}:${seconds.toString().padStart(2, '0')}`)
    }
    const interval = setInterval(tick, 1000)
    tick()

    return () => clearInterval(interval)
  }, [expiresAt])

  async function endSession() {
    if (typeof window === 'undefined') return
    const impersonationToken = getImpersonation()?.token
    if (impersonationToken) {
      // PR #232 review: wait for the server to revoke before discarding the
      // token or navigating — a fire-and-forget POST can be cancelled by the
      // page unload, leaving the token live for the rest of its 15 minutes.
      const { ok } = await apiPost('/internal/admin/impersonate/stop', adminTokenRef.current, { token: impersonationToken })
      if (!ok) {
        setEndError('Could not end the session on the server. Try again.')
        return
      }
    }
    clearImpersonation()
    window.location.href = '/internal/admin'
  }

  if (!impersonation) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] bg-clay-600 text-oatmeal-50 py-2 px-4 flex items-center justify-center gap-4 text-sm font-sans shadow-lg">
      <span>
        You are viewing as <strong>{impersonation.email}</strong> — Read-only mode — {timeRemaining} remaining
        {endError && <span role="alert"> — {endError}</span>}
      </span>
      <button
        onClick={() => { void endSession() }}
        className="px-3 py-1 bg-oatmeal-50 text-clay-700 rounded font-medium hover:bg-clay-50 transition-colors"
      >
        End Session
      </button>
    </div>
  )
}
