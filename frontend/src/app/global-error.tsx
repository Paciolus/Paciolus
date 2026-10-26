'use client'

/**
 * Global Error Boundary — catches root layout errors.
 *
 * Next.js requirement: must include its own <html> and <body> tags
 * since it replaces the root layout entirely when triggered.
 *
 * Uses hardcoded Oat & Obsidian brand hex (vault exterior) since
 * ThemeProvider and CSS custom properties are unavailable here.
 * Every literal below maps to a value in tailwind.config.js — see the
 * BRAND_TOKENS map so future readers never reach for a random gray.
 *
 * Next.js App Router Hardening
 */

// Literal brand hex copies of tailwind.config.js — kept in sync manually since
// CSS custom properties do not resolve in the global-error boundary.
const BRAND_TOKENS = {
  obsidianDeep: '#121212',
  obsidianBase: '#212121',
  obsidianElevated: '#303030',
  oatmealBase: '#EBE9E4',
  oatmealMuted: '#B5AD9F', // oatmeal-500: secondary body text on dark surface
  oatmealDisabled: '#B5AD9F', // oatmeal-500 — oatmeal-700 measured 3.4:1 on this panel (Sprint 828)
  clayBase: '#BC4749',
  clayLight: '#E99A9B',
  sageBase: '#4A7C59',
  sageHover: '#3D6649',
} as const

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html lang="en" data-theme="dark">
      {/*
        Sprint 807 (findings C-1 / C-2): the `<link>` to
        `fonts.googleapis.com` that used to sit here is gone.

        It was missed by the review and by the first pass of this sprint,
        because both looked at `globals.css` and the CSP and this is neither —
        a `<link>` tag inside a component. `scripts/lint_subprocessors.py` now
        scans TSX for third-party `<link href>` as well, so the class is closed
        rather than this instance.

        No webfont replaces it, deliberately. This component renders when the
        root layout itself has thrown, which means it replaces that layout
        entirely and never receives the `next/font` CSS variables. Reaching for
        a remote stylesheet on the one page whose job is to render instantly —
        in the state where the application has already failed — is the wrong
        trade even setting the privacy problem aside. The `fontFamily` values
        below name the brand families first and fall through to the system
        stack, which is what a visitor sees here now.
      */}
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: BRAND_TOKENS.obsidianDeep,
          backgroundImage: `linear-gradient(to bottom, ${BRAND_TOKENS.obsidianDeep}, ${BRAND_TOKENS.obsidianBase} 40%, #1a1a1a 60%, ${BRAND_TOKENS.obsidianDeep})`,
          color: BRAND_TOKENS.oatmealBase,
          fontFamily: 'Lato, sans-serif',
        }}
      >
        <div style={{ maxWidth: '28rem', width: '100%', textAlign: 'center', padding: '2rem' }}>
          {/* Error icon */}
          <div
            style={{
              width: '4rem',
              height: '4rem',
              margin: '0 auto 1.5rem',
              borderRadius: '50%',
              backgroundColor: 'rgba(188, 71, 73, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke={BRAND_TOKENS.clayBase}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </div>

          <h1
            style={{
              fontFamily: 'Merriweather, serif',
              fontSize: '1.5rem',
              fontWeight: 700,
              marginBottom: '0.75rem',
              color: BRAND_TOKENS.oatmealBase,
            }}
          >
            Something went wrong
          </h1>

          <p
            style={{
              color: BRAND_TOKENS.oatmealMuted,
              marginBottom: '2rem',
              lineHeight: 1.6,
            }}
          >
            Paciolus encountered a critical error. Anything you had already saved is unaffected; an upload that was in progress
            was not kept, so you may need to upload it again.
          </p>

          {process.env.NODE_ENV === 'development' && (
            <div
              style={{
                marginBottom: '1.5rem',
                padding: '1rem',
                backgroundColor: 'rgba(48, 48, 48, 0.8)',
                borderRadius: '0.5rem',
                border: '1px solid rgba(188, 71, 73, 0.3)',
                textAlign: 'left',
              }}
            >
              <p
                style={{
                  fontFamily: 'monospace',
                  fontSize: '0.75rem',
                  color: BRAND_TOKENS.clayLight,
                  wordBreak: 'break-all',
                  margin: 0,
                }}
              >
                {error.message}
              </p>
              {error.digest && (
                <p
                  style={{
                    fontFamily: 'monospace',
                    fontSize: '0.7rem',
                    color: BRAND_TOKENS.oatmealDisabled,
                    marginTop: '0.5rem',
                    marginBottom: 0,
                  }}
                >
                  Digest: {error.digest}
                </p>
              )}
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
            <button
              type="button"
              onClick={() => reset()}
              aria-label="Retry the last action that failed"
              style={{
                padding: '0.625rem 1.5rem',
                backgroundColor: BRAND_TOKENS.sageBase,
                color: BRAND_TOKENS.oatmealBase,
                border: 'none',
                borderRadius: '0.5rem',
                fontFamily: 'Lato, sans-serif',
                fontSize: '0.875rem',
                fontWeight: 700,
                cursor: 'pointer',
                outline: 'none',
                transition: 'background-color 200ms, outline-color 200ms',
              }}
              onMouseOver={(e) => (e.currentTarget.style.backgroundColor = BRAND_TOKENS.sageHover)}
              onMouseOut={(e) => (e.currentTarget.style.backgroundColor = BRAND_TOKENS.sageBase)}
              onFocus={(e) => {
                e.currentTarget.style.backgroundColor = BRAND_TOKENS.sageHover
                e.currentTarget.style.outline = `2px solid ${BRAND_TOKENS.oatmealBase}`
                e.currentTarget.style.outlineOffset = '2px'
              }}
              onBlur={(e) => {
                e.currentTarget.style.backgroundColor = BRAND_TOKENS.sageBase
                e.currentTarget.style.outline = 'none'
              }}
            >
              Try Again
            </button>
            <button
              type="button"
              onClick={() => window.location.reload()}
              aria-label="Reload the Paciolus application"
              style={{
                padding: '0.625rem 1.5rem',
                backgroundColor: 'transparent',
                color: BRAND_TOKENS.oatmealBase,
                border: '1px solid rgba(235, 233, 228, 0.2)',
                borderRadius: '0.5rem',
                fontFamily: 'Lato, sans-serif',
                fontSize: '0.875rem',
                fontWeight: 700,
                cursor: 'pointer',
                outline: 'none',
                transition: 'border-color 200ms, outline-color 200ms',
              }}
              onMouseOver={(e) => (e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.4)')}
              onMouseOut={(e) => (e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.2)')}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.4)'
                e.currentTarget.style.outline = `2px solid ${BRAND_TOKENS.oatmealBase}`
                e.currentTarget.style.outlineOffset = '2px'
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.2)'
                e.currentTarget.style.outline = 'none'
              }}
            >
              Reload Paciolus
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}
