/**
 * PR #254 review: account-deletion refusals carry counts and specifics an
 * exact-string allowlist cannot match, so the backend sends a stable
 * `detail.code` and the transport maps it to frontend-owned text.
 */
import { codedErrorMessage, performFetch, SAFE_CODE_MESSAGES } from '@/utils/transport'

describe('codedErrorMessage', () => {
  it('maps a known code to its safe text', () => {
    expect(codedErrorMessage({ code: 'ERASURE_ORG_HAS_MEMBERS', message: 'anything' })).toBe(
      SAFE_CODE_MESSAGES.ERASURE_ORG_HAS_MEMBERS,
    )
  })

  it('returns null for unknown codes, strings and inherited keys', () => {
    expect(codedErrorMessage({ code: 'SOMETHING_ELSE' })).toBeNull()
    expect(codedErrorMessage({ code: 'toString' })).toBeNull()
    expect(codedErrorMessage('ERASURE_SUPERADMIN')).toBeNull()
    expect(codedErrorMessage(null)).toBeNull()
  })
})

describe('performFetch with a coded error body', () => {
  const realFetch = global.fetch
  afterEach(() => {
    global.fetch = realFetch
  })

  function respond(status: number, body: unknown) {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status,
      headers: { get: () => 'application/json' },
      json: async () => body,
    }) as unknown as typeof fetch
  }

  it('shows the mapped text, never the raw backend message', async () => {
    respond(503, {
      code: 'HTTP_503',
      message: 'We could not remove a shared report from storage. 2 shared link(s) were removed first.',
      detail: { code: 'ERASURE_PARTIAL_CLEANUP', message: 'raw backend text' },
    })
    const result = await performFetch('/auth/account/delete', {}, 'POST', undefined, 5000)
    expect(result.ok).toBe(false)
    expect(result.error).toBe(SAFE_CODE_MESSAGES.ERASURE_PARTIAL_CLEANUP)
  })

  it('still falls back to the generic message for an unknown code', async () => {
    respond(409, { code: 'CONFLICT', message: 'internal detail', detail: { code: 'NOPE', message: 'internal detail' } })
    const result = await performFetch('/x', {}, 'POST', undefined, 5000)
    expect(result.error).not.toContain('internal detail')
  })
})
