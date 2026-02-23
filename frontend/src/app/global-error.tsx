'use client'

/**
 * Global Error Boundary — catches root layout errors.
 *
 * Next.js requirement: must include its own <html> and <body> tags
 * since it replaces the root layout entirely when triggered.
 *
 * Uses hardcoded Oat & Obsidian dark theme (vault exterior) since
 * ThemeProvider and CSS custom properties are unavailable here.
 *
 * Sprint 204: Phase XXVII — Next.js App Router Hardening
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html lang="en" data-theme="dark">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700&family=Lato:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body
        style={{
          margin: 0,
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#121212',
          backgroundImage: 'linear-gradient(to bottom, #121212, #212121 40%, #1a1a1a 60%, #121212)',
          color: '#EBE9E4',
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
              stroke="#BC4749"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
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
              color: '#EBE9E4',
            }}
          >
            Something went wrong
          </h1>

          <p
            style={{
              color: '#9e9e9e',
              marginBottom: '2rem',
              lineHeight: 1.6,
            }}
          >
            Paciolus encountered a critical error. Your data has not been affected
            &mdash; Zero-Storage processing means nothing was persisted.
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
                  color: '#E99A9B',
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
                    color: '#757575',
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
              onClick={() => reset()}
              style={{
                padding: '0.625rem 1.5rem',
                backgroundColor: '#4A7C59',
                color: '#EBE9E4',
                border: 'none',
                borderRadius: '0.5rem',
                fontFamily: 'Lato, sans-serif',
                fontSize: '0.875rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'background-color 200ms',
              }}
              onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#3D6649')}
              onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#4A7C59')}
              onFocus={(e) => (e.currentTarget.style.backgroundColor = '#3D6649')}
              onBlur={(e) => (e.currentTarget.style.backgroundColor = '#4A7C59')}
            >
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '0.625rem 1.5rem',
                backgroundColor: 'transparent',
                color: '#EBE9E4',
                border: '1px solid rgba(235, 233, 228, 0.2)',
                borderRadius: '0.5rem',
                fontFamily: 'Lato, sans-serif',
                fontSize: '0.875rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'border-color 200ms',
              }}
              onMouseOver={(e) => (e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.4)')}
              onMouseOut={(e) => (e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.2)')}
              onFocus={(e) => (e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.4)')}
              onBlur={(e) => (e.currentTarget.style.borderColor = 'rgba(235, 233, 228, 0.2)')}
            >
              Reload Paciolus
            </button>
          </div>
        </div>
      </body>
    </html>
  )
}
