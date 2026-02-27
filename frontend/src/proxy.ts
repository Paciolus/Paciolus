import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Per-request CSP nonce proxy (Phase LXV — CSP Tightening).
 *
 * Why proxy instead of next.config.js headers():
 *   CSP nonces must be unique per request; static headers() can only emit a fixed
 *   string. Moving CSP here allows `'nonce-{n}'` in script-src, which causes all
 *   CSP3 browsers to ignore `unsafe-inline` even if it is listed as a fallback.
 *
 * script-src policy:
 *   Production: 'self' + nonce only — unsafe-eval removed.
 *   Development: 'unsafe-eval' retained for webpack HMR / fast-refresh.
 *
 * style-src policy:
 *   'unsafe-inline' intentionally retained. React's style prop compiles to HTML
 *   style="" attributes; CSP cannot nonce individual style attributes (only <style>
 *   elements), so removing unsafe-inline here would break all dynamic inline styles
 *   across the platform. This is a known limitation documented in SECURITY_POLICY.md.
 *
 * Next.js integration:
 *   Next.js App Router reads the 'x-nonce' request header set below and
 *   automatically applies the nonce to all inline scripts it injects (RSC streaming
 *   self.__next_f.push([...]) scripts). No changes to layout.tsx are required for
 *   the framework scripts; pass nonce={nonce} to any custom <Script> components.
 */
export function proxy(request: NextRequest) {
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const isDev = process.env.NODE_ENV !== 'production'

  // In development, retain 'unsafe-eval' so webpack HMR / eval source maps work.
  // In production, the nonce alone is sufficient — no eval is needed.
  const scriptSrc = isDev
    ? `script-src 'self' 'nonce-${nonce}' 'unsafe-eval'`
    : `script-src 'self' 'nonce-${nonce}'`

  const csp = [
    "default-src 'self'",
    scriptSrc,
    // unsafe-inline required: React style props → HTML style="" attributes.
    // CSP3 browsers ignore unsafe-inline when nonce is present in script-src,
    // but style-src is a separate directive and must keep unsafe-inline for styles.
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    `connect-src 'self' ${apiUrl} https://*.sentry.io`,
    // Explicit frame-src (was previously absent, falling through to default-src).
    "frame-src 'none'",
    "frame-ancestors 'none'",
    // Explicit object-src (Flash / plugin execution — belt-and-suspenders).
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ')

  // Forward the nonce to the Next.js server rendering pipeline so the framework
  // can apply it to its own inline scripts (RSC streaming, router bootstrap).
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-nonce', nonce)

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  })

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
