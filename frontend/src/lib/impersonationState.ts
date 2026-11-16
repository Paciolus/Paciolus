/**
 * Impersonation state — in memory only (Sprint 872, AZ-13).
 *
 * The impersonation access token and the customer's email are never written
 * to browser storage (session or local), where any script on the origin could read
 * them. They live in this module for the life of the page: ending the
 * session or logging out clears them, and a reload loses them (the admin
 * starts impersonation again). Revocation stays server-side
 * (`/internal/admin/impersonate/stop`).
 */

import { useSyncExternalStore } from 'react'
import { onSessionEnd } from '@/utils/sessionScope'

export interface ImpersonationState {
  token: string
  email: string
  expiresAt: string
}

let current: ImpersonationState | null = null
const listeners = new Set<() => void>()

function notify(): void {
  listeners.forEach(listener => listener())
}

export function startImpersonation(state: ImpersonationState): void {
  current = { ...state }
  notify()
}

export function clearImpersonation(): void {
  if (current === null) return
  current = null
  notify()
}

export function getImpersonation(): ImpersonationState | null {
  return current
}

export function subscribeImpersonation(listener: () => void): () => void {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

/** Current impersonation state; re-renders when it starts or ends. */
export function useImpersonation(): ImpersonationState | null {
  return useSyncExternalStore(subscribeImpersonation, getImpersonation, () => null)
}

// Logging out (or any end of the admin's signed-in session) drops it.
onSessionEnd(clearImpersonation)
