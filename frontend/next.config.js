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
