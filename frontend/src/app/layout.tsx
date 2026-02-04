import type { Metadata } from 'next'
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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
