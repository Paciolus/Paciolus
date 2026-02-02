import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CloseSignify - Audit-Ready Trial Balances in Seconds',
  description: 'Fractional CFOs: Eliminate sign errors and misclassifications with automated Close Health Reports.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  )
}
