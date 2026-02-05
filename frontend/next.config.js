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

module.exports = nextConfig
