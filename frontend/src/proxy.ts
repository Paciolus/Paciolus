import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Per-request CSP proxy (Phase LXV — CSP Tightening, Phase LXV.1 — Proper Nonce Support).
 *
 * Next.js 16 convention: this file MUST be named proxy.ts (not middleware.ts, which is
 * deprecated in Next.js 16). The exported function MUST be named `proxy`.
 *
 * How nonce propagation works:
 *   1. This function generates a per-request nonce and sets it on the *request* headers
 *      (both x-nonce and Content-Security-Policy) so that Next.js can read it during SSR.
 *   2. The root layout (app/layout.tsx) calls headers() from next/headers, which:
 *      a. Forces dynamic rendering for the entire route tree (opt-out of static pre-rendering)
 *      b. Signals to Next.js to inject the nonce into all inline scripts it emits
 *   3. The nonce is also set on the *response* headers so the browser enforces the policy.
 *
 *   IMPORTANT: Nonce-based CSP requires dynamic rendering. Static pre-rendered pages
 *   cannot have per-request nonces injected into their cached HTML — the nonce in the
 *   CSP header would never match. Reading headers() in the root layout solves this by
 *   forcing all pages to render dynamically per request.
 *
 * script-src policy:
 *   Production: 'nonce-{nonce}' + 'strict-dynamic'
 *     - No 'unsafe-inline': nonce whitelists Next.js inline scripts.
 *     - No 'unsafe-eval': removes eval-based attack surface.
 *     - 'strict-dynamic': propagates trust to scripts loaded by nonce-approved scripts
 *       (dynamic chunks, etc.) — host allowlists are superseded but that is intentional.
 *   Development: adds 'unsafe-eval' (webpack HMR / eval source maps) and 'unsafe-inline'
 *     as a CSP2 fallback for older tooling.  In modern browsers 'unsafe-inline' is ignored
 *     when 'strict-dynamic' is present, so no effective security regression in dev.
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

  // Generate a cryptographically random per-request nonce.
  // Buffer.from(uuid).toString('base64') yields a URL-safe base64 string that satisfies
  // the CSP nonce grammar (base64-value = /[a-zA-Z0-9+/]+=*/).
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  const scriptSrc = isDev
    ? `script-src 'self' 'nonce-${nonce}' 'strict-dynamic' 'unsafe-eval' 'unsafe-inline'`
    : `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`

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

  // Set nonce + CSP on the *request* headers so Next.js App Router can read the nonce
  // server-side and inject it into all inline scripts before streaming the response.
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)
  requestHeaders.set('Content-Security-Policy', csp)

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  })

  // Also set CSP on the *response* headers so the browser enforces the policy.
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
