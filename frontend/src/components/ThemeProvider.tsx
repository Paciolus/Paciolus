'use client'

import { useEffect } from 'react'
import { usePathname } from 'next/navigation'

/**
 * Route-based theme provider — "The Vault" architecture.
 *
 * Sets data-theme attribute on <html> based on current route:
 * - Dark theme (vault exterior): homepage, auth pages
 * - Light theme (vault interior): tool pages, engagements, settings, etc.
 *
 * NOT user-toggleable — theme is determined by route.
 */

const DARK_ROUTES = [
  '/',
  '/login',
  '/register',
  '/verify-email',
  '/verification-pending',
]

function isDarkRoute(pathname: string): boolean {
  return DARK_ROUTES.includes(pathname)
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  useEffect(() => {
    const theme = isDarkRoute(pathname) ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', theme)
  }, [pathname])

  return <>{children}</>
}
