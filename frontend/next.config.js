/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker deployments
  // This creates a minimal production build that includes only necessary dependencies
  output: 'standalone',

  // Production optimizations
  reactStrictMode: true,

  // Disable x-powered-by header for security
  poweredByHeader: false,
}

module.exports = nextConfig
