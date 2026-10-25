import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Trust & Security — How Paciolus Protects Your Data',
  description: 'TLS in transit, provider-managed encryption at rest, CSRF protection and layered security controls. Uploaded files are processed in memory and not kept; see exactly what we do keep.',
  openGraph: {
    title: 'Trust & Security — How Paciolus Protects Your Data',
    description: 'How Paciolus handles your data, and exactly what it keeps.',
  },
}

export default function TrustLayout({ children }: { children: React.ReactNode }) {
  return children
}
