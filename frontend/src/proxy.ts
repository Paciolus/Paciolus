import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Per-request CSP proxy (Phase LXV — CSP Tightening).
 *
 * Why proxy instead of next.config.js headers():
 *   Keeping CSP here (Edge layer) allows per-request dynamic values (e.g. API URL)
 *   and a single authoritative place for the full policy.
 *
 * script-src policy:
 *   Production: 'self' + 'unsafe-inline' — unsafe-eval removed (Phase LXV goal).
 *   Development: 'unsafe-eval' retained for webpack HMR / fast-refresh.
 *   Nonce-based script-src is NOT used: Next.js streaming SSR emits inline
 *   activation scripts without nonce attributes, so a nonce-only policy blocks
 *   React hydration and leaves pages blank.  See todo.md for the proper fix.
 *
 * style-src policy:
 *   'unsafe-inline' intentionally retained. React's style prop compiles to HTML
 *   style="" attributes; CSP cannot nonce individual style attributes (only <style>
 *   elements), so removing unsafe-inline here would break all dynamic inline styles
 *   across the platform. This is a known limitation documented in SECURITY_POLICY.md.
 */
export function proxy(request: NextRequest) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const isDev = process.env.NODE_ENV !== 'production'

  // In development, retain 'unsafe-eval' so webpack HMR / eval source maps work.
  // In production, 'unsafe-inline' is required: Next.js streaming SSR emits inline
  // activation scripts that cannot receive a nonce attribute — they are blocked when
  // only nonce-based script-src is in effect.  The key security gain of Phase LXV
  // (removing 'unsafe-eval' from production) is preserved.
  //
  // NOTE: Nonce propagation to Next.js streaming scripts is a known gap.
  // Proper nonce support requires either (a) Next.js exposing a nonce injection API
  // for streaming chunks, or (b) a hash-based CSP approach.  Track in todo.md.
  const scriptSrc = isDev
    ? `script-src 'self' 'unsafe-inline' 'unsafe-eval'`
    : `script-src 'self' 'unsafe-inline'`

  const csp = [
    "default-src 'self'",
    scriptSrc,
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    `connect-src 'self' ${apiUrl} https://*.sentry.io`,
    "frame-src 'none'",
    "frame-ancestors 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ')

  const response = NextResponse.next()
  response.headers.set('Content-Security-Policy', csp)

  return response
}

export const config = {
  matcher: [
    {
      // Run on all routes except Next.js static assets and image optimisation URLs.
      // Excluding these avoids unnecessary nonce generation for binary responses.
      source:
        '/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:png|ico|svg|jpg|jpeg|gif|webp)$).*)',
      missing: [
        // Skip prefetch requests — they don't render pages.
        { type: 'header', key: 'next-router-prefetch' },
        { type: 'header', key: 'purpose', value: 'prefetch' },
      ],
    },
  ],
}
