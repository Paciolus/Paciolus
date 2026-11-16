/**
 * Sprint 872 (DH-01): the browser cache never crosses an account boundary.
 *
 * Drives the real AuthProvider and the real apiClient against a fake server
 * that answers as whichever account's cookie the browser currently holds.
 * Account A loads clients, history and engagements, logs out, account B
 * signs in on the same tab and asks for the same URLs: B must only ever see
 * B's data — including when A's request is still in flight when B signs in.
 */
import { ReactNode, useEffect, useState } from 'react'
import { act, render, renderHook, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import { apiGet, invalidateCache, stopCacheSweep, setCsrfToken } from '@/utils/apiClient'
import { getSessionGeneration } from '@/utils/sessionScope'

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({ push: jest.fn(), replace: jest.fn() })),
}))

const PRIVATE_URLS = ['/clients?page=1', '/activity/history', '/engagements']

const USERS: Record<string, { id: number; email: string }> = {
  'a@firm-a.test': { id: 101, email: 'a@firm-a.test' },
  'b@firm-b.test': { id: 202, email: 'b@firm-b.test' },
}

/** Fake server: whoever's cookie the browser holds at *response* time. */
let cookieUser: string | null = null
/** Endpoints whose response is held back until released by the test. */
const held = new Map<string, Array<() => void>>()
let holdNext: string | null = null

function jsonResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    headers: new Headers(),
  } as unknown as Response
}

function userBody(email: string) {
  const u = USERS[email]!
  return {
    user: { ...u, name: email, is_verified: true, is_active: true, created_at: '2026-01-01' },
    csrf_token: `csrf-${u.id}`,
  }
}

const mockFetch = jest.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
  const url = String(input)
  const path = url.replace(/^https?:\/\/[^/]+/, '')
  if (path.endsWith('/auth/refresh')) {
    return cookieUser ? jsonResponse(200, userBody(cookieUser)) : jsonResponse(401, { detail: 'no session' })
  }
  if (path.endsWith('/auth/login')) {
    const { email } = JSON.parse(String(init?.body)) as { email: string }
    cookieUser = email
    return jsonResponse(200, userBody(email))
  }
  if (path.endsWith('/auth/logout')) {
    cookieUser = null
    return jsonResponse(200, { ok: true })
  }
  const answer = () => (cookieUser
    ? jsonResponse(200, { owner: cookieUser, path })
    : jsonResponse(401, { detail: 'not signed in' }))
  if (holdNext && path.includes(holdNext)) {
    // Capture *nothing* about the session now — answer as whoever holds the
    // cookie at release time, like a slow server would.
    const key = holdNext
    holdNext = null
    return new Promise<Response>(resolve => {
      const list = held.get(key) ?? []
      list.push(() => resolve(answer()))
      held.set(key, list)
    })
  }
  return answer()
})

function wrapper({ children }: { children: ReactNode }) {
  return <AuthProvider>{children}</AuthProvider>
}

beforeEach(() => {
  global.fetch = mockFetch as unknown as typeof fetch
  mockFetch.mockClear()
  cookieUser = null
  held.clear()
  holdNext = null
  invalidateCache()
  stopCacheSweep()
  setCsrfToken(null)
})

async function signIn(result: { current: ReturnType<typeof useAuth> }, email: string) {
  await act(async () => {
    const r = await result.current.login({ email, password: 'pw' })
    expect(r.success).toBe(true)
  })
  await waitFor(() => expect(result.current.user?.email).toBe(email))
}

async function signOut(result: { current: ReturnType<typeof useAuth> }) {
  await act(async () => { await result.current.logout() })
  await waitFor(() => expect(result.current.user).toBeNull())
}

async function owners(token: string | null) {
  const out: string[] = []
  for (const url of PRIVATE_URLS) {
    const res = await apiGet<{ owner: string }>(url, token)
    out.push(res.data?.owner ?? `error:${res.status}`)
  }
  return out
}

