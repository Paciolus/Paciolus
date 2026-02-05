/**
 * Email Verification Types — Sprint 58
 *
 * Type definitions for the email verification flow.
 * Maps to Sprint 57 backend endpoints.
 */

/**
 * Response from GET /auth/verification-status
 */
export interface VerificationStatus {
  is_verified: boolean
  email: string
  verified_at: string | null
  can_resend: boolean
  resend_cooldown_seconds: number
  email_service_configured: boolean
}

/**
 * Response from POST /auth/verify-email
 */
export interface VerifyEmailResponse {
  message: string
  user: {
    id: number
    email: string
    is_verified: boolean
  }
}

/**
 * Response from POST /auth/resend-verification
 */
export interface ResendVerificationResponse {
  message: string
  cooldown_minutes: number
}
