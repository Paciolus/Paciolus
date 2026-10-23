/**
 * Sprint 809 — findings D-1 and D-4: the route → theme map.
 *
 * D-4's defect was a hand-maintained exact-match array that had stopped
 * matching: `/forgot-password`, `/reset-password`, `/checkout` and
 * `/checkout/success` were all missing. The `(auth)` layout paints
 * `bg-gradient-obsidian` itself, which masked it for the two password routes,
 * but `/checkout` paints its own `bg-surface-page` / `bg-surface-card` and uses
 * 33 semantic tokens — so it resolved the light palette and rendered as a light
 * page inside the dark auth shell, on the page where customers pay.
 *
 * The DEC review found the same shape elsewhere and called it H3: a
 * hand-maintained list that stopped matching. A URL does not carry its route
 * group, so this map has to stay data. What it does not have to stay is
 * unchecked.
 *
 * This suite walks `src/app` for every `page.tsx`, derives each route's URL and
 * its route group, and asserts the dark set is *exactly* the pages under
 * `(marketing)` and `(auth)`. Adding a route to either group without adding it
 * to `DARK_ROUTES` fails here, and so does the reverse.
 */

import { readdirSync, statSync } from 'fs'
import { join } from 'path'
import { DARK_ROUTES, DEFAULT_THEME, resolveTheme } from '@/lib/theme-routes'

const APP_DIR = join(process.cwd(), 'src', 'app')

/** Route groups whose pages are served with the dark theme. */
const DARK_ROUTE_GROUPS = ['(marketing)', '(auth)']

interface DiscoveredRoute {
  /** Path relative to src/app, e.g. "(marketing)/about" */
  readonly file: string
  /** The URL the route is served at, e.g. "/about" */
  readonly url: string
  /** The route group it sits in, or null */
  readonly group: string | null
}

function walk(dir: string, acc: string[] = [], base = ''): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      walk(full, acc, base ? `${base}/${entry}` : entry)
    } else if (entry === 'page.tsx' || entry === 'page.ts') {
      acc.push(base)
    }
  }
  return acc
}

function discoverRoutes(): DiscoveredRoute[] {
  return walk(APP_DIR).map((file) => {
    const segments = file.split('/').filter(Boolean)
    // A route group is a path segment wrapped in parentheses. It does not
    // appear in the URL — which is the whole reason the theme cannot be
    // derived from the pathname at runtime.
    const group = segments.find((s) => s.startsWith('(') && s.endsWith(')')) ?? null
    const urlSegments = segments.filter((s) => !(s.startsWith('(') && s.endsWith(')')))
    return {
      file: file || '(root)',
      url: urlSegments.length ? `/${urlSegments.join('/')}` : '/',
      group,
    }
  })
}

describe('route → theme map', () => {
  const routes = discoverRoutes()

  it('discovers the app routes at all (guards against a broken walk)', () => {
    // A silently empty walk would make every assertion below vacuous — which is
    // precisely how a gate stops gating.
    expect(routes.length).toBeGreaterThan(50)
    expect(routes.some((r) => r.url === '/')).toBe(true)
    expect(routes.some((r) => r.url === '/login')).toBe(true)
    expect(routes.some((r) => r.url.startsWith('/tools/'))).toBe(true)
  })

  it('DARK_ROUTES is exactly the pages in the dark route groups', () => {
    const expected = routes
      .filter((r) => r.group !== null && DARK_ROUTE_GROUPS.includes(r.group))
      .map((r) => r.url)
      .sort()
    const declared = [...DARK_ROUTES].sort()

    expect(declared).toEqual(expected)
  })

  it('every discovered route resolves to exactly one theme', () => {
    for (const route of routes) {
      const theme = resolveTheme(route.url)
      expect(['dark', 'light']).toContain(theme)

      const expectedDark = route.group !== null && DARK_ROUTE_GROUPS.includes(route.group)
      expect(theme).toBe(expectedDark ? 'dark' : 'light')
    }
  })

  it('declares no route that does not exist', () => {
    const urls = new Set(routes.map((r) => r.url))
    for (const declared of DARK_ROUTES) {
      expect(urls.has(declared)).toBe(true)
    }
  })

  describe('the four routes D-4 measured as missing', () => {
    // All four are in the (auth) group. The auth layout's own gradient masked
    // the first two; /checkout paints its own surfaces and did not benefit.
    it.each(['/forgot-password', '/reset-password', '/checkout', '/checkout/success'])(
      '%s resolves to dark',
      (url) => {
        expect(resolveTheme(url)).toBe('dark')
      }
    )

    it('/checkout is dark, matching the auth shell it renders inside', () => {
      // The finding: it resolved light, so a light page rendered inside a dark
      // gradient — on the payment page.
      expect(resolveTheme('/checkout')).toBe('dark')
    })
  })

  describe('the interior is light', () => {
    it.each([
      '/tools',
      '/tools/trial-balance',
      '/tools/statistical-sampling',
      '/settings',
      '/settings/billing',
      '/engagements',
      '/portfolio',
      '/history',
      '/dashboard',
      '/flux',
      '/recon',
    ])('%s resolves to light', (url) => {
      expect(resolveTheme(url)).toBe('light')
    })
  })

  describe('the exterior is dark', () => {
    it.each(['/', '/pricing', '/about', '/privacy', '/terms', '/trust', '/demo', '/login', '/register'])(
      '%s resolves to dark',
      (url) => {
        expect(resolveTheme(url)).toBe('dark')
      }
    )
  })

  describe('input tolerance', () => {
    // The server reads a raw request header; the client passes usePathname().
    // Both must land on the same answer, or D-1's flash comes back as a
    // hydration mismatch instead.
    it('tolerates a trailing slash', () => {
      expect(resolveTheme('/pricing/')).toBe('dark')
      expect(resolveTheme('/')).toBe('dark')
    })

    it('tolerates a query string and hash', () => {
      expect(resolveTheme('/pricing?plan=solo')).toBe('dark')
      expect(resolveTheme('/checkout?session=abc#top')).toBe('dark')
      expect(resolveTheme('/tools/trial-balance?tab=2')).toBe('light')
    })

    it('falls back to the light default when the pathname is absent', () => {
      // If the proxy header is ever missing, being wrong toward light is being
      // wrong toward the majority of routes.
      expect(resolveTheme(null)).toBe(DEFAULT_THEME)
      expect(resolveTheme(undefined)).toBe(DEFAULT_THEME)
      expect(resolveTheme('')).toBe(DEFAULT_THEME)
      expect(DEFAULT_THEME).toBe('light')
    })

    it('an unknown route is light rather than throwing', () => {
      expect(resolveTheme('/not-a-real-route')).toBe('light')
    })
  })

  it('most routes are light, which is why the flash mattered', () => {
    const light = routes.filter((r) => resolveTheme(r.url) === 'light')
    // The review measured 49 of 62. The exact split moves as routes are added;
    // what matters is that the majority are light, so a hardcoded
    // `data-theme="dark"` was wrong for most of the app.
    expect(light.length).toBeGreaterThan(routes.length / 2)
  })
})
