/**
 * Auth Types
 * Phase 2 Refactor: Extracted from AuthContext.tsx
 *
 * Types for authentication state and API responses.
 */

/**
 * User model returned by the API.
 */
export interface User {
  id: number;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
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
}

/**
 * Credentials for registration request.
 */
export interface RegisterCredentials {
  email: string;
  password: string;
}

/**
 * Response from login/register API endpoints.
 */
export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
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
  login: (credentials: LoginCredentials) => Promise<AuthResult>;
  register: (credentials: RegisterCredentials) => Promise<AuthResult>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}
