/**
 * Regression test for the 2026-04-09 verify-email 422 incident.
 *
 * The bug: `VerificationContext.verifyEmail` was POSTing the token as a
 * URL query parameter with an empty body, but the backend's
 * `VerifyEmailRequest` is a Pydantic body model. Every click-through from
 * a verification email produced 422 "Field required" because the body
 * lacked `token`. Phase 1 only verified that the email *arrived*, never
 * that clicking the link actually worked.
 *
 * This test locks the fix in place: the token must travel in the JSON body.
 */
import { ReactNode } from 'react'
import { renderHook, act } from '@testing-library/react'
import {
  VerificationProvider,
  useVerificationContext,
} from '@/contexts/VerificationContext'
import { apiPost } from '@/utils'

// Minimal AuthSession mock — VerificationProvider reads token + refreshUser
jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: () => ({
    token: null,
    refreshUser: jest.fn(),
  }),
}))

jest.mock('@/utils', () => ({
  apiPost: jest.fn(),
  apiGet: jest.fn(),
}))

const mockApiPost = apiPost as jest.Mock

function wrapper({ children }: { children: ReactNode }) {
  return <VerificationProvider>{children}</VerificationProvider>
}

describe('VerificationContext.verifyEmail — 2026-04-09 regression guard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockApiPost.mockResolvedValue({
      ok: true,
      data: { message: 'ok', user: { id: 1, email: 'a@b.c', is_verified: true } },
    })
  })

  it('POSTs token in the JSON body, not in the URL query string', async () => {
    const { result } = renderHook(() => useVerificationContext(), { wrapper })

    await act(async () => {
      await result.current.verifyEmail('test-token-abc-123')
    })

    expect(mockApiPost).toHaveBeenCalledTimes(1)
    const [endpoint, token, body] = mockApiPost.mock.calls[0]

    // Endpoint must be the clean path without query params — Pydantic body
    // models cannot read from the query string.
    expect(endpoint).toBe('/auth/verify-email')
    expect(endpoint).not.toContain('?')
    expect(endpoint).not.toContain('token=')

    // No bearer token (public endpoint).
    expect(token).toBeNull()

    // Body must contain the token field the backend schema expects.
    expect(body).toEqual({ token: 'test-token-abc-123' })
  })

  it('returns success: true on 2xx response', async () => {
    const { result } = renderHook(() => useVerificationContext(), { wrapper })

    let response: { success: boolean; error?: string } | undefined
    await act(async () => {
      response = await result.current.verifyEmail('valid-token')
    })

    expect(response).toEqual({ success: true })
  })

  it('returns success: false with error message on failure', async () => {
    mockApiPost.mockResolvedValue({
      ok: false,
      error: 'Invalid verification token',
    })

    const { result } = renderHook(() => useVerificationContext(), { wrapper })

    let response: { success: boolean; error?: string } | undefined
    await act(async () => {
      response = await result.current.verifyEmail('bad-token')
    })

    expect(response).toEqual({
      success: false,
      error: 'Invalid verification token',
    })
  })
})
