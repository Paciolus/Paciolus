/**
 * Route → theme resolution for "The Vault" architecture.
 *
 * Dark is the vault exterior: the marketing surfaces and the authentication
 * flow. Light is the vault interior: tools, engagements, settings, diagnostics.
 * The theme is a property of the route, not a user preference, so there is no
 * toggle.
 *
 * Sprint 809 (findings D-1 and D-4) moved this out of `ThemeProvider` for two
 * reasons.
 *
 * **D-1 — the flash.** `layout.tsx` server-rendered `data-theme="dark"`
 * unconditionally and `ThemeProvider` resolved the real theme in a
 * `useEffect`. 49 of the 62 routes are light — every tool, engagement and
 * settings page — so all of them were served dark, painted dark, and flipped
 * to light after hydration. `await headers()` in the root layout forces dynamic
 * rendering for CSP nonces, so no static prerender softened it. The resolution
 * now happens on the server (the proxy puts the pathname in a request header)
 * *and* on the client for subsequent navigations, both through this one
 * function, so the two cannot disagree.
 *
 * **D-4 — the list that stopped matching.** The previous `DARK_ROUTES` array
 * was compared with `.includes(pathname)` and was missing four shipped routes:
 * `/forgot-password`, `/reset-password`, `/checkout` and `/checkout/success`.
 * The `(auth)` layout paints `bg-gradient-obsidian` itself, which masked the
 * omission for the two password routes. **`/checkout` did not benefit:** it
 * paints its own `bg-surface-page` / `bg-surface-card` and uses 33 semantic
 * tokens, so it resolved the *light* palette and rendered as a light page
 * inside the dark auth shell — on the page where customers pay.
 *
 * A URL does not carry its route group (`(marketing)/about` is served at
 * `/about`), so this cannot be derived from the pathname at runtime and the set
 * below is necessarily data. What changed is that it is no longer *merely*
 * hand-maintained: `theme-routes.test.ts` walks `src/app` for every `page.tsx`,
 * derives each route's URL and its route group, and asserts that this set is
 * exactly the pages under `(marketing)` and `(auth)`. Adding a route to either
 * group without adding it here fails the suite. That is the difference between
 * a list that can silently stop matching and one that cannot.
 */

export type Theme = 'dark' | 'light'

/**
 * Every route served with the dark theme: the `(marketing)` and `(auth)` route
 * groups. All are static paths — neither group contains a dynamic segment —
 * which is why exact matching is sufficient and no prefix rules are needed.
 *
 * Keep alphabetised within each group. `theme-routes.test.ts` is the authority
 * on the contents.
 */
export const DARK_ROUTES: ReadonlySet<string> = new Set([
  // (marketing)
  '/',
  '/about',
  '/approach',
  '/contact',
  '/demo',
  '/pricing',
  '/privacy',
  '/terms',
  '/trust',
  // (auth)
  '/checkout',
  '/checkout/success',
  '/forgot-password',
  '/login',
  '/register',
  '/reset-password',
  '/verification-pending',
  '/verify-email',
])

/** The theme applied to any route not in `DARK_ROUTES`. */
export const DEFAULT_THEME: Theme = 'light'

/**
 * Resolve a pathname to its theme.
 *
 * Tolerates a trailing slash and a query string so that a caller reading a raw
 * request header gets the same answer as one passing `usePathname()`.
 */
export function resolveTheme(pathname: string | null | undefined): Theme {
  if (!pathname) return DEFAULT_THEME

  // Strip query/hash, then any trailing slash (but keep the root '/').
  // `?? ''` because `noUncheckedIndexedAccess` types `split()[0]` as possibly
  // undefined even though it never is.
  let path = pathname.split(/[?#]/)[0] ?? ''
  if (path.length > 1 && path.endsWith('/')) {
    path = path.replace(/\/+$/, '')
  }
  if (path === '') path = '/'

  return DARK_ROUTES.has(path) ? 'dark' : DEFAULT_THEME
}
