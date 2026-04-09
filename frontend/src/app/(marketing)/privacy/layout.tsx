import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy — Paciolus',
  description: 'Privacy Policy for Paciolus. We use zero-storage architecture — your financial data is processed in-memory and never stored at rest.',
  openGraph: {
    title: 'Privacy Policy — Paciolus',
    description: 'We use zero-storage architecture — your financial data is never stored at rest.',
  },
}

export default function PrivacyLayout({ children }: { children: React.ReactNode }) {
  return children
}
