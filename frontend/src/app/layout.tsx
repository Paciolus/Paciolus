import type { Metadata } from 'next'
import { Merriweather, Lato, JetBrains_Mono } from 'next/font/google'
import { headers } from 'next/headers'
import './globals.css'
import { resolveTheme } from '@/lib/theme-routes'
import { Providers } from './providers'

/**
 * Sprint 807 (findings C-1 / C-2): the three Oat & Obsidian families, self-hosted.
 *
 * `globals.css` used to open with
 * `@import url('https://fonts.googleapis.com/css2?...')`, which did three bad
 * things at once. It made Google LLC a processor of every visitor's IP address
 * and User-Agent on every page load, while the Data Processing Addendum commits
 * in writing to maintaining a list of subprocessors that did not mention them.
 * It needed two hosts in the CSP allowlist. And a CSS `@import` of a
 * third-party stylesheet is the slowest way to load a font: it blocks
 * stylesheet parsing, then needs DNS + TLS + two serial round trips to a second
 * origin before any text paints.
 *
 * `next/font/google` downloads the files at build time and serves them from our
 * own origin, so the disclosure problem is resolved by elimination rather than
 * by adding a row to the list. Sprint 703 planned exactly this and never
 * executed it.
 */
const merriweather = Merriweather({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-serif',
  display: 'swap',
})

const lato = Lato({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-sans',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Paciolus - Surgical Precision for Trial Balance Diagnostics',
  description: 'Financial Professionals: flags likely sign errors and misclassifications with automated Close Health Reports. Uploaded files are processed in memory and not kept after analysis.',
  icons: {
    icon: '/PaciolusLogo_LightBG.png',
    apple: '/PaciolusLogo_LightBG.png',
  },
  openGraph: {
    title: 'Paciolus - Surgical Precision for Trial Balance Diagnostics',
    description: 'Upload. Map. Export. Trial balance diagnostics for Financial Professionals.',
    type: 'website',
    url: 'https://paciolus.com',
    siteName: 'Paciolus',
    images: [
      {
        url: '/PaciolusLogo_LightBG.png',
        width: 800,
        height: 600,
        alt: 'Paciolus — Trial Balance Diagnostics',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Paciolus - Surgical Precision for Trial Balance Diagnostics',
    description: 'Upload. Map. Export. Trial balance diagnostics for Financial Professionals.',
    images: ['/PaciolusLogo_LightBG.png'],
  },
  metadataBase: new URL('https://paciolus.com'),
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Reading headers() forces dynamic rendering for the entire route tree.
  // This is required for nonce-based CSP: static pre-rendered pages cannot have
  // per-request nonces injected into their cached HTML, so all pages must render
  // dynamically so Next.js can inject the nonce from the proxy into inline scripts.
  const requestHeaders = await headers()

  // Sprint 809 (finding D-1): resolve the route's theme on the server so the
  // first paint is already correct. This used to be a hardcoded
  // `data-theme="dark"` corrected by a client effect after hydration, and 49 of
  // the 62 routes are light — every tool, engagement and settings page — so all
  // of them were served dark, painted dark, and flipped. Nothing softened it:
  // the `await headers()` above forces dynamic rendering, so there is no static
  // prerender to hide behind.
  //
  // `x-pathname` is set by `src/proxy.ts`. If it is ever absent the fallback is
  // the light default, which is the majority of routes and the less jarring
  // direction to be wrong in.
  const theme = resolveTheme(requestHeaders.get('x-pathname'))

  return (
    <html
      lang="en"
      data-theme={theme}
      className={`${merriweather.variable} ${lato.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
