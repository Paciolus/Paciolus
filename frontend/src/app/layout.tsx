import type { Metadata } from 'next'
import { headers } from 'next/headers'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
  title: 'Paciolus - Surgical Precision for Trial Balance Diagnostics',
  description: 'Financial Professionals: Eliminate sign errors and misclassifications with automated Close Health Reports. Zero-Storage processing ensures your client data never leaves memory.',
  icons: {
    icon: '/PaciolusLogo_LightBG.png',
    apple: '/PaciolusLogo_LightBG.png',
  },
  openGraph: {
    title: 'Paciolus - Surgical Precision for Trial Balance Diagnostics',
    description: 'Upload. Map. Export. Zero-Storage trial balance diagnostics for Financial Professionals.',
    type: 'website',
  },
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
  await headers()

  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
