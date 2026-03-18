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