describe('DH-01: private cache is scoped to the signed-in account', () => {
  it('B never receives A\'s cached clients, history or engagements after A logs out', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await signIn(result, 'a@firm-a.test')
    expect(await owners(result.current.token)).toEqual(Array(3).fill('a@firm-a.test'))

    await signOut(result)
    await signIn(result, 'b@firm-b.test')

    expect(await owners(result.current.token)).toEqual(Array(3).fill('b@firm-b.test'))
  })

  it('B is not served A\'s data when A\'s request completes after B has signed in', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await signIn(result, 'a@firm-a.test')
    // A's clients request is sent but the response is held back.
    holdNext = '/clients'
    const aPending = apiGet<{ owner: string }>('/clients?page=1', result.current.token)

    await signOut(result)
    await signIn(result, 'b@firm-b.test')

    // B asks for the same URL while A's request is still in flight: it must
    // not be de-duplicated onto A's request.
    const bFirst = await apiGet<{ owner: string }>('/clients?page=1', result.current.token)
    expect(bFirst.data?.owner).toBe('b@firm-b.test')

    // A's request now completes — answered with A's data, as if the server
    // had produced it before the switch.
    cookieUser = 'a@firm-a.test'
    held.get('/clients')!.forEach(release => release())
    await aPending
    cookieUser = 'b@firm-b.test'

    // A's late response must not have refilled the cache for B.
    const bAgain = await apiGet<{ owner: string }>('/clients?page=1', result.current.token)
    expect(bAgain.data?.owner).toBe('b@firm-b.test')
  })

  it('A\'s late response is not cached even before B requests the URL', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))

    await signIn(result, 'a@firm-a.test')
    holdNext = '/engagements'
    const aPending = apiGet('/engagements', result.current.token)
    await signOut(result)
    await signIn(result, 'b@firm-b.test')

    cookieUser = 'a@firm-a.test'
    held.get('/engagements')!.forEach(release => release())
    await aPending
    cookieUser = 'b@firm-b.test'

    const b = await apiGet<{ owner: string }>('/engagements', result.current.token)
    expect(b.data?.owner).toBe('b@firm-b.test')
  })

  it('a refresh that returns a different account clears the old account\'s cache', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    await signIn(result, 'a@firm-a.test')
    expect(await owners(result.current.token)).toEqual(Array(3).fill('a@firm-a.test'))

    // Another tab signs in as B; this tab's next refresh comes back as B.
    cookieUser = 'b@firm-b.test'
    // (the next 401-triggered silent refresh is what notices it)
    await act(async () => {
      await (await import('@/utils/authMiddleware')).getTokenRefreshCallback()!()
    })
    await waitFor(() => expect(result.current.user?.email).toBe('b@firm-b.test'))

    expect(await owners(result.current.token)).toEqual(Array(3).fill('b@firm-b.test'))
  })

  it('a failed refresh (auth failure) clears the private cache', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    await signIn(result, 'a@firm-a.test')
    await owners(result.current.token)

    cookieUser = null // session revoked server-side
    await act(async () => {
      await (await import('@/utils/authMiddleware')).getTokenRefreshCallback()!()
    })
    await waitFor(() => expect(result.current.user).toBeNull())

    expect(await owners(result.current.token)).toEqual(Array(3).fill('error:401'))
  })
})

describe('DH-01: contexts holding financial data reset at the session boundary', () => {
  function DataHolder({ onMount }: { onMount: () => void }) {
    const [loaded] = useState(() => 'firm-a-ledger')
    useEffect(() => { onMount() }, [onMount])
    return <span data-testid="held">{loaded}</span>
  }

  it('remounts everything under AuthProvider on logout, not on sign-in', async () => {
    const onMount = jest.fn()
    let auth: ReturnType<typeof useAuth> | null = null
    function Probe() { auth = useAuth(); return null }

    render(
      <AuthProvider>
        <Probe />
        <DataHolder onMount={onMount} />
      </AuthProvider>,
    )
    await waitFor(() => expect(auth!.isLoading).toBe(false))
    const mountsAfterInit = onMount.mock.calls.length

    await act(async () => { await auth!.login({ email: 'a@firm-a.test', password: 'pw' }) })
    await waitFor(() => expect(auth!.user?.email).toBe('a@firm-a.test'))
    expect(onMount.mock.calls.length).toBe(mountsAfterInit) // sign-in: no remount

    const before = getSessionGeneration()
    await act(async () => { await auth!.logout() })
    await waitFor(() => expect(auth!.user).toBeNull())
    expect(getSessionGeneration()).toBeGreaterThan(before)
    expect(onMount.mock.calls.length).toBe(mountsAfterInit + 1) // logout: state discarded
  })
})
