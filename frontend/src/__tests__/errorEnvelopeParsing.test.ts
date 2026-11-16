/**
 * Sprint 872 (AZ-14): the frontend parses the single backend error shape
 * `{code, message, request_id, detail}` for every status — including the
 * bodies the CSRF, body-size and rate-limit layers used to send in other
 * shapes (`{"detail": ...}`, `{"error": ...}`).
 */
import { parseErrorResponse, performFetch } from '@/utils/transport'

const RID = 'abc123def456'

const BODIES: Array<[number, Record<string, unknown>]> = [
  [401, { code: 'UNAUTHORIZED', message: 'Not authenticated', request_id: RID, detail: 'Not authenticated' }],
  [403, { code: 'CSRF_FAILED', message: 'CSRF validation failed', request_id: RID, detail: 'CSRF validation failed' }],
  [413, { code: 'PAYLOAD_TOO_LARGE', message: 'Request body too large', request_id: RID, detail: 'Request body too large' }],
  [422, { code: 'VALIDATION_ERROR', message: 'The request could not be processed. Please check your input.', request_id: RID, detail: null }],
  [429, { code: 'RATE_LIMITED', message: 'Too many requests. Please try again later.', request_id: RID, detail: 'Too many requests. Please try again later.' }],
  [500, { code: 'INTERNAL_ERROR', message: 'Internal server error', request_id: RID, detail: 'Internal server error' }],
  [403, {
    code: 'FORBIDDEN',
    message: 'Email verification required. Please check your inbox for the verification email.',
    request_id: RID,
    detail: { code: 'EMAIL_NOT_VERIFIED', message: 'Email verification required. Please check your inbox for the verification email.' },
  }],
]

describe('AZ-14: one error shape, one parser', () => {
  it.each(BODIES)('parses a %i envelope', async (status, body) => {
    const parsed = parseErrorResponse(body, status)
    expect(parsed.code).toBe(body.code)
    expect(parsed.requestId).toBe(RID)
    expect(parsed.message).toBe(body.message)

    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status,
      json: () => Promise.resolve(body),
    }) as unknown as typeof fetch
    const result = await performFetch('/x', {}, 'GET', undefined, 1000)
    expect(result.ok).toBe(false)
    expect(result.status).toBe(status)
    expect(typeof result.error).toBe('string')
    expect(result.error!.length).toBeGreaterThan(0)
    expect(result.error).not.toMatch(/\[object Object\]|undefined/)
  })

  it('shows the rate-limit message for 429', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: () => Promise.resolve(BODIES[4]![1]),
    }) as unknown as typeof fetch
    const result = await performFetch('/x', {}, 'GET', undefined, 1000)
    expect(result.error).toMatch(/too many requests/i)
  })
})
