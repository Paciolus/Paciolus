/**
 * Session scope for client-side private data (Sprint 872, DH-01).
 *
 * The browser access token lives in an HttpOnly cookie, so the `token`
 * the frontend passes around is a constant sentinel and says nothing about
 * *who* is signed in. This module holds that identity instead:
 *
 * - `scope`      — the signed-in account's id, or null when signed out.
 *                  Every cache key and in-flight de-duplication key is
 *                  prefixed with it, so one account's entries are never
 *                  looked up for another.
 * - `generation` — bumped whenever a signed-in session ends (logout, auth
 *                  failure, account switch, account deletion). A request
 *                  started under an older generation may not write to the
 *                  cache, and React subtrees keyed by the generation
 *                  remount, discarding any financial data they held.
 *
 * Signing in from a signed-out state does not bump the generation: there
 * is no private data to discard, and remounting the login page mid-flow
 * would only cause flicker.
 */

type Listener = () => void

let scope: string | null = null
let generation = 0
const listeners = new Set<Listener>()
const clearers = new Set<() => void>()

export function getSessionScope(): string | null {
  return scope
}

export function getSessionGeneration(): number {
  return generation
}

/** Register a private store to empty whenever a signed-in session ends. */
export function onSessionEnd(clear: () => void): void {
  clearers.add(clear)
}

export function subscribeSessionGeneration(listener: Listener): () => void {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

/**
 * End the current signed-in session: empty every private store and move to
 * a new generation. No-op when nobody is signed in.
 */
export function endSession(): void {
  if (scope === null) return
  scope = null
  generation++
  clearers.forEach(clear => clear())
  listeners.forEach(listener => listener())
}

/**
 * Record the account a session belongs to. Switching from one account to a
 * different one ends the old session first.
 */
export function beginSession(accountId: string | number): void {
  const next = String(accountId)
  if (scope === next) return
  endSession()
  scope = next
}
