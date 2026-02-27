const { withSentryConfig } = require('@sentry/nextjs');

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker deployments
  // This creates a minimal production build that includes only necessary dependencies
  output: 'standalone',

  // Production optimizations
  reactStrictMode: true,

  // Disable x-powered-by header for security
  poweredByHeader: false,

  // Sprint 25: Remove console.log statements in production builds
  // Keeps console.error and console.warn for debugging production issues
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },

  // Phase LXV: CSP is now set per-request with a unique nonce in src/middleware.ts.
  // Static headers() cannot carry nonces (must be unique per request), so CSP was
  // moved there. Remaining headers are static and safe to keep here.
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ]
  },
}

// Sprint 275: Sentry APM — wrap only when DSN is configured
module.exports = process.env.NEXT_PUBLIC_SENTRY_DSN
  ? withSentryConfig(nextConfig, {
      // Suppress source map upload logs during build
      silent: true,
      // Don't upload source maps by default (opt-in via SENTRY_AUTH_TOKEN)
      disableServerWebpackPlugin: !process.env.SENTRY_AUTH_TOKEN,
      disableClientWebpackPlugin: !process.env.SENTRY_AUTH_TOKEN,
    })
  : nextConfig;
