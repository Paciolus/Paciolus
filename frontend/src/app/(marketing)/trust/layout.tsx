import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Trust & Security — How Paciolus Protects Your Data',
  description: 'Our security controls, exactly what we keep, and what we do not claim. Your uploaded files are processed in memory and not kept after analysis.',
  openGraph: {
    title: 'Trust & Security — How Paciolus Protects Your Data',
    description: 'How Paciolus handles your data, and exactly what it keeps.',
  },
}

export default function TrustLayout({ children }: { children: React.ReactNode }) {
  return children
}
