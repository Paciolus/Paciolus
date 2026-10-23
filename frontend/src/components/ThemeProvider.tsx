'use client'

import { useEffect, type ReactElement } from 'react'
import { usePathname } from 'next/navigation'
import { resolveTheme } from '@/lib/theme-routes'

/**
 * Keeps `data-theme` correct across client-side navigations.
 *
 * Sprint 809 (finding D-1): this component used to be the *only* thing that
 * resolved the theme, and it did so in a `useEffect` after hydration. The root
 * layout server-rendered `data-theme="dark"` unconditionally, so every one of
 * the 49 light routes was served dark, painted dark, and flipped. The server
 * now resolves the theme from the pathname (see `app/layout.tsx`), which
 * removes the flash on first paint.
 *
 * This effect is still needed: an App Router client-side navigation does not
 * re-render the root layout, so the `<html>` attribute would keep the theme of
 * whichever route was server-rendered first. Both paths call the same
 * `resolveTheme`, so they cannot disagree — the route→theme map lives in
 * `lib/theme-routes.ts` and is asserted against the filesystem by
 * `theme-routes.test.ts` (finding D-4).
 */
export function ThemeProvider({ children }: { children: React.ReactNode }): ReactElement {
  const pathname = usePathname()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', resolveTheme(pathname))
  }, [pathname])

  return <>{children}</>
}
