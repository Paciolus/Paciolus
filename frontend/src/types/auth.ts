/**
 * Auth Types
 * Phase 2 Refactor: Extracted from AuthContext.tsx
 *
 * Types for authentication state and API responses.
 */

import type { VerificationStatus } from './verification'

/**
 * User model returned by the API.
 */
export interface User {
  id: number;
  email: string;
  name?: string | null;
  pending_email?: string | null;  // Sprint 203
  is_active: boolean;
  is_verified: boolean;
  tier?: 'free' | 'solo' | 'professional' | 'team' | 'enterprise';
  created_at: string;
}

/**
 * Profile update request (Sprint 48).
 */
export interface ProfileUpdate {
  name?: string;
  email?: string;
}

/**
 * Password change request (Sprint 48).
 */
export interface PasswordChange {
  current_password: string;
  new_password: string;
}

/**
 * Internal auth state managed by AuthContext.
 */
export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

/**
 * Credentials for login request.
 */
export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;  // Controls cookie max_age server-side
}

/**
 * Credentials for registration request.
 */
export interface RegisterCredentials {
  email: string;
  password: string;
}

/**
 * Response from login/register/refresh API endpoints.
 * refresh_token removed — now an HttpOnly cookie set server-side.
 * csrf_token: user-bound CSRF token (Security Sprint).
 */
export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  csrf_token?: string | null;
}

/**
 * Result type for auth operations.
 */
export interface AuthResult {
  success: boolean;
  error?: string;
}

/**
 * Full context type including state and methods.
 */
export interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials & { rememberMe?: boolean }) => Promise<AuthResult>;
  register: (credentials: RegisterCredentials) => Promise<AuthResult>;
  logout: () => void | Promise<void>;
  refreshUser: () => Promise<void>;
  updateProfile: (data: ProfileUpdate) => Promise<AuthResult>;
  changePassword: (data: PasswordChange) => Promise<AuthResult>;
  verifyEmail: (token: string) => Promise<AuthResult>;
  resendVerification: () => Promise<AuthResult>;
  checkVerificationStatus: () => Promise<VerificationStatus | null>;
}
