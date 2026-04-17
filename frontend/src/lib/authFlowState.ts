/**
 * Transient in-memory state for auth flow handoffs.
 *
 * Used to pass data between auth pages during client-side navigation
 * without exposing it in URLs, browser history, or storage.
 * Values are cleared after first read to prevent stale data.
 */

let pendingRegistrationEmail: string | null = null

export function setPendingEmail(email: string): void {
  pendingRegistrationEmail = email
}

export function consumePendingEmail(): string | null {
  const email = pendingRegistrationEmail
  pendingRegistrationEmail = null
  return email
}

// Sprint 603: plan/interval handoff from pricing CTA through register → verify-email → checkout.
// sessionStorage is used (not in-memory) so the selection survives the fresh page load when
// the user clicks the verification email link in the same tab.
const PLAN_SELECTION_KEY = 'paciolus.pendingPlanSelection'

export interface PendingPlanSelection {
  plan: string
  interval: string
}

const ALLOWED_PLANS = new Set(['solo', 'professional', 'enterprise'])
const ALLOWED_INTERVALS = new Set(['monthly', 'annual'])

export function setPendingPlanSelection(plan: string, interval: string): void {
  if (typeof window === 'undefined') return
  if (!ALLOWED_PLANS.has(plan) || !ALLOWED_INTERVALS.has(interval)) return
  try {
    window.sessionStorage.setItem(PLAN_SELECTION_KEY, JSON.stringify({ plan, interval }))
  } catch {
    // sessionStorage unavailable (e.g. privacy mode) — silent fallback
  }
}

export function consumePendingPlanSelection(): PendingPlanSelection | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(PLAN_SELECTION_KEY)
    if (!raw) return null
    window.sessionStorage.removeItem(PLAN_SELECTION_KEY)
    const parsed = JSON.parse(raw) as PendingPlanSelection
    if (!ALLOWED_PLANS.has(parsed.plan) || !ALLOWED_INTERVALS.has(parsed.interval)) return null
    return parsed
  } catch {
    return null
  }
}

export function peekPendingPlanSelection(): PendingPlanSelection | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.sessionStorage.getItem(PLAN_SELECTION_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as PendingPlanSelection
    if (!ALLOWED_PLANS.has(parsed.plan) || !ALLOWED_INTERVALS.has(parsed.interval)) return null
    return parsed
  } catch {
    return null
  }
}
