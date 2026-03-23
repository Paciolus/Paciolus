import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Trust & Security — How Paciolus Protects Your Data',
  description: 'Zero-storage architecture, enterprise-grade encryption, CSRF protection, and defense-in-depth security. Your financial data is never stored at rest.',
  openGraph: {
    title: 'Trust & Security — How Paciolus Protects Your Data',
    description: 'Zero-storage architecture, enterprise-grade encryption, and defense-in-depth security.',
  },
}

export default function TrustLayout({ children }: { children: React.ReactNode }) {
  return children
}
